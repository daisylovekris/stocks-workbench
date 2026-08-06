import copy
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from tools import review_manifest as phase_c
from tools import run_daily_facts_after_close as runner


def write_calendar(
    path: Path,
    *,
    trading_days: list[str] | None = None,
    coverage_start: str = "2026-07-01",
    coverage_end: str = "2026-07-31",
    timezone: str = "Asia/Shanghai",
) -> Path:
    payload = {
        "schema_version": "0.1",
        "timezone": timezone,
        "source": "pytest",
        "calendar_version": "pytest",
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "trading_days": trading_days
        or [
            "2026-07-13",
            "2026-07-14",
            "2026-07-15",
            "2026-07-16",
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_repository_calendar_repairs_2026_07_15_omission():
    calendar_path = runner.DEFAULT_CALENDAR
    payload = json.loads(calendar_path.read_text(encoding="utf-8"))
    days = payload["trading_days"]

    assert payload["coverage_start"] == "2026-07-01"
    assert payload["coverage_end"] == "2026-07-31"
    assert payload["timezone"] == "Asia/Shanghai"
    assert payload["source"] == "sse_szse_official_2026_holiday_notices_verified_2026-07-22"
    assert payload["calendar_version"] == "2026-07-phase-a-2026-07-15-omission-fix-v1"
    assert days == sorted(days)
    assert len(days) == len(set(days))
    index = days.index("2026-07-15")
    assert days[index - 1 : index + 2] == ["2026-07-14", "2026-07-15", "2026-07-16"]
    for weekend in (
        "2026-07-04",
        "2026-07-05",
        "2026-07-11",
        "2026-07-12",
        "2026-07-18",
        "2026-07-19",
        "2026-07-25",
        "2026-07-26",
    ):
        assert weekend not in days

    calendar = runner.load_calendar(calendar_path)
    for trading_day in (
        "2026-07-15",
        "2026-07-16",
        "2026-07-17",
        "2026-07-20",
        "2026-07-21",
        "2026-07-22",
    ):
        assert calendar.is_trading_day(runner.parse_trade_date(trading_day))
    assert not calendar.is_trading_day(runner.parse_trade_date("2026-07-19"))


def parse_args(tmp_path: Path, calendar: Path, *extra: str):
    argv = [
        "--dry-run",
        "--symbol",
        "300274",
        "--runtime-dir",
        str(tmp_path / "runtime"),
        "--calendar",
        str(calendar),
        *extra,
    ]
    return runner.build_parser().parse_args(argv)


def parse_write_args(tmp_path: Path, calendar: Path, *extra: str):
    argv = [
        "--write-official",
        "--symbol",
        "300274",
        "--runtime-dir",
        str(tmp_path / "runtime"),
        "--calendar",
        str(calendar),
        *extra,
    ]
    return runner.build_parser().parse_args(argv)


def install_temp_repo_root(monkeypatch, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "data" / "daily").mkdir(parents=True)
    monkeypatch.setattr(runner, "REPO_ROOT", repo)
    monkeypatch.setattr(runner.ofl, "DEFAULT_LOCK_DIR", repo / ".test-locks")
    return repo


def eligible_official_candidate(*, status: str = "success", source_date: str = "2026-07-16") -> dict:
    candidate = generator_object(status=status, source_date=source_date)
    candidate["quote_verification"]["status"] = "confirmed"
    candidate["volume_ratio"] = {
        "candidate_value": 1.2,
        "confirmed_value": 1.2,
        "verification": {
            "status": "manual_confirmed",
            "method": "legacy_manual_confirmation",
            "source_date": source_date,
        },
        "manual_verification": {
            "decided_by": "pytest",
            "decided_at": "2026-07-16T16:00:00Z",
            "source": "pytest",
            "reason": "controlled test fixture",
        },
    }
    candidate["needs_manual_check"] = {
        "volume_ratio": False,
        "market_indices": status == "partial",
        "sector_context": status == "partial",
        "disclosure_status": status == "partial",
        "news_policy_context": status == "partial",
    }
    candidate["missing"] = {
        "market_indices": None,
        "sector_context": None,
        "disclosure_status": None,
        "news_policy_context": None,
    }
    return candidate


def semantic_timestamp_pair(*, status: str = "success") -> tuple[dict, dict]:
    official = eligible_official_candidate(status=status)
    official["generated_at"] = "2026-07-16T08:00:00Z"
    official["quote_verification"]["fetched_at"] = "2026-07-16T08:00:01Z"
    official["run"]["fetched_at"] = "2026-07-16T08:00:02Z"
    official["volume_ratio"]["five_day_volume_check"] = {"fetched_at": "2026-07-16T08:00:03Z"}
    official["volume_ratio"]["snapshot_ohlc_check"] = {"fetched_at": "2026-07-16T08:00:04Z"}
    official["volume_ratio"]["verification"]["fetched_at"] = "2026-07-16T08:00:05Z"
    candidate = copy.deepcopy(official)
    candidate["generated_at"] = "2026-07-16T09:00:00Z"
    candidate["quote_verification"]["fetched_at"] = "2026-07-16T09:00:01Z"
    candidate["run"]["fetched_at"] = "2026-07-16T09:00:02Z"
    candidate["volume_ratio"]["five_day_volume_check"]["fetched_at"] = "2026-07-16T09:00:03Z"
    candidate["volume_ratio"]["snapshot_ohlc_check"]["fetched_at"] = "2026-07-16T09:00:04Z"
    candidate["volume_ratio"]["verification"]["fetched_at"] = "2026-07-16T09:00:05Z"
    return official, candidate


def historical_semantic_timestamp_pair() -> tuple[dict, dict]:
    """Replicate the 2026-07-27 official facts volume-ratio structure.

    The historical method carries exactly seven timestamp leaves and no
    ``snapshot_ohlc_check``: generated_at, quote_verification.fetched_at,
    run.fetched_at, volume_ratio.five_day_volume_check.fetched_at,
    volume_ratio.source_volume_checks.{sohu_history,tencent_history}.fetched_at,
    and volume_ratio.verification.fetched_at.
    """

    official = eligible_official_candidate(status="partial")
    official["trade_date"] = "2026-07-27"
    official["generated_at"] = "2026-08-02T20:20:20Z"
    official["quote_verification"]["source_date"] = "2026-07-27"
    official["quote_verification"]["fetched_at"] = "2026-08-02T20:20:19Z"
    official["run"]["fetched_at"] = "2026-08-02T20:20:19Z"
    trade_dates = [
        "2026-07-20",
        "2026-07-21",
        "2026-07-22",
        "2026-07-23",
        "2026-07-24",
        "2026-07-27",
    ]
    volumes = [659284.0, 670682.0, 847182.0, 930068.0, 550996.0, 407188.0]
    six_day = {
        "status": "passed",
        "trade_dates": trade_dates,
        "volumes": volumes,
        "target_volume": 407188.0,
        "calculated_value": 0.56,
        "expected_value": 0.56,
        "tolerance": 0.01,
        "formula": "target_day_volume / mean(prior_5_trading_day_volume)",
    }
    official["volume_ratio"] = {
        "candidate_value": 0.56,
        "confirmed_value": 0.56,
        "source": "sohu_five_day_volume+tencent_five_day_volume",
        "cross_check": {
            "value": 0.56,
            "source": "tencent_five_day_volume_derived",
            "source_date": "2026-07-27",
            "formula": "target_day_volume / mean(prior_5_trading_day_volume)",
            "tolerance": 0.01,
            "delta": 0.0,
        },
        "five_day_volume_check": {
            **six_day,
            "source": "tencent_history",
            "fetched_at": "2026-08-02T20:20:20Z",
        },
        "source_volume_checks": {
            "sohu_history": {
                **six_day,
                "source": "sohu_history",
                "fetched_at": "2026-08-02T20:20:20Z",
            },
            "tencent_history": {
                **six_day,
                "source": "tencent_history",
                "fetched_at": "2026-08-02T20:20:20Z",
            },
        },
        "verification": {
            "status": "confirmed",
            "method": "historical_five_day_volume_cross_check",
            "confirmed_by": "automation_cross_check",
            "source": "sohu_five_day_volume+tencent_five_day_volume",
            "source_date": "2026-07-27",
            "fetched_at": "2026-08-02T20:20:20Z",
            "notes": (
                "historical volume ratio confirmed from Sohu and Tencent daily volume; "
                "amount-based ratios are not accepted"
            ),
            "error_type": None,
            "error_message": None,
        },
    }
    candidate = copy.deepcopy(official)
    candidate["generated_at"] = "2026-08-02T22:09:19Z"
    candidate["quote_verification"]["fetched_at"] = "2026-08-02T22:09:18Z"
    candidate["run"]["fetched_at"] = "2026-08-02T22:09:18Z"
    candidate["volume_ratio"]["five_day_volume_check"]["fetched_at"] = "2026-08-02T22:09:19Z"
    candidate["volume_ratio"]["source_volume_checks"]["sohu_history"]["fetched_at"] = "2026-08-02T22:09:19Z"
    candidate["volume_ratio"]["source_volume_checks"]["tencent_history"]["fetched_at"] = "2026-08-02T22:09:19Z"
    candidate["volume_ratio"]["verification"]["fetched_at"] = "2026-08-02T22:09:19Z"
    return official, candidate


def historical_calendar(path: Path) -> Path:
    return write_calendar(
        path,
        trading_days=[
            "2026-07-20",
            "2026-07-21",
            "2026-07-22",
            "2026-07-23",
            "2026-07-24",
            "2026-07-27",
        ],
    )


SAME_DAY_TIMESTAMP_PATHS = [
    "generated_at",
    "quote_verification.fetched_at",
    "run.fetched_at",
    "volume_ratio.five_day_volume_check.fetched_at",
    "volume_ratio.snapshot_ohlc_check.fetched_at",
    "volume_ratio.verification.fetched_at",
]


def same_day_facts_pair_07_24() -> tuple[dict, dict]:
    """Real same-day facts pair derived from the tracked 2026-07-24 official file.

    The tracked file carries ``verification.method =
    same_day_snapshot_plus_sohu_five_day_cross_check`` and exactly the six
    same-day profile timestamp paths.
    """

    official = json.loads(Path("data/daily/300274_2026-07-24_facts.json").read_text(encoding="utf-8"))
    candidate = copy.deepcopy(official)
    for path in SAME_DAY_TIMESTAMP_PATHS:
        current = candidate
        parts = path.split(".")
        for part in parts[:-1]:
            current = current[part]
        current[parts[-1]] = "2026-08-03T00:00:00Z"
    return official, candidate


def same_day_calendar(path: Path) -> Path:
    return write_calendar(
        path,
        trading_days=[
            "2026-07-17",
            "2026-07-20",
            "2026-07-21",
            "2026-07-22",
            "2026-07-23",
            "2026-07-24",
        ],
    )


HISTORICAL_TIMESTAMP_PATHS = [
    "generated_at",
    "quote_verification.fetched_at",
    "run.fetched_at",
    "volume_ratio.five_day_volume_check.fetched_at",
    "volume_ratio.source_volume_checks.sohu_history.fetched_at",
    "volume_ratio.source_volume_checks.tencent_history.fetched_at",
    "volume_ratio.verification.fetched_at",
]


def set_json_path(payload: dict, path: str, value) -> None:
    current = payload
    parts = path.split(".")
    for part in parts[:-1]:
        current = current[part]
    current[parts[-1]] = value


def delete_json_path(payload: dict, path: str) -> None:
    current = payload
    parts = path.split(".")
    for part in parts[:-1]:
        current = current[part]
    del current[parts[-1]]


def marker_for(candidate: dict) -> str:
    return runner.CANDIDATE_STDOUT_MARKER + json.dumps(candidate, ensure_ascii=False, separators=(",", ":"))


def generator_object(
    *,
    status: str = "success",
    source_date: str = "2026-07-16",
    trade_date: str | None = None,
    symbol: str = "300274",
) -> dict:
    return {
        "schema_version": "facts_pack_v0.2",
        "trade_date": trade_date or source_date,
        "symbol": symbol,
        "quote": {
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.0,
            "prev_close": 100.0,
            "pct_change": 1.0,
            "amount": 123456.0,
            "turnover_rate": 1.2,
        },
        "quote_verification": {"source_date": source_date},
        "run": {"status": status},
        "volume_ratio": {},
        "missing": {},
        "needs_manual_check": {},
    }


def generator_payload(**overrides) -> str:
    payload = generator_object(**overrides)
    return runner.CANDIDATE_STDOUT_MARKER + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def patch_generator(monkeypatch, *, returncode: int = 0, stdout: str | None = None, stderr: str = ""):
    calls = []

    def fake_run(command):
        calls.append(command)
        return subprocess.CompletedProcess(
            command,
            returncode,
            stdout=stdout if stdout is not None else generator_payload(),
            stderr=stderr,
        )

    monkeypatch.setattr(runner, "run_generator", fake_run)
    return calls


def patch_validator(monkeypatch, *, status: str = "passed"):
    def fake_validator(candidate, candidate_path, target_date):  # noqa: ARG001
        if status == "failed":
            return {"status": "failed", "exception_type": "ValueError", "message": "facts-pack validator failed"}
        return {"status": "passed"}

    monkeypatch.setattr(runner, "validator_summary", fake_validator)


def patch_official_validator(monkeypatch, *, status: str = "passed"):
    def fake_official_validator(candidate, *, official_path, target_date, validator=None):  # noqa: ARG001
        if status == "failed":
            return {"status": "failed", "exception_type": "ValueError", "message": "official validator failed"}
        return {"status": "passed"}

    monkeypatch.setattr(runner.oft, "_validator_summary", fake_official_validator)


def load_manifest(manifest: dict) -> dict:
    return json.loads(Path(manifest["manifest_path"]).read_text(encoding="utf-8"))


def write_run_manifest(
    path: Path,
    *,
    run_id: str,
    symbol: str = "300274",
    mode: str = "today_after_close",
    target_date: str = "2026-07-16",
    dry_run: bool = True,
    outcome: str = "needs_manual_review",
    finished_at: str = "2026-07-16T15:30:00+08:00",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "symbol": symbol,
                "mode": mode,
                "target_date": target_date,
                "dry_run": dry_run,
                "outcome": outcome,
                "finished_at": finished_at,
            }
        ),
        encoding="utf-8",
    )


