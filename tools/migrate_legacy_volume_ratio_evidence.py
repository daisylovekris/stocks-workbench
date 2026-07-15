#!/usr/bin/env python3
"""Migrate legacy 07-14 volume-ratio evidence to archived snapshot reverification.

This tool is intentionally narrow: it does not fetch a new Tencent same-day
snapshot and it does not rewrite the quote fields from Sohu history. It keeps
the existing facts pack values and adds an auditable historical reverification
layer for legacy facts whose same-day Tencent evidence was archived in the pack.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import generate_daily_facts as gdf  # noqa: E402
from tools import official_facts_lock as ofl  # noqa: E402
from tools import volume_ratio_evidence as vre  # noqa: E402


TOOL_VERSION = "migrate_legacy_volume_ratio_evidence_v0.1"
ARCHIVED_METHOD = vre.METHOD_ARCHIVED_REVERIFICATION
LEGACY_METHOD = vre.METHOD_SAME_DAY_SNAPSHOT
OHLC_FIELDS = vre.OHLC_FIELDS
ARCHIVED_SOURCE = vre.ARCHIVED_COMPOSITE_SOURCE
LEGACY_SOURCE = vre.LEGACY_SNAPSHOT_COMPOSITE_SOURCE
CANONICAL_SOURCE_PACK_PATHS = list(vre.CANONICAL_ARCHIVED_SOURCE_PACK_PATHS)


PROFILE_2026_07_14_LEAF_PATHS = {
    "volume_ratio.source",
    "volume_ratio.verification.status",
    "volume_ratio.verification.method",
    "volume_ratio.verification.source",
    "volume_ratio.verification.source_date",
    "volume_ratio.verification.notes",
    "volume_ratio.legacy_verification.status",
    "volume_ratio.legacy_verification.method",
    "volume_ratio.legacy_verification.confirmed_by",
    "volume_ratio.legacy_verification.source",
    "volume_ratio.legacy_verification.source_date",
    "volume_ratio.legacy_verification.fetched_at",
    "volume_ratio.legacy_verification.notes",
    "volume_ratio.legacy_verification.error_type",
    "volume_ratio.legacy_verification.error_message",
    "volume_ratio.archived_snapshot_source.source",
    "volume_ratio.archived_snapshot_source.source_date",
    "volume_ratio.archived_snapshot_source.ohlc.open",
    "volume_ratio.archived_snapshot_source.ohlc.high",
    "volume_ratio.archived_snapshot_source.ohlc.low",
    "volume_ratio.archived_snapshot_source.ohlc.close",
    "volume_ratio.archived_snapshot_source.previous_close",
    "volume_ratio.archived_snapshot_source.pct_change",
    "volume_ratio.archived_snapshot_source.amount",
    "volume_ratio.archived_snapshot_source.turnover_rate",
    "volume_ratio.archived_snapshot_source.volume_ratio",
    "volume_ratio.archived_snapshot_source.original_fetched_at",
    "volume_ratio.archived_snapshot_source.source_pack_paths",
    "volume_ratio.historical_ohlc_check.status",
    "volume_ratio.historical_ohlc_check.archived_source",
    "volume_ratio.historical_ohlc_check.archived_source_date",
    "volume_ratio.historical_ohlc_check.historical_source",
    "volume_ratio.historical_ohlc_check.historical_source_date",
    "volume_ratio.historical_ohlc_check.ohlc.open",
    "volume_ratio.historical_ohlc_check.ohlc.high",
    "volume_ratio.historical_ohlc_check.ohlc.low",
    "volume_ratio.historical_ohlc_check.ohlc.close",
    "volume_ratio.historical_ohlc_check.archived_ohlc.open",
    "volume_ratio.historical_ohlc_check.archived_ohlc.high",
    "volume_ratio.historical_ohlc_check.archived_ohlc.low",
    "volume_ratio.historical_ohlc_check.archived_ohlc.close",
    "volume_ratio.historical_ohlc_check.tolerance",
    "volume_ratio.historical_ohlc_check.compared_fields",
    "volume_ratio.historical_ohlc_check.field_results.open.left",
    "volume_ratio.historical_ohlc_check.field_results.open.right",
    "volume_ratio.historical_ohlc_check.field_results.open.delta",
    "volume_ratio.historical_ohlc_check.field_results.open.matched",
    "volume_ratio.historical_ohlc_check.field_results.high.left",
    "volume_ratio.historical_ohlc_check.field_results.high.right",
    "volume_ratio.historical_ohlc_check.field_results.high.delta",
    "volume_ratio.historical_ohlc_check.field_results.high.matched",
    "volume_ratio.historical_ohlc_check.field_results.low.left",
    "volume_ratio.historical_ohlc_check.field_results.low.right",
    "volume_ratio.historical_ohlc_check.field_results.low.delta",
    "volume_ratio.historical_ohlc_check.field_results.low.matched",
    "volume_ratio.historical_ohlc_check.field_results.close.left",
    "volume_ratio.historical_ohlc_check.field_results.close.right",
    "volume_ratio.historical_ohlc_check.field_results.close.delta",
    "volume_ratio.historical_ohlc_check.field_results.close.matched",
    "volume_ratio.historical_ohlc_check.fetched_at",
    "volume_ratio.historical_ohlc_check.source",
    "volume_ratio.historical_ohlc_check.source_date",
    "volume_ratio.five_day_volume_check.status",
    "volume_ratio.five_day_volume_check.source",
    "volume_ratio.five_day_volume_check.trade_dates",
    "volume_ratio.five_day_volume_check.volumes",
    "volume_ratio.five_day_volume_check.target_volume",
    "volume_ratio.five_day_volume_check.calculated_value",
    "volume_ratio.five_day_volume_check.expected_value",
    "volume_ratio.five_day_volume_check.tolerance",
    "volume_ratio.five_day_volume_check.formula",
    "volume_ratio.five_day_volume_check.fetched_at",
    "volume_ratio.cross_check.value",
    "volume_ratio.cross_check.source",
    "volume_ratio.cross_check.source_date",
    "volume_ratio.cross_check.formula",
    "volume_ratio.cross_check.tolerance",
    "volume_ratio.cross_check.delta",
    "volume_ratio.migration.old_file_sha256",
    "volume_ratio.migration.migrated_at",
    "volume_ratio.migration.tool_version",
    "volume_ratio.migration.tool",
    "volume_ratio.migration.migration_type",
}

_SOURCE_CHECK_LEAVES = {
    f"volume_ratio.source_volume_checks.{source}.{field}"
    for source in ("sohu_history", "tencent_history")
    for field in (
        "status",
        "source",
        "trade_dates",
        "volumes",
        "target_volume",
        "calculated_value",
        "expected_value",
        "tolerance",
        "formula",
        "fetched_at",
    )
}
PROFILE_2026_07_13_LEAF_PATHS = _SOURCE_CHECK_LEAVES | {
    "volume_ratio.migration.old_file_sha256",
    "volume_ratio.migration.migrated_at",
    "volume_ratio.migration.tool_version",
    "volume_ratio.migration.tool",
    "volume_ratio.migration.migration_type",
}

MIGRATION_PROFILES = {
    "2026-07-13": {
        "source_method": vre.METHOD_HISTORICAL_FIVE_DAY,
        "target_method": vre.METHOD_HISTORICAL_FIVE_DAY,
        "migration_type": "historical_dual_source_volume_evidence_enrichment",
        "leaf_paths": PROFILE_2026_07_13_LEAF_PATHS,
    },
    "2026-07-14": {
        "source_method": vre.METHOD_SAME_DAY_SNAPSHOT,
        "target_method": ARCHIVED_METHOD,
        "migration_type": "legacy_archived_tencent_snapshot_reverification",
        "leaf_paths": PROFILE_2026_07_14_LEAF_PATHS,
    },
}


def utc_now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_from_bytes(data: bytes) -> dict[str, Any]:
    loaded = json.loads(data.decode("utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("JSON root must be an object")
    return loaded


def read_expected_json_bytes(path: Path, expected_sha256: str, *, label: str) -> tuple[bytes, str, dict[str, Any]]:
    data = path.read_bytes()
    actual = sha256_bytes(data)
    if actual != expected_sha256:
        raise ValueError(f"{label} sha256 mismatch: expected {expected_sha256}, got {actual}")
    return data, actual, load_json_from_bytes(data)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    os.replace(tmp, path)
    try:
        dir_fd = os.open(str(path.parent), os.O_DIRECTORY)
    except OSError:
        return
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def write_validated_candidate(
    *,
    output_path: Path,
    candidate: dict[str, Any],
    review_file: str,
    target_date: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_name(f".{output_path.name}.candidate-{os.getpid()}")
    atomic_write_json(tmp, candidate)
    try:
        assert_validator_pass(tmp, review_file=review_file, target_date=target_date)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    os.replace(tmp, output_path)


def ohlc_from(mapping: dict[str, Any], *, prefix: str) -> dict[str, float]:
    return vre.normalize_ohlc(mapping, prefix=prefix)


def assert_close(left: float, right: float, *, tolerance: float, label: str) -> None:
    if abs(left - right) > tolerance:
        raise ValueError(f"{label} mismatch: {left} vs {right}, tolerance={tolerance}")


def sohu_target_and_window(rows: list[dict[str, Any]], target_date: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    dated = [(gdf.record_date_text(row), row) for row in rows if gdf.record_date_text(row)]
    sorted_rows = [row for _date, row in sorted(dated, key=lambda item: item[0] or "")]
    target_index = next((idx for idx, row in enumerate(sorted_rows) if gdf.record_date_text(row) == target_date), None)
    if target_index is None:
        raise ValueError(f"Sohu rows do not include target date {target_date}")
    if target_index < 5:
        raise ValueError("Sohu rows do not include five prior trading days")
    window = sorted_rows[target_index - 5 : target_index + 1]
    dates = [gdf.record_date_text(row) for row in window]
    if len(set(dates)) != len(dates):
        raise ValueError(f"Sohu five-day window contains duplicate dates: {dates}")
    return sorted_rows[target_index], window


def assert_validator_pass(
    candidate_path: Path,
    *,
    review_file: str,
    target_date: str,
    migration_base_path: Path | None = None,
) -> None:
    cmd = [
        sys.executable,
        str(REPO_ROOT / "tools" / "validate_review_chain.py"),
        "--files",
        review_file,
        "--date",
        target_date,
        "--previous-date",
        "2026-07-13",
        "--key-levels",
        "100.73,106.80,108.00,108.29,109.26,112.54,114.05,114.79,118.06",
        "--facts-pack",
        str(candidate_path),
    ]
    if migration_base_path is not None:
        cmd.extend(["--migration-base-facts", str(migration_base_path)])
    result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise ValueError(f"candidate validator failed: {result.stdout.strip()} {result.stderr.strip()}")


def assert_validator_pass_bytes(
    candidate_bytes: bytes,
    *,
    review_file: str,
    target_date: str,
    migration_base_bytes: bytes | None = None,
) -> None:
    with tempfile.NamedTemporaryFile(
        "wb",
        suffix=".candidate-validator.json",
        prefix="volume-ratio-",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
        handle.write(candidate_bytes)
        handle.flush()
        os.fsync(handle.fileno())
    base_path: Path | None = None
    if migration_base_bytes is not None:
        with tempfile.NamedTemporaryFile(
            "wb",
            suffix=".migration-base.json",
            prefix="volume-ratio-",
            delete=False,
        ) as base_handle:
            base_path = Path(base_handle.name)
            base_handle.write(migration_base_bytes)
            base_handle.flush()
            os.fsync(base_handle.fileno())
    try:
        assert_validator_pass(
            temp_path,
            review_file=review_file,
            target_date=target_date,
            migration_base_path=base_path,
        )
    finally:
        temp_path.unlink(missing_ok=True)
        if base_path is not None:
            base_path.unlink(missing_ok=True)


def assert_input_sha(input_path: Path, expected_sha: str) -> str:
    actual = sha256_file(input_path)
    if actual != expected_sha:
        raise ValueError(f"input sha256 mismatch: expected {expected_sha}, got {actual}")
    return actual


def assert_first_migration_allowed(facts: dict[str, Any], *, symbol: str, target_date: str) -> None:
    if facts.get("symbol") != symbol:
        raise ValueError(f"symbol mismatch: expected {symbol}, got {facts.get('symbol')}")
    if facts.get("trade_date") != target_date:
        raise ValueError(f"trade_date mismatch: expected {target_date}, got {facts.get('trade_date')}")
    volume_ratio = facts.get("volume_ratio")
    if not isinstance(volume_ratio, dict):
        raise ValueError("facts.volume_ratio missing or invalid")
    verification = volume_ratio.get("verification")
    if not isinstance(verification, dict):
        raise ValueError("volume_ratio.verification missing or invalid")
    if verification.get("status") != "confirmed":
        raise ValueError("legacy pack must have volume_ratio.verification.status=confirmed")
    if verification.get("method") != LEGACY_METHOD:
        raise ValueError(f"legacy pack method must be {LEGACY_METHOD}")
    if verification.get("source") != LEGACY_SOURCE:
        raise ValueError("legacy pack source must be original Tencent snapshot plus Sohu volume")
    vre.parse_timezone_datetime(
        verification.get("fetched_at"),
        field="volume_ratio.verification.fetched_at",
    )
    if volume_ratio.get("migration") or verification.get("method") == ARCHIVED_METHOD:
        raise ValueError("pack is already migrated")


def assert_historical_migration_allowed(facts: dict[str, Any], *, symbol: str, target_date: str) -> None:
    if facts.get("symbol") != symbol:
        raise ValueError(f"symbol mismatch: expected {symbol}, got {facts.get('symbol')}")
    if facts.get("trade_date") != target_date:
        raise ValueError(f"trade_date mismatch: expected {target_date}, got {facts.get('trade_date')}")
    volume_ratio = facts.get("volume_ratio")
    if not isinstance(volume_ratio, dict):
        raise ValueError("facts.volume_ratio missing or invalid")
    verification = volume_ratio.get("verification")
    if not isinstance(verification, dict):
        raise ValueError("volume_ratio.verification missing or invalid")
    if verification.get("status") != "confirmed":
        raise ValueError("historical pack must have volume_ratio.verification.status=confirmed")
    if verification.get("method") != vre.METHOD_HISTORICAL_FIVE_DAY:
        raise ValueError(f"historical pack method must be {vre.METHOD_HISTORICAL_FIVE_DAY}")
    if isinstance(volume_ratio.get("source_volume_checks"), dict):
        raise ValueError("historical pack already has source_volume_checks")


def build_historical_candidate_from_facts(
    *,
    facts: dict[str, Any],
    old_sha: str,
    target_date: str,
    symbol: str,
    timeout: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    assert_historical_migration_allowed(facts, symbol=symbol, target_date=target_date)
    current_vr = facts["volume_ratio"]
    confirmed_value = vre.positive_float(current_vr.get("confirmed_value"), field="volume_ratio.confirmed_value")
    fresh = gdf.fetch_volume_ratio_candidate(symbol, target_date, timeout)
    if not isinstance(fresh, dict):
        raise ValueError("unable to fetch historical volume-ratio candidate")
    if fresh.get("method") != vre.METHOD_HISTORICAL_FIVE_DAY or fresh.get("verification_status") != "confirmed":
        raise ValueError("fresh historical candidate did not reach confirmed dual-source status")
    fresh_value = vre.positive_float(fresh.get("candidate_value"), field="fresh.candidate_value")
    if abs(fresh_value - confirmed_value) > vre.HISTORICAL_VOLUME_RATIO_ABS_TOLERANCE:
        raise ValueError("fresh historical candidate does not match formal volume_ratio")
    checks = fresh.get("source_volume_checks")
    if not isinstance(checks, dict):
        raise ValueError("fresh historical candidate is missing source_volume_checks")
    for key in ("sohu_history", "tencent_history"):
        if key not in checks:
            raise ValueError(f"fresh historical candidate missing {key} check")
    migrated = copy.deepcopy(facts)
    migrated["volume_ratio"] = copy.deepcopy(current_vr)
    migrated["volume_ratio"]["source_volume_checks"] = copy.deepcopy(checks)
    migrated["volume_ratio"]["migration"] = {
        "old_file_sha256": old_sha,
        "migrated_at": utc_now_iso_z(),
        "tool_version": TOOL_VERSION,
        "tool": "tools/migrate_legacy_volume_ratio_evidence.py",
        "migration_type": "historical_dual_source_volume_evidence_enrichment",
    }
    summary = {
        "old_file_sha256": old_sha,
        "trade_date": target_date,
        "symbol": symbol,
        "calculated_values": {
            "sohu_history": checks["sohu_history"].get("calculated_value"),
            "tencent_history": checks["tencent_history"].get("calculated_value"),
        },
        "confirmed_value": confirmed_value,
        "migrated_at": migrated["volume_ratio"]["migration"]["migrated_at"],
    }
    return migrated, summary


def is_already_migrated(facts: dict[str, Any], *, target_date: str) -> bool:
    volume_ratio = facts.get("volume_ratio")
    verification = volume_ratio.get("verification") if isinstance(volume_ratio, dict) else None
    migration = volume_ratio.get("migration") if isinstance(volume_ratio, dict) else None
    profile = MIGRATION_PROFILES.get(target_date)
    return (
        isinstance(profile, dict)
        and isinstance(verification, dict)
        and verification.get("method") == profile["target_method"]
        and isinstance(migration, dict)
        and migration.get("migration_type") == profile["migration_type"]
    )


def build_candidate(*, input_path: Path, target_date: str, symbol: str, timeout: float, expected_input_sha256: str) -> tuple[dict[str, Any], dict[str, Any]]:
    _input_bytes, old_sha, facts = read_expected_json_bytes(input_path, expected_input_sha256, label="input")
    return build_candidate_from_facts(
        facts=facts,
        old_sha=old_sha,
        target_date=target_date,
        symbol=symbol,
        timeout=timeout,
    )


def build_candidate_from_facts(
    *,
    facts: dict[str, Any],
    old_sha: str,
    target_date: str,
    symbol: str,
    timeout: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    profile = migration_profile(target_date)
    if is_already_migrated(facts, target_date=target_date):
        migration = facts.get("volume_ratio", {}).get("migration", {})
        summary = {
            "status": "already_migrated",
            "input_sha256": old_sha,
            "old_file_sha256": migration.get("old_file_sha256") if isinstance(migration, dict) else None,
            "trade_date": facts.get("trade_date"),
            "symbol": facts.get("symbol"),
            "migrated_at": migration.get("migrated_at") if isinstance(migration, dict) else None,
        }
        return facts, summary
    method = facts.get("volume_ratio", {}).get("verification", {}).get("method")
    if method != profile["source_method"]:
        raise ValueError(
            f"migration profile {target_date} requires source method {profile['source_method']}"
        )
    if method == vre.METHOD_HISTORICAL_FIVE_DAY:
        return build_historical_candidate_from_facts(
            facts=facts,
            old_sha=old_sha,
            target_date=target_date,
            symbol=symbol,
            timeout=timeout,
        )
    assert_first_migration_allowed(facts, symbol=symbol, target_date=target_date)
    if facts.get("symbol") != symbol:
        raise ValueError(f"symbol mismatch: expected {symbol}, got {facts.get('symbol')}")
    if facts.get("trade_date") != target_date:
        raise ValueError(f"trade_date mismatch: expected {target_date}, got {facts.get('trade_date')}")

    quote = facts.get("quote")
    if not isinstance(quote, dict):
        raise ValueError("facts.quote missing or invalid")
    archived_ohlc = ohlc_from(quote, prefix="quote")
    prev_close = vre.finite_float(quote.get("prev_close"), field="quote.prev_close")
    pct_change = vre.finite_float(quote.get("pct_change"), field="quote.pct_change")
    amount = vre.finite_float(quote.get("amount"), field="quote.amount")
    turnover_rate = vre.finite_float(quote.get("turnover_rate"), field="quote.turnover_rate")

    volume_ratio = facts.get("volume_ratio")
    if not isinstance(volume_ratio, dict):
        raise ValueError("facts.volume_ratio missing or invalid")
    confirmed_value = vre.positive_float(volume_ratio.get("confirmed_value"), field="volume_ratio.confirmed_value")
    candidate_value = vre.positive_float(volume_ratio.get("candidate_value"), field="volume_ratio.candidate_value")
    assert_close(candidate_value, confirmed_value, tolerance=0.0, label="candidate/confirmed volume_ratio")
    verification = volume_ratio.get("verification")
    if not isinstance(verification, dict):
        raise ValueError("volume_ratio.verification missing or invalid")
    if verification.get("source_date") != target_date:
        raise ValueError("volume_ratio.verification.source_date does not match target_date")

    sohu = gdf.fetch_sohu_quote(None, symbol, target_date, timeout)
    if sohu.get("status") != "ok":
        raise ValueError(f"Sohu fetch failed: {sohu.get('status')} {sohu.get('error_message')}")
    sohu_quote = sohu.get("quote")
    if not isinstance(sohu_quote, dict):
        raise ValueError("Sohu quote missing")
    sohu_ohlc = ohlc_from(sohu_quote, prefix="sohu.quote")
    ohlc_tolerance = vre.OHLC_TOLERANCE
    vre.validate_ohlc_match(archived_ohlc, sohu_ohlc, tolerance=ohlc_tolerance, left_label="archived_ohlc", right_label="sohu_ohlc")

    target_row, window = sohu_target_and_window(sohu.get("rows") or [], target_date)
    calculated = gdf.derive_five_day_volume_ratio(sohu.get("rows") or [], target_date)
    if calculated is None:
        raise ValueError("Unable to derive five-day volume ratio from Sohu rows")
    volume_tolerance = vre.ARCHIVED_VOLUME_RATIO_TOLERANCE
    assert_close(float(calculated), confirmed_value, tolerance=volume_tolerance, label="volume_ratio recalculation")
    trade_dates = [gdf.record_date_text(row) for row in window]
    volumes = [vre.positive_float(row.get("volume"), field=f"volume[{gdf.record_date_text(row)}]") for row in window]

    migrated = copy.deepcopy(facts)
    migrated_volume_ratio = copy.deepcopy(volume_ratio)
    old_verification = copy.deepcopy(verification)
    migrated_at = utc_now_iso_z()
    migrated_volume_ratio["source"] = ARCHIVED_SOURCE
    migrated_volume_ratio["verification"] = {
        **old_verification,
        "status": "confirmed",
        "method": ARCHIVED_METHOD,
        "source": ARCHIVED_SOURCE,
        "source_date": target_date,
        "notes": (
            "legacy Tencent 2026-07-14 snapshot value retained from archived facts pack; "
            "Sohu historical OHLC and five-day volume evidence used for post-hoc reverification"
        ),
    }
    migrated_volume_ratio["legacy_verification"] = copy.deepcopy(old_verification)
    migrated_volume_ratio["archived_snapshot_source"] = {
        "source": "tencent_qt_direct_index_49",
        "source_date": target_date,
        "ohlc": archived_ohlc,
        "previous_close": prev_close,
        "pct_change": pct_change,
        "amount": amount,
        "turnover_rate": turnover_rate,
        "volume_ratio": confirmed_value,
        "original_fetched_at": old_verification.get("fetched_at"),
        "source_pack_paths": copy.deepcopy(CANONICAL_SOURCE_PACK_PATHS),
    }
    migrated_volume_ratio["historical_ohlc_check"] = vre.build_ohlc_check(
        archived_source="tencent_qt_direct_index_49",
        archived_source_date=target_date,
        archived_ohlc=archived_ohlc,
        historical_source=vre.SOHU_HISTORY_SOURCE,
        historical_source_date=target_date,
        historical_ohlc=sohu_ohlc,
        tolerance=ohlc_tolerance,
        fetched_at=sohu.get("fetched_at"),
    )
    migrated_volume_ratio["historical_ohlc_check"]["source"] = vre.SOHU_HISTORY_SOURCE
    migrated_volume_ratio["historical_ohlc_check"]["source_date"] = target_date
    migrated_volume_ratio["five_day_volume_check"] = vre.build_five_day_volume_check(
        source=vre.SOHU_HISTORY_SOURCE,
        trade_dates=trade_dates,
        volumes=volumes,
        target_date=target_date,
        expected_value=confirmed_value,
        tolerance=volume_tolerance,
        fetched_at=sohu.get("fetched_at"),
    )
    migrated_volume_ratio["cross_check"] = vre.build_cross_check(
        value=migrated_volume_ratio["five_day_volume_check"]["calculated_value"],
        confirmed_value=confirmed_value,
        source=vre.SOHU_DERIVED_CROSS_CHECK_SOURCE,
        source_date=target_date,
        tolerance=vre.ARCHIVED_CROSS_CHECK_TOLERANCE,
    )
    migrated_volume_ratio["migration"] = {
        "old_file_sha256": old_sha,
        "migrated_at": migrated_at,
        "tool_version": TOOL_VERSION,
        "tool": "tools/migrate_legacy_volume_ratio_evidence.py",
        "migration_type": "legacy_archived_tencent_snapshot_reverification",
    }
    migrated["volume_ratio"] = migrated_volume_ratio

    summary = {
        "old_file_sha256": old_sha,
        "trade_date": target_date,
        "symbol": symbol,
        "archived_ohlc": archived_ohlc,
        "sohu_ohlc": sohu_ohlc,
        "trade_dates": trade_dates,
        "volumes": volumes,
        "calculated_value": float(calculated),
        "confirmed_value": confirmed_value,
        "migrated_at": migrated_at,
    }
    return migrated, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate legacy volume-ratio evidence for a facts pack")
    parser.add_argument("--input", help="Existing facts JSON")
    parser.add_argument("--output", help=argparse.SUPPRESS)
    parser.add_argument("--candidate-dir", help="Directory for generated candidate files; defaults to the system temp directory")
    parser.add_argument("--expected-input-sha256", dest="expected_input_sha256")
    parser.add_argument("--symbol", default="300274")
    parser.add_argument("--date", default="2026-07-14")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--summary", help="Optional summary JSON path")
    parser.add_argument("--review-file", default="sungrow/reviews/sungrow_review_2026-07-14.md")
    parser.add_argument("--promote", action="store_true", help="Promote a validated candidate into the official path")
    parser.add_argument("--candidate", help="Candidate JSON for --promote")
    parser.add_argument("--official", help="Official JSON for --promote")
    parser.add_argument("--expected-candidate-sha256", dest="expected_candidate_sha256")
    parser.add_argument("--expected-official-sha256", dest="expected_official_sha256")
    parser.add_argument(
        "--lock-dir",
        help="Override the shared official-facts lock directory (tests only)",
    )
    return parser.parse_args()


def _flatten_leaf_paths(value: Any, path: tuple[str, ...]) -> list[tuple[str, ...]]:
    if isinstance(value, dict) and value:
        leaves: list[tuple[str, ...]] = []
        for key in sorted(value, key=str):
            leaves.extend(_flatten_leaf_paths(value[key], (*path, str(key))))
        return leaves
    return [path]


def _diff_leaf_paths(left: Any, right: Any, path: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    if type(left) is not type(right):
        return sorted(set(_flatten_leaf_paths(left, path) + _flatten_leaf_paths(right, path)))
    if isinstance(left, dict):
        diffs: list[tuple[str, ...]] = []
        for key in sorted(set(left) | set(right), key=str):
            child = (*path, str(key))
            if key not in left:
                diffs.extend(_flatten_leaf_paths(right[key], child))
            elif key not in right:
                diffs.extend(_flatten_leaf_paths(left[key], child))
            else:
                diffs.extend(_diff_leaf_paths(left[key], right[key], child))
        return diffs
    return [] if left == right else [path]


def _path_text(path: tuple[str, ...]) -> str:
    return ".".join(path) or "<root>"


def _get_path(mapping: dict[str, Any], path_text: str) -> Any:
    current: Any = mapping
    for part in path_text.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"candidate is missing required leaf path: {path_text}")
        current = current[part]
    return current


def migration_profile(target_date: str) -> dict[str, Any]:
    profile = MIGRATION_PROFILES.get(target_date)
    if profile is None:
        raise ValueError(f"no migration profile for trade_date {target_date}")
    return profile

def _archived_verification(old_verification: dict[str, Any], target_date: str) -> dict[str, Any]:
    expected = copy.deepcopy(old_verification)
    expected.update(
        {
            "status": "confirmed",
            "method": ARCHIVED_METHOD,
            "source": ARCHIVED_SOURCE,
            "source_date": target_date,
            "notes": (
                f"legacy Tencent {target_date} snapshot value retained from archived facts pack; "
                "Sohu historical OHLC and five-day volume evidence used for post-hoc reverification"
            ),
        }
    )
    return expected


def _archived_snapshot_from_official(official: dict[str, Any], target_date: str) -> dict[str, Any]:
    quote = official.get("quote")
    volume_ratio = official.get("volume_ratio")
    verification = volume_ratio.get("verification") if isinstance(volume_ratio, dict) else None
    if not isinstance(quote, dict) or not isinstance(volume_ratio, dict) or not isinstance(verification, dict):
        raise ValueError("locked official is missing quote or legacy volume-ratio evidence")
    fetched_at = verification.get("fetched_at")
    vre.parse_timezone_datetime(fetched_at, field="volume_ratio.verification.fetched_at")
    return {
        "source": vre.TENCENT_ARCHIVED_SNAPSHOT_SOURCE,
        "source_date": target_date,
        "ohlc": ohlc_from(quote, prefix="quote"),
        "previous_close": vre.finite_float(quote.get("prev_close"), field="quote.prev_close"),
        "pct_change": vre.finite_float(quote.get("pct_change"), field="quote.pct_change"),
        "amount": vre.finite_float(quote.get("amount"), field="quote.amount"),
        "turnover_rate": vre.finite_float(quote.get("turnover_rate"), field="quote.turnover_rate"),
        "volume_ratio": vre.positive_float(
            volume_ratio.get("confirmed_value"),
            field="volume_ratio.confirmed_value",
        ),
        "original_fetched_at": fetched_at,
        "source_pack_paths": copy.deepcopy(CANONICAL_SOURCE_PACK_PATHS),
    }


def expected_candidate_from_locked_official(
    official: dict[str, Any],
    candidate: dict[str, Any],
    *,
    expected_official_sha256: str,
    target_date: str,
) -> dict[str, Any]:
    profile = migration_profile(target_date)
    if official.get("trade_date") != target_date or candidate.get("trade_date") != target_date:
        raise ValueError("migration profile trade_date mismatch")
    expected = copy.deepcopy(official)
    old_volume_ratio = official.get("volume_ratio")
    if not isinstance(old_volume_ratio, dict):
        raise ValueError("locked official volume_ratio is missing")
    old_verification = old_volume_ratio.get("verification")
    if not isinstance(old_verification, dict):
        raise ValueError("locked official volume_ratio.verification is missing")
    if old_verification.get("method") != profile["source_method"]:
        raise ValueError("locked official does not match migration profile source method")

    if target_date == "2026-07-14":
        expected_volume_ratio = expected["volume_ratio"]
        expected_volume_ratio["source"] = ARCHIVED_SOURCE
        expected_volume_ratio["verification"] = _archived_verification(old_verification, target_date)
        expected_volume_ratio["legacy_verification"] = copy.deepcopy(old_verification)
        expected_volume_ratio["archived_snapshot_source"] = _archived_snapshot_from_official(
            official,
            target_date,
        )
        historical_fetched_at = _get_path(
            candidate,
            "volume_ratio.historical_ohlc_check.fetched_at",
        )
        vre.parse_timezone_datetime(
            historical_fetched_at,
            field="historical_ohlc_check.fetched_at",
        )
        historical_ohlc = {
            field: _get_path(candidate, f"volume_ratio.historical_ohlc_check.ohlc.{field}")
            for field in OHLC_FIELDS
        }
        historical_check = vre.build_ohlc_check(
            archived_source=vre.TENCENT_ARCHIVED_SNAPSHOT_SOURCE,
            archived_source_date=target_date,
            archived_ohlc=expected_volume_ratio["archived_snapshot_source"]["ohlc"],
            historical_source=vre.SOHU_HISTORY_SOURCE,
            historical_source_date=target_date,
            historical_ohlc=historical_ohlc,
            tolerance=vre.OHLC_TOLERANCE,
            fetched_at=historical_fetched_at,
        )
        historical_check["source"] = vre.SOHU_HISTORY_SOURCE
        historical_check["source_date"] = target_date
        expected_volume_ratio["historical_ohlc_check"] = historical_check

        five_day_fetched_at = _get_path(
            candidate,
            "volume_ratio.five_day_volume_check.fetched_at",
        )
        vre.parse_timezone_datetime(
            five_day_fetched_at,
            field="five_day_volume_check.fetched_at",
        )
        five_day = vre.build_five_day_volume_check(
            source=vre.SOHU_HISTORY_SOURCE,
            trade_dates=_get_path(candidate, "volume_ratio.five_day_volume_check.trade_dates"),
            volumes=_get_path(candidate, "volume_ratio.five_day_volume_check.volumes"),
            target_date=target_date,
            expected_value=old_volume_ratio.get("confirmed_value"),
            tolerance=vre.ARCHIVED_VOLUME_RATIO_TOLERANCE,
            fetched_at=five_day_fetched_at,
        )
        expected_volume_ratio["five_day_volume_check"] = five_day
        expected_volume_ratio["cross_check"] = vre.build_cross_check(
            value=five_day.get("calculated_value"),
            confirmed_value=old_volume_ratio.get("confirmed_value"),
            source=vre.SOHU_DERIVED_CROSS_CHECK_SOURCE,
            source_date=target_date,
            tolerance=vre.ARCHIVED_CROSS_CHECK_TOLERANCE,
        )
    else:
        expected_checks: dict[str, Any] = {}
        for source in (vre.SOHU_HISTORY_SOURCE, vre.TENCENT_HISTORY_SOURCE):
            fetched_at = _get_path(
                candidate,
                f"volume_ratio.source_volume_checks.{source}.fetched_at",
            )
            vre.parse_timezone_datetime(
                fetched_at,
                field=f"source_volume_checks.{source}.fetched_at",
            )
            expected_checks[source] = vre.build_five_day_volume_check(
                source=source,
                trade_dates=_get_path(
                    candidate,
                    f"volume_ratio.source_volume_checks.{source}.trade_dates",
                ),
                volumes=_get_path(
                    candidate,
                    f"volume_ratio.source_volume_checks.{source}.volumes",
                ),
                target_date=target_date,
                expected_value=old_volume_ratio.get("confirmed_value"),
                tolerance=vre.HISTORICAL_VOLUME_RATIO_TOLERANCE,
                fetched_at=fetched_at,
            )
        expected["volume_ratio"]["source_volume_checks"] = expected_checks

    migrated_at = _get_path(candidate, "volume_ratio.migration.migrated_at")
    vre.parse_timezone_datetime(migrated_at, field="volume_ratio.migration.migrated_at")
    expected["volume_ratio"]["migration"] = {
        "old_file_sha256": expected_official_sha256,
        "migrated_at": migrated_at,
        "tool_version": TOOL_VERSION,
        "tool": "tools/migrate_legacy_volume_ratio_evidence.py",
        "migration_type": profile["migration_type"],
    }
    return expected


def compare_profiled_candidate(
    official: dict[str, Any],
    candidate: dict[str, Any],
    *,
    expected_official_sha256: str,
    target_date: str,
) -> None:
    profile = migration_profile(target_date)
    changed_paths = {_path_text(path) for path in _diff_leaf_paths(official, candidate)}
    forbidden = sorted(changed_paths - profile["leaf_paths"])
    if forbidden:
        raise ValueError(f"non-profile leaf changed: {', '.join(forbidden[:10])}")
    expected = expected_candidate_from_locked_official(
        official,
        candidate,
        expected_official_sha256=expected_official_sha256,
        target_date=target_date,
    )
    mismatches = [_path_text(path) for path in _diff_leaf_paths(expected, candidate)]
    if mismatches:
        raise ValueError(f"candidate does not match deterministic migration profile: {', '.join(mismatches[:10])}")


def promote_candidate(args: argparse.Namespace) -> dict[str, Any]:
    if not args.candidate or not args.official or not args.expected_candidate_sha256 or not args.expected_official_sha256:
        raise ValueError("--promote requires --candidate, --official, --expected-candidate-sha256, and --expected-official-sha256")
    candidate_path = Path(args.candidate)
    official_path = Path(args.official)
    candidate_bytes, candidate_sha, candidate = read_expected_json_bytes(
        candidate_path,
        args.expected_candidate_sha256,
        label="candidate",
    )
    migration = candidate.get("volume_ratio", {}).get("migration", {})
    if not isinstance(migration, dict) or migration.get("old_file_sha256") != args.expected_official_sha256:
        raise ValueError("candidate migration.old_file_sha256 must equal expected official sha256")
    lock_dir = Path(args.lock_dir) if getattr(args, "lock_dir", None) else None
    final_official_sha: str | None = None
    with ofl.official_facts_lock(official_path, lock_dir=lock_dir) as lock_state:
        official_bytes, actual_sha = ofl.read_locked_official(
            official_path,
            expected_sha256=args.expected_official_sha256,
            lock_state=lock_state,
        )
        if official_bytes is None or actual_sha is None:
            raise ValueError("official facts must exist for promotion")
        official = load_json_from_bytes(official_bytes)
        assert_validator_pass_bytes(
            candidate_bytes,
            review_file=args.review_file,
            target_date=args.date,
            migration_base_bytes=official_bytes,
        )
        compare_profiled_candidate(
            official,
            candidate,
            expected_official_sha256=args.expected_official_sha256,
            target_date=args.date,
        )

        tmp = official_path.with_name(f".{official_path.name}.promote-{os.getpid()}")
        try:
            fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(candidate_bytes)
                handle.flush()
                os.fsync(handle.fileno())
            final_official_sha = sha256_file(official_path)
            if final_official_sha != args.expected_official_sha256:
                raise ValueError(
                    f"official sha256 changed before replace: expected {args.expected_official_sha256}, got {final_official_sha}"
                )
            if sha256_bytes(candidate_bytes) != candidate_sha:
                raise ValueError("candidate bytes changed before replace")
            os.replace(tmp, official_path)
            try:
                dir_fd = os.open(str(official_path.parent), os.O_DIRECTORY)
            except OSError:
                pass
            else:
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            final_bytes, final_official_sha = ofl.read_current_official(
                official_path,
                lock_state=lock_state,
            )
            if final_bytes != candidate_bytes or final_official_sha != candidate_sha:
                raise RuntimeError("promoted official bytes do not match the pinned candidate")
        finally:
            tmp.unlink(missing_ok=True)
    if final_official_sha is None:
        raise RuntimeError("promote completed without a locked final sha256")
    return {
        "status": "promoted",
        "official": str(official_path),
        "old_official_sha256": args.expected_official_sha256,
        "candidate_sha256": candidate_sha,
        "new_official_sha256": final_official_sha,
    }


def main() -> int:
    args = parse_args()
    if args.promote:
        print(json.dumps(promote_candidate(args), ensure_ascii=False, sort_keys=True))
        return 0
    if args.output:
        raise SystemExit("--output is not supported in candidate mode; use --candidate-dir for test temp directories")
    if not args.input or not args.expected_input_sha256:
        raise SystemExit("--input and --expected-input-sha256 are required in candidate mode")
    candidate_dir = Path(args.candidate_dir) if args.candidate_dir else Path(tempfile.gettempdir())
    resolved_candidate_dir = candidate_dir.resolve()
    forbidden_dir = (REPO_ROOT / "data" / "daily").resolve()
    if resolved_candidate_dir == forbidden_dir or forbidden_dir in resolved_candidate_dir.parents:
        raise SystemExit("candidate mode must not write into repository data/daily")
    candidate, summary = build_candidate(
        input_path=Path(args.input),
        target_date=args.date,
        symbol=args.symbol,
        timeout=args.timeout,
        expected_input_sha256=args.expected_input_sha256,
    )
    if summary.get("status") == "already_migrated":
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 0
    candidate_bytes = json_bytes(candidate)
    candidate_sha = sha256_bytes(candidate_bytes)
    candidate_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb",
        dir=str(candidate_dir),
        prefix=f"{args.symbol}_{args.date}_",
        suffix=".candidate.json",
        delete=False,
    ) as handle:
        candidate_path = Path(handle.name)
        os.chmod(candidate_path, 0o600)
        handle.write(candidate_bytes)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        assert_validator_pass_bytes(candidate_bytes, review_file=args.review_file, target_date=args.date)
    except Exception:
        candidate_path.unlink(missing_ok=True)
        raise
    if args.summary:
        atomic_write_json(Path(args.summary), summary)
    print(
        json.dumps(
            {
                "status": "ok",
                "candidate": str(candidate_path),
                "candidate_sha256": candidate_sha,
                **summary,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
