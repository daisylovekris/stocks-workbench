from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "secret_scan.py"
ASSIGNMENT_PREFIX = "DEMO_" + "API_KEY="


def run_scanner(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "scanner-test@example.invalid")
    git(repo, "config", "user.name", "scanner-test")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    git(repo, "add", "base.txt")
    git(repo, "commit", "-qm", "base")
    return repo


def test_file_scan_blocks_synthetic_assignment_without_echoing_value(tmp_path: Path) -> None:
    secret = "abcdefghijklmnopqrstuvwx12345678"
    path = tmp_path / "bad.txt"
    path.write_text(ASSIGNMENT_PREFIX + secret + "\n", encoding="utf-8")

    result = run_scanner(tmp_path, "--files", str(path))

    assert result.returncode == 1
    assert "SECRET_SCAN_BLOCKED" in result.stdout
    assert "api_key_assignment" in result.stdout
    assert secret not in result.stdout


def test_file_scan_allows_environment_reference(tmp_path: Path) -> None:
    path = tmp_path / "env.txt"
    path.write_text(ASSIGNMENT_PREFIX + "${DEMO_API_KEY}\n", encoding="utf-8")

    result = run_scanner(tmp_path, "--files", str(path))

    assert result.returncode == 0
    assert result.stdout.strip() == "SECRET_SCAN_CLEAN"


def test_file_scan_allows_redaction_marker(tmp_path: Path) -> None:
    path = tmp_path / "redacted.txt"
    path.write_text(ASSIGNMENT_PREFIX + "***REDACTED***\n", encoding="utf-8")

    result = run_scanner(tmp_path, "--files", str(path))

    assert result.returncode == 0


def test_redaction_marker_does_not_allow_appended_secret(tmp_path: Path) -> None:
    secret = "abcdefghijklmnopqrstuvwx12345678"
    path = tmp_path / "bad-redacted.txt"
    path.write_text(ASSIGNMENT_PREFIX + "***REDACTED***" + secret + "\n", encoding="utf-8")

    result = run_scanner(tmp_path, "--files", str(path))

    assert result.returncode == 1
    assert secret not in result.stdout


def test_environment_reference_does_not_allow_appended_secret(tmp_path: Path) -> None:
    secret = "abcdefghijklmnopqrstuvwx12345678"
    path = tmp_path / "bad-env.txt"
    path.write_text(ASSIGNMENT_PREFIX + "${DEMO_API_KEY}" + secret + "\n", encoding="utf-8")

    result = run_scanner(tmp_path, "--files", str(path))

    assert result.returncode == 1
    assert secret not in result.stdout


def test_commit_scan_catches_add_then_delete_history(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base = git(repo, "rev-parse", "HEAD")
    secret = "abcdefghijklmnopqrstuvwx12345678"

    (repo / "leak.txt").write_text(ASSIGNMENT_PREFIX + secret + "\n", encoding="utf-8")
    git(repo, "add", "leak.txt")
    git(repo, "commit", "-qm", "add synthetic secret")
    (repo / "leak.txt").unlink()
    git(repo, "add", "-u")
    git(repo, "commit", "-qm", "remove synthetic secret")
    tip = git(repo, "rev-parse", "HEAD")

    result = run_scanner(repo, "--commits", f"{base}..{tip}")

    assert result.returncode == 1
    assert "SECRET_SCAN_BLOCKED" in result.stdout
    assert "leak.txt" in result.stdout
    assert secret not in result.stdout


def test_commit_scan_single_tip_covers_full_reachable_history(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    secret = "abcdefghijklmnopqrstuvwx12345678"
    (repo / "leak.txt").write_text(ASSIGNMENT_PREFIX + secret + "\n", encoding="utf-8")
    git(repo, "add", "leak.txt")
    git(repo, "commit", "-qm", "add synthetic secret")
    tip = git(repo, "rev-parse", "HEAD")

    result = run_scanner(repo, "--commits", tip)

    assert result.returncode == 1
    assert secret not in result.stdout


def test_staged_scan_ignores_deleted_secret_and_checks_new_blob(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    old_secret = "abcdefghijklmnopqrstuvwx12345678"
    path = repo / "tracked.txt"
    path.write_text(ASSIGNMENT_PREFIX + old_secret + "\n", encoding="utf-8")
    git(repo, "add", "tracked.txt")
    git(repo, "commit", "-qm", "fixture with synthetic secret")

    path.write_text(ASSIGNMENT_PREFIX + "${DEMO_API_KEY}\n", encoding="utf-8")
    git(repo, "add", "tracked.txt")
    clean = run_scanner(repo, "--staged")
    assert clean.returncode == 0

    new_secret = "zyxwvutsrqponmlkjihgfedcba987654"
    path.write_text(ASSIGNMENT_PREFIX + new_secret + "\n", encoding="utf-8")
    git(repo, "add", "tracked.txt")
    blocked = run_scanner(repo, "--staged")
    assert blocked.returncode == 1
    assert new_secret not in blocked.stdout