def test_normal_trading_day_after_close_runs_generator_dry_run(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_validator(monkeypatch)
    calls = patch_generator(monkeypatch)

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    )

    saved = load_manifest(manifest)
    assert code == 0
    assert saved["outcome"] == "success"
    assert saved["reason_code"] is None
    assert saved["dry_run"] is True
    assert "--dry-run" in calls[0]
    assert "--emit-runner-marker" in calls[0]
    assert not str(saved["candidate_path"]).startswith(str(runner.REPO_ROOT / "data" / "daily"))
    assert Path(saved["candidate_path"]).exists()


def test_repository_calendar_2026_07_15_today_after_close_and_manifest_hash(tmp_path, monkeypatch):
    calendar = runner.DEFAULT_CALENDAR
    patch_validator(monkeypatch)
    calls = patch_generator(monkeypatch, stdout=generator_payload(source_date="2026-07-15"))

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-15T15:25:00+08:00")
    )

    saved = load_manifest(manifest)
    assert code == 0
    assert saved["outcome"] == "success"
    assert saved["reason_code"] is None
    assert saved["calendar"]["sha256"] == runner.sha256_bytes(calendar.read_bytes())
    assert saved["calendar"]["version"] == "2026-07-phase-a-2026-07-15-omission-fix-v1"
    assert len(calls) == 1


def test_repository_calendar_2026_07_19_remains_non_trading_day(tmp_path, monkeypatch):
    calendar = runner.DEFAULT_CALENDAR
    calls = patch_generator(monkeypatch)

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-19T15:25:00+08:00")
    )

    assert code == 0
    assert load_manifest(manifest)["reason_code"] == "non_trading_day"
    assert calls == []


def test_trading_day_before_close_skips(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    calls = patch_generator(monkeypatch)

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:19:00+08:00")
    )

    assert code == 0
    saved = load_manifest(manifest)
    assert saved["reason_code"] == "before_close"
    assert saved["stage"] == "finished"
    assert saved["last_stage"] == "gate"
    assert calls == []


@pytest.mark.parametrize(
    ("now", "reason"),
    [
        ("2026-07-18T15:25:00+08:00", "non_trading_day"),
        ("2026-07-19T15:25:00+08:00", "non_trading_day"),
    ],
)
def test_non_trading_days_skip(tmp_path, monkeypatch, now, reason):
    calendar = write_calendar(tmp_path / "calendar.json")
    calls = patch_generator(monkeypatch)

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", now))

    assert code == 0
    assert load_manifest(manifest)["reason_code"] == reason
    assert calls == []


def test_calendar_uncovered_skips(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    calls = patch_generator(monkeypatch)

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-08-03T15:25:00+08:00")
    )

    assert code == 0
    assert load_manifest(manifest)["reason_code"] == "calendar_uncovered"
    assert calls == []


def test_missing_calendar_fails_closed(tmp_path):
    args = parse_args(tmp_path, tmp_path / "missing.json", "--now", "2026-07-16T15:25:00+08:00")

    code, manifest = runner.execute(args)

    assert code == 1
    assert manifest["reason_code"] == "calendar_invalid"


def test_broken_calendar_json_fails_closed(tmp_path):
    calendar = tmp_path / "calendar.json"
    calendar.write_text("{broken", encoding="utf-8")

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    )

    assert code == 1
    assert manifest["reason_code"] == "calendar_invalid"


@pytest.mark.parametrize(
    "days",
    [
        ["2026-07-13", "2026-07-13", "2026-07-16"],
        ["2026-07-16", "2026-07-14"],
    ],
)
def test_calendar_duplicate_or_unsorted_dates_fail_closed(tmp_path, days):
    calendar = write_calendar(tmp_path / "calendar.json", trading_days=days)

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    )

    assert code == 1
    assert manifest["reason_code"] == "calendar_invalid"


def test_calendar_wrong_timezone_fails_closed(tmp_path):
    calendar = write_calendar(tmp_path / "calendar.json", timezone="UTC")

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    )

    assert code == 1
    assert manifest["reason_code"] == "calendar_invalid"


def test_historical_backfill_requires_reason(tmp_path):
    calendar = write_calendar(tmp_path / "calendar.json")

    code, manifest = runner.execute(
        parse_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-14",
            "--now",
            "2026-07-16T10:00:00+08:00",
        )
    )

    assert code == 1
    saved = load_manifest(manifest)
    assert saved["reason_code"] == "calendar_invalid"
    assert saved["target_date"] == "2026-07-14"


def test_historical_backfill_non_trading_day_skips(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    calls = patch_generator(monkeypatch)

    code, manifest = runner.execute(
        parse_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-19",
            "--reason",
            "manual replay",
            "--now",
            "2026-07-16T10:00:00+08:00",
        )
    )

    assert code == 0
    assert load_manifest(manifest)["reason_code"] == "non_trading_day"
    assert calls == []


def test_repository_calendar_historical_backfill_2026_07_15_passes_trading_day_gate(tmp_path, monkeypatch):
    calendar = runner.DEFAULT_CALENDAR
    patch_validator(monkeypatch)
    calls = patch_generator(monkeypatch, stdout=generator_payload(source_date="2026-07-15"))

    code, manifest = runner.execute(
        parse_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-15",
            "--reason",
            "verified calendar omission repair",
            "--now",
            "2026-07-16T10:00:00+08:00",
        )
    )

    saved = load_manifest(manifest)
    assert code == 0
    assert saved["target_date"] == "2026-07-15"
    assert saved["outcome"] == "success"
    assert saved["reason_code"] is None
    assert len(calls) == 1


def test_generator_partial_creates_alert_and_needs_manual_review(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_validator(monkeypatch)
    patch_generator(monkeypatch, returncode=2, stdout=generator_payload(status="partial"))

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    )

    saved = load_manifest(manifest)
    assert code == 2
    assert saved["outcome"] == "needs_manual_review"
    assert saved["reason_code"] == "generator_partial"
    assert saved["alerts"]
    assert Path(saved["alerts"][0]).exists()


def test_generator_nonzero_exit_fails(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_generator(monkeypatch, returncode=4, stdout="null")

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    )

    saved = load_manifest(manifest)
    assert code == 1
    assert saved["reason_code"] == "stdout_candidate_missing"


def test_source_date_mismatch_fails(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_validator(monkeypatch)
    patch_generator(monkeypatch, stdout=generator_payload(source_date="2026-07-14"))

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    )

    assert code == 1
    assert load_manifest(manifest)["reason_code"] == "source_date_mismatch"


def test_validator_failure_fails(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_validator(monkeypatch, status="failed")
    patch_generator(monkeypatch)

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    )

    saved = load_manifest(manifest)
    assert code == 1
    assert saved["reason_code"] == "validator_failed"


