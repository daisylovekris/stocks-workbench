import importlib.util
import hashlib
import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "akshare_daily_quote_check_v0.1.py"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )


def test_off_benchmark_date_fails_closed_before_network() -> None:
    result = run_script("--date", "2026-07-13")

    assert result.returncode == 2
    assert "2026-07-06" in result.stdout
    assert "tools/generate_daily_facts.py" in result.stdout
    assert "\u672a\u53d1\u8d77\u4efb\u4f55\u8054\u7f51\u8bf7\u6c42" in result.stdout
    assert "\u8bf7\u66f4\u65b0 THS_BENCHMARK" not in result.stdout


def test_help_identifies_frozen_benchmark_and_production_entry() -> None:
    result = run_script("--help")

    assert result.returncode == 0
    assert "2026-07-06" in result.stdout
    assert "tools/generate_daily_facts.py" in result.stdout


def test_optional_facts_output_uses_shared_persistent_lock(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location("akshare_daily_quote_check", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    official = tmp_path / "300274_2026-07-06_facts.json"
    lock_dir = tmp_path / "locks"
    args = SimpleNamespace(symbol="300274", date="2026-07-06")
    facts, final_sha256 = module.write_facts_json(
        official,
        args=args,
        tencent_data={
            "开盘": 126.0,
            "最高": 131.9,
            "最低": 126.0,
            "收盘": 128.18,
            "涨跌幅": 1.6,
            "成交额": 67.81,
            "换手率": 3.29,
        },
        realtime_volume_ratio={"candidate_value": None},
        expected_sha256=None,
        lock_dir=lock_dir,
    )
    assert json.loads(official.read_text(encoding="utf-8")) == facts
    assert final_sha256 == module.ofl.sha256_file(official)
    assert list(lock_dir.glob("*.lock"))
    assert not list(tmp_path.glob("*.lock"))
    assert not [path for path in tmp_path.iterdir() if path.name.startswith(".300274_")]


def test_akshare_full_write_actions_observe_held_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = importlib.util.spec_from_file_location("akshare_daily_quote_check_lock_scope", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    official = tmp_path / "300274_2026-07-06_facts.json"
    lock_dir = tmp_path / "locks"
    args = SimpleNamespace(symbol="300274", date="2026-07-06")
    holder: dict[str, object] = {}
    events: list[str] = []
    real_lock = module.ofl.official_facts_lock

    @contextmanager
    def observed_lock(*lock_args, **lock_kwargs):
        with real_lock(*lock_args, **lock_kwargs) as state:
            holder["state"] = state
            events.append("lock_enter")
            yield state
            assert state.held
        events.append("lock_exit")

    def mark(name: str) -> None:
        state = holder.get("state")
        assert isinstance(state, module.ofl.OfficialFactsLockState) and state.held
        events.append(name)

    real_read = module.ofl.read_current_official
    real_sha = module.ofl.sha256_bytes
    real_parse = module.parse_existing_official_bytes
    real_build = module.build_facts_json
    real_validate = module.validate_facts_json_structure
    real_temp = module.tempfile.NamedTemporaryFile
    real_replace = module.os.replace

    def observed_read(*call_args, **call_kwargs):
        mark("read_official")
        return real_read(*call_args, **call_kwargs)

    def observed_sha(data):
        mark("sha256")
        return real_sha(data)

    def observed_parse(*call_args, **call_kwargs):
        mark("parse_official")
        return real_parse(*call_args, **call_kwargs)

    def observed_build(*call_args, **call_kwargs):
        mark("build_final")
        return real_build(*call_args, **call_kwargs)

    def observed_validate(*call_args, **call_kwargs):
        mark("structure_validator")
        return real_validate(*call_args, **call_kwargs)

    def observed_temp(*call_args, **call_kwargs):
        mark("temp_write")
        return real_temp(*call_args, **call_kwargs)

    def observed_replace(src, dst):
        mark("replace")
        return real_replace(src, dst)

    monkeypatch.setattr(module.ofl, "official_facts_lock", observed_lock)
    monkeypatch.setattr(module.ofl, "read_current_official", observed_read)
    monkeypatch.setattr(module.ofl, "sha256_bytes", observed_sha)
    monkeypatch.setattr(module, "parse_existing_official_bytes", observed_parse)
    monkeypatch.setattr(module, "build_facts_json", observed_build)
    monkeypatch.setattr(module, "validate_facts_json_structure", observed_validate)
    monkeypatch.setattr(module.tempfile, "NamedTemporaryFile", observed_temp)
    monkeypatch.setattr(module.os, "replace", observed_replace)

    _facts, final_sha = module.write_facts_json(
        official,
        args=args,
        tencent_data={
            "开盘": 126.0,
            "最高": 131.9,
            "最低": 126.0,
            "收盘": 128.18,
            "涨跌幅": 1.6,
            "成交额": 67.81,
            "换手率": 3.29,
        },
        realtime_volume_ratio={"candidate_value": None},
        expected_sha256=None,
        lock_dir=lock_dir,
    )
    assert final_sha == hashlib.sha256(official.read_bytes()).hexdigest()
    assert events[0] == "lock_enter" and events[-1] == "lock_exit"
    for required in (
        "read_official",
        "sha256",
        "parse_official",
        "build_final",
        "structure_validator",
        "temp_write",
        "replace",
    ):
        assert required in events
    replace_index = events.index("replace")
    assert "read_official" in events[replace_index + 1 :]
    assert "sha256" in events[replace_index + 1 :]
