import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

import tools.migrate_legacy_volume_ratio_evidence as migrate


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "tools" / "migrate_legacy_volume_ratio_evidence.py"
TARGET_DATE = "2026-07-14"
SYMBOL = "300274"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, payload: dict) -> str:
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    path.write_bytes(data)
    return sha256_bytes(data)


def legacy_pack() -> dict:
    return {
        "schema_version": "facts_pack_v0.2",
        "trade_date": TARGET_DATE,
        "symbol": SYMBOL,
        "generated_at": "2026-07-14T08:05:00Z",
        "quote": {
            "open": 108.0,
            "high": 109.26,
            "low": 100.73,
            "close": 108.29,
            "prev_close": 108.0,
            "pct_change": 0.2685185185185235,
            "amount": 100.65149576,
            "turnover_rate": 6.05,
        },
        "quote_verification": {"status": "confirmed", "source_date": TARGET_DATE},
        "volume_ratio": {
            "candidate_value": 1.49,
            "confirmed_value": 1.49,
            "source": "tencent_qt_direct_index_49+sohu_five_day_volume",
            "verification": {
                "status": "confirmed",
                "method": "same_day_snapshot_plus_sohu_five_day_cross_check",
                "source": "tencent_qt_direct_index_49+sohu_five_day_volume",
                "source_date": TARGET_DATE,
                "fetched_at": "2026-07-14T08:05:00Z",
            },
            "cross_check": {
                "value": 1.49,
                "source": "sohu_five_day_volume_derived",
                "source_date": TARGET_DATE,
                "tolerance": 0.05,
                "delta": 0.0,
            },
        },
        "needs_manual_check": {
            "volume_ratio": False,
            "market_indices": True,
            "sector_context": True,
            "disclosure_status": True,
            "news_policy_context": True,
        },
        "missing": {
            "market_indices": None,
            "sector_context": None,
            "disclosure_status": None,
            "news_policy_context": None,
        },
        "run": {"status": "partial"},
    }


def sohu_result() -> dict:
    return {
        "status": "ok",
        "source": "sohu",
        "source_date": TARGET_DATE,
        "fetched_at": "2026-07-15T08:00:00Z",
        "quote": {
            "open": 108.0,
            "high": 109.26,
            "low": 100.73,
            "close": 108.29,
            "prev_close": 108.0,
            "pct_change": 0.2685185185185235,
            "amount": 100.6515,
            "turnover_rate": 6.05,
        },
        "rows": [
            {"date": "2026-07-06", "volume": "522306"},
            {"date": "2026-07-07", "volume": "442203"},
            {"date": "2026-07-08", "volume": "413086"},
            {"date": "2026-07-09", "volume": "673516"},
            {"date": "2026-07-10", "volume": "939380"},
            {"date": "2026-07-13", "volume": "745683"},
            {"date": TARGET_DATE, "volume": "960311"},
        ],
    }


def historical_pack() -> dict:
    pack = legacy_pack()
    pack["trade_date"] = "2026-07-13"
    pack["volume_ratio"] = {
        "candidate_value": 1.25,
        "confirmed_value": 1.25,
        "source": "sohu_five_day_volume+tencent_five_day_volume",
        "verification": {
            "status": "confirmed",
            "method": "historical_five_day_volume_cross_check",
            "confirmed_by": "automation_cross_check",
            "source": "sohu_five_day_volume+tencent_five_day_volume",
            "source_date": "2026-07-13",
            "fetched_at": "2026-07-14T21:47:48Z",
        },
        "cross_check": {
            "value": 1.25,
            "source": "tencent_five_day_volume_derived",
            "source_date": "2026-07-13",
            "formula": "target_day_volume / mean(prior_5_trading_day_volume)",
            "tolerance": 0.01,
            "delta": 0.0,
        },
    }
    return pack


def historical_candidate_result() -> dict:
    dates = ["2026-07-06", "2026-07-07", "2026-07-08", "2026-07-09", "2026-07-10", "2026-07-13"]
    volumes = [100.0, 110.0, 120.0, 130.0, 140.0, 150.0]
    check = {
        "status": "passed",
        "trade_dates": dates,
        "volumes": volumes,
        "target_volume": 150.0,
        "calculated_value": 1.25,
        "expected_value": 1.25,
        "tolerance": 0.01,
        "formula": "target_day_volume / mean(prior_5_trading_day_volume)",
        "fetched_at": "2026-07-15T08:00:00Z",
    }
    return {
        "method": "historical_five_day_volume_cross_check",
        "verification_status": "confirmed",
        "candidate_value": 1.25,
        "source_volume_checks": {
            "sohu_history": {**check, "source": "sohu_history"},
            "tencent_history": {**check, "source": "tencent_history"},
        },
    }


def build_candidate_from_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict, dict, Path, str]:
    input_path = tmp_path / "legacy.json"
    expected_sha = write_json(input_path, legacy_pack())
    monkeypatch.setattr(migrate.gdf, "fetch_sohu_quote", lambda *_args: copy.deepcopy(sohu_result()))
    candidate, summary = migrate.build_candidate(
        input_path=input_path,
        target_date=TARGET_DATE,
        symbol=SYMBOL,
        timeout=1,
        expected_input_sha256=expected_sha,
    )
    return candidate, summary, input_path, expected_sha