def test_same_symbol_date_mode_runner_lock_blocks_second_instance(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    args = parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    target_date = runner.parse_trade_date("2026-07-16")
    ctx = runner.build_context(args, tmp_path / "runtime", target_date, "today_after_close")
    patch_generator(monkeypatch)

    with runner.runner_lock(ctx) as acquired:
        assert acquired
        code, manifest = runner.execute(args)

    assert code == 0
    assert load_manifest(manifest)["reason_code"] == "runner_already_active"


def test_existing_formal_success_record_skips_already_completed(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    runtime = tmp_path / "runtime"
    previous = runtime / "runs" / "2026-07-16" / "old" / "manifest.json"
    write_run_manifest(previous, run_id="old", dry_run=False, outcome="success")
    calls = patch_generator(monkeypatch)

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    )

    assert code == 0
    assert load_manifest(manifest)["outcome"] == "success"
    assert calls


def test_previous_partial_record_allows_rerun_and_records_previous_run_id(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    runtime = tmp_path / "runtime"
    previous = runtime / "runs" / "2026-07-16" / "old" / "manifest.json"
    write_run_manifest(previous, run_id="old")
    patch_validator(monkeypatch)
    patch_generator(monkeypatch)

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    )

    saved = load_manifest(manifest)
    assert code == 0
    assert saved["outcome"] == "success"
    assert saved["previous_run_id"] == "old"


def test_sealed_facts_exists_skips(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official = repo / "data" / "daily" / "300274_2026-07-16_facts.json"
    official.write_text(json.dumps({"sealed": True}), encoding="utf-8")
    calls = patch_generator(monkeypatch)

    code, manifest = runner.execute(
        parse_args(
            tmp_path,
            calendar,
            "--now",
            "2026-07-16T15:25:00+08:00",
        )
    )

    assert code == 0
    assert load_manifest(manifest)["reason_code"] == "sealed_exists"
    assert calls == []


def test_runtime_directory_not_writable_fails_closed(tmp_path):
    calendar = write_calendar(tmp_path / "calendar.json")
    args = runner.build_parser().parse_args(
        [
            "--dry-run",
            "--runtime-dir",
            "/dev/null",
            "--calendar",
            str(calendar),
            "--now",
            "2026-07-16T15:25:00+08:00",
        ]
    )

    code, manifest = runner.execute(args)

    assert code == 1
    assert manifest["reason_code"] == "manifest_write_failed"
    assert manifest["manifest_path"] is None


def test_summary_write_failure_leaves_failed_manifest_not_success(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_validator(monkeypatch)
    patch_generator(monkeypatch)
    original_build_context = runner.build_context

    def context_with_summary_collision(args, runtime_dir, target_date, mode):
        ctx = original_build_context(args, runtime_dir, target_date, mode)
        ctx.summary_path.mkdir(parents=True)
        return ctx

    monkeypatch.setattr(runner, "build_context", context_with_summary_collision)

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    )

    assert code == 1
    assert manifest["reason_code"] == "manifest_write_failed"
    saved = load_manifest(manifest)
    assert saved["outcome"] == "failed"
    assert saved["reason_code"] == "manifest_write_failed"


def test_stdout_and_stderr_are_sanitized(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_validator(monkeypatch)
    patch_generator(
        monkeypatch,
        stdout=generator_payload() + "\n",
        stderr="Authorization: Bearer secret-token\nCookie: session=abc\nsk-secretSECRET123456",
    )

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    )

    assert code == 0
    stderr = Path(load_manifest(manifest)["generator"]["stderr_path"]).read_text(encoding="utf-8")
    assert "secret-token" not in stderr
    assert "session=abc" not in stderr
    assert "sk-secretSECRET123456" not in stderr
    assert "[REDACTED]" in stderr


def test_dry_run_artifacts_stay_outside_data_daily(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_validator(monkeypatch)
    patch_generator(monkeypatch)

    code, manifest = runner.execute(
        parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    )

    saved = load_manifest(manifest)
    assert code == 0
    assert runner.REPO_ROOT / "data" / "daily" not in Path(saved["candidate_path"]).parents
    assert runner.REPO_ROOT / "logs" not in Path(saved["manifest_path"]).parents if "manifest_path" in saved else True


def test_main_without_dry_run_is_rejected(tmp_path, capsys):
    calendar = write_calendar(tmp_path / "calendar.json")

    with pytest.raises(SystemExit) as exc:
        runner.main(
            [
                "--runtime-dir",
                str(tmp_path / "runtime"),
                "--calendar",
                str(calendar),
                "--now",
                "2026-07-16T15:25:00+08:00",
            ]
        )

    assert exc.value.code == 2
    assert "one of the arguments --dry-run --write-official is required" in capsys.readouterr().err


def test_cli_rejects_dry_run_and_write_official_together(tmp_path, capsys):
    calendar = write_calendar(tmp_path / "calendar.json")

    with pytest.raises(SystemExit) as exc:
        runner.main(
            [
                "--dry-run",
                "--write-official",
                "--runtime-dir",
                str(tmp_path / "runtime"),
                "--calendar",
                str(calendar),
            ]
        )

    assert exc.value.code == 2
    assert "not allowed with argument" in capsys.readouterr().err


def git_status_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=runner.REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.splitlines()


def repository_file_set() -> set[str]:
    return {
        str(path.relative_to(runner.REPO_ROOT))
        for path in runner.REPO_ROOT.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(runner.REPO_ROOT).parts
    }


@pytest.mark.parametrize("relative", [".", "data/daily", "logs", "sungrow/reviews", "not-created/runtime"])
def test_cli_runtime_inside_repository_is_rejected_without_writes(relative, capsys):
    target = runner.REPO_ROOT if relative == "." else runner.REPO_ROOT / relative
    before_files = repository_file_set()
    before_status = git_status_paths()

    code = runner.main(["--dry-run", "--runtime-dir", str(target)])

    output = json.loads(capsys.readouterr().err)
    assert code == 1
    assert output["reason_code"] == "runtime_inside_repository"
    assert output["manifest"] is None
    assert repository_file_set() == before_files
    assert git_status_paths() == before_status
    if relative == "not-created/runtime":
        assert not target.exists()


def test_environment_runtime_inside_repository_is_rejected(monkeypatch):
    monkeypatch.setenv("STOCKS_RUNTIME_DIR", str(runner.REPO_ROOT / "logs"))
    args = runner.build_parser().parse_args(["--dry-run"])

    with pytest.raises(runner.RunnerError) as exc:
        runner.execute(args)

    assert exc.value.reason_code == "runtime_inside_repository"


def test_runtime_symlink_resolving_into_repository_is_rejected(tmp_path):
    link = tmp_path / "repo-link"
    link.symlink_to(runner.REPO_ROOT, target_is_directory=True)
    args = runner.build_parser().parse_args(["--dry-run", "--runtime-dir", str(link / "logs")])

    with pytest.raises(runner.RunnerError) as exc:
        runner.execute(args)

    assert exc.value.reason_code == "runtime_inside_repository"


@pytest.mark.parametrize(
    ("overrides", "expected_previous", "expected_diagnostic"),
    [
        ({"symbol": "600000"}, None, True),
        ({"mode": "historical_backfill"}, None, True),
        ({"target_date": "2026-07-14"}, None, False),
    ],
)
def test_previous_runs_do_not_cross_task_identity(
    tmp_path, overrides, expected_previous, expected_diagnostic
):
    runtime = tmp_path / "runtime"
    manifest_date = overrides.get("target_date", "2026-07-16")
    path = runtime / "runs" / manifest_date / "other" / "manifest.json"
    write_run_manifest(path, run_id="other", dry_run=False, outcome="success", **overrides)

    reason, previous, diagnostics = runner.scan_previous_runs(
        runtime,
        runner.parse_trade_date("2026-07-16"),
        symbol="300274",
        mode="today_after_close",
    )

    assert reason is None
    assert previous is expected_previous
    assert bool(diagnostics) is expected_diagnostic
    if expected_diagnostic:
        assert diagnostics == [
            {"path": str(path), "reason": "completion invalid: completion_identity_mismatch"}
        ]


def test_previous_runs_choose_latest_matching_and_skip_corrupt(tmp_path):
    runtime = tmp_path / "runtime"
    base = runtime / "runs" / "2026-07-16"
    write_run_manifest(base / "old" / "manifest.json", run_id="old", finished_at="2026-07-16T15:21:00+08:00")
    corrupt = base / "middle" / "manifest.json"
    corrupt.parent.mkdir(parents=True)
    corrupt.write_text("{broken", encoding="utf-8")
    write_run_manifest(base / "new" / "manifest.json", run_id="new", finished_at="2026-07-16T15:40:00+08:00")
    write_run_manifest(
        base / "dry-success" / "manifest.json",
        run_id="dry-success",
        dry_run=True,
        outcome="success",
        finished_at="2026-07-16T15:35:00+08:00",
    )

    reason, previous, diagnostics = runner.scan_previous_runs(
        runtime,
        runner.parse_trade_date("2026-07-16"),
        symbol="300274",
        mode="today_after_close",
    )

    assert reason is None
    assert previous == "new"
    assert len(diagnostics) == 4
    assert diagnostics[0]["path"] == str(corrupt)
    assert diagnostics[0]["reason"] == "invalid manifest skipped: JSONDecodeError"
    assert all(
        item["reason"] == "completion invalid: completion_schema_invalid"
        for item in diagnostics[1:]
    )


def test_corrupt_previous_manifest_diagnostic_is_persisted(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    runtime = tmp_path / "runtime"
    corrupt = runtime / "runs" / "2026-07-16" / "corrupt" / "manifest.json"
    corrupt.parent.mkdir(parents=True)
    corrupt.write_text("{broken", encoding="utf-8")
    patch_generator(monkeypatch)
    patch_validator(monkeypatch)

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    saved = load_manifest(manifest)
    assert code == 0
    assert saved["previous_run_id"] is None
    assert saved["scan_diagnostics"] == [
        {"path": str(corrupt), "reason": "invalid manifest skipped: JSONDecodeError"}
    ]


def test_matching_formal_success_completes_but_previous_is_latest_record(tmp_path):
    runtime = tmp_path / "runtime"
    base = runtime / "runs" / "2026-07-16"
    write_run_manifest(
        base / "formal" / "manifest.json",
        run_id="formal",
        dry_run=False,
        outcome="success",
        finished_at="2026-07-16T15:25:00+08:00",
    )
    write_run_manifest(base / "later" / "manifest.json", run_id="later", finished_at="2026-07-16T15:45:00+08:00")

    reason, previous, _ = runner.scan_previous_runs(
        runtime,
        runner.parse_trade_date("2026-07-16"),
        symbol="300274",
        mode="today_after_close",
    )

    assert reason is None
    assert previous == "later"


def test_write_official_with_now_is_rejected(tmp_path):
    calendar = write_calendar(tmp_path / "calendar.json")
    args = parse_write_args(
        tmp_path,
        calendar,
        "--mode",
        "historical_backfill",
        "--date",
        "2026-07-16",
        "--reason",
        "controlled replay",
        "--now",
        "2026-07-16T15:25:00+08:00",
    )

    with pytest.raises(runner.RunnerError) as exc:
        runner.execute(args)

    assert exc.value.reason_code == "invalid_now"


def test_write_official_success_candidate_creates_canonical_official(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate()
    calls = patch_generator(monkeypatch, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled replay",
        )
    )

    saved = load_manifest(manifest)
    official = repo / "data" / "daily" / "300274_2026-07-16_facts.json"
    assert code == 0
    assert saved["dry_run"] is False
    assert saved["write_official"] is True
    assert saved["write_action"] == "created"
    assert saved["reason_code"] == "official_written"
    assert saved["official_path"] == str(official)
    assert official.exists()
    assert saved["official_sha256_after"] == runner.sha256_bytes(official.read_bytes())
    assert Path(saved["candidate_path"]).read_bytes() == official.read_bytes()

    rerun_code, rerun_manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled replay",
        )
    )
    assert rerun_code == 0
    assert load_manifest(rerun_manifest)["reason_code"] == "already_completed"
    assert len(calls) == 1


def test_write_official_partial_whitelist_creates_partial_not_success(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate(status="partial")
    candidate["volume_ratio"]["verification"]["status"] = "derived_confirmed"
    candidate["volume_ratio"]["verification"]["method"] = "historical_five_day_volume_cross_check"
    candidate["volume_ratio"].pop("manual_verification", None)
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))
    patch_validator(monkeypatch)
    patch_official_validator(monkeypatch)

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled partial replay",
        )
    )

    saved = load_manifest(manifest)
    assert code == 0
    assert saved["outcome"] == "partial"
    assert saved["needs_manual_review"] is True
    assert saved["reason_code"] == "official_written_partial"
    assert saved["write_action"] == "created"
    assert saved["partial_write_policy"]["eligible"] is True
    assert saved["partial_write_policy"]["needs_manual_review"] is True


def test_write_official_partial_manual_confirmed_volume_ratio_is_not_eligible(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate(status="partial")
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))
    patch_official_validator(monkeypatch)
    monkeypatch.setattr(
        runner.oft,
        "promote_candidate_to_official",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("official transaction must not run")),
    )

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled partial replay",
        )
    )

    saved = load_manifest(manifest)
    assert code == 2
    assert saved["outcome"] == "needs_manual_review"
    assert saved["reason_code"] == "partial_not_eligible_for_official"
    assert saved["write_action"] == "not_eligible"
    assert saved["partial_write_policy"]["eligible"] is False
    assert not (repo / "data" / "daily" / "300274_2026-07-16_facts.json").exists()


def test_write_official_partial_volume_ratio_candidate_is_not_eligible(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate(status="partial")
    candidate["volume_ratio"].pop("confirmed_value")
    candidate["volume_ratio"]["verification"]["status"] = "candidate"
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled partial replay",
        )
    )

    saved = load_manifest(manifest)
    assert code == 2
    assert saved["outcome"] == "needs_manual_review"
    assert saved["reason_code"] == "partial_not_eligible_for_official"
    assert saved["write_action"] == "not_eligible"
    assert not (repo / "data" / "daily" / "300274_2026-07-16_facts.json").exists()


def test_write_official_existing_identical_is_noop_and_completed(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate()
    official = repo / "data" / "daily" / "300274_2026-07-16_facts.json"
    official.write_bytes(runner._json_payload(candidate))
    before = official.read_bytes()
    before_sha = runner.sha256_bytes(before)
    calls = patch_generator(monkeypatch, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled replay",
        )
    )

    saved = load_manifest(manifest)
    assert code == 0
    assert saved["write_action"] == "identical_noop"
    assert saved["reason_code"] == "official_already_identical"
    assert saved["official_changed"] is False
    assert saved["official_bytes_equal_candidate"] is True
    assert saved["official_sha256_before"] == before_sha
    assert saved["official_sha256_after"] == before_sha
    assert saved["comparison"] is None
    assert official.read_bytes() == before
    assert runner.sha256_bytes(official.read_bytes()) == before_sha

    rerun_code, rerun_manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled replay",
        )
    )
    assert rerun_code == 0
    assert load_manifest(rerun_manifest)["reason_code"] == "already_completed"
    assert len(calls) == 1


def test_write_official_same_day_profile_semantic_noop(tmp_path, monkeypatch):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    before = official.read_bytes()
    before_sha = runner.sha256_bytes(before)
    calls = patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))

    args = parse_write_args(
        tmp_path,
        calendar,
        "--mode",
        "historical_backfill",
        "--date",
        "2026-07-24",
        "--reason",
        "controlled replay",
    )
    code, manifest = runner.execute(args)

    saved = load_manifest(manifest)
    comparison = saved["comparison"]
    assert code == 0
    assert saved["write_action"] == "semantic_noop"
    assert saved["outcome"] == "official_unchanged"
    assert saved["reason_code"] == "official_semantically_identical"
    assert saved["official_changed"] is False
    assert saved["official_bytes_equal_candidate"] is False
    assert official.read_bytes() == before
    profile_config = runner.oft.load_method_profile_config()
    assert comparison["comparison_mode"] == runner.oft.SEMANTIC_COMPARISON_V3_MODE
    assert comparison["profile_version"] == profile_config.profile_version
    assert comparison["profile_sha256"] == profile_config.sha256
    assert comparison["verification_method"] == "same_day_snapshot_plus_sohu_five_day_cross_check"
    assert comparison["required_paths"] == SAME_DAY_TIMESTAMP_PATHS
    assert comparison["optional_paths"] == []
    assert comparison["candidate_discovered_paths"] == SAME_DAY_TIMESTAMP_PATHS
    assert comparison["official_discovered_paths"] == SAME_DAY_TIMESTAMP_PATHS
    assert comparison["candidate_missing_required_paths"] == []
    assert comparison["official_missing_required_paths"] == []
    assert comparison["candidate_extra_paths"] == []
    assert comparison["official_extra_paths"] == []
    assert comparison["all_values_valid_timezone_datetime"] is True
    assert comparison["candidate_raw_sha256"] != comparison["official_raw_sha256"]
    assert comparison["candidate_semantic_sha256"] == comparison["official_semantic_sha256"]
    assert comparison["semantic_equal"] is True
    assert runner.sha256_bytes(official.read_bytes()) == before_sha
    assert len(calls) == 1

    rerun_code, rerun_manifest = runner.execute(args)
    rerun_saved = load_manifest(rerun_manifest)
    assert rerun_code == 0
    assert rerun_saved["outcome"] == "skipped"
    assert rerun_saved["reason_code"] == "already_completed"
    assert rerun_saved["previous_run_id"] == saved["run_id"]
    assert len(calls) == 1
    assert official.read_bytes() == before
    assert runner.sha256_bytes(official.read_bytes()) == before_sha


