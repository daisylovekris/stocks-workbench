"""Pure helpers for volume-ratio evidence contracts.

No network, file I/O, or trading judgment lives here.  The generator,
migration tool, and validator share these functions so evidence construction and
evidence validation use the same OHLC and volume-ratio semantics.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import math
from typing import Any


OHLC_FIELDS = ("open", "high", "low", "close")

METHOD_SAME_DAY_SNAPSHOT = "same_day_snapshot_plus_sohu_five_day_cross_check"
METHOD_ARCHIVED_REVERIFICATION = "archived_tencent_snapshot_plus_sohu_historical_reverification"
METHOD_HISTORICAL_FIVE_DAY = "historical_five_day_volume_cross_check"
METHOD_LEGACY_MANUAL = "legacy_manual_confirmation"

REGISTERED_VOLUME_RATIO_METHODS = {
    METHOD_SAME_DAY_SNAPSHOT,
    METHOD_ARCHIVED_REVERIFICATION,
    METHOD_HISTORICAL_FIVE_DAY,
    METHOD_LEGACY_MANUAL,
}

SOHU_HISTORY_SOURCE = "sohu_history"
TENCENT_HISTORY_SOURCE = "tencent_history"
TENCENT_ARCHIVED_SNAPSHOT_SOURCE = "tencent_qt_direct_index_49"
ARCHIVED_COMPOSITE_SOURCE = "archived_tencent_snapshot+sohu_history"
LEGACY_SNAPSHOT_COMPOSITE_SOURCE = "tencent_qt_direct_index_49+sohu_five_day_volume"
SOHU_DERIVED_CROSS_CHECK_SOURCE = "sohu_five_day_volume_derived"
CANONICAL_ARCHIVED_SOURCE_PACK_PATHS = (
    "quote.open",
    "quote.high",
    "quote.low",
    "quote.close",
    "quote.prev_close",
    "quote.pct_change",
    "quote.amount",
    "quote.turnover_rate",
    "volume_ratio.candidate_value",
    "volume_ratio.confirmed_value",
    "volume_ratio.verification.fetched_at",
)
METHOD_ALLOWED_STATUSES = {
    METHOD_SAME_DAY_SNAPSHOT: {"confirmed"},
    METHOD_ARCHIVED_REVERIFICATION: {"confirmed"},
    METHOD_HISTORICAL_FIVE_DAY: {"confirmed", "derived_confirmed"},
    METHOD_LEGACY_MANUAL: {"manual_confirmed"},
}
OHLC_ABS_TOLERANCE = 0.02
SAME_DAY_VOLUME_RATIO_ABS_TOLERANCE = 0.05
HISTORICAL_VOLUME_RATIO_ABS_TOLERANCE = 0.01
ARCHIVED_VOLUME_RATIO_ABS_TOLERANCE = 0.02
ARCHIVED_CROSS_CHECK_ABS_TOLERANCE = SAME_DAY_VOLUME_RATIO_ABS_TOLERANCE
VOLUME_RATIO_FORMULA_ID = "target_day_volume / mean(prior_5_trading_day_volume)"

OHLC_TOLERANCE = OHLC_ABS_TOLERANCE
SAME_DAY_VOLUME_RATIO_TOLERANCE = SAME_DAY_VOLUME_RATIO_ABS_TOLERANCE
HISTORICAL_VOLUME_RATIO_TOLERANCE = HISTORICAL_VOLUME_RATIO_ABS_TOLERANCE
ARCHIVED_VOLUME_RATIO_TOLERANCE = ARCHIVED_VOLUME_RATIO_ABS_TOLERANCE
ARCHIVED_CROSS_CHECK_TOLERANCE = ARCHIVED_CROSS_CHECK_ABS_TOLERANCE


class EvidenceError(ValueError):
    """Raised when evidence fails the shared contract."""


def parse_timezone_datetime(value: object, *, field: str = "timestamp") -> datetime:
    if not isinstance(value, str) or value != value.strip() or not value:
        raise EvidenceError(f"{field} must be a non-empty datetime string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EvidenceError(f"{field} must be a valid ISO datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise EvidenceError(f"{field} must include a timezone")
    return parsed


def parse_trade_date(value: object) -> date:
    if not isinstance(value, str):
        raise EvidenceError("trade date must be an ISO date string")
    if value != value.strip() or not value:
        raise EvidenceError("trade date must not contain surrounding whitespace")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise EvidenceError(f"trade date is not a valid ISO date: {value!r}") from exc
    if value != parsed.isoformat():
        raise EvidenceError(f"trade date must be canonical ISO format: {value!r}")
    if parsed.year < 1900:
        raise EvidenceError(f"trade date year is outside supported market-data range: {value!r}")
    return parsed


def _decimal(value: Any, *, field: str) -> Decimal:
    if isinstance(value, bool):
        raise EvidenceError(f"{field} must be a finite decimal number, got bool")
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise EvidenceError(f"{field} must be a finite decimal number") from exc
    if not decimal_value.is_finite():
        raise EvidenceError(f"{field} must be finite")
    return decimal_value


def validate_tolerance_metadata(value: Any, expected: float, *, field: str = "tolerance") -> float:
    actual_decimal = _decimal(value, field=field)
    expected_decimal = _decimal(expected, field=f"{field}.expected")
    if actual_decimal != expected_decimal:
        raise EvidenceError(f"{field} must equal authoritative tolerance {expected_decimal}")
    expected_float = float(expected_decimal)
    if expected_float < 0:
        raise EvidenceError(f"{field}.expected must not be negative")
    return expected_float


def validate_formula(value: Any, *, field: str = "formula") -> str:
    if value != VOLUME_RATIO_FORMULA_ID:
        raise EvidenceError(f"{field} must equal {VOLUME_RATIO_FORMULA_ID!r}")
    return VOLUME_RATIO_FORMULA_ID


def finite_float(value: Any, *, field: str = "value") -> float:
    if isinstance(value, bool):
        raise EvidenceError(f"{field} must be a finite number, got bool")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceError(f"{field} must be a finite number") from exc
    if not math.isfinite(numeric):
        raise EvidenceError(f"{field} must be finite")
    return numeric


def positive_float(value: Any, *, field: str = "value") -> float:
    numeric = finite_float(value, field=field)
    if numeric <= 0:
        raise EvidenceError(f"{field} must be positive")
    return numeric


def normalize_ohlc(mapping: Any, *, prefix: str = "ohlc") -> dict[str, float]:
    if not isinstance(mapping, dict):
        raise EvidenceError(f"{prefix} must be an object")
    return {field: finite_float(mapping.get(field), field=f"{prefix}.{field}") for field in OHLC_FIELDS}


def compare_ohlc(
    left: Any,
    right: Any,
    *,
    tolerance: float = OHLC_ABS_TOLERANCE,
    left_label: str = "left",
    right_label: str = "right",
) -> dict[str, Any]:
    left_ohlc = normalize_ohlc(left, prefix=left_label)
    right_ohlc = normalize_ohlc(right, prefix=right_label)
    tolerance_value = finite_float(tolerance, field="tolerance")
    field_results = {}
    for field in OHLC_FIELDS:
        delta = abs(left_ohlc[field] - right_ohlc[field])
        field_results[field] = {
            "left": left_ohlc[field],
            "right": right_ohlc[field],
            "delta": delta,
            "matched": delta <= tolerance_value,
        }
    status = "passed" if all(result["matched"] for result in field_results.values()) else "failed"
    return {
        "status": status,
        "tolerance": tolerance_value,
        "fields": list(OHLC_FIELDS),
        "field_results": field_results,
    }


def validate_ohlc_match(
    left: Any,
    right: Any,
    *,
    tolerance: float = OHLC_ABS_TOLERANCE,
    left_label: str = "left",
    right_label: str = "right",
) -> dict[str, Any]:
    result = compare_ohlc(left, right, tolerance=tolerance, left_label=left_label, right_label=right_label)
    if result["status"] != "passed":
        mismatches = [field for field, field_result in result["field_results"].items() if not field_result["matched"]]
        raise EvidenceError(f"OHLC mismatch for fields: {', '.join(mismatches)}")
    return result


def validate_six_day_window(trade_dates: Any, volumes: Any, *, target_date: str) -> tuple[list[str], list[float]]:
    target = parse_trade_date(target_date)
    if not isinstance(trade_dates, list) or len(trade_dates) != 6:
        raise EvidenceError("five_day_volume_check.trade_dates must contain exactly six dates")
    parsed_dates = [parse_trade_date(item) for item in trade_dates]
    normalized_dates = [item.isoformat() for item in parsed_dates]
    if normalized_dates != trade_dates:
        raise EvidenceError("five_day_volume_check.trade_dates must use canonical ISO dates")
    if len(set(parsed_dates)) != len(parsed_dates):
        raise EvidenceError("five_day_volume_check.trade_dates contains duplicate dates")
    if parsed_dates != sorted(parsed_dates):
        raise EvidenceError("five_day_volume_check.trade_dates must be strictly increasing")
    if parsed_dates[-1] != target:
        raise EvidenceError("five_day_volume_check final trade date must equal target_date")
    if any(item >= target for item in parsed_dates[:-1]):
        raise EvidenceError("five_day_volume_check prior dates must be earlier than target_date")
    if not isinstance(volumes, list) or len(volumes) != 6:
        raise EvidenceError("five_day_volume_check.volumes must contain exactly six values")
    normalized_volumes = [positive_float(value, field=f"five_day_volume_check.volumes[{index}]") for index, value in enumerate(volumes)]
    return normalized_dates, normalized_volumes


def calculate_volume_ratio_from_window(volumes: list[float]) -> float:
    if len(volumes) != 6:
        raise EvidenceError("six volume values are required")
    prior_average = sum(volumes[:5]) / 5
    if prior_average <= 0:
        raise EvidenceError("prior five-day average volume must be positive")
    return round(volumes[5] / prior_average, 2)


def validate_recalculated_volume_ratio(
    *,
    trade_dates: Any,
    volumes: Any,
    target_date: str,
    calculated_value: Any,
    expected_value: Any,
    confirmed_value: Any,
    tolerance: float,
    authoritative_tolerance: float | None = None,
    formula: Any = VOLUME_RATIO_FORMULA_ID,
) -> dict[str, Any]:
    normalized_dates, normalized_volumes = validate_six_day_window(trade_dates, volumes, target_date=target_date)
    actual = calculate_volume_ratio_from_window(normalized_volumes)
    declared = finite_float(calculated_value, field="five_day_volume_check.calculated_value")
    expected = finite_float(expected_value, field="five_day_volume_check.expected_value")
    confirmed = finite_float(confirmed_value, field="volume_ratio.confirmed_value")
    expected_tolerance = authoritative_tolerance if authoritative_tolerance is not None else tolerance
    tolerance_value = validate_tolerance_metadata(tolerance, expected_tolerance, field="five_day_volume_check.tolerance")
    validate_formula(formula, field="five_day_volume_check.formula")
    for label, value in (("calculated_value", declared), ("expected_value", expected), ("confirmed_value", confirmed)):
        if abs(actual - value) > tolerance_value:
            raise EvidenceError(f"{label} does not match recomputed volume_ratio {actual}")
    return {
        "status": "passed",
        "trade_dates": normalized_dates,
        "volumes": normalized_volumes,
        "calculated_value": actual,
        "expected_value": expected,
        "confirmed_value": confirmed,
        "tolerance": tolerance_value,
    }


def build_ohlc_check(
    *,
    archived_source: str,
    archived_source_date: str,
    archived_ohlc: Any,
    historical_source: str,
    historical_source_date: str,
    historical_ohlc: Any,
    tolerance: float = OHLC_ABS_TOLERANCE,
    fetched_at: str | None = None,
) -> dict[str, Any]:
    comparison = validate_ohlc_match(
        archived_ohlc,
        historical_ohlc,
        tolerance=tolerance,
        left_label="archived_ohlc",
        right_label="historical_ohlc",
    )
    evidence = {
        "status": comparison["status"],
        "archived_source": archived_source,
        "archived_source_date": archived_source_date,
        "historical_source": historical_source,
        "historical_source_date": historical_source_date,
        "ohlc": normalize_ohlc(historical_ohlc, prefix="historical_ohlc"),
        "archived_ohlc": normalize_ohlc(archived_ohlc, prefix="archived_ohlc"),
        "tolerance": comparison["tolerance"],
        "compared_fields": list(OHLC_FIELDS),
        "field_results": comparison["field_results"],
    }
    if fetched_at:
        evidence["fetched_at"] = fetched_at
    return evidence


def build_five_day_volume_check(
    *,
    source: str,
    trade_dates: list[str],
    volumes: list[Any],
    target_date: str,
    expected_value: Any,
    tolerance: float,
    fetched_at: str | None = None,
) -> dict[str, Any]:
    normalized_dates, normalized_volumes = validate_six_day_window(trade_dates, volumes, target_date=target_date)
    calculated = calculate_volume_ratio_from_window(normalized_volumes)
    expected = finite_float(expected_value, field="expected_value")
    status = "passed" if abs(calculated - expected) <= finite_float(tolerance, field="tolerance") else "failed"
    evidence = {
        "status": status,
        "source": source,
        "trade_dates": normalized_dates,
        "volumes": normalized_volumes,
        "target_volume": normalized_volumes[-1],
        "calculated_value": calculated,
        "expected_value": expected,
        "tolerance": finite_float(tolerance, field="tolerance"),
        "formula": VOLUME_RATIO_FORMULA_ID,
    }
    if fetched_at:
        evidence["fetched_at"] = fetched_at
    if status != "passed":
        raise EvidenceError(f"calculated volume ratio {calculated} does not match expected {expected}")
    return evidence


def build_cross_check(
    *,
    value: Any,
    confirmed_value: Any,
    source: str,
    source_date: str,
    tolerance: float,
) -> dict[str, Any]:
    cross_value = finite_float(value, field="cross_check.value")
    confirmed = finite_float(confirmed_value, field="volume_ratio.confirmed_value")
    tolerance_value = finite_float(tolerance, field="cross_check.tolerance")
    return {
        "value": cross_value,
        "source": source,
        "source_date": source_date,
        "formula": VOLUME_RATIO_FORMULA_ID,
        "tolerance": tolerance_value,
        "delta": abs(cross_value - confirmed),
    }


def validate_cross_check(
    cross_check: Any,
    *,
    expected_value: Any,
    confirmed_value: Any,
    source: str,
    source_date: str,
    tolerance: float,
) -> dict[str, Any]:
    if not isinstance(cross_check, dict):
        raise EvidenceError("cross_check must be an object")
    expected = build_cross_check(
        value=expected_value,
        confirmed_value=confirmed_value,
        source=source,
        source_date=source_date,
        tolerance=tolerance,
    )
    if set(cross_check) != set(expected):
        raise EvidenceError("cross_check fields do not match the canonical field set")
    validate_formula(cross_check.get("formula"), field="cross_check.formula")
    validate_tolerance_metadata(
        cross_check.get("tolerance"),
        tolerance,
        field="cross_check.tolerance",
    )
    if cross_check.get("source") != source:
        raise EvidenceError(f"cross_check.source must be {source}")
    if cross_check.get("source_date") != source_date:
        raise EvidenceError("cross_check.source_date does not match target date")
    for field in ("value", "delta"):
        actual = finite_float(cross_check.get(field), field=f"cross_check.{field}")
        if abs(actual - expected[field]) > tolerance:
            raise EvidenceError(f"cross_check.{field} does not match recomputed value")
    return expected