def build_historical_candidate_from_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict, dict, Path, str]:
    input_path = tmp_path / "historical.json"
    expected_sha = write_json(input_path, historical_pack())
    monkeypatch.setattr(
        migrate.gdf,
        "fetch_volume_ratio_candidate",
        lambda *_args: copy.deepcopy(historical_candidate_result()),
    )
    candidate, summary = migrate.build_candidate(
        input_path=input_path,
        target_date="2026-07-13",
        symbol=SYMBOL,
        timeout=1,
        expected_input_sha256=expected_sha,
    )
    return candidate, summary, input_path, expected_sha


def test_build_candidate_requires_expected_sha(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_path = tmp_path / "legacy.json"
    write_json(input_path, legacy_pack())
    monkeypatch.setattr(migrate.gdf, "fetch_sohu_quote", lambda *_args: copy.deepcopy(sohu_result()))
    with pytest.raises(ValueError, match="input sha256 mismatch"):
        migrate.build_candidate(
            input_path=input_path,
            target_date=TARGET_DATE,
            symbol=SYMBOL,
            timeout=1,
            expected_input_sha256="0" * 64,
        )


def test_date_profiles_use_distinct_leaf_path_sets() -> None:
    assert "volume_ratio.archived_snapshot_source.source" in migrate.PROFILE_2026_07_14_LEAF_PATHS
    assert "volume_ratio.archived_snapshot_source.source" not in migrate.PROFILE_2026_07_13_LEAF_PATHS
    assert "volume_ratio.source_volume_checks.sohu_history.source" in migrate.PROFILE_2026_07_13_LEAF_PATHS
    assert "volume_ratio.source_volume_checks.sohu_history.source" not in migrate.PROFILE_2026_07_14_LEAF_PATHS


def test_0713_profile_build_compare_and_rerun_are_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "historical.json"
    old = historical_pack()
    old_sha = write_json(input_path, old)
    monkeypatch.setattr(
        migrate.gdf,
        "fetch_volume_ratio_candidate",
        lambda *_args: copy.deepcopy(historical_candidate_result()),
    )
    candidate, _summary = migrate.build_candidate(
        input_path=input_path,
        target_date="2026-07-13",
        symbol=SYMBOL,
        timeout=1,
        expected_input_sha256=old_sha,
    )
    migrate.compare_profiled_candidate(
        old,
        candidate,
        expected_official_sha256=old_sha,
        target_date="2026-07-13",
    )
    migrated_path = tmp_path / "migrated.json"
    migrated_sha = write_json(migrated_path, candidate)
    before = migrated_path.read_bytes()
    rerun, summary = migrate.build_candidate(
        input_path=migrated_path,
        target_date="2026-07-13",
        symbol=SYMBOL,
        timeout=1,
        expected_input_sha256=migrated_sha,
    )
    assert summary["status"] == "already_migrated"
    assert rerun == candidate
    assert migrated_path.read_bytes() == before


def test_0713_first_promote_succeeds_with_real_validator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate, _summary, _input_path, old_sha = build_historical_candidate_from_fixture(
        tmp_path,
        monkeypatch,
    )
    official_path = tmp_path / "official-0713.json"
    write_json(official_path, historical_pack())
    candidate_path = tmp_path / "candidate-0713.json"
    candidate_sha = write_json(candidate_path, candidate)
    review = tmp_path / "review-0713.md"
    review.write_text("## 当前结论\n仅作观察。\n", encoding="utf-8")
    result = migrate.promote_candidate(
        argparse.Namespace(
            candidate=str(candidate_path),
            official=str(official_path),
            expected_candidate_sha256=candidate_sha,
            expected_official_sha256=old_sha,
            review_file=str(review),
            date="2026-07-13",
            lock_dir=str(tmp_path / "locks-0713"),
        )
    )
    assert result["status"] == "promoted"
    assert result["new_official_sha256"] == candidate_sha
    assert official_path.read_bytes() == candidate_path.read_bytes()
    assert not list(tmp_path.glob("*.promote-*"))


def test_cli_rejects_arbitrary_output_path(tmp_path: Path) -> None:
    input_path = tmp_path / "legacy.json"
    expected_sha = write_json(input_path, legacy_pack())
    result = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--input",
            str(input_path),
            "--output",
            str(input_path),
            "--expected-input-sha256",
            expected_sha,
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode != 0
    assert "--output is not supported" in result.stderr


def test_cli_rejects_candidate_dir_inside_formal_facts_path(tmp_path: Path) -> None:
    input_path = tmp_path / "legacy.json"
    expected_sha = write_json(input_path, legacy_pack())
    result = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--input",
            str(input_path),
            "--expected-input-sha256",
            expected_sha,
            "--candidate-dir",
            str(REPO_ROOT / "data" / "daily"),
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode != 0
    assert "must not write into repository data/daily" in result.stderr


def test_read_expected_json_bytes_returns_object_from_fixed_bytes(tmp_path: Path) -> None:
    input_path = tmp_path / "legacy.json"
    expected_sha = write_json(input_path, legacy_pack())
    data, actual_sha, loaded = migrate.read_expected_json_bytes(input_path, expected_sha, label="input")
    changed = legacy_pack()
    changed["symbol"] = "000000"
    write_json(input_path, changed)
    assert actual_sha == expected_sha
    assert loaded["symbol"] == SYMBOL
    assert migrate.sha256_bytes(data) == expected_sha


def test_build_candidate_rejects_wrong_legacy_method(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pack = legacy_pack()
    pack["volume_ratio"]["verification"]["method"] = "derived_candidate"
    input_path = tmp_path / "legacy.json"
    expected_sha = write_json(input_path, pack)
    monkeypatch.setattr(migrate.gdf, "fetch_sohu_quote", lambda *_args: copy.deepcopy(sohu_result()))
    with pytest.raises(ValueError, match="migration profile"):
        migrate.build_candidate(
            input_path=input_path,
            target_date=TARGET_DATE,
            symbol=SYMBOL,
            timeout=1,
            expected_input_sha256=expected_sha,
        )


def test_build_candidate_rejects_wrong_original_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pack = legacy_pack()
    pack["volume_ratio"]["verification"]["source"] = "sohu_history"
    input_path = tmp_path / "legacy.json"
    expected_sha = write_json(input_path, pack)
    monkeypatch.setattr(migrate.gdf, "fetch_sohu_quote", lambda *_args: copy.deepcopy(sohu_result()))
    with pytest.raises(ValueError, match="legacy pack source"):
        migrate.build_candidate(
            input_path=input_path,
            target_date=TARGET_DATE,
            symbol=SYMBOL,
            timeout=1,
            expected_input_sha256=expected_sha,
        )


def test_first_migration_success_builds_complete_archived_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate, summary, _input_path, expected_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    volume_ratio = candidate["volume_ratio"]
    assert summary["old_file_sha256"] == expected_sha
    assert volume_ratio["verification"]["method"] == "archived_tencent_snapshot_plus_sohu_historical_reverification"
    assert volume_ratio["legacy_verification"]["method"] == "same_day_snapshot_plus_sohu_five_day_cross_check"
    assert volume_ratio["archived_snapshot_source"]["original_fetched_at"] == "2026-07-14T08:05:00Z"
    assert volume_ratio["historical_ohlc_check"]["status"] == "passed"
    assert volume_ratio["five_day_volume_check"]["calculated_value"] == 1.49
    assert volume_ratio["migration"]["old_file_sha256"] == expected_sha


def test_already_migrated_rerun_is_noop_and_preserves_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate, _summary, _input_path, _expected_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    migrated_path = tmp_path / "migrated.json"
    migrated_sha = write_json(migrated_path, candidate)
    before = migrated_path.read_bytes()
    rerun_candidate, rerun_summary = migrate.build_candidate(
        input_path=migrated_path,
        target_date=TARGET_DATE,
        symbol=SYMBOL,
        timeout=1,
        expected_input_sha256=migrated_sha,
    )
    assert rerun_summary["status"] == "already_migrated"
    assert rerun_summary["input_sha256"] == migrated_sha
    assert rerun_summary["old_file_sha256"] == candidate["volume_ratio"]["migration"]["old_file_sha256"]
    assert rerun_candidate == candidate
    assert migrated_path.read_bytes() == before
    assert rerun_candidate["volume_ratio"]["legacy_verification"] == candidate["volume_ratio"]["legacy_verification"]


def test_sohu_network_failure_does_not_write_candidate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_path = tmp_path / "legacy.json"
    output_path = tmp_path / "candidate.json"
    expected_sha = write_json(input_path, legacy_pack())
    monkeypatch.setattr(migrate.gdf, "fetch_sohu_quote", lambda *_args: {"status": "network_error", "error_message": "dns"})
    with pytest.raises(ValueError, match="Sohu fetch failed"):
        candidate, _summary = migrate.build_candidate(
            input_path=input_path,
            target_date=TARGET_DATE,
            symbol=SYMBOL,
            timeout=1,
            expected_input_sha256=expected_sha,
        )
        migrate.write_validated_candidate(output_path=output_path, candidate=candidate, review_file="review.md", target_date=TARGET_DATE)
    assert not output_path.exists()


def test_write_validated_candidate_failure_leaves_no_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate, _summary, _input_path, _expected_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    output_path = tmp_path / "candidate.json"
    monkeypatch.setattr(migrate, "assert_validator_pass", lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad candidate")))
    with pytest.raises(ValueError, match="bad candidate"):
        migrate.write_validated_candidate(
            output_path=output_path,
            candidate=candidate,
            review_file="review.md",
            target_date=TARGET_DATE,
        )
    assert not output_path.exists()


def test_promote_rejects_official_sha_mismatch_without_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate, _summary, _input_path, expected_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    official_path = tmp_path / "official.json"
    official = legacy_pack()
    official["name"] = "changed outside"
    write_json(official_path, official)
    candidate_path = tmp_path / "candidate.json"
    candidate_sha = write_json(candidate_path, candidate)
    review = tmp_path / "review.md"
    review.write_text("## 当前结论\n仅作观察。\n", encoding="utf-8")
    before = official_path.read_bytes()
    args = argparse.Namespace(
        candidate=str(candidate_path),
        official=str(official_path),
        expected_candidate_sha256=candidate_sha,
        expected_official_sha256=expected_sha,
        review_file=str(review),
        date=TARGET_DATE,
    )
    with pytest.raises(ValueError, match="official sha256 mismatch"):
        migrate.promote_candidate(args)
    assert official_path.read_bytes() == before


def test_promote_rejects_candidate_sha_mismatch_without_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate, _summary, _input_path, expected_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    official_path = tmp_path / "official.json"
    write_json(official_path, legacy_pack())
    candidate_path = tmp_path / "candidate.json"
    write_json(candidate_path, candidate)
    before = official_path.read_bytes()
    args = argparse.Namespace(
        candidate=str(candidate_path),
        official=str(official_path),
        expected_candidate_sha256="0" * 64,
        expected_official_sha256=expected_sha,
        review_file="review.md",
        date=TARGET_DATE,
    )
    with pytest.raises(ValueError, match="candidate sha256 mismatch"):
        migrate.promote_candidate(args)
    assert official_path.read_bytes() == before


def test_promote_rejects_migration_old_sha_mismatch_without_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate, _summary, _input_path, expected_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    candidate["volume_ratio"]["migration"]["old_file_sha256"] = "0" * 64
    official_path = tmp_path / "official.json"
    write_json(official_path, legacy_pack())
    candidate_path = tmp_path / "candidate.json"
    candidate_sha = write_json(candidate_path, candidate)
    before = official_path.read_bytes()
    args = argparse.Namespace(
        candidate=str(candidate_path),
        official=str(official_path),
        expected_candidate_sha256=candidate_sha,
        expected_official_sha256=expected_sha,
        review_file="review.md",
        date=TARGET_DATE,
    )
    with pytest.raises(ValueError, match="migration.old_file_sha256"):
        migrate.promote_candidate(args)
    assert official_path.read_bytes() == before


@pytest.mark.parametrize("field,value", [("symbol", "000000"), ("name", "漂移"), ("trade_date", "2026-07-15"), ("schema_version", "x")])
def test_promote_rejects_identity_field_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: str) -> None:
    candidate, _summary, _input_path, expected_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    candidate[field] = value
    official_path = tmp_path / "official.json"
    write_json(official_path, legacy_pack())
    candidate_path = tmp_path / "candidate.json"
    candidate_sha = write_json(candidate_path, candidate)
    review = tmp_path / "review.md"
    review.write_text("## 当前结论\n仅作观察。\n", encoding="utf-8")
    before = official_path.read_bytes()
    args = argparse.Namespace(
        candidate=str(candidate_path),
        official=str(official_path),
        expected_candidate_sha256=candidate_sha,
        expected_official_sha256=expected_sha,
        review_file=str(review),
        date=TARGET_DATE,
    )
    with pytest.raises(ValueError, match="non-profile leaf changed"):
        migrate.promote_candidate(args)
    assert official_path.read_bytes() == before


def test_promote_rejects_validator_failure_without_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate, _summary, _input_path, _expected_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    official_path = tmp_path / "official.json"
    official_sha = write_json(official_path, legacy_pack())
    candidate_path = tmp_path / "candidate.json"
    candidate_sha = write_json(candidate_path, candidate)
    before = official_path.read_bytes()
    monkeypatch.setattr(migrate, "assert_validator_pass", lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("validator failed")))
    args = argparse.Namespace(
        candidate=str(candidate_path),
        official=str(official_path),
        expected_candidate_sha256=candidate_sha,
        expected_official_sha256=official_sha,
        review_file="review.md",
        date=TARGET_DATE,
    )
    with pytest.raises(ValueError, match="validator failed"):
        migrate.promote_candidate(args)
    assert official_path.read_bytes() == before


def test_promote_rejects_official_change_during_validator_window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate, _summary, _input_path, expected_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    official_path = tmp_path / "official.json"
    write_json(official_path, legacy_pack())
    candidate_path = tmp_path / "candidate.json"
    candidate_sha = write_json(candidate_path, candidate)
    before = official_path.read_bytes()

    def mutate_official(*_args, **_kwargs):
        changed = legacy_pack()
        changed["name"] = "external change"
        write_json(official_path, changed)

    monkeypatch.setattr(migrate, "assert_validator_pass", mutate_official)
    args = argparse.Namespace(
        candidate=str(candidate_path),
        official=str(official_path),
        expected_candidate_sha256=candidate_sha,
        expected_official_sha256=expected_sha,
        review_file="review.md",
        date=TARGET_DATE,
    )
    with pytest.raises(ValueError, match="official sha256 changed before replace"):
        migrate.promote_candidate(args)
    assert official_path.read_bytes() != before
    assert json.loads(official_path.read_text(encoding="utf-8"))["name"] == "external change"


def test_promote_rejects_official_change_before_final_replace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate, _summary, _input_path, expected_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    official_path = tmp_path / "official.json"
    write_json(official_path, legacy_pack())
    candidate_path = tmp_path / "candidate.json"
    candidate_sha = write_json(candidate_path, candidate)
    review = tmp_path / "review.md"
    review.write_text("## 当前结论\n仅作观察。\n", encoding="utf-8")

    def mutate_before_final_check(_official, _candidate, **_kwargs):
        changed = legacy_pack()
        changed["name"] = "late external change"
        write_json(official_path, changed)

    monkeypatch.setattr(migrate, "compare_profiled_candidate", mutate_before_final_check)
    args = argparse.Namespace(
        candidate=str(candidate_path),
        official=str(official_path),
        expected_candidate_sha256=candidate_sha,
        expected_official_sha256=expected_sha,
        review_file=str(review),
        date=TARGET_DATE,
    )
    with pytest.raises(ValueError, match="official sha256 changed before replace"):
        migrate.promote_candidate(args)
    assert json.loads(official_path.read_text(encoding="utf-8"))["name"] == "late external change"
    assert not list(tmp_path.glob("*.promote-*"))
    assert not list(tmp_path.glob("*.lock"))


def test_promote_uses_fixed_candidate_bytes_if_candidate_path_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate, _summary, _input_path, expected_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    official_path = tmp_path / "official.json"
    official_sha = write_json(official_path, legacy_pack())
    candidate_path = tmp_path / "candidate.json"
    candidate_sha = write_json(candidate_path, candidate)

    def mutate_candidate_path(*_args, **_kwargs):
        changed = copy.deepcopy(candidate)
        changed["symbol"] = "000000"
        write_json(candidate_path, changed)

    monkeypatch.setattr(migrate, "assert_validator_pass", mutate_candidate_path)
    args = argparse.Namespace(
        candidate=str(candidate_path),
        official=str(official_path),
        expected_candidate_sha256=candidate_sha,
        expected_official_sha256=official_sha,
        review_file="review.md",
        date=TARGET_DATE,
    )
    summary = migrate.promote_candidate(args)
    assert summary["status"] == "promoted"
    assert json.loads(official_path.read_text(encoding="utf-8"))["symbol"] == SYMBOL


def test_promote_success_writes_candidate_atomically(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate, _summary, _input_path, _expected_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    official_path = tmp_path / "official.json"
    official_sha = write_json(official_path, legacy_pack())
    candidate_path = tmp_path / "candidate.json"
    candidate_sha = write_json(candidate_path, candidate)
    review = tmp_path / "review.md"
    review.write_text("## 当前结论\n仅作观察。\n", encoding="utf-8")
    lock_dir = tmp_path / "locks"
    args = argparse.Namespace(
        candidate=str(candidate_path),
        official=str(official_path),
        expected_candidate_sha256=candidate_sha,
        expected_official_sha256=official_sha,
        review_file=str(review),
        date=TARGET_DATE,
        lock_dir=str(lock_dir),
    )
    summary = migrate.promote_candidate(args)
    assert summary["status"] == "promoted"
    assert json.loads(official_path.read_text(encoding="utf-8")) == candidate
    assert list(lock_dir.glob("*.lock"))
    assert not list(tmp_path.glob("*.lock"))
    assert not list(tmp_path.glob("*.promote-*"))


def test_promote_actions_and_final_sha_observe_held_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate, _summary, _input_path, old_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    official_path = tmp_path / "official.json"
    write_json(official_path, legacy_pack())
    candidate_path = tmp_path / "candidate.json"
    candidate_sha = write_json(candidate_path, candidate)
    review = tmp_path / "review.md"
    review.write_text("## 当前结论\n仅作观察。\n", encoding="utf-8")
    holder: dict[str, object] = {}
    events: list[str] = []
    real_lock = migrate.ofl.official_facts_lock

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
        assert isinstance(state, migrate.ofl.OfficialFactsLockState) and state.held
        events.append(name)

    real_read = migrate.ofl.read_current_official
    real_sha = migrate.ofl.sha256_bytes
    real_validator = migrate.assert_validator_pass_bytes
    real_compare = migrate.compare_profiled_candidate
    real_replace = migrate.os.replace

    def observed_read(*call_args, **call_kwargs):
        mark("read_official")
        return real_read(*call_args, **call_kwargs)

    def observed_sha(data):
        mark("sha256")
        return real_sha(data)

    def observed_validator(*call_args, **call_kwargs):
        mark("validator")
        return real_validator(*call_args, **call_kwargs)

    def observed_compare(*call_args, **call_kwargs):
        mark("profile_compare")
        return real_compare(*call_args, **call_kwargs)

    def observed_replace(src, dst):
        mark("replace")
        return real_replace(src, dst)

    monkeypatch.setattr(migrate.ofl, "official_facts_lock", observed_lock)
    monkeypatch.setattr(migrate.ofl, "read_current_official", observed_read)
    monkeypatch.setattr(migrate.ofl, "sha256_bytes", observed_sha)
    monkeypatch.setattr(migrate, "assert_validator_pass_bytes", observed_validator)
    monkeypatch.setattr(migrate, "compare_profiled_candidate", observed_compare)
    monkeypatch.setattr(migrate.os, "replace", observed_replace)

    result = migrate.promote_candidate(
        argparse.Namespace(
            candidate=str(candidate_path),
            official=str(official_path),
            expected_candidate_sha256=candidate_sha,
            expected_official_sha256=old_sha,
            review_file=str(review),
            date=TARGET_DATE,
            lock_dir=str(tmp_path / "locks"),
        )
    )
    assert result["new_official_sha256"] == candidate_sha
    assert events[0] == "lock_enter" and events[-1] == "lock_exit"
    for required in (
        "read_official",
        "sha256",
        "validator",
        "profile_compare",
        "replace",
    ):
        assert required in events
    replace_index = events.index("replace")
    assert "read_official" in events[replace_index + 1 :]
    assert "sha256" in events[replace_index + 1 :]


MUTATION_MATRIX = [
    ("volume_ratio.source", "unexpected_source"),
    ("volume_ratio.verification.source", "unexpected_source"),
    ("volume_ratio.verification.source_date", "2026-07-13"),
    ("volume_ratio.verification.status", "unverified"),
    ("volume_ratio.verification.method", "unexpected_method"),
    ("volume_ratio.legacy_verification", None),
    ("volume_ratio.legacy_verification.method", "unexpected_method"),
    ("volume_ratio.archived_snapshot_source.source", "unexpected_source"),
    ("volume_ratio.archived_snapshot_source.previous_close", 999),
    ("volume_ratio.archived_snapshot_source.pct_change", 999),
    ("volume_ratio.archived_snapshot_source.amount", 999),
    ("volume_ratio.archived_snapshot_source.turnover_rate", 999),
    ("volume_ratio.archived_snapshot_source.source_pack_paths", ["quote.open"]),
    ("volume_ratio.archived_snapshot_source.original_fetched_at", "not-a-time"),
    ("volume_ratio.cross_check", {"unexpected": True}),
    ("volume_ratio.unexpected_field", "unexpected"),
    ("run", None),
    ("volume_ratio.verification.status", "unknown_status"),
    ("volume_ratio.verification.status", ""),
    ("volume_ratio.verification.status", "derived_confirmed"),
]


def mutate_path(payload: dict, path_text: str, value) -> None:
    parts = path_text.split(".")
    current = payload
    for part in parts[:-1]:
        current = current[part]
    if value is None:
        current.pop(parts[-1], None)
    else:
        current[parts[-1]] = value


@pytest.mark.parametrize("path_text,value", MUTATION_MATRIX)
def test_promote_rejects_candidate_field_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path_text: str,
    value,
) -> None:
    candidate, _summary, _input_path, official_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    mutate_path(candidate, path_text, value)
    official_path = tmp_path / "official.json"
    write_json(official_path, legacy_pack())
    candidate_path = tmp_path / "candidate.json"
    candidate_sha = write_json(candidate_path, candidate)
    review = tmp_path / "review.md"
    review.write_text("## 当前结论\n仅作观察。\n", encoding="utf-8")
    before = official_path.read_bytes()
    args = argparse.Namespace(
        candidate=str(candidate_path),
        official=str(official_path),
        expected_candidate_sha256=candidate_sha,
        expected_official_sha256=official_sha,
        review_file=str(review),
        date=TARGET_DATE,
        lock_dir=str(tmp_path / "locks"),
    )
    with pytest.raises(ValueError):
        migrate.promote_candidate(args)
    assert official_path.read_bytes() == before
    assert not list(tmp_path.glob("*.promote-*"))
    assert not list(tmp_path.glob("*.lock"))


PROFILE_0713_NEGATIVE_CASES = [
    "profile_outside_added",
    "nonprofile_object_deleted",
    "allowed_leaf_type_changed",
    "fixed_leaf_type_changed",
    "sohu_check_deleted",
    "tencent_check_deleted",
    "source_identifier_changed",
    "trade_dates_changed",
    "volumes_changed",
    "calculated_value_changed",
    "expected_value_changed",
    "tolerance_changed",
    "formula_changed",
    "old_file_sha_changed",
    "migration_type_changed",
    "symbol_changed",
    "trade_date_changed",
    "quote_changed",
    "missing_changed",
    "migration_field_added",
]


def mutate_0713_candidate(candidate: dict, case: str) -> None:
    volume_ratio = candidate["volume_ratio"]
    checks = volume_ratio["source_volume_checks"]
    sohu = checks["sohu_history"]
    tencent = checks["tencent_history"]
    if case == "profile_outside_added":
        volume_ratio["unexpected"] = True
    elif case == "nonprofile_object_deleted":
        candidate.pop("run")
    elif case == "allowed_leaf_type_changed":
        sohu["tolerance"] = "0.01"
    elif case == "fixed_leaf_type_changed":
        candidate["quote"]["close"] = str(candidate["quote"]["close"])
    elif case == "sohu_check_deleted":
        checks.pop("sohu_history")
    elif case == "tencent_check_deleted":
        checks.pop("tencent_history")
    elif case == "source_identifier_changed":
        sohu["source"] = "unexpected_source"
    elif case == "trade_dates_changed":
        sohu["trade_dates"] = [*sohu["trade_dates"][:-1], "2026-07-12"]
    elif case == "volumes_changed":
        tencent["volumes"] = [*tencent["volumes"][:-1], 151.0]
    elif case == "calculated_value_changed":
        sohu["calculated_value"] = 9.99
    elif case == "expected_value_changed":
        tencent["expected_value"] = 9.99
    elif case == "tolerance_changed":
        sohu["tolerance"] = 9.99
    elif case == "formula_changed":
        tencent["formula"] = "unexpected formula"
    elif case == "old_file_sha_changed":
        volume_ratio["migration"]["old_file_sha256"] = "0" * 64
    elif case == "migration_type_changed":
        volume_ratio["migration"]["migration_type"] = "unexpected"
    elif case == "symbol_changed":
        candidate["symbol"] = "000000"
    elif case == "trade_date_changed":
        candidate["trade_date"] = "2026-07-12"
    elif case == "quote_changed":
        candidate["quote"]["close"] = 999.0
    elif case == "missing_changed":
        candidate.pop("missing")
    elif case == "migration_field_added":
        volume_ratio["migration"]["unexpected"] = True
    else:
        raise AssertionError(f"unknown 07-13 mutation case: {case}")


@pytest.mark.parametrize("case", PROFILE_0713_NEGATIVE_CASES)
def test_0713_profile_negative_matrix_rejects_without_official_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    candidate, _summary, _input_path, old_sha = build_historical_candidate_from_fixture(
        tmp_path,
        monkeypatch,
    )
    mutate_0713_candidate(candidate, case)
    official_path = tmp_path / "official-0713.json"
    write_json(official_path, historical_pack())
    before_bytes = official_path.read_bytes()
    before_sha = sha256_bytes(before_bytes)
    candidate_path = tmp_path / "candidate-0713.json"
    candidate_sha = write_json(candidate_path, candidate)
    review = tmp_path / "review-0713.md"
    review.write_text("## 当前结论\n仅作观察。\n", encoding="utf-8")
    with pytest.raises(ValueError):
        migrate.promote_candidate(
            argparse.Namespace(
                candidate=str(candidate_path),
                official=str(official_path),
                expected_candidate_sha256=candidate_sha,
                expected_official_sha256=old_sha,
                review_file=str(review),
                date="2026-07-13",
                lock_dir=str(tmp_path / "locks-0713"),
            )
        )
    assert official_path.read_bytes() == before_bytes
    assert sha256_bytes(official_path.read_bytes()) == before_sha == old_sha
    assert not list(tmp_path.glob("*.promote-*"))
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))