def _mutate_semantic_completion(case, saved, official):
    manifest_path = Path(saved["manifest_path"])
    candidate_path = Path(saved["candidate_path"])
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if case == "outcome_failed":
        payload["outcome"] = "failed"
    elif case == "bundle_failed":
        payload["manifest_bundle_failed"] = True
    elif case == "manifest_write_failed":
        payload["outcome"] = "failed"
        payload["reason_code"] = "manifest_write_failed"
        payload["manifest_bundle_failed"] = True
    elif case == "forged_reason":
        payload["reason_code"] = "forged_reason"
    elif case == "comparison_missing":
        payload["comparison"] = None
    elif case == "candidate_path_missing":
        payload["candidate_path"] = None
    elif case == "candidate_path_escape":
        payload["candidate_path"] = str(candidate_path.parent.parent / "candidate.json")
    elif case == "candidate_deleted":
        candidate_path.unlink()
    elif case == "candidate_symlink":
        outside = candidate_path.parent.parent.parent / "outside-candidate.json"
        outside.write_bytes(candidate_path.read_bytes())
        candidate_path.unlink()
        candidate_path.symlink_to(outside)
    elif case == "candidate_tampered":
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate["quote"]["close"] += 1
        candidate_path.write_text(json.dumps(candidate, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    elif case == "official_changed_true":
        payload["official_changed"] = True
    elif case == "before_after_differ":
        payload["official_sha256_before"] = "0" * 64
    elif case == "after_sha_wrong":
        payload["official_sha256_before"] = "0" * 64
        payload["official_sha256_after"] = "0" * 64
        payload["comparison"]["official_raw_sha256"] = "0" * 64
    elif case == "raw_sha_same":
        candidate_path.write_bytes(official.read_bytes())
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        official_payload = json.loads(official.read_text(encoding="utf-8"))
        candidate_sha = runner.sha256_bytes(candidate_path.read_bytes())
        payload["candidate_sha256"] = candidate_sha
        payload["comparison"] = runner.oft.build_semantic_comparison(
            candidate=candidate,
            official=official_payload,
            candidate_bytes=candidate_path.read_bytes(),
            official_bytes=official.read_bytes(),
            symbol="300274",
            target_date="2026-07-24",
        )
    elif case == "semantic_sha_differ":
        payload["comparison"]["candidate_semantic_sha256"] = "0" * 64
    elif case == "excluded_paths_missing":
        payload["comparison"]["candidate_discovered_paths"] = payload["comparison"]["candidate_discovered_paths"][:-1]
    elif case == "excluded_paths_extra":
        payload["comparison"]["candidate_discovered_paths"].append("quote.close")
    elif case == "excluded_paths_order":
        payload["comparison"]["candidate_discovered_paths"] = list(
            reversed(payload["comparison"]["candidate_discovered_paths"])
        )
    elif case == "excluded_paths_content":
        payload["comparison"]["candidate_discovered_paths"][0] = "quote.close"
    elif case == "profile_sha256_tampered":
        payload["comparison"]["profile_sha256"] = "0" * 64
    elif case == "verification_method_tampered":
        payload["comparison"]["verification_method"] = "historical_five_day_volume_cross_check"
    elif case == "stage_running":
        payload["stage"] = "running"
    elif case == "write_official_false":
        payload["write_official"] = False
    elif case == "dry_run_true":
        payload["dry_run"] = True
    elif case == "identity_symbol":
        payload["symbol"] = "600000"
    elif case == "identity_date":
        payload["target_date"] = "2026-07-15"
    elif case == "identity_mode":
        payload["mode"] = "today_after_close"
    elif case == "identity_run_id":
        payload["run_id"] = str(uuid.uuid4())
    else:
        raise AssertionError(f"unknown completion corruption: {case}")
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    "case",
    [
        "outcome_failed",
        "bundle_failed",
        "manifest_write_failed",
        "forged_reason",
        "comparison_missing",
        "candidate_path_missing",
        "candidate_path_escape",
        "candidate_deleted",
        "candidate_symlink",
        "candidate_tampered",
        "official_changed_true",
        "before_after_differ",
        "after_sha_wrong",
        "raw_sha_same",
        "semantic_sha_differ",
        "excluded_paths_missing",
        "excluded_paths_extra",
        "excluded_paths_order",
        "excluded_paths_content",
        "profile_sha256_tampered",
        "verification_method_tampered",
        "stage_running",
        "write_official_false",
        "dry_run_true",
        "identity_symbol",
        "identity_date",
        "identity_mode",
        "identity_run_id",
    ],
)
def test_invalid_semantic_completion_is_diagnosed_and_generator_reruns(tmp_path, monkeypatch, case):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    protected_official = official.read_bytes()
    calls = patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))
    args = parse_write_args(
        tmp_path,
        calendar,
        "--mode",
        "historical_backfill",
        "--date",
        "2026-07-24",
        "--reason",
        "completion corruption regression",
    )
    first_code, first_manifest = runner.execute(args)
    first = load_manifest(first_manifest)
    assert first_code == 0
    assert first["write_action"] == "semantic_noop"

    _mutate_semantic_completion(case, first, official)
    rerun_code, rerun_manifest = runner.execute(args)
    rerun = load_manifest(rerun_manifest)

    assert rerun_code == 0
    assert rerun["reason_code"] != "already_completed"
    assert len(calls) == 2
    assert any(
        item["path"] == first["manifest_path"] and item["reason"].startswith("completion invalid:")
        for item in rerun["scan_diagnostics"]
    )
    assert official.read_bytes() == protected_official


def test_semantic_noop_bundle_failure_rerun_converges(tmp_path, monkeypatch):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    protected_official = official.read_bytes()
    calls = patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))
    original_build_context = runner.build_context
    build_count = 0

    def collide_first_summary(args, runtime_dir, target_date, mode):
        nonlocal build_count
        ctx = original_build_context(args, runtime_dir, target_date, mode)
        build_count += 1
        if build_count == 1:
            ctx.summary_path.mkdir(parents=True)
        return ctx

    monkeypatch.setattr(runner, "build_context", collide_first_summary)
    args = parse_write_args(
        tmp_path,
        calendar,
        "--mode",
        "historical_backfill",
        "--date",
        "2026-07-24",
        "--reason",
        "bundle failure convergence",
    )

    first_code, first_manifest = runner.execute(args)
    first = load_manifest(first_manifest)
    assert first_code == 1
    assert first["write_action"] == "semantic_noop"
    assert first["outcome"] == "failed"
    assert first["reason_code"] == "manifest_write_failed"
    assert first["manifest_bundle_failed"] is True

    failed_review = phase_c.generate_review(
        phase_c.ReviewOptions(
            runtime_dir=tmp_path / "phase-c-failed-bundle",
            runner_runtime_dir=tmp_path / "runtime",
            symbol="300274",
            trade_date="2026-07-24",
            runner_manifest_path=Path(first["manifest_path"]),
            repo_root=repo,
            official_lock_dir=tmp_path / "phase-c-failed-locks",
            now=lambda: datetime(2026, 7, 24, 16, 31, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
    )
    failed_review_payload = json.loads(failed_review.manifest_path.read_text(encoding="utf-8"))
    assert failed_review_payload["artifact_type"] == "incident_review"
    assert failed_review_payload["review_state"] == "needs_manual_review"

    rerun_code, rerun_manifest = runner.execute(args)
    rerun = load_manifest(rerun_manifest)
    assert rerun_code == 0
    assert rerun["write_action"] == "semantic_noop"
    assert rerun["reason_code"] == "official_semantically_identical"
    assert any(
        item["path"] == first["manifest_path"] and item["reason"] == "completion invalid: completion_outcome_failed"
        for item in rerun["scan_diagnostics"]
    )
    assert len(calls) == 2
    assert official.read_bytes() == protected_official


def test_completion_scan_runs_while_runner_lock_is_held(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_validator(monkeypatch)
    patch_generator(monkeypatch)
    original_scan = runner.scan_previous_runs
    observed = []

    def assert_locked(runtime_dir, target_date, **kwargs):
        probe_args = parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
        probe = runner.build_context(probe_args, runtime_dir, target_date, kwargs["mode"])
        with runner.runner_lock(probe) as acquired:
            observed.append(acquired)
        return original_scan(runtime_dir, target_date, **kwargs)

    monkeypatch.setattr(runner, "scan_previous_runs", assert_locked)
    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    assert code == 0
    assert load_manifest(manifest)["outcome"] == "success"
    assert observed == [False]


def test_phase_b_semantic_noop_manifest_is_accepted_by_phase_c_with_real_validator(tmp_path, monkeypatch):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    before = official.read_bytes()
    before_sha = runner.sha256_bytes(before)
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-24",
            "--reason",
            "cross-stage semantic noop integration",
        )
    )
    saved = load_manifest(manifest)
    assert code == 0, {
        key: saved.get(key)
        for key in ("outcome", "reason_code", "write_action", "validator", "official_validator_before", "exception")
    }
    assert saved["write_action"] == "semantic_noop"
    assert phase_c.oft.build_semantic_comparison is runner.oft.build_semantic_comparison

    result = phase_c.generate_review(
        phase_c.ReviewOptions(
            runtime_dir=tmp_path / "phase-c-runtime",
            runner_runtime_dir=tmp_path / "runtime",
            symbol="300274",
            trade_date="2026-07-24",
            runner_manifest_path=Path(saved["manifest_path"]),
            repo_root=repo,
            official_lock_dir=tmp_path / "phase-c-locks",
            now=lambda: datetime(2026, 7, 24, 16, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
    )
    review = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert result.status == "review_created"
    assert review["artifact_type"] == "facts_review"
    assert review["write_action"] == "semantic_noop"
    assert review["evidence_summary"]["semantic_comparison"] == saved["comparison"]
    assert official.read_bytes() == before
    assert runner.sha256_bytes(official.read_bytes()) == before_sha


def test_write_official_schema_version_difference_is_not_semantic_noop(tmp_path, monkeypatch):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official_payload["schema_version"] = "facts_pack_v0.1"
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    before = official.read_bytes()
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-24",
            "--reason",
            "schema mismatch replay",
        )
    )
    saved = load_manifest(manifest)
    assert code == 2
    assert saved["write_action"] == "conflict_blocked"
    assert saved["comparison"]["semantic_equal"] is False
    assert official.read_bytes() == before


@pytest.mark.parametrize("side", ["candidate", "official"])
@pytest.mark.parametrize("path", runner.oft.SEMANTIC_NOOP_EXCLUDED_JSON_PATHS)
def test_write_official_any_approved_timestamp_without_timezone_is_rejected(
    tmp_path,
    monkeypatch,
    side,
    path,
):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    target = candidate if side == "candidate" else official_payload
    set_json_path(target, path, "2026-07-16T09:00:00")
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    before = official.read_bytes()
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-24",
            "--reason",
            "timezone rejection replay",
        )
    )
    saved = load_manifest(manifest)
    assert code == 2
    assert saved["write_action"] == "conflict_blocked"
    assert saved["comparison"]["all_values_valid_timezone_datetime"] is False
    assert official.read_bytes() == before


@pytest.mark.parametrize(
    "path",
    [
        "missing.market_indices",
        "needs_manual_check.market_indices",
        "volume_ratio.candidate_value",
    ],
)
def test_write_official_deleted_business_field_is_conflict(tmp_path, monkeypatch, path):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    parent, key = path.rsplit(".", 1)
    current = candidate
    for part in parent.split("."):
        current = current[part]
    del current[key]
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    before = official.read_bytes()
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-24",
            "--reason",
            "business field deletion replay",
        )
    )
    saved = load_manifest(manifest)
    assert code == 2
    assert saved["write_action"] == "conflict_blocked"
    assert saved["comparison"]["candidate_semantic_sha256"] != saved["comparison"]["official_semantic_sha256"]
    assert saved["comparison"]["semantic_equal"] is False
    assert official.read_bytes() == before


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("quote.high", 999.0),
        ("quote.amount", 999999.0),
        ("quote.turnover_rate", 9.9),
        ("name", "changed official name"),
        ("missing.market_indices", "changed"),
        ("needs_manual_check.market_indices", False),
    ],
)
def test_write_official_business_change_remains_conflict(tmp_path, monkeypatch, path, value):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    set_json_path(candidate, path, value)
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    before = official.read_bytes()
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-24",
            "--reason",
            "controlled replay",
        )
    )

    saved = load_manifest(manifest)
    assert code == 2
    assert saved["write_action"] == "conflict_blocked"
    assert saved["reason_code"] == "official_conflict"
    assert saved["comparison"]["candidate_semantic_sha256"] != saved["comparison"]["official_semantic_sha256"]
    assert saved["comparison"]["semantic_equal"] is False
    assert official.read_bytes() == before


def test_write_official_unknown_field_remains_conflict(tmp_path, monkeypatch):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    candidate["unknown_business_field"] = "must-not-be-ignored"
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-24",
            "--reason",
            "controlled replay",
        )
    )
    assert code == 2
    assert load_manifest(manifest)["write_action"] == "conflict_blocked"


@pytest.mark.parametrize(
    ("mutation", "expected_check"),
    [
        ("candidate_timestamp_leaf_missing", "candidate_missing_required_paths"),
        ("candidate_extra_timestamp_leaf", "candidate_extra_paths"),
        ("timestamp_wrong_type", "all_values_valid_timezone_datetime"),
        ("timestamp_invalid", "all_values_valid_timezone_datetime"),
    ],
)
def test_write_official_invalid_semantic_evidence_remains_conflict(
    tmp_path,
    monkeypatch,
    mutation,
    expected_check,
):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    if mutation == "candidate_timestamp_leaf_missing":
        del candidate["volume_ratio"]["snapshot_ohlc_check"]["fetched_at"]
    elif mutation == "candidate_extra_timestamp_leaf":
        candidate["volume_ratio"]["extra_check"] = {"fetched_at": "2026-07-16T09:00:06Z"}
    elif mutation == "timestamp_wrong_type":
        candidate["run"]["fetched_at"] = 123
    elif mutation == "timestamp_invalid":
        candidate["generated_at"] = "not-a-timestamp"
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-24",
            "--reason",
            "controlled replay",
        )
    )
    saved = load_manifest(manifest)
    assert code == 2
    assert saved["write_action"] == "conflict_blocked"
    assert saved["comparison"]["semantic_equal"] is False
    if expected_check == "all_values_valid_timezone_datetime":
        assert saved["comparison"][expected_check] is False
    else:
        assert len(saved["comparison"][expected_check]) > 0


def test_historical_semantic_noop_07_27_structure(tmp_path, monkeypatch):
    calendar = historical_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = historical_semantic_timestamp_pair()
    official = repo / "data" / "daily" / "300274_2026-07-27_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    before = official.read_bytes()
    calls = patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))
    args = parse_write_args(
        tmp_path,
        calendar,
        "--mode",
        "historical_backfill",
        "--date",
        "2026-07-27",
        "--reason",
        "historical semantic noop replay",
    )

    code, manifest = runner.execute(args)

    saved = load_manifest(manifest)
    comparison = saved["comparison"]
    assert code == 0
    assert saved["write_action"] == "semantic_noop"
    assert saved["reason_code"] == "official_semantically_identical"
    assert official.read_bytes() == before
    assert "snapshot_ohlc_check" not in candidate["volume_ratio"]
    profile_config = runner.oft.load_method_profile_config()
    assert comparison["comparison_mode"] == runner.oft.SEMANTIC_COMPARISON_V3_MODE
    assert comparison["profile_version"] == profile_config.profile_version
    assert comparison["profile_sha256"] == profile_config.sha256
    assert comparison["verification_method"] == "historical_five_day_volume_cross_check"
    assert comparison["required_paths"] == HISTORICAL_TIMESTAMP_PATHS
    assert comparison["optional_paths"] == []
    assert comparison["candidate_discovered_paths"] == HISTORICAL_TIMESTAMP_PATHS
    assert comparison["official_discovered_paths"] == HISTORICAL_TIMESTAMP_PATHS
    assert comparison["candidate_missing_required_paths"] == []
    assert comparison["official_missing_required_paths"] == []
    assert comparison["candidate_extra_paths"] == []
    assert comparison["official_extra_paths"] == []
    assert comparison["all_values_valid_timezone_datetime"] is True
    assert comparison["candidate_semantic_sha256"] == comparison["official_semantic_sha256"]
    assert comparison["semantic_equal"] is True
    assert len(calls) == 1


