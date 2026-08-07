from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "validate_history_sanitization.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("history_sanitization_validator", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def run_validator(repo: Path, rev: str = "HEAD") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repo), "--rev", rev],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "history-test@example.invalid")
    git(repo, "config", "user.name", "history-test")
    return repo


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", ".")
    git(repo, "commit", "-qm", message)


def write_synthetic_appendix(repo: Path, validator) -> tuple[str, ...]:
    old = tuple(f"{index:x}" + "a" * 39 for index in range(1, 9))
    new = tuple(f"{index:x}" + "b" * 39 for index in range(1, 9))
    appendix = repo / validator.MIGRATION_APPENDIX
    appendix.parent.mkdir(parents=True)
    rows = ["| 旧 | 新 |", "|---|---|"]
    rows.extend(f"| {old_sha} | {new_sha} |" for old_sha, new_sha in zip(old, new))
    appendix.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return old


def test_current_repository_contract_passes() -> None:
    result = run_validator(ROOT)
    assert result.returncode == 0
    assert "HISTORY_SANITIZATION_POLICY_PASS" in result.stdout
    assert "OPERATIONAL_OLD_IDENTITY_FILE_COUNT=0" in result.stdout


def test_operational_old_identity_is_blocked(tmp_path: Path) -> None:
    validator = load_validator()
    repo = init_repo(tmp_path)
    old = write_synthetic_appendix(repo, validator)
    (repo / "current.md").write_text(
        f"current authority {old[0]}\n",
        encoding="utf-8",
    )
    commit_all(repo, "fixture")

    result = run_validator(repo)

    assert result.returncode == 1
    assert "HISTORY_SANITIZATION_POLICY_BLOCKED" in result.stdout
    assert "current.md" in result.stdout


def test_allowed_sealed_archive_may_preserve_old_identity(tmp_path: Path) -> None:
    validator = load_validator()
    repo = init_repo(tmp_path)
    old = write_synthetic_appendix(repo, validator)
    allowed = repo / next(path for path in validator.ALLOWED_HISTORICAL_PATHS if path != validator.MIGRATION_APPENDIX)
    allowed.parent.mkdir(parents=True, exist_ok=True)
    allowed.write_text(
        f"historical testimony {old[0]}\n",
        encoding="utf-8",
    )
    commit_all(repo, "fixture")

    result = run_validator(repo)

    assert result.returncode == 0
    assert "HISTORY_SANITIZATION_POLICY_PASS" in result.stdout


def test_standalone_old_prefix_is_blocked(tmp_path: Path) -> None:
    validator = load_validator()
    repo = init_repo(tmp_path)
    old = write_synthetic_appendix(repo, validator)
    prefix = old[0][:8]
    (repo / "current.md").write_text(f"old short identity {prefix}\n", encoding="utf-8")
    commit_all(repo, "fixture")

    result = run_validator(repo)

    assert result.returncode == 1
    assert "current.md" in result.stdout