def test_generator_and_promote_share_lock_and_stale_promote_stops(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate, _summary, _input_path, old_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    official_path = tmp_path / "official.json"
    write_json(official_path, legacy_pack())
    candidate_path = tmp_path / "candidate.json"
    candidate_sha = write_json(candidate_path, candidate)
    review = tmp_path / "review.md"
    review.write_text("## 当前结论\n仅作观察。\n", encoding="utf-8")
    lock_dir = tmp_path / "locks"
    generator_payload = legacy_pack()
    generator_payload["name"] = "generator result"

    generator_at_replace = threading.Event()
    release_generator = threading.Event()
    original_replace = migrate.os.replace

    def delayed_replace(src, dst):
        if threading.current_thread().name == "generator-writer" and Path(dst) == official_path:
            generator_at_replace.set()
            assert release_generator.wait(5)
        return original_replace(src, dst)

    monkeypatch.setattr(migrate.os, "replace", delayed_replace)
    results: dict[str, object] = {}

    def generator_writer() -> None:
        generator_args = argparse.Namespace(
            symbol=SYMBOL,
            date=TARGET_DATE,
            output=str(official_path),
            source="tencent",
            dry_run=False,
            no_write=False,
            write_partial=True,
            timeout=1.0,
        )
        quote_result = {
            "status": "ok",
            "source": "tencent",
            "source_date": TARGET_DATE,
            "source_name": "generator result",
            "fetched_at": "2026-07-14T09:00:00Z",
            "quote": copy.deepcopy(generator_payload["quote"]),
            "errors": [],
        }
        migrate.gdf.write_generated_facts_transaction(
            args=generator_args,
            output_path=official_path,
            quote_result=quote_result,
            volume_ratio_candidate=None,
            expected_sha256=old_sha,
            lock_dir=lock_dir,
        )
        results["generator"] = "written"

    def promoter() -> None:
        args = argparse.Namespace(
            candidate=str(candidate_path),
            official=str(official_path),
            expected_candidate_sha256=candidate_sha,
            expected_official_sha256=old_sha,
            review_file=str(review),
            date=TARGET_DATE,
            lock_dir=str(lock_dir),
        )
        try:
            migrate.promote_candidate(args)
        except Exception as exc:  # asserted below
            results["promote"] = exc

    generator = threading.Thread(target=generator_writer, name="generator-writer")
    promote = threading.Thread(target=promoter, name="promote-writer")
    generator.start()
    assert generator_at_replace.wait(5)
    promote.start()
    time.sleep(0.05)
    assert promote.is_alive()
    release_generator.set()
    generator.join(5)
    promote.join(5)

    assert results["generator"] == "written"
    assert isinstance(results["promote"], migrate.ofl.OfficialFactsChangedError)
    assert json.loads(official_path.read_text(encoding="utf-8"))["name"] == "generator result"
    assert not list(tmp_path.glob("*.promote-*"))
    assert not list(tmp_path.glob("*.lock"))
    assert list(lock_dir.glob("*.lock"))


def test_akshare_writer_waits_for_promote_then_stale_sha_stops(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate, _summary, _input_path, old_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    official_path = tmp_path / "official.json"
    write_json(official_path, legacy_pack())
    candidate_path = tmp_path / "candidate.json"
    candidate_sha = write_json(candidate_path, candidate)
    review = tmp_path / "review.md"
    review.write_text("## 当前结论\n仅作观察。\n", encoding="utf-8")
    lock_dir = tmp_path / "locks"
    script = REPO_ROOT / "tools" / "akshare_daily_quote_check_v0.1.py"
    spec = importlib.util.spec_from_file_location("akshare_lock_concurrency", script)
    assert spec is not None and spec.loader is not None
    akshare_tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(akshare_tool)

    promote_at_replace = threading.Event()
    release_promote = threading.Event()
    original_replace = migrate.os.replace

    def delayed_replace(src, dst):
        if threading.current_thread().name == "promote-writer" and Path(dst) == official_path:
            promote_at_replace.set()
            assert release_promote.wait(5)
        return original_replace(src, dst)

    monkeypatch.setattr(migrate.os, "replace", delayed_replace)
    results: dict[str, object] = {}

    def promoter() -> None:
        results["promote"] = migrate.promote_candidate(
            argparse.Namespace(
                candidate=str(candidate_path),
                official=str(official_path),
                expected_candidate_sha256=candidate_sha,
                expected_official_sha256=old_sha,
                review_file=str(review),
                date=TARGET_DATE,
                lock_dir=str(lock_dir),
            )
        )

    def akshare_writer() -> None:
        try:
            akshare_tool.write_facts_json(
                official_path,
                args=argparse.Namespace(symbol=SYMBOL, date=TARGET_DATE),
                tencent_data={
                    "开盘": 108.0,
                    "最高": 109.26,
                    "最低": 100.73,
                    "收盘": 108.29,
                    "涨跌幅": 0.2685185185185235,
                    "成交额": 100.65149576,
                    "换手率": 6.05,
                },
                realtime_volume_ratio={"candidate_value": None},
                expected_sha256=old_sha,
                lock_dir=lock_dir,
            )
        except Exception as exc:  # asserted below
            results["akshare"] = exc

    promote_thread = threading.Thread(target=promoter, name="promote-writer")
    akshare_thread = threading.Thread(target=akshare_writer, name="akshare-writer")
    promote_thread.start()
    assert promote_at_replace.wait(5)
    akshare_thread.start()
    time.sleep(0.05)
    assert akshare_thread.is_alive()
    release_promote.set()
    promote_thread.join(5)
    akshare_thread.join(5)

    assert results["promote"]["new_official_sha256"] == candidate_sha
    assert isinstance(results["akshare"], migrate.ofl.OfficialFactsChangedError)
    assert official_path.read_bytes() == candidate_path.read_bytes()
    assert not list(tmp_path.glob("*.promote-*"))


def test_promote_final_sha_is_locked_while_next_writer_waits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate, _summary, _input_path, old_sha = build_candidate_from_fixture(tmp_path, monkeypatch)
    official_path = tmp_path / "official.json"
    write_json(official_path, legacy_pack())
    candidate_path = tmp_path / "candidate.json"
    candidate_sha = write_json(candidate_path, candidate)
    candidate_bytes = candidate_path.read_bytes()
    review = tmp_path / "review.md"
    review.write_text("## 当前结论\n仅作观察。\n", encoding="utf-8")
    lock_dir = tmp_path / "locks"
    promote_at_final_read = threading.Event()
    release_promote = threading.Event()
    real_read = migrate.ofl.read_current_official

    def delayed_final_read(*call_args, **call_kwargs):
        data, sha256 = real_read(*call_args, **call_kwargs)
        if threading.current_thread().name == "promote-writer" and data == candidate_bytes:
            promote_at_final_read.set()
            assert release_promote.wait(5)
        return data, sha256

    monkeypatch.setattr(migrate.ofl, "read_current_official", delayed_final_read)
    results: dict[str, object] = {}

    def promoter() -> None:
        results["promote"] = migrate.promote_candidate(
            argparse.Namespace(
                candidate=str(candidate_path),
                official=str(official_path),
                expected_candidate_sha256=candidate_sha,
                expected_official_sha256=old_sha,
                review_file=str(review),
                date=TARGET_DATE,
                lock_dir=str(lock_dir),
            )
        )

    def next_generator() -> None:
        args = argparse.Namespace(
            symbol=SYMBOL,
            date=TARGET_DATE,
            output=str(official_path),
            source="tencent",
            dry_run=False,
            no_write=False,
            write_partial=True,
            timeout=1.0,
        )
        quote_result = {
            "status": "ok",
            "source": "tencent",
            "source_date": TARGET_DATE,
            "source_name": "next writer",
            "fetched_at": "2026-07-14T09:00:00Z",
            "quote": copy.deepcopy(legacy_pack()["quote"]),
            "errors": [],
        }
        results["next"] = migrate.gdf.write_generated_facts_transaction(
            args=args,
            output_path=official_path,
            quote_result=quote_result,
            volume_ratio_candidate=None,
            expected_sha256=candidate_sha,
            lock_dir=lock_dir,
        )

    promote_thread = threading.Thread(target=promoter, name="promote-writer")
    next_thread = threading.Thread(target=next_generator, name="next-writer")
    promote_thread.start()
    assert promote_at_final_read.wait(5)
    next_thread.start()
    time.sleep(0.05)
    assert next_thread.is_alive()
    assert "next" not in results
    release_promote.set()
    promote_thread.join(5)
    next_thread.join(5)

    assert results["promote"]["new_official_sha256"] == candidate_sha
    assert results["next"][2] is True
    assert not list(tmp_path.glob("*.promote-*"))