def test_symmetric_extra_timestamp_leaf_is_blocked_by_v3(tmp_path, monkeypatch):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official_payload["volume_ratio"]["extra_check"] = {"fetched_at": "2026-07-24T08:00:06Z"}
    candidate["volume_ratio"]["extra_check"] = {"fetched_at": "2026-07-24T09:00:06Z"}
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    before = official.read_bytes()
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-24",
            "--reason",
            "symmetric extra timestamp replay",
        )
    )
    saved = load_manifest(manifest)
    comparison = saved["comparison"]
    assert code == 2
    assert saved["write_action"] == "conflict_blocked"
    assert comparison["semantic_equal"] is False
    assert comparison["candidate_semantic_sha256"] is None
    assert "volume_ratio.extra_check.fetched_at" in comparison["candidate_extra_paths"]
    assert "volume_ratio.extra_check.fetched_at" in comparison["official_extra_paths"]
    assert official.read_bytes() == before


def test_historical_semantic_noop_accepted_by_phase_c(tmp_path, monkeypatch):
    calendar = historical_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = historical_semantic_timestamp_pair()
    official = repo / "data" / "daily" / "300274_2026-07-27_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    before = official.read_bytes()
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-27",
            "--reason",
            "cross-stage historical semantic noop",
        )
    )
    saved = load_manifest(manifest)
    assert code == 0
    assert saved["write_action"] == "semantic_noop"

    result = phase_c.generate_review(
        phase_c.ReviewOptions(
            runtime_dir=tmp_path / "phase-c-runtime",
            runner_runtime_dir=tmp_path / "runtime",
            symbol="300274",
            trade_date="2026-07-27",
            runner_manifest_path=Path(saved["manifest_path"]),
            repo_root=repo,
            official_lock_dir=tmp_path / "phase-c-locks",
            now=lambda: datetime(2026, 8, 2, 16, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
    )
    review = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert result.status == "review_created"
    assert review["artifact_type"] == "facts_review"
    assert review["write_action"] == "semantic_noop"
    assert review["evidence_summary"]["semantic_comparison"] == saved["comparison"]
    assert official.read_bytes() == before


def test_v1_legacy_phase_b_manifest_still_completes(tmp_path, monkeypatch):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    before = official.read_bytes()
    calls = patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))
    args = parse_write_args(
        tmp_path,
        calendar,
        "--mode",
        "historical_backfill",
        "--date",
        "2026-07-24",
        "--reason",
        "v1 legacy replay",
    )

    code, manifest = runner.execute(args)
    saved = load_manifest(manifest)
    assert code == 0
    assert saved["write_action"] == "semantic_noop"

    manifest_path = Path(saved["manifest_path"])
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidate_bytes = Path(payload["candidate_path"]).read_bytes()
    official_bytes = official.read_bytes()
    payload["comparison"] = runner.oft.build_semantic_comparison(
        candidate=json.loads(candidate_bytes.decode("utf-8")),
        official=json.loads(official_bytes.decode("utf-8")),
        candidate_bytes=candidate_bytes,
        official_bytes=official_bytes,
        symbol="300274",
        target_date="2026-07-24",
        comparison_mode=runner.oft.SEMANTIC_COMPARISON_V1_MODE,
    )
    assert payload["comparison"]["comparison_mode"] == runner.oft.SEMANTIC_COMPARISON_V1_MODE
    assert payload["comparison"]["semantic_equal"] is True
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rerun_code, rerun_manifest = runner.execute(args)
    rerun = load_manifest(rerun_manifest)
    assert rerun_code == 0
    assert rerun["reason_code"] == "already_completed"
    assert len(calls) == 1
    assert official.read_bytes() == before


def test_v1_legacy_phase_b_manifest_tampered_rejected(tmp_path, monkeypatch):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    calls = patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))
    args = parse_write_args(
        tmp_path,
        calendar,
        "--mode",
        "historical_backfill",
        "--date",
        "2026-07-24",
        "--reason",
        "v1 legacy tamper replay",
    )

    code, manifest = runner.execute(args)
    saved = load_manifest(manifest)
    assert code == 0
    assert saved["write_action"] == "semantic_noop"

    manifest_path = Path(saved["manifest_path"])
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["comparison"] = runner.oft.build_semantic_comparison(
        candidate=json.loads(Path(payload["candidate_path"]).read_bytes().decode("utf-8")),
        official=json.loads(official.read_bytes().decode("utf-8")),
        candidate_bytes=Path(payload["candidate_path"]).read_bytes(),
        official_bytes=official.read_bytes(),
        symbol="300274",
        target_date="2026-07-24",
        comparison_mode=runner.oft.SEMANTIC_COMPARISON_V1_MODE,
    )
    payload["comparison"]["candidate_semantic_sha256"] = "0" * 64
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rerun_code, rerun_manifest = runner.execute(args)
    rerun = load_manifest(rerun_manifest)
    assert rerun_code == 0
    assert rerun["reason_code"] != "already_completed"
    assert len(calls) == 2
    assert any(
        item["path"] == saved["manifest_path"] and item["reason"].startswith("completion invalid:")
        for item in rerun["scan_diagnostics"]
    )


def test_v2_legacy_phase_b_manifest_still_completes(tmp_path, monkeypatch):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    before = official.read_bytes()
    calls = patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))
    args = parse_write_args(
        tmp_path,
        calendar,
        "--mode",
        "historical_backfill",
        "--date",
        "2026-07-24",
        "--reason",
        "v2 legacy replay",
    )

    code, manifest = runner.execute(args)
    saved = load_manifest(manifest)
    assert code == 0
    assert saved["write_action"] == "semantic_noop"

    manifest_path = Path(saved["manifest_path"])
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidate_bytes = Path(payload["candidate_path"]).read_bytes()
    official_bytes = official.read_bytes()
    payload["comparison"] = runner.oft.build_semantic_comparison(
        candidate=json.loads(candidate_bytes.decode("utf-8")),
        official=json.loads(official_bytes.decode("utf-8")),
        candidate_bytes=candidate_bytes,
        official_bytes=official_bytes,
        symbol="300274",
        target_date="2026-07-24",
        comparison_mode=runner.oft.SEMANTIC_COMPARISON_V2_MODE,
    )
    assert payload["comparison"]["comparison_mode"] == runner.oft.SEMANTIC_COMPARISON_V2_MODE
    assert payload["comparison"]["semantic_equal"] is True
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rerun_code, rerun_manifest = runner.execute(args)
    rerun = load_manifest(rerun_manifest)
    assert rerun_code == 0
    assert rerun["reason_code"] == "already_completed"
    assert len(calls) == 1
    assert official.read_bytes() == before


def test_v2_phase_b_manifest_tampered_rejected(tmp_path, monkeypatch):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    calls = patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))
    args = parse_write_args(
        tmp_path,
        calendar,
        "--mode",
        "historical_backfill",
        "--date",
        "2026-07-24",
        "--reason",
        "v2 tamper replay",
    )

    code, manifest = runner.execute(args)
    saved = load_manifest(manifest)
    assert code == 0
    assert saved["write_action"] == "semantic_noop"

    manifest_path = Path(saved["manifest_path"])
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidate_bytes = Path(payload["candidate_path"]).read_bytes()
    official_bytes = official.read_bytes()
    payload["comparison"] = runner.oft.build_semantic_comparison(
        candidate=json.loads(candidate_bytes.decode("utf-8")),
        official=json.loads(official_bytes.decode("utf-8")),
        candidate_bytes=candidate_bytes,
        official_bytes=official_bytes,
        symbol="300274",
        target_date="2026-07-24",
        comparison_mode=runner.oft.SEMANTIC_COMPARISON_V2_MODE,
    )
    assert payload["comparison"]["comparison_mode"] == runner.oft.SEMANTIC_COMPARISON_V2_MODE
    payload["comparison"]["excluded_json_paths"] = list(
        reversed(payload["comparison"]["excluded_json_paths"])
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rerun_code, rerun_manifest = runner.execute(args)
    rerun = load_manifest(rerun_manifest)
    assert rerun_code == 0
    assert rerun["reason_code"] != "already_completed"
    assert len(calls) == 2
    assert any(
        item["path"] == saved["manifest_path"] and item["reason"].startswith("completion invalid:")
        for item in rerun["scan_diagnostics"]
    )


REQUIRED_TIMESTAMP_PATHS = [
    "generated_at",
    "quote_verification.fetched_at",
    "run.fetched_at",
    "volume_ratio.five_day_volume_check.fetched_at",
    "volume_ratio.verification.fetched_at",
]


@pytest.mark.parametrize("side", ["candidate", "official", "both"])
@pytest.mark.parametrize("required_path", REQUIRED_TIMESTAMP_PATHS)
def test_required_timestamp_path_deletion_blocks_semantic_noop(
    tmp_path,
    monkeypatch,
    side,
    required_path,
):
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    if side in {"candidate", "both"}:
        delete_json_path(candidate, required_path)
    if side in {"official", "both"}:
        delete_json_path(official_payload, required_path)
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    before = official.read_bytes()
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-24",
            "--reason",
            "required path deletion replay",
        )
    )

    saved = load_manifest(manifest)
    comparison = saved["comparison"]
    expected_candidate_missing = [required_path] if side in {"candidate", "both"} else []
    expected_official_missing = [required_path] if side in {"official", "both"} else []
    assert code == 2
    assert saved["write_action"] == "conflict_blocked"
    assert saved["reason_code"] == "official_conflict"
    assert comparison["semantic_equal"] is False
    assert comparison["candidate_semantic_sha256"] is None
    assert comparison["official_semantic_sha256"] is None
    assert comparison["candidate_missing_required_paths"] == expected_candidate_missing
    assert comparison["official_missing_required_paths"] == expected_official_missing
    assert official.read_bytes() == before


def _v3_pair_from_real_facts(day: str) -> tuple[dict, dict]:
    official = json.loads(Path(f"data/daily/300274_{day}_facts.json").read_text(encoding="utf-8"))
    candidate = copy.deepcopy(official)
    for path in runner.oft.discover_timestamp_leaf_paths(official):
        current = candidate
        parts = path.split(".")
        for part in parts[:-1]:
            current = current[part]
        current[parts[-1]] = "2026-08-03T00:00:00Z"
    return official, candidate


