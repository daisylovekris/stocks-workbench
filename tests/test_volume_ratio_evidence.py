import math

import pytest

from tools import volume_ratio_evidence as vre


def test_compare_ohlc_passes_within_tolerance():
    result = vre.validate_ohlc_match(
        {"open": 108.0, "high": 109.26, "low": 100.73, "close": 108.29},
        {"open": "108.00", "high": "109.26", "low": "100.73", "close": "108.29"},
        tolerance=0.02,
    )
    assert result["status"] == "passed"


def test_compare_ohlc_rejects_non_finite_values():
    with pytest.raises(vre.EvidenceError):
        vre.validate_ohlc_match(
            {"open": math.nan, "high": 109.26, "low": 100.73, "close": 108.29},
            {"open": 108.0, "high": 109.26, "low": 100.73, "close": 108.29},
        )


def test_validate_six_day_window_rejects_disorder_duplicate_and_bad_volume():
    dates = ["2026-07-07", "2026-07-08", "2026-07-09", "2026-07-10", "2026-07-13", "2026-07-14"]
    volumes = [442203, 413086, 673516, 939380, 745683, 960311]
    assert vre.validate_six_day_window(dates, volumes, target_date="2026-07-14")[0] == dates
    with pytest.raises(vre.EvidenceError):
        vre.validate_six_day_window([dates[1], dates[0], *dates[2:]], volumes, target_date="2026-07-14")
    with pytest.raises(vre.EvidenceError):
        vre.validate_six_day_window([*dates[:2], dates[1], *dates[3:]], volumes, target_date="2026-07-14")
    with pytest.raises(vre.EvidenceError):
        vre.validate_six_day_window(dates, [*volumes[:3], 0, *volumes[4:]], target_date="2026-07-14")


@pytest.mark.parametrize(
    "bad_date",
    ["0001-01-01", "2026-7-14", "", " 2026-07-14", "2026-13-01", "2026-02-30"],
)
def test_parse_trade_date_rejects_non_canonical_or_invalid_dates(bad_date):
    with pytest.raises(vre.EvidenceError):
        vre.parse_trade_date(bad_date)


def test_validate_six_day_window_rejects_fake_ancient_dates():
    with pytest.raises(vre.EvidenceError):
        vre.validate_six_day_window(
            ["0001-01-01", "0001-01-02", "0001-01-03", "0001-01-04", "0001-01-05", "2026-07-14"],
            [1, 1, 1, 1, 1, 1],
            target_date="2026-07-14",
        )


@pytest.mark.parametrize("bad_tolerance", [1e9, -0.02, "nan", "inf", 0.03])
def test_tolerance_metadata_must_equal_authoritative_constant(bad_tolerance):
    with pytest.raises(vre.EvidenceError):
        vre.validate_tolerance_metadata(bad_tolerance, vre.OHLC_ABS_TOLERANCE)


def test_formula_must_match_authoritative_id():
    with pytest.raises(vre.EvidenceError):
        vre.validate_formula("target / average")


def test_recalculate_volume_ratio_from_real_window():
    volumes = [442203.0, 413086.0, 673516.0, 939380.0, 745683.0, 960311.0]
    assert vre.calculate_volume_ratio_from_window(volumes) == 1.49
    result = vre.validate_recalculated_volume_ratio(
        trade_dates=["2026-07-07", "2026-07-08", "2026-07-09", "2026-07-10", "2026-07-13", "2026-07-14"],
        volumes=volumes,
        target_date="2026-07-14",
        calculated_value=1.49,
        expected_value=1.49,
        confirmed_value=1.49,
        tolerance=0.02,
    )
    assert result["status"] == "passed"


def test_recalculate_volume_ratio_rejects_stale_declared_value():
    with pytest.raises(vre.EvidenceError):
        vre.validate_recalculated_volume_ratio(
            trade_dates=["2026-07-07", "2026-07-08", "2026-07-09", "2026-07-10", "2026-07-13", "2026-07-14"],
            volumes=[1, 1, 1, 1, 1, 999],
            target_date="2026-07-14",
            calculated_value=1.49,
            expected_value=1.49,
            confirmed_value=1.49,
            tolerance=0.02,
        )


def test_timezone_datetime_requires_valid_timezone_text():
    assert vre.parse_timezone_datetime("2026-07-14T21:04:50Z").utcoffset() is not None
    for value in ("not-a-time", "2026-07-14T21:04:50", ""):
        with pytest.raises(vre.EvidenceError):
            vre.parse_timezone_datetime(value)


def test_archived_cross_check_is_canonical_and_recomputed():
    cross_check = vre.build_cross_check(
        value=1.49,
        confirmed_value=1.49,
        source=vre.SOHU_DERIVED_CROSS_CHECK_SOURCE,
        source_date="2026-07-14",
        tolerance=vre.ARCHIVED_CROSS_CHECK_TOLERANCE,
    )
    assert vre.validate_cross_check(
        cross_check,
        expected_value=1.49,
        confirmed_value=1.49,
        source=vre.SOHU_DERIVED_CROSS_CHECK_SOURCE,
        source_date="2026-07-14",
        tolerance=vre.ARCHIVED_CROSS_CHECK_TOLERANCE,
    ) == cross_check
    changed = dict(cross_check)
    changed["delta"] = 99
    with pytest.raises(vre.EvidenceError):
        vre.validate_cross_check(
            changed,
            expected_value=1.49,
            confirmed_value=1.49,
            source=vre.SOHU_DERIVED_CROSS_CHECK_SOURCE,
            source_date="2026-07-14",
            tolerance=vre.ARCHIVED_CROSS_CHECK_TOLERANCE,
        )