def _v3_compare(
    official: dict,
    candidate: dict,
    *,
    registry_path: Path | None = None,
    profile_version: str | None = None,
) -> dict:
    official_bytes = json.dumps(official, ensure_ascii=False, sort_keys=True).encode("utf-8")
    candidate_bytes = json.dumps(candidate, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return runner.oft.build_semantic_comparison(
        candidate=candidate,
        official=official,
        candidate_bytes=candidate_bytes,
        official_bytes=official_bytes,
        symbol="300274",
        target_date=str(official["trade_date"]),
        profile_version=profile_version,
        registry_path=registry_path,
    )


def test_archived_profile_legal_paths():
    official, candidate = _v3_pair_from_real_facts("2026-07-14")
    comparison = _v3_compare(official, candidate)
    assert comparison["verification_method"] == "archived_tencent_snapshot_plus_sohu_historical_reverification"
    assert comparison["semantic_equal"] is True
    assert comparison["candidate_missing_required_paths"] == []
    assert comparison["official_missing_required_paths"] == []
    assert comparison["candidate_extra_paths"] == []
    assert comparison["official_extra_paths"] == []
    assert comparison["all_values_valid_timezone_datetime"] is True


def test_legacy_manual_profile_is_fail_closed_blocked():
    official, candidate = _v3_pair_from_real_facts("2026-07-24")
    for payload in (official, candidate):
        payload["volume_ratio"]["verification"]["method"] = "legacy_manual_confirmation"
    comparison = _v3_compare(official, candidate)
    assert comparison["verification_method"] == "legacy_manual_confirmation"
    assert comparison["semantic_equal"] is False
    assert comparison["candidate_semantic_sha256"] is None
    assert comparison["official_semantic_sha256"] is None


def test_unknown_method_profile_is_fail_closed():
    official, candidate = _v3_pair_from_real_facts("2026-07-24")
    for payload in (official, candidate):
        payload["volume_ratio"]["verification"]["method"] = "unregistered_method"
    comparison = _v3_compare(official, candidate)
    assert comparison["verification_method"] == "unregistered_method"
    assert comparison["semantic_equal"] is False
    assert comparison["candidate_semantic_sha256"] is None


def test_profile_missing_is_fail_closed():
    official, candidate = _v3_pair_from_real_facts("2026-07-24")
    for payload in (official, candidate):
        payload["volume_ratio"]["verification"]["method"] = "method_without_profile"
    comparison = _v3_compare(official, candidate)
    assert comparison["verification_method"] == "method_without_profile"
    assert comparison["semantic_equal"] is False
    assert comparison["candidate_semantic_sha256"] is None


def test_method_mismatch_is_fail_closed():
    official, candidate = _v3_pair_from_real_facts("2026-07-24")
    candidate["volume_ratio"]["verification"]["method"] = "historical_five_day_volume_cross_check"
    comparison = _v3_compare(official, candidate)
    assert comparison["semantic_equal"] is False
    assert comparison["candidate_semantic_sha256"] is None
    assert comparison["official_semantic_sha256"] is None


def test_list_index_timestamp_path_is_fail_closed():
    official, candidate = _v3_pair_from_real_facts("2026-07-24")
    for payload in (official, candidate):
        payload["run"]["events"] = [{"fetched_at": "2026-08-03T00:00:00Z"}]
    comparison = _v3_compare(official, candidate)
    assert comparison["semantic_equal"] is False
    assert comparison["candidate_semantic_sha256"] is None
    assert comparison["official_semantic_sha256"] is None


def install_temp_profile_env(
    monkeypatch,
    tmp_path: Path,
    *,
    versions: tuple[str, ...] = ("v0.3",),
    active: str = "v0.3",
    config_mutator=None,
    registry_mutator=None,
) -> Path:
    """Install a temp rules/ registry with simulated profile versions."""

    rules_dir = tmp_path / "rules"
    rules_dir.mkdir(parents=True)
    base = json.loads(Path("rules/semantic_noop_timestamp_profiles_v0.3.json").read_text(encoding="utf-8"))
    entries = {}
    for version in versions:
        config = copy.deepcopy(base)
        config["profile_version"] = version
        if config_mutator:
            config_mutator(config, version)
        config_path = rules_dir / f"profiles_{version}.json"
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        canonical = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        entries[version] = {
            "path": f"rules/profiles_{version}.json",
            "comparison_mode": "method_profile_timestamp_paths_v3",
            "profile_sha256": hashlib.sha256(canonical).hexdigest(),
            "status": "active" if version == active else "frozen",
        }
    registry = {
        "schema_version": "semantic_noop_timestamp_profile_registry_v0.1",
        "active_profile_version": active,
        "profiles": entries,
    }
    if registry_mutator:
        registry_mutator(registry)
    registry_path = rules_dir / "registry.json"
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr(runner.oft, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(runner.oft, "METHOD_PROFILE_REGISTRY_PATH", registry_path)
    return registry_path


def test_optional_path_single_side_appearance_is_fail_closed(tmp_path, monkeypatch):
    def config_mutator(config, version):
        profile = config["profiles"]["same_day_snapshot_plus_sohu_five_day_cross_check"]
        profile["optional_paths"] = ["volume_ratio.extra_check.fetched_at"]
        profile["optional_presence_conditions"] = {
            "volume_ratio.extra_check.fetched_at": {"present_when_parent": "volume_ratio"}
        }

    install_temp_profile_env(monkeypatch, tmp_path, config_mutator=config_mutator)
    official, candidate = _v3_pair_from_real_facts("2026-07-24")
    candidate["volume_ratio"]["extra_check"] = {"fetched_at": "2026-08-03T00:00:01Z"}
    official["volume_ratio"]["extra_check"] = {"fetched_at": "2026-08-03T00:00:02Z"}

    both_present = _v3_compare(official, candidate)
    assert both_present["semantic_equal"] is True

    del official["volume_ratio"]["extra_check"]
    single_side = _v3_compare(official, candidate)
    assert single_side["semantic_equal"] is False
    assert single_side["candidate_semantic_sha256"] is None


def test_method_profile_config_validates_and_hashes():
    config = runner.oft.load_method_profile_config()
    assert config.comparison_mode == runner.oft.SEMANTIC_COMPARISON_V3_MODE
    assert config.profile_version == "v0.3"
    assert set(config.common_required_paths) == set(REQUIRED_TIMESTAMP_PATHS)
    assert len(config.profiles) == 4
    assert config.profiles["legacy_manual_confirmation"]["profile_status"] == "blocked"
    assert config.sha256 == "11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1"


def test_v03_active_new_write_uses_v03():
    registry = runner.oft.load_method_profile_registry()
    assert registry.active_profile_version == "v0.3"
    assert registry.entries["v0.3"].status == "active"
    assert registry.entries["v0.3"].profile_sha256 == "11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1"
    config, entry = runner.oft.active_method_profile_config()
    assert config.profile_version == "v0.3"
    assert entry.status == "active"


def test_v03_frozen_history_recomputable_and_active_switch_preserves_history(tmp_path, monkeypatch):
    install_temp_profile_env(monkeypatch, tmp_path, versions=("v0.3", "v0.4"), active="v0.3")
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    before = official.read_bytes()
    calls = patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))
    args = parse_write_args(
        tmp_path,
        calendar,
        "--mode",
        "historical_backfill",
        "--date",
        "2026-07-24",
        "--reason",
        "registry history replay",
    )

    code, manifest = runner.execute(args)
    saved = load_manifest(manifest)
    assert code == 0
    assert saved["write_action"] == "semantic_noop"
    assert saved["comparison"]["profile_version"] == "v0.3"

    registry_path = Path(runner.oft.METHOD_PROFILE_REGISTRY_PATH)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["active_profile_version"] = "v0.4"
    registry["profiles"]["v0.3"]["status"] = "frozen"
    registry["profiles"]["v0.4"]["status"] = "active"
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert runner.oft.load_method_profile_registry().entries["v0.3"].status == "frozen"

    rerun_code, rerun_manifest = runner.execute(args)
    rerun = load_manifest(rerun_manifest)
    assert rerun_code == 0
    assert rerun["reason_code"] == "already_completed"
    assert len(calls) == 1
    assert official.read_bytes() == before


def test_new_write_uses_simulated_v04(tmp_path, monkeypatch):
    install_temp_profile_env(monkeypatch, tmp_path, versions=("v0.3", "v0.4"), active="v0.4")
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-24",
            "--reason",
            "simulated v0.4 new write",
        )
    )
    saved = load_manifest(manifest)
    assert code == 0
    assert saved["write_action"] == "semantic_noop"
    assert saved["comparison"]["profile_version"] == "v0.4"
    assert saved["comparison"]["profile_sha256"] != "11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1"


def test_unknown_profile_version_blocked(tmp_path, monkeypatch):
    install_temp_profile_env(monkeypatch, tmp_path)
    with pytest.raises(ValueError):
        runner.oft.resolve_profile_for_version("v9.9")
    with pytest.raises(ValueError):
        runner.oft.build_semantic_comparison(
            candidate={},
            official={},
            candidate_bytes=b"{}",
            official_bytes=b"{}",
            symbol="300274",
            target_date="2026-07-24",
            profile_version="v9.9",
        )


def test_registry_sha_mismatch_blocked(tmp_path, monkeypatch):
    install_temp_profile_env(monkeypatch, tmp_path)
    registry_path = Path(runner.oft.METHOD_PROFILE_REGISTRY_PATH)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["profiles"]["v0.3"]["profile_sha256"] = "0" * 64
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        runner.oft.load_method_profile_registry()


def test_manifest_profile_sha_mismatch_historical_blocked(tmp_path, monkeypatch):
    install_temp_profile_env(monkeypatch, tmp_path)
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    calls = patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))
    args = parse_write_args(
        tmp_path,
        calendar,
        "--mode",
        "historical_backfill",
        "--date",
        "2026-07-24",
        "--reason",
        "manifest sha mismatch replay",
    )
    code, manifest = runner.execute(args)
    saved = load_manifest(manifest)
    assert code == 0
    assert saved["write_action"] == "semantic_noop"

    manifest_path = Path(saved["manifest_path"])
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["comparison"]["profile_sha256"] = "0" * 64
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    rerun_code, rerun_manifest = runner.execute(args)
    rerun = load_manifest(rerun_manifest)
    assert rerun_code == 0
    assert rerun["reason_code"] != "already_completed"
    assert len(calls) == 2


def test_missing_historical_config_blocked(tmp_path, monkeypatch):
    install_temp_profile_env(monkeypatch, tmp_path, versions=("v0.3", "v0.4"), active="v0.4")
    (tmp_path / "rules" / "profiles_v0.3.json").unlink()
    with pytest.raises(ValueError):
        runner.oft.load_method_profile_registry()


def test_registry_path_escape_blocked(tmp_path, monkeypatch):
    install_temp_profile_env(monkeypatch, tmp_path)
    registry_path = Path(runner.oft.METHOD_PROFILE_REGISTRY_PATH)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["profiles"]["v0.3"]["path"] = "../escape.json"
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        runner.oft.load_method_profile_registry()


def test_registry_duplicate_key_blocked(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(
        '{"schema_version": "semantic_noop_timestamp_profile_registry_v0.1", '
        '"schema_version": "duplicate", "active_profile_version": "v0.3", "profiles": {}}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        runner.oft.load_method_profile_registry(path)


def test_profile_json_duplicate_key_blocked(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text(
        '{"schema_version": "semantic_noop_timestamp_profiles_v0.3", '
        '"schema_version": "duplicate"}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        runner.oft.load_method_profile_config(path)


def _write_temp_profile_config(tmp_path: Path, mutator) -> Path:
    config = json.loads(Path("rules/semantic_noop_timestamp_profiles_v0.3.json").read_text(encoding="utf-8"))
    mutator(config)
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps(config, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def test_unknown_top_level_field_blocked(tmp_path):
    path = _write_temp_profile_config(tmp_path, lambda config: config.update({"extra_field": 1}))
    with pytest.raises(ValueError):
        runner.oft.load_method_profile_config(path)


def test_unknown_profile_field_blocked(tmp_path):
    def mutator(config):
        config["profiles"]["same_day_snapshot_plus_sohu_five_day_cross_check"]["extra_field"] = 1

    path = _write_temp_profile_config(tmp_path, mutator)
    with pytest.raises(ValueError):
        runner.oft.load_method_profile_config(path)


def test_unknown_condition_field_blocked(tmp_path):
    def mutator(config):
        profile = config["profiles"]["same_day_snapshot_plus_sohu_five_day_cross_check"]
        profile["optional_paths"] = ["volume_ratio.extra_check.fetched_at"]
        profile["optional_presence_conditions"] = {
            "volume_ratio.extra_check.fetched_at": {
                "present_when_parent": "volume_ratio",
                "unknown_condition_field": True,
            }
        }

    path = _write_temp_profile_config(tmp_path, mutator)
    with pytest.raises(ValueError):
        runner.oft.load_method_profile_config(path)


def test_blocked_profile_with_required_path_blocked(tmp_path):
    def mutator(config):
        config["profiles"]["legacy_manual_confirmation"]["required_paths"] = ["generated_at"]

    path = _write_temp_profile_config(tmp_path, mutator)
    with pytest.raises(ValueError):
        runner.oft.load_method_profile_config(path)


def test_blocked_profile_missing_reason_blocked(tmp_path):
    def mutator(config):
        del config["profiles"]["legacy_manual_confirmation"]["reason"]

    path = _write_temp_profile_config(tmp_path, mutator)
    with pytest.raises(ValueError):
        runner.oft.load_method_profile_config(path)


def test_active_profile_with_reason_blocked(tmp_path):
    def mutator(config):
        config["profiles"]["same_day_snapshot_plus_sohu_five_day_cross_check"]["reason"] = "not allowed"

    path = _write_temp_profile_config(tmp_path, mutator)
    with pytest.raises(ValueError):
        runner.oft.load_method_profile_config(path)


def test_canonical_ensure_ascii_false_recompute():
    from pathlib import Path as _Path

    config = runner.oft.load_method_profile_config()
    parsed = json.loads(_Path("rules/semantic_noop_timestamp_profiles_v0.3.json").read_text(encoding="utf-8"))
    canonical = runner.oft.canonical_json_bytes(parsed)
    assert hashlib.sha256(canonical).hexdigest() == config.sha256
    assert config.sha256 == "11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1"
    ascii_free = runner.oft.canonical_json_bytes({"name": "阳光电源"}).decode("utf-8")
    assert "阳光电源" in ascii_free
    assert "\\u" not in ascii_free
    doc = _Path("rules/run_daily_facts_after_close_phase_b_v0.3.md").read_text(encoding="utf-8")
    assert "ensure_ascii=False" in doc
    assert "sort_keys=True" in doc
    assert 'separators=(",", ":")' in doc


def test_v1_v2_recompute_unaffected_by_registry(tmp_path, monkeypatch):
    install_temp_profile_env(monkeypatch, tmp_path, versions=("v0.3", "v0.4"), active="v0.4")
    official, candidate = _v3_pair_from_real_facts("2026-07-24")
    official_bytes = json.dumps(official, ensure_ascii=False, sort_keys=True).encode("utf-8")
    candidate_bytes = json.dumps(candidate, ensure_ascii=False, sort_keys=True).encode("utf-8")
    v1 = runner.oft.build_semantic_comparison(
        candidate=candidate,
        official=official,
        candidate_bytes=candidate_bytes,
        official_bytes=official_bytes,
        symbol="300274",
        target_date="2026-07-24",
        comparison_mode=runner.oft.SEMANTIC_COMPARISON_V1_MODE,
    )
    v2 = runner.oft.build_semantic_comparison(
        candidate=candidate,
        official=official,
        candidate_bytes=candidate_bytes,
        official_bytes=official_bytes,
        symbol="300274",
        target_date="2026-07-24",
        comparison_mode=runner.oft.SEMANTIC_COMPARISON_V2_MODE,
    )
    assert v1["semantic_equal"] is True
    assert v2["semantic_equal"] is True


def test_phase_b_phase_c_historical_version_dispatch_equivalent(tmp_path, monkeypatch):
    install_temp_profile_env(monkeypatch, tmp_path, versions=("v0.3", "v0.4"), active="v0.3")
    calendar = same_day_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    official_payload, candidate = same_day_facts_pair_07_24()
    official = repo / "data" / "daily" / "300274_2026-07-24_facts.json"
    official.write_bytes(runner._json_payload(official_payload))
    calls = patch_generator(monkeypatch, returncode=2, stdout=marker_for(candidate))
    args = parse_write_args(
        tmp_path,
        calendar,
        "--mode",
        "historical_backfill",
        "--date",
        "2026-07-24",
        "--reason",
        "historical dispatch equivalence",
    )
    code, manifest = runner.execute(args)
    saved = load_manifest(manifest)
    assert code == 0
    assert saved["write_action"] == "semantic_noop"
    assert saved["comparison"]["profile_version"] == "v0.3"

    registry_path = Path(runner.oft.METHOD_PROFILE_REGISTRY_PATH)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["active_profile_version"] = "v0.4"
    registry["profiles"]["v0.3"]["status"] = "frozen"
    registry["profiles"]["v0.4"]["status"] = "active"
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rerun_code, rerun_manifest = runner.execute(args)
    rerun = load_manifest(rerun_manifest)
    assert rerun_code == 0
    assert rerun["reason_code"] == "already_completed"
    assert len(calls) == 1

    result = phase_c.generate_review(
        phase_c.ReviewOptions(
            runtime_dir=tmp_path / "phase-c-runtime",
            runner_runtime_dir=tmp_path / "runtime",
            symbol="300274",
            trade_date="2026-07-24",
            runner_manifest_path=Path(saved["manifest_path"]),
            repo_root=repo,
            official_lock_dir=tmp_path / "phase-c-locks",
            now=lambda: datetime(2026, 7, 24, 16, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
    )
    review = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert result.status == "review_created"
    assert review["artifact_type"] == "facts_review"
    assert review["write_action"] == "semantic_noop"
    assert review["evidence_summary"]["semantic_comparison"]["profile_version"] == "v0.3"
    assert review["evidence_summary"]["semantic_comparison"]["semantic_equal"] is True


def test_write_official_existing_different_conflict_blocks(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate()
    existing = eligible_official_candidate()
    existing["name"] = "old official"
    official = repo / "data" / "daily" / "300274_2026-07-16_facts.json"
    official.write_bytes(runner._json_payload(existing))
    before = official.read_bytes()
    patch_generator(monkeypatch, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled replay",
        )
    )

    saved = load_manifest(manifest)
    assert code == 2
    assert saved["write_action"] == "conflict_blocked"
    assert saved["reason_code"] == "official_conflict"
    assert official.read_bytes() == before


@pytest.mark.parametrize(
    ("mutator", "action", "reason"),
    [
        (lambda value: value.update({"sealed": True}), "sealed_blocked", "sealed_exists"),
        (lambda value: value["run"].update({"sealed": True}), "sealed_blocked", "sealed_exists"),
        (lambda value: value.update({"manual": True}), "manual_blocked", "manual_exists"),
        (lambda value: value["run"].update({"manual": True}), "manual_blocked", "manual_exists"),
    ],
)
def test_write_official_sealed_or_manual_blocks_without_overwrite(tmp_path, monkeypatch, mutator, action, reason):
    calendar = write_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate()
    existing = eligible_official_candidate()
    mutator(existing)
    official = repo / "data" / "daily" / "300274_2026-07-16_facts.json"
    official.write_bytes(runner._json_payload(existing))
    before = official.read_bytes()
    patch_generator(monkeypatch, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled replay",
        )
    )

    saved = load_manifest(manifest)
    assert code == 0
    assert saved["write_action"] == action
    assert saved["reason_code"] == reason
    assert official.read_bytes() == before


@pytest.mark.parametrize("mutator", [
    lambda value: value.update({"sealed": "true"}),
    lambda value: value["run"].update({"sealed": "true"}),
    lambda value: value.update({"manual": "true"}),
    lambda value: value["run"].update({"manual": "true"}),
])
def test_write_official_malformed_sealed_or_manual_marker_does_not_bypass_conflict(tmp_path, monkeypatch, mutator):
    calendar = write_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate()
    existing = eligible_official_candidate()
    existing["name"] = "different existing official"
    mutator(existing)
    official = repo / "data" / "daily" / "300274_2026-07-16_facts.json"
    official.write_bytes(runner._json_payload(existing))
    before = official.read_bytes()
    patch_generator(monkeypatch, stdout=marker_for(candidate))

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled replay",
        )
    )

    saved = load_manifest(manifest)
    assert code == 2
    assert saved["write_action"] == "conflict_blocked"
    assert saved["reason_code"] == "official_conflict"
    assert official.read_bytes() == before


def test_official_written_but_manifest_bundle_failure_reports_compensation_state(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate()
    patch_generator(monkeypatch, stdout=marker_for(candidate))
    captured = install_context_collision(monkeypatch, "summary")

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled replay",
        )
    )

    official = repo / "data" / "daily" / "300274_2026-07-16_facts.json"
    saved = load_manifest(manifest)
    assert code == 1
    assert official.exists()
    assert manifest["reason_code"] == "official_written_manifest_failed"
    assert saved["reason_code"] == "official_written_manifest_failed"
    assert saved["official_sha256_after"] == runner.sha256_bytes(official.read_bytes())
    assert not list(captured["ctx"].run_dir.glob("*.tmp"))


def test_post_write_validator_failure_records_changed_official_evidence(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate()
    patch_generator(monkeypatch, stdout=marker_for(candidate))
    calls = {"count": 0}

    def validator_second_failure(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return {"status": "passed"}
        return {"status": "failed", "exception_type": "ValueError", "message": "post-write bad"}

    monkeypatch.setattr(runner.oft, "_validator_summary", validator_second_failure)

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled replay",
        )
    )

    official = repo / "data" / "daily" / "300274_2026-07-16_facts.json"
    saved = load_manifest(manifest)
    summary = Path(saved["manifest_path"]).with_name("summary.md").read_text(encoding="utf-8")
    alert = json.loads(Path(saved["alerts"][0]).read_text(encoding="utf-8"))
    assert code == 2
    assert official.exists()
    assert saved["stage"] == "finished"
    assert saved["last_stage"] == "validate"
    assert saved["outcome"] == "needs_manual_review"
    assert saved["reason_code"] == "official_written_postcheck_failed"
    assert saved["write_action"] == "created_postcheck_failed"
    assert saved["official_changed"] is True
    assert saved["official_bytes_equal_candidate"] is True
    assert saved["official_sha256_after"] == runner.sha256_bytes(official.read_bytes())
    assert saved["candidate_sha256"] == saved["official_sha256_after"]
    assert saved["official_validator_after"]["status"] == "failed"
    assert saved["official_post_write_error"]["stage"] == "post_write_validator"
    assert alert["official_changed"] is True
    assert "Post-write check failed after official facts changed" in summary
    assert not list((repo / "data" / "daily").glob("*.tmp"))


@pytest.mark.parametrize("tampered", [b'{"tampered":true}\n', b'{"schema_version"'])
def test_post_write_bytes_mismatch_records_actual_after_sha(tmp_path, monkeypatch, tampered):
    calendar = write_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate()
    patch_generator(monkeypatch, stdout=marker_for(candidate))
    official = repo / "data" / "daily" / "300274_2026-07-16_facts.json"
    stop = threading.Event()
    tampered_event = threading.Event()
    original_fsync = runner.oft.os.fsync

    def slow_fsync(fd):
        result = original_fsync(fd)
        if official.exists() and not tampered_event.is_set():
            deadline = time.monotonic() + 2
            while not tampered_event.is_set() and time.monotonic() < deadline:
                time.sleep(0.005)
        return result

    def external_tamper():
        deadline = time.monotonic() + 2
        while not stop.is_set() and time.monotonic() < deadline:
            if official.exists():
                official.write_bytes(tampered)
                tampered_event.set()
                return
            time.sleep(0.001)

    monkeypatch.setattr(runner.oft.os, "fsync", slow_fsync)
    tamper_thread = threading.Thread(target=external_tamper, name="external-tamper")
    tamper_thread.start()

    try:
        code, manifest = runner.execute(
            parse_write_args(
                tmp_path,
                calendar,
                "--mode",
                "historical_backfill",
                "--date",
                "2026-07-16",
                "--reason",
                "controlled replay",
            )
        )
    finally:
        stop.set()
        tamper_thread.join(5)

    saved = load_manifest(manifest)
    assert tampered_event.is_set()
    assert code == 2
    assert official.read_bytes() == tampered
    assert saved["last_stage"] == "validate"
    assert saved["outcome"] == "needs_manual_review"
    assert saved["reason_code"] == "official_written_bytes_mismatch"
    assert saved["write_action"] == "created_postcheck_failed"
    assert saved["official_changed"] is True
    assert saved["official_bytes_equal_candidate"] is False
    assert saved["official_sha256_after"] == runner.sha256_bytes(tampered)
    assert saved["candidate_sha256"] != saved["official_sha256_after"]
    assert not list((repo / "data" / "daily").glob("*.tmp"))


def test_post_write_read_failure_records_changed_official_without_sha(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate()
    patch_generator(monkeypatch, stdout=marker_for(candidate))
    original_write = runner.oft._write_bytes_locked

    def write_then_read_failure(output_path, payload_bytes, *, lock_state):
        final_bytes, final_sha, error = original_write(output_path, payload_bytes, lock_state=lock_state)
        assert final_bytes == payload_bytes and final_sha and error is None
        return None, None, {"type": "OSError", "message": "cannot read after write", "stage": "post_write_read"}

    monkeypatch.setattr(runner.oft, "_write_bytes_locked", write_then_read_failure)

    code, manifest = runner.execute(
        parse_write_args(
            tmp_path,
            calendar,
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled replay",
        )
    )

    official = repo / "data" / "daily" / "300274_2026-07-16_facts.json"
    saved = load_manifest(manifest)
    assert code == 2
    assert official.exists()
    assert saved["reason_code"] == "official_written_postcheck_failed"
    assert saved["write_action"] == "created_postcheck_failed"
    assert saved["official_changed"] is True
    assert saved["official_sha256_after"] is None
    assert saved["official_post_write_error"]["stage"] == "post_write_read"


def test_post_write_failure_then_rerun_is_not_reported_as_plain_success(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate()
    patch_generator(monkeypatch, stdout=marker_for(candidate))
    calls = {"count": 0}

    def validator_second_failure(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            return {"status": "failed", "exception_type": "ValueError", "message": "post-write bad"}
        return {"status": "passed"}

    monkeypatch.setattr(runner.oft, "_validator_summary", validator_second_failure)
    args = parse_write_args(
        tmp_path,
        calendar,
        "--mode",
        "historical_backfill",
        "--date",
        "2026-07-16",
        "--reason",
        "controlled replay",
    )
    first_code, first_manifest = runner.execute(args)
    assert first_code == 2
    assert load_manifest(first_manifest)["reason_code"] == "official_written_postcheck_failed"

    calls["count"] = 0
    second_code, second_manifest = runner.execute(args)
    second = load_manifest(second_manifest)
    assert second_code == 0
    assert second["write_action"] == "identical_noop"
    assert second["reason_code"] == "official_already_identical"
    assert second["official_sha256_after"] == runner.sha256_bytes((repo / "data" / "daily" / "300274_2026-07-16_facts.json").read_bytes())


def test_post_write_failure_bundle_failure_keeps_transaction_reason_on_stderr(tmp_path, monkeypatch, capsys):
    calendar = write_calendar(tmp_path / "calendar.json")
    install_temp_repo_root(monkeypatch, tmp_path)
    candidate = eligible_official_candidate()
    patch_generator(monkeypatch, stdout=marker_for(candidate))
    install_context_collision(monkeypatch, "summary")
    calls = {"count": 0}

    def validator_second_failure(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return {"status": "passed"}
        return {"status": "failed", "exception_type": "ValueError", "message": "post-write bad"}

    monkeypatch.setattr(runner.oft, "_validator_summary", validator_second_failure)

    code = runner.main(
        [
            "--write-official",
            "--symbol",
            "300274",
            "--runtime-dir",
            str(tmp_path / "runtime"),
            "--calendar",
            str(calendar),
            "--mode",
            "historical_backfill",
            "--date",
            "2026-07-16",
            "--reason",
            "controlled replay",
        ]
    )

    payload = json.loads(capsys.readouterr().err)
    assert code == 1
    assert payload["reason_code"] == "official_written_postcheck_failed"
    assert payload["manifest_bundle_reason_code"] == "official_written_manifest_failed"
    assert payload["official_path"]
    assert payload["official_sha256_after"]
    assert payload["write_action"] == "created_postcheck_failed"


def test_stdout_marker_allows_surrounding_logs_and_other_json():
    payload = generator_object()
    stdout = "INFO {\"log\":1}\n\n" + generator_payload() + "\nWARNING {\"other\":2}\n"

    assert runner.parse_generator_stdout(stdout) == payload


@pytest.mark.parametrize(
    ("stdout", "reason"),
    [
        ("INFO only", "stdout_candidate_missing"),
        (generator_payload() + "\n" + generator_payload(), "stdout_candidate_ambiguous"),
        (runner.CANDIDATE_STDOUT_MARKER + "{\"broken\":", "stdout_parse_failed"),
        (runner.CANDIDATE_STDOUT_MARKER + "not-json", "stdout_parse_failed"),
    ],
)
def test_stdout_marker_failures_are_distinct(stdout, reason):
    with pytest.raises(runner.RunnerError) as exc:
        runner.parse_generator_stdout(stdout)

    assert exc.value.reason_code == reason


def test_stderr_json_is_never_a_candidate(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_generator(monkeypatch, stdout="INFO no marker", stderr=generator_payload())

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    assert code == 1
    assert load_manifest(manifest)["reason_code"] == "stdout_candidate_missing"


@pytest.mark.parametrize(
    ("mutator", "reason"),
    [
        (lambda value: value.pop("trade_date"), "source_date_mismatch"),
        (lambda value: value.pop("symbol"), "candidate_identity_mismatch"),
        (lambda value: value["quote_verification"].pop("source_date"), "source_date_mismatch"),
        (lambda value: value.update({"schema_version": "unexpected"}), "candidate_schema_invalid"),
        (lambda value: value.update({"symbol": "600000"}), "candidate_identity_mismatch"),
        (lambda value: value.update({"trade_date": "2026-07-14"}), "source_date_mismatch"),
        (lambda value: value["quote"].pop("close"), "candidate_schema_invalid"),
        (lambda value: value["quote"].update({"close": True}), "candidate_schema_invalid"),
    ],
)
def test_candidate_identity_gate_rejects_malformed_objects(tmp_path, monkeypatch, mutator, reason):
    calendar = write_calendar(tmp_path / "calendar.json")
    candidate = generator_object()
    mutator(candidate)
    patch_generator(
        monkeypatch,
        stdout=runner.CANDIDATE_STDOUT_MARKER + json.dumps(candidate, separators=(",", ":")),
    )

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    assert code == 1
    assert load_manifest(manifest)["reason_code"] == reason


def test_candidate_with_only_success_status_is_rejected(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    raw = runner.CANDIDATE_STDOUT_MARKER + json.dumps({"run": {"status": "success"}})
    patch_generator(monkeypatch, stdout=raw)

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    assert code == 1
    assert load_manifest(manifest)["reason_code"] == "candidate_schema_invalid"


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        ("schema_error", "generator_failed"),
        ("failed", "generator_failed"),
        ("error", "generator_failed"),
        ("unknown", "generator_failed"),
        ("made_up", "unknown_generator_status"),
        ("", "generator_failed"),
    ],
)
def test_generator_status_mapping_fails_closed(tmp_path, monkeypatch, status, reason):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_generator(monkeypatch, stdout=generator_payload(status=status))

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    assert code == 1
    assert load_manifest(manifest)["reason_code"] == reason


def test_non_finite_candidate_json_is_rejected_before_identity_gate():
    candidate = generator_object()
    candidate["quote"]["close"] = float("nan")
    stdout = runner.CANDIDATE_STDOUT_MARKER + json.dumps(candidate)

    with pytest.raises(runner.RunnerError) as exc:
        runner.parse_generator_stdout(stdout)

    assert exc.value.reason_code == "stdout_parse_failed"


@pytest.mark.parametrize(
    "value",
    [
        "not-a-time",
        "2026-07-16T15:25:00",
        "2026-07-16T15:25:00Z",
        "2026-07-16T15:25:00+00:00",
        "2026-07-16T15:25:00+08:30",
    ],
)
def test_invalid_now_values_are_structured_and_do_not_create_runtime(tmp_path, value, capsys):
    runtime = tmp_path / "runtime"

    code = runner.main(["--dry-run", "--runtime-dir", str(runtime), "--now", value])

    payload = json.loads(capsys.readouterr().err)
    assert code == 1
    assert payload["reason_code"] == "invalid_now"
    assert payload["manifest"] is None
    assert not runtime.exists()


def test_close_gate_boundary_151959_and_152000(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    calls = patch_generator(monkeypatch)
    patch_validator(monkeypatch)

    before_code, before = runner.execute(parse_args(tmp_path / "before", calendar, "--now", "2026-07-16T15:19:59+08:00"))
    at_code, at = runner.execute(parse_args(tmp_path / "at", calendar, "--now", "2026-07-16T15:20:00+08:00"))

    assert before_code == 0
    assert load_manifest(before)["reason_code"] == "before_close"
    assert at_code == 0
    assert load_manifest(at)["outcome"] == "success"
    assert len(calls) == 1


def test_calendar_empty_trading_days_fails_closed(tmp_path):
    calendar = write_calendar(tmp_path / "calendar.json", trading_days=[])
    data = json.loads(calendar.read_text())
    data["trading_days"] = []
    calendar.write_text(json.dumps(data), encoding="utf-8")

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    assert code == 1
    assert load_manifest(manifest)["reason_code"] == "calendar_invalid"


def install_context_collision(monkeypatch, kind: str):
    original = runner.build_context
    captured = {}

    def build(args, runtime_dir, target_date, mode):
        ctx = original(args, runtime_dir, target_date, mode)
        captured["ctx"] = ctx
        if kind == "candidate":
            ctx.candidate_path.mkdir(parents=True)
        elif kind == "summary":
            ctx.summary_path.mkdir(parents=True)
        elif kind == "alert":
            (ctx.alerts_dir / f"{ctx.run_id}.json").mkdir(parents=True)
        return ctx

    monkeypatch.setattr(runner, "build_context", build)
    return captured


@pytest.mark.parametrize("kind", ["candidate", "alert"])
def test_bundle_artifact_failure_never_leaves_success_manifest(tmp_path, monkeypatch, kind):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_validator(monkeypatch)
    patch_generator(
        monkeypatch,
        returncode=2 if kind == "alert" else 0,
        stdout=generator_payload(status="partial" if kind == "alert" else "success"),
    )
    install_context_collision(monkeypatch, kind)

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    assert code == 1
    saved = load_manifest(manifest)
    assert saved["outcome"] == "failed"
    assert saved["reason_code"] == "manifest_write_failed"
    assert not list((tmp_path / "runtime").rglob("*.tmp"))


def test_success_manifest_replace_failure_is_committed_as_failed(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_validator(monkeypatch)
    patch_generator(monkeypatch)
    original_replace = runner.os.replace
    manifest_attempts = 0

    def fail_first_manifest_replace(source, destination):
        nonlocal manifest_attempts
        if Path(destination).name == "manifest.json":
            manifest_attempts += 1
            if manifest_attempts == 1:
                raise OSError("simulated final manifest replace failure")
        return original_replace(source, destination)

    monkeypatch.setattr(runner.os, "replace", fail_first_manifest_replace)

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    assert code == 1
    assert manifest_attempts == 2
    saved = load_manifest(manifest)
    assert saved["outcome"] == "failed"
    assert saved["reason_code"] == "manifest_write_failed"
    assert not list((tmp_path / "runtime").rglob("*.tmp"))


def test_failure_manifest_unwritable_returns_null_manifest_path(tmp_path, monkeypatch, capsys):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_validator(monkeypatch)
    patch_generator(monkeypatch)
    original_replace = runner.os.replace

    def fail_all_manifest_replaces(source, destination):
        if Path(destination).name == "manifest.json":
            raise OSError("simulated persistent manifest failure")
        return original_replace(source, destination)

    monkeypatch.setattr(runner.os, "replace", fail_all_manifest_replaces)

    code = runner.main(
        [
            "--dry-run",
            "--runtime-dir",
            str(tmp_path / "runtime"),
            "--calendar",
            str(calendar),
            "--now",
            "2026-07-16T15:25:00+08:00",
        ]
    )

    payload = json.loads(capsys.readouterr().err)
    assert code == 1
    assert payload["outcome"] == "failed"
    assert payload["reason_code"] == "manifest_write_failed"
    assert payload["manifest"] is None
    assert not list((tmp_path / "runtime").rglob("manifest.json"))
    assert not list((tmp_path / "runtime").rglob("*.tmp"))


def test_unexpected_generator_exception_persists_structured_failure(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")

    def explode(_command):
        raise RuntimeError("fictional generator crash")

    monkeypatch.setattr(runner, "run_generator", explode)

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    saved = load_manifest(manifest)
    assert code == 1
    assert saved["stage"] == "finished"
    assert saved["last_stage"] == "fetch"
    assert saved["outcome"] == "failed"
    assert saved["reason_code"] == "runner_unexpected_error"


@pytest.mark.parametrize(
    "text",
    [
        "Authorization: Bearer FAKE_BEARER_123",
        "Authorization: Basic FAKE_BASIC_123",
        "Cookie: sid=FAKE_COOKIE",
        "Set-Cookie: sid=FAKE_COOKIE",
        "X-API-Key: FAKE_HEADER_KEY",
        "Proxy-Authorization: Basic FAKE_PROXY",
        "https://example.invalid/?token=FAKE_TOKEN&key=FAKE_KEY",
        "https://example.invalid/?access_token=FAKE_ACCESS&password=FAKE_PASSWORD",
        "api_key=FAKE_API_KEY",
        "OPENAI_API_KEY=FAKE_OPENAI",
        "GITHUB_TOKEN=FAKE_GITHUB",
        "AWS_SECRET_ACCESS_KEY=FAKE_AWS_SECRET",
        "AWS_ACCESS_KEY_ID=FAKE_AWS_ID",
        "CUSTOM_PASSWORD=FAKE_CUSTOM",
    ],
)
def test_sensitive_text_matrix_preserves_name_and_redacts_value(text):
    sanitized = runner.sanitize_text(text)
    assert "FAKE_" not in sanitized
    assert "[REDACTED]" in sanitized


def test_sensitive_filter_does_not_erase_ordinary_diagnostics():
    text = "token refresh failed because key lookup timed out"
    assert runner.sanitize_text(text) == text


def test_sensitive_candidate_key_is_rejected_and_stdout_is_sanitized(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    candidate = generator_object()
    candidate["OPENAI_API_KEY"] = "FAKE_CANDIDATE_SECRET"
    raw = runner.CANDIDATE_STDOUT_MARKER + json.dumps(candidate, separators=(",", ":"))
    patch_generator(monkeypatch, stdout=raw)

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    saved = load_manifest(manifest)
    stdout = Path(saved["generator"]["stdout_path"]).read_text()
    assert code == 1
    assert saved["reason_code"] == "stdout_parse_failed"
    assert "FAKE_CANDIDATE_SECRET" not in stdout
    assert not Path(saved["candidate_path"]).exists()


def test_success_manifest_has_full_uuid_finished_stage_and_candidate_sha(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    install_temp_repo_root(monkeypatch, tmp_path)
    patch_validator(monkeypatch)
    patch_generator(monkeypatch)

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    saved = load_manifest(manifest)
    assert code == 0
    assert str(uuid.UUID(saved["run_id"])) == saved["run_id"]
    assert saved["stage"] == "finished"
    assert saved["last_stage"] == "validate"
    assert saved["official_sha256_before"] is None
    assert saved["official_sha256_after"] is None
    candidate_bytes = Path(saved["candidate_path"]).read_bytes()
    assert saved["candidate_sha256"] == runner.sha256_bytes(candidate_bytes)


def test_dry_run_snapshot_isolated_from_outside_same_date_official(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    outside_official = tmp_path / "outside-repository" / "data" / "daily" / "300274_2026-07-16_facts.json"
    outside_official.parent.mkdir(parents=True)
    outside_official.write_text('{"outside": true}\n', encoding="utf-8")
    repo = install_temp_repo_root(monkeypatch, tmp_path)
    patch_validator(monkeypatch)
    patch_generator(monkeypatch)

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    saved = load_manifest(manifest)
    assert code == 0
    assert saved["official_path"] == str(repo / "data" / "daily" / "300274_2026-07-16_facts.json")
    assert saved["official_sha256_before"] is None
    assert saved["official_sha256_after"] is None
    assert outside_official.read_text(encoding="utf-8") == '{"outside": true}\n'
    assert (repo / ".test-locks").is_dir()


def test_partial_manifest_is_finished_with_fetch_last_stage(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    patch_validator(monkeypatch)
    patch_generator(monkeypatch, returncode=2, stdout=generator_payload(status="partial"))

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    saved = load_manifest(manifest)
    assert code == 2
    assert saved["stage"] == "finished"
    assert saved["last_stage"] == "fetch"


def test_runner_lock_blocks_a_real_second_process(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    runtime = tmp_path / "runtime"
    args = parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00")
    child_code = r'''
import sys
from pathlib import Path
from tools import run_daily_facts_after_close as runner
runtime = Path(sys.argv[1])
calendar = Path(sys.argv[2])
args = runner.build_parser().parse_args([
    "--dry-run", "--runtime-dir", str(runtime), "--calendar", str(calendar),
    "--now", "2026-07-16T15:25:00+08:00",
])
ctx = runner.build_context(args, runtime, runner.parse_trade_date("2026-07-16"), "today_after_close")
with runner.runner_lock(ctx) as acquired:
    print("READY" if acquired else "FAILED", flush=True)
    sys.stdin.readline()
'''
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(runner.REPO_ROOT)
    child = subprocess.Popen(
        [sys.executable, "-B", "-c", child_code, str(runtime), str(calendar)],
        cwd=runner.REPO_ROOT,
        env=env,
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "READY"
        calls = patch_generator(monkeypatch)
        code, manifest = runner.execute(args)
        assert code == 0
        assert load_manifest(manifest)["reason_code"] == "runner_already_active"
        assert calls == []
    finally:
        if child.stdin:
            child.stdin.write("stop\n")
            child.stdin.flush()
        child.wait(timeout=5)


def test_real_subprocess_generator_marker_to_validator_bundle(tmp_path, monkeypatch):
    calendar = write_calendar(tmp_path / "calendar.json")
    wrapper = tmp_path / "generator_wrapper.py"
    candidate = generator_object()
    wrapper.write_text(
        "from tools import generate_daily_facts as g\n"
        f"candidate = {candidate!r}\n"
        "def fake_run(args, **kwargs):\n"
        "    return g.RunOutcome(exit_code=0, facts_pack=candidate, wrote_file=False, "
        "output_path=None, status='success')\n"
        "g.run = fake_run\n"
        "raise SystemExit(g.main())\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "GENERATOR", wrapper)

    code, manifest = runner.execute(parse_args(tmp_path, calendar, "--now", "2026-07-16T15:25:00+08:00"))

    saved = load_manifest(manifest)
    assert code == 0
    assert saved["outcome"] == "success"
    assert saved["validator"]["status"] == "passed"
    assert saved["generator"]["exit_code"] == 0
    assert Path(saved["candidate_path"]).exists()
