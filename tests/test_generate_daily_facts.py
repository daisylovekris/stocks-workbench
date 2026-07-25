import contextlib
import copy
import io
import json
import math
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import time

import tools.generate_daily_facts as gdf


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "daily_facts"
VALIDATOR = REPO_ROOT / "tools" / "validate_review_chain.py"
REVIEW_0710 = REPO_ROOT / "sungrow" / "reviews" / "sungrow_review_2026-07-10.md"


def load_fixture(name: str) -> dict:
    with (FIXTURE_ROOT / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def make_args(**overrides):
    defaults = {
        "symbol": "300274",
        "date": "2026-07-10",
        "output": str(REPO_ROOT / "tmp" / "daily_facts.json"),
        "source": "auto",
        "dry_run": False,
        "no_write": False,
        "write_official": False,
        "write_partial": False,
        "timeout": 15.0,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_fetcher(payload: dict):
    def _fetcher(*_args, **_kwargs):
        return copy.deepcopy(payload)

    return _fetcher


def make_error_fetcher(status: str, error_message: str):
    def _fetcher(*_args, **_kwargs):
        return {
            "status": status,
            "source": "mock",
            "target_date": "2026-07-10",
            "source_date": None,
            "quote": None,
            "source_pct_change": None,
            "fetched_at": "2026-07-13T00:00:00Z",
            "error_type": status,
            "error_message": error_message,
            "errors": [],
        }

    return _fetcher


def make_context_complete_pack(existing_name: str = "阳光电源") -> dict:
    pack = load_fixture("existing_manual_confirmed_status.json")
    pack["name"] = existing_name
    pack["needs_manual_check"] = {
        "volume_ratio": False,
        "market_indices": False,
        "sector_context": False,
        "disclosure_status": False,
        "news_policy_context": False,
    }
    pack["missing"] = {
        "market_indices": None,
        "sector_context": None,
        "disclosure_status": None,
        "news_policy_context": None,
    }
    return pack


def run_main(argv, run_outcome):
    with mock.patch.object(gdf, "run", return_value=run_outcome):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = gdf.main(argv)
    return exit_code, stdout.getvalue()


def make_quote_result(
    *,
    status: str,
    source: str,
    source_date: str,
    quote: dict | None = None,
    source_pct_change=None,
    error_type=None,
    error_message=None,
) -> dict:
    return {
        "status": status,
        "source": source,
        "target_date": "2026-07-10",
        "source_date": source_date,
        "quote": quote,
        "source_pct_change": source_pct_change,
        "fetched_at": "2026-07-13T00:00:00Z",
        "error_type": error_type,
        "error_message": error_message,
        "errors": [],
    }


def make_table_client(*, daily_rows=None, hist_rows=None):
    class TableClient:
        def stock_zh_a_daily(self, **_kwargs):
            return copy.deepcopy(daily_rows or [])

        def stock_zh_a_hist(self, **_kwargs):
            return copy.deepcopy(hist_rows or [])

    return TableClient()


def make_tencent_qt_fields(*, source_timestamp="20260714161436", volume_ratio="1.49", overrides=None):
    fields = [""] * 88
    values = {
        0: "51",
        1: "阳光电源",
        2: "300274",
        3: "108.29",
        4: "108.00",
        5: "108.00",
        30: source_timestamp,
        32: "0.27",
        33: "109.26",
        34: "100.73",
        35: "108.29/960311/10065149576",
        36: "960311",
        37: "1006515",
        38: "6.05",
        49: volume_ratio,
    }
    if overrides:
        values.update(overrides)
    for index, value in values.items():
        fields[index] = value
    return fields


def make_tencent_kline_payload(*, qt_fields=None, include_qt=True):
    stock_data = {
        "day": [
            ["2026-07-06", "126.000", "128.180", "131.900", "126.000", "522306.000"],
            ["2026-07-07", "127.450", "127.530", "131.680", "126.350", "442203.000"],
            ["2026-07-08", "127.000", "124.490", "130.130", "124.010", "413086.000"],
            ["2026-07-09", "124.000", "124.010", "124.600", "118.060", "673516.000"],
            ["2026-07-10", "123.170", "114.790", "123.800", "114.000", "939380.000"],
            ["2026-07-13", "112.540", "108.000", "114.050", "106.800", "745683.000"],
            ["2026-07-14", "108.000", "108.290", "109.260", "100.730", "960311.000"],
        ],
    }
    if include_qt:
        stock_data["qt"] = {"sz300274": qt_fields or make_tencent_qt_fields()}
    return json.dumps({"code": 0, "msg": "", "data": {"sz300274": stock_data}})


def make_sohu_volume_result():
    return {
        "status": "ok",
        "source": "sohu",
        "source_date": "2026-07-14",
        "quote": {
            "open": 108.0,
            "high": 109.26,
            "low": 100.73,
            "close": 108.29,
            "prev_close": 108.0,
            "amount": 100.6515,
            "turnover_rate": 6.05,
        },
        "fetched_at": "2026-07-15T00:00:00Z",
        "rows": [
            {"date": "2026-07-06", "volume": "522306"},
            {"date": "2026-07-07", "volume": "442203"},
            {"date": "2026-07-08", "volume": "413086"},
            {"date": "2026-07-09", "volume": "673516"},
            {"date": "2026-07-10", "volume": "939380"},
            {"date": "2026-07-13", "volume": "745683"},
            {"date": "2026-07-14", "volume": "960311"},
        ],
    }


class GenerateDailyFactsTests(unittest.TestCase):
    def test_quote_values_match_requires_complete_ohlc(self):
        left = {"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5}
        self.assertFalse(gdf._quote_values_match(left, {"open": 1.0}))
        self.assertFalse(gdf._quote_values_match(left, {"open": 1.0, "low": 0.5, "close": 1.5}))
        self.assertTrue(gdf._quote_values_match(left, {"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5}))
        self.assertFalse(gdf._quote_values_match(left, {"open": 1.0, "high": 2.03, "low": 0.5, "close": 1.5}))

    def test_quote_values_match_rejects_non_finite_and_boolean_ohlc_values(self):
        finite_left = {"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5}
        finite_right = {"open": 1.01, "high": 2.0, "low": 0.5, "close": 1.5}

        cases = [
            ("left nan", {"open": math.nan, "high": 2.0, "low": 0.5, "close": 1.5}, finite_right),
            ("right nan", finite_left, {"open": math.nan, "high": 2.0, "low": 0.5, "close": 1.5}),
            ("left +inf", {"open": math.inf, "high": 2.0, "low": 0.5, "close": 1.5}, finite_right),
            ("right +inf", finite_left, {"open": math.inf, "high": 2.0, "low": 0.5, "close": 1.5}),
            ("left -inf", {"open": -math.inf, "high": 2.0, "low": 0.5, "close": 1.5}, finite_right),
            ("right -inf", finite_left, {"open": -math.inf, "high": 2.0, "low": 0.5, "close": 1.5}),
            ("both nan", {"open": math.nan, "high": 2.0, "low": 0.5, "close": 1.5}, {"open": math.nan, "high": 2.0, "low": 0.5, "close": 1.5}),
            ("both +inf", {"open": math.inf, "high": 2.0, "low": 0.5, "close": 1.5}, {"open": math.inf, "high": 2.0, "low": 0.5, "close": 1.5}),
            ("both -inf", {"open": -math.inf, "high": 2.0, "low": 0.5, "close": 1.5}, {"open": -math.inf, "high": 2.0, "low": 0.5, "close": 1.5}),
            ("left bool", {"open": True, "high": 2.0, "low": 0.5, "close": 1.5}, finite_right),
            ("right bool", finite_left, {"open": False, "high": 2.0, "low": 0.5, "close": 1.5}),
        ]
        for label, left, right in cases:
            with self.subTest(label=label):
                self.assertFalse(gdf._quote_values_match(left, right))

    def test_quote_values_match_keeps_finite_tolerance_behavior(self):
        left = {"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5}
        within_tolerance = {"open": 1.019, "high": 2.0, "low": 0.5, "close": 1.5}
        outside_tolerance = {"open": 1.021, "high": 2.0, "low": 0.5, "close": 1.5}

        self.assertTrue(gdf._quote_values_match(left, within_tolerance))
        self.assertFalse(gdf._quote_values_match(left, outside_tolerance))

    def test_parse_tencent_snapshot_uses_close_field_mapping(self):
        snapshot = gdf.parse_tencent_snapshot(make_tencent_qt_fields())
        self.assertEqual(snapshot["source_date"], "2026-07-14")
        self.assertTrue(snapshot["is_closed"])
        self.assertEqual(snapshot["amount"], 100.65149576)
        self.assertEqual(snapshot["turnover_rate"], 6.05)
        self.assertEqual(snapshot["volume_ratio"], 1.49)
        self.assertEqual(snapshot["pct_change"], 0.27)

    def test_tencent_direct_same_day_snapshot_fills_amount_and_turnover(self):
        with mock.patch.object(gdf, "_http_get_text_direct", return_value=make_tencent_kline_payload()):
            result = gdf.fetch_tencent_direct_quote(None, "300274", "2026-07-14", 15.0)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["quote"]["amount"], 100.65149576)
        self.assertEqual(result["quote"]["turnover_rate"], 6.05)
        self.assertEqual(result["source_pct_change"], 0.27)
        self.assertEqual(result["field_sources"]["turnover_rate"], "tencent_qt_snapshot")
        self.assertEqual(result["source_name"], "阳光电源")

    def test_tencent_snapshot_missing_close_does_not_fill_amount_or_turnover(self):
        fields = make_tencent_qt_fields(overrides={3: ""})
        with (
            mock.patch.object(gdf, "_http_get_text_direct", return_value=make_tencent_kline_payload(qt_fields=fields)),
            mock.patch.object(gdf, "fetch_sohu_quote", return_value={"status": "network_error", "rows": []}),
        ):
            result = gdf.fetch_tencent_direct_quote(None, "300274", "2026-07-14", 15.0)
        self.assertIsNone(result["quote"]["amount"])
        self.assertIsNone(result["quote"]["turnover_rate"])
        self.assertNotIn("amount", result["field_sources"])
        self.assertNotIn("turnover_rate", result["field_sources"])

    def test_sohu_history_maps_amount_and_turnover(self):
        payload = (
            'historySearchHandler([{"status":0,"hq":['
            '["2026-07-14","108.00","108.29","0.29","0.27%","100.73","109.26",'
            '"960311","1006515.00","6.05%","164.00"],'
            '["2026-07-13","112.54","108.00","-6.79","-5.92%","106.80","114.05",'
            '"745683","816836.88","4.70%","209.00"]],"code":"cn_300274"}])'
        )
        with mock.patch.object(gdf, "_http_get_text_direct", return_value=payload):
            result = gdf.fetch_sohu_quote(None, "300274", "2026-07-13", 15.0)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["quote"]["amount"], 81.683688)
        self.assertEqual(result["quote"]["turnover_rate"], 4.7)
        self.assertEqual(result["source_pct_change"], -5.92)
        self.assertEqual(result["quote"]["prev_close"], 114.79)

    def test_sohu_fallback_missing_ohlc_does_not_fill_amount_or_turnover(self):
        sohu_result = make_quote_result(
            status="ok",
            source="sohu",
            source_date="2026-07-14",
            quote={
                "open": 108.0,
                "high": None,
                "low": 100.73,
                "close": 108.29,
                "prev_close": 108.0,
                "amount": 100.65149576,
                "turnover_rate": 6.05,
            },
            source_pct_change=0.27,
        )
        stale_snapshot = make_tencent_qt_fields(source_timestamp="20260713161436")
        with (
            mock.patch.object(gdf, "_http_get_text_direct", return_value=make_tencent_kline_payload(qt_fields=stale_snapshot)),
            mock.patch.object(gdf, "fetch_sohu_quote", return_value=sohu_result),
        ):
            result = gdf.fetch_tencent_direct_quote(None, "300274", "2026-07-14", 15.0)
        self.assertIsNone(result["quote"]["amount"])
        self.assertIsNone(result["quote"]["turnover_rate"])
        self.assertNotIn("amount", result["field_sources"])
        self.assertNotIn("turnover_rate", result["field_sources"])

    def test_tencent_direct_rejects_latest_snapshot_for_historical_date_and_uses_sohu(self):
        sohu_result = make_quote_result(
            status="ok",
            source="sohu",
            source_date="2026-07-13",
            quote={
                "open": 112.54,
                "high": 114.05,
                "low": 106.8,
                "close": 108.0,
                "prev_close": 114.79,
                "amount": 81.683688,
                "turnover_rate": 4.7,
            },
            source_pct_change=-5.92,
        )
        with (
            mock.patch.object(gdf, "_http_get_text_direct", return_value=make_tencent_kline_payload()),
            mock.patch.object(gdf, "fetch_sohu_quote", return_value=sohu_result),
        ):
            result = gdf.fetch_tencent_direct_quote(None, "300274", "2026-07-13", 15.0)
        self.assertEqual(result["quote"]["amount"], 81.683688)
        self.assertEqual(result["quote"]["turnover_rate"], 4.7)
        self.assertEqual(result["field_sources"]["turnover_rate"], "sohu_history")
        self.assertEqual(result["source_name"], "阳光电源")

    def test_volume_ratio_candidate_uses_same_day_snapshot(self):
        quote_text = f'v_sz300274="{"~".join(make_tencent_qt_fields())}";'
        def fake_http(url, **_kwargs):
            return quote_text if "qt.gtimg.cn" in url else make_tencent_kline_payload(include_qt=False)

        with (
            mock.patch.object(gdf, "_http_get_text_direct", side_effect=fake_http),
            mock.patch.object(gdf, "fetch_sohu_quote", return_value=make_sohu_volume_result()),
        ):
            candidate = gdf.fetch_volume_ratio_candidate("300274", "2026-07-14", 15.0)
        self.assertEqual(candidate["candidate_value"], 1.49)
        self.assertEqual(candidate["source_date"], "2026-07-14")
        self.assertEqual(candidate["verification_status"], "confirmed")
        self.assertEqual(candidate["confirmed_by"], "automation_cross_check")
        self.assertEqual(candidate["cross_check"]["value"], 1.49)
        self.assertEqual(candidate["snapshot_ohlc_check"]["status"], "passed")
        self.assertEqual(candidate["snapshot_ohlc_check"]["compared_fields"], ["open", "high", "low", "close"])
        self.assertEqual(candidate["snapshot_ohlc_check"]["snapshot_source"], "tencent_qt_direct_index_49")
        self.assertEqual(candidate["snapshot_ohlc_check"]["matched_to"], "sohu_history")
        self.assertIn("field_results", candidate["snapshot_ohlc_check"])
        self.assertEqual(candidate["five_day_volume_check"]["status"], "passed")
        self.assertEqual(candidate["five_day_volume_check"]["source"], "sohu_history")
        self.assertEqual(candidate["five_day_volume_check"]["calculated_value"], 1.49)

    def test_generator_same_day_volume_ratio_facts_pass_validator(self):
        quote_text = f'v_sz300274="{"~".join(make_tencent_qt_fields())}";'

        def fake_http(url, **_kwargs):
            return quote_text if "qt.gtimg.cn" in url else make_tencent_kline_payload(include_qt=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            review = Path(tmpdir) / "review.md"
            review.write_text("## 当前结论\n仅作观察，不输出买卖动作。\n", encoding="utf-8")
            existing = {
                "symbol": "300274",
                "trade_date": "2026-07-14",
                "name": "阳光电源",
                "needs_manual_check": {
                    "volume_ratio": False,
                    "market_indices": False,
                    "sector_context": False,
                    "disclosure_status": False,
                    "news_policy_context": False,
                },
                "missing": {
                    "market_indices": None,
                    "sector_context": None,
                    "disclosure_status": None,
                    "news_policy_context": None,
                },
            }
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), date="2026-07-14", source="tencent")
            quote_result = make_quote_result(
                status="ok",
                source="tencent",
                source_date="2026-07-14",
                quote={
                    "open": 108.0,
                    "high": 109.26,
                    "low": 100.73,
                    "close": 108.29,
                    "prev_close": 108.0,
                    "amount": 100.65149576,
                    "turnover_rate": 6.05,
                },
                source_pct_change=0.27,
            )
            quote_result["field_sources"] = {"amount": "tencent_qt_snapshot", "turnover_rate": "tencent_qt_snapshot"}
            with (
                mock.patch.object(gdf, "_http_get_text_direct", side_effect=fake_http),
                mock.patch.object(gdf, "fetch_sohu_quote", return_value=make_sohu_volume_result()),
            ):
                outcome = gdf.run(
                    args,
                    fetch_primary=make_fetcher(quote_result),
                    fetch_fallback=make_error_fetcher("source_error", "unused"),
                    volume_ratio_candidate_provider=gdf.fetch_volume_ratio_candidate,
                )

            self.assertEqual(outcome.exit_code, gdf.EXIT_SUCCESS)
            facts = outcome.facts_pack
            self.assertEqual(facts["volume_ratio"]["verification"]["method"], "same_day_snapshot_plus_sohu_five_day_cross_check")
            self.assertIn("snapshot_ohlc_check", facts["volume_ratio"])
            self.assertIn("five_day_volume_check", facts["volume_ratio"])
            self.assertFalse(outcome.wrote_file)
            result = subprocess.run(
                [
                    "python3",
                    str(VALIDATOR),
                    "--files",
                    str(review),
                    "--date",
                    "2026-07-14",
                    "--previous-date",
                    "2026-07-13",
                    "--key-levels",
                    "100.73,108.00,108.29,109.26",
                    "--facts-pack",
                    str(output),
                ],
                cwd=REPO_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_volume_ratio_uses_embedded_snapshot_when_direct_quote_fails(self):
        def fake_http(url, **_kwargs):
            if "qt.gtimg.cn" in url:
                raise OSError("SSL EOF")
            return make_tencent_kline_payload()

        with (
            mock.patch.object(gdf, "_http_get_text_direct", side_effect=fake_http),
            mock.patch.object(gdf, "fetch_sohu_quote", return_value=make_sohu_volume_result()),
        ):
            candidate = gdf.fetch_volume_ratio_candidate("300274", "2026-07-14", 15.0)
        self.assertEqual(candidate["verification_status"], "confirmed")
        self.assertEqual(candidate["candidate_value"], 1.49)
        self.assertIn("tencent_kline_embedded_qt_index_49", candidate["source"])
        self.assertEqual(candidate["snapshot_ohlc_check"]["snapshot_source"], "tencent_kline_embedded_qt_index_49")

    def test_volume_ratio_snapshot_date_mismatch_does_not_use_same_day_confirmation(self):
        fields = make_tencent_qt_fields(source_timestamp="20260715161436")
        quote_text = f'v_sz300274="{"~".join(fields)}";'

        def fake_http(url, **_kwargs):
            return quote_text if "qt.gtimg.cn" in url else make_tencent_kline_payload(include_qt=False)

        with (
            mock.patch.object(gdf, "_http_get_text_direct", side_effect=fake_http),
            mock.patch.object(gdf, "fetch_sohu_quote", return_value=make_sohu_volume_result()),
        ):
            candidate = gdf.fetch_volume_ratio_candidate("300274", "2026-07-14", 15.0)
        self.assertEqual(candidate["method"], "historical_five_day_volume_cross_check")
        self.assertEqual(candidate["verification_status"], "confirmed")
        self.assertNotIn("snapshot_ohlc_check", candidate)

    def test_volume_ratio_direct_snapshot_ohlc_mismatch_downgrades_to_historical_confirmed(self):
        fields = make_tencent_qt_fields(overrides={3: "109.99"})
        quote_text = f'v_sz300274="{"~".join(fields)}";'

        def fake_http(url, **_kwargs):
            return quote_text if "qt.gtimg.cn" in url else make_tencent_kline_payload(include_qt=False)

        with (
            mock.patch.object(gdf, "_http_get_text_direct", side_effect=fake_http),
            mock.patch.object(gdf, "fetch_sohu_quote", return_value=make_sohu_volume_result()),
        ):
            candidate = gdf.fetch_volume_ratio_candidate("300274", "2026-07-14", 15.0)
        self.assertEqual(candidate["candidate_value"], 1.49)
        self.assertEqual(candidate["method"], "historical_five_day_volume_cross_check")
        self.assertEqual(candidate["verification_status"], "confirmed")
        self.assertEqual(candidate["source"], "sohu_five_day_volume+tencent_five_day_volume")
        self.assertNotIn("snapshot_ohlc_check", candidate)

    def test_volume_ratio_embedded_snapshot_ohlc_mismatch_downgrades_to_historical_confirmed(self):
        fields = make_tencent_qt_fields(overrides={3: "109.99"})

        def fake_http(url, **_kwargs):
            if "qt.gtimg.cn" in url:
                raise OSError("SSL EOF")
            return make_tencent_kline_payload(qt_fields=fields)

        with (
            mock.patch.object(gdf, "_http_get_text_direct", side_effect=fake_http),
            mock.patch.object(gdf, "fetch_sohu_quote", return_value=make_sohu_volume_result()),
        ):
            candidate = gdf.fetch_volume_ratio_candidate("300274", "2026-07-14", 15.0)
        self.assertEqual(candidate["method"], "historical_five_day_volume_cross_check")
        self.assertEqual(candidate["verification_status"], "confirmed")
        self.assertEqual(candidate["cross_check"]["source"], "tencent_five_day_volume_derived")
        self.assertNotIn("snapshot_ohlc_check", candidate)

    def test_volume_ratio_snapshot_missing_ohlc_downgrades_to_historical_confirmed(self):
        fields = make_tencent_qt_fields(overrides={33: ""})
        quote_text = f'v_sz300274="{"~".join(fields)}";'

        def fake_http(url, **_kwargs):
            return quote_text if "qt.gtimg.cn" in url else make_tencent_kline_payload(include_qt=False)

        with (
            mock.patch.object(gdf, "_http_get_text_direct", side_effect=fake_http),
            mock.patch.object(gdf, "fetch_sohu_quote", return_value=make_sohu_volume_result()),
        ):
            candidate = gdf.fetch_volume_ratio_candidate("300274", "2026-07-14", 15.0)
        self.assertEqual(candidate["method"], "historical_five_day_volume_cross_check")
        self.assertEqual(candidate["verification_status"], "confirmed")
        self.assertNotIn("snapshot_ohlc_check", candidate)

    def test_automatic_cross_check_populates_confirmed_value(self):
        candidate = {
            "candidate_value": 1.49,
            "source": "tencent_qt_index_49+sohu_five_day_volume",
            "source_date": "2026-07-14",
            "fetched_at": "2026-07-14T16:00:00Z",
            "method": "same_day_snapshot_plus_sohu_five_day_cross_check",
            "confirmed_by": "automation_cross_check",
            "verification_status": "confirmed",
            "cross_check": {"value": 1.49, "delta": 0.0, "tolerance": 0.05},
        }
        block = gdf.build_volume_ratio_block(
            existing_volume_ratio=None,
            candidate=candidate,
            target_date="2026-07-14",
            fetched_at="2026-07-14T16:00:00Z",
        )
        self.assertEqual(block["confirmed_value"], 1.49)
        self.assertEqual(block["verification"]["status"], "confirmed")
        self.assertEqual(block["verification"]["confirmed_by"], "automation_cross_check")

    def test_automatic_cross_check_conflict_remains_unconfirmed(self):
        fields = make_tencent_qt_fields(volume_ratio="1.70")
        quote_text = f'v_sz300274="{"~".join(fields)}";'
        def fake_http(url, **_kwargs):
            return quote_text if "qt.gtimg.cn" in url else make_tencent_kline_payload(include_qt=False)

        with (
            mock.patch.object(gdf, "_http_get_text_direct", side_effect=fake_http),
            mock.patch.object(gdf, "fetch_sohu_quote", return_value=make_sohu_volume_result()),
        ):
            candidate = gdf.fetch_volume_ratio_candidate("300274", "2026-07-14", 15.0)
        block = gdf.build_volume_ratio_block(
            existing_volume_ratio=None,
            candidate=candidate,
            target_date="2026-07-14",
            fetched_at="2026-07-14T16:00:00Z",
        )
        self.assertEqual(candidate["verification_status"], "conflict")
        self.assertIsNone(block["confirmed_value"])
        self.assertEqual(block["verification"]["status"], "conflict")

    def test_volume_ratio_candidate_derives_historical_date_without_reusing_latest_snapshot(self):
        quote_text = f'v_sz300274="{"~".join(make_tencent_qt_fields())}";'

        def fake_http(url, **_kwargs):
            return quote_text if "qt.gtimg.cn" in url else make_tencent_kline_payload()

        with (
            mock.patch.object(gdf, "_http_get_text_direct", side_effect=fake_http),
            mock.patch.object(gdf, "fetch_sohu_quote", return_value=make_sohu_volume_result()),
        ):
            candidate = gdf.fetch_volume_ratio_candidate("300274", "2026-07-13", 15.0)
        self.assertEqual(candidate["candidate_value"], 1.25)
        self.assertEqual(candidate["source_date"], "2026-07-13")
        self.assertEqual(candidate["method"], "historical_five_day_volume_cross_check")
        self.assertEqual(candidate["verification_status"], "confirmed")
        self.assertEqual(candidate["confirmed_by"], "automation_cross_check")
        self.assertEqual(candidate["cross_check"]["value"], 1.25)
        self.assertEqual(candidate["cross_check"]["tolerance"], 0.01)

    def test_historical_volume_ratio_cross_check_conflict_stays_unconfirmed(self):
        quote_text = f'v_sz300274="{"~".join(make_tencent_qt_fields())}";'
        sohu_result = make_sohu_volume_result()
        for row in sohu_result["rows"]:
            if row["date"] == "2026-07-13":
                row["volume"] = "900000"

        def fake_http(url, **_kwargs):
            return quote_text if "qt.gtimg.cn" in url else make_tencent_kline_payload()

        with (
            mock.patch.object(gdf, "_http_get_text_direct", side_effect=fake_http),
            mock.patch.object(gdf, "fetch_sohu_quote", return_value=sohu_result),
        ):
            candidate = gdf.fetch_volume_ratio_candidate("300274", "2026-07-13", 15.0)
        block = gdf.build_volume_ratio_block(
            existing_volume_ratio=None,
            candidate=candidate,
            target_date="2026-07-13",
            fetched_at="2026-07-15T00:00:00Z",
        )
        self.assertEqual(candidate["verification_status"], "conflict")
        self.assertIsNone(block["confirmed_value"])
        self.assertEqual(block["verification"]["status"], "conflict")

    def test_historical_volume_ratio_single_source_remains_candidate(self):
        quote_text = f'v_sz300274="{"~".join(make_tencent_qt_fields())}";'

        def fake_http(url, **_kwargs):
            return quote_text if "qt.gtimg.cn" in url else make_tencent_kline_payload()

        with (
            mock.patch.object(gdf, "_http_get_text_direct", side_effect=fake_http),
            mock.patch.object(
                gdf,
                "fetch_sohu_quote",
                return_value={"status": "network_error", "rows": []},
            ),
        ):
            candidate = gdf.fetch_volume_ratio_candidate("300274", "2026-07-13", 15.0)
        self.assertEqual(candidate["candidate_value"], 1.25)
        self.assertEqual(candidate["verification_status"], "candidate")
        self.assertEqual(candidate["method"], "derived_candidate")
        self.assertEqual(candidate["source"], "tencent_five_day_volume_derived")

    def test_derive_five_day_volume_ratio_rejects_duplicate_target_date(self):
        rows = make_sohu_volume_result()["rows"]
        duplicate_target = [*rows, {"date": "2026-07-14", "volume": "960311"}]
        self.assertIsNone(gdf.derive_five_day_volume_ratio(duplicate_target, "2026-07-14"))

    def test_derive_five_day_volume_ratio_rejects_duplicate_prior_window_date(self):
        rows = [
            {"date": "2026-07-06", "volume": "522306"},
            {"date": "2026-07-07", "volume": "442203"},
            {"date": "2026-07-08", "volume": "413086"},
            {"date": "2026-07-08", "volume": "413086"},
            {"date": "2026-07-09", "volume": "673516"},
            {"date": "2026-07-10", "volume": "939380"},
            {"date": "2026-07-13", "volume": "745683"},
        ]
        self.assertIsNone(gdf.derive_five_day_volume_ratio(rows, "2026-07-13"))

    def test_derive_five_day_volume_ratio_keeps_normal_independent_trading_days(self):
        rows = make_sohu_volume_result()["rows"]
        self.assertEqual(gdf.derive_five_day_volume_ratio(rows, "2026-07-13"), 1.25)
        self.assertEqual(gdf.derive_five_day_volume_ratio(rows, "2026-07-14"), 1.49)

    def test_derive_five_day_volume_ratio_requires_five_prior_trading_days(self):
        rows = make_sohu_volume_result()["rows"][:5]
        self.assertIsNone(gdf.derive_five_day_volume_ratio(rows, "2026-07-10"))

    def test_main_wires_volume_ratio_candidate_provider(self):
        outcome = gdf.RunOutcome(
            exit_code=gdf.EXIT_PARTIAL,
            facts_pack={"run": {"source_used": "tencent"}},
            wrote_file=False,
            output_path=None,
            status="partial",
        )
        argv = [
            "--symbol",
            "300274",
            "--date",
            "2026-07-14",
            "--output",
            "/tmp/facts.json",
            "--no-write",
        ]
        with mock.patch.object(gdf, "run", return_value=outcome) as run_mock:
            with contextlib.redirect_stdout(io.StringIO()):
                gdf.main(argv)
        self.assertIs(
            run_mock.call_args.kwargs["volume_ratio_candidate_provider"],
            gdf.fetch_volume_ratio_candidate,
        )

    def test_network_failure_exit_and_no_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output))
            outcome = gdf.run(
                args,
                fetch_primary=make_error_fetcher("network_error", "dns fail"),
                fetch_fallback=make_error_fetcher("network_error", "dns fail"),
            )
            self.assertEqual(outcome.exit_code, gdf.EXIT_NETWORK_ERROR)
            self.assertFalse(output.exists())
            self.assertEqual(outcome.status, "network_error")
            self.assertIsNone(outcome.facts_pack)

    def test_primary_success_source_used(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="auto")
            primary = make_fetcher(load_fixture("tencent_quote_0710.json"))
            fallback = mock.Mock(side_effect=AssertionError("fallback should not be called"))
            outcome = gdf.run(args, fetch_primary=primary, fetch_fallback=fallback)
            self.assertEqual(outcome.status, "partial")
            self.assertEqual(outcome.exit_code, gdf.EXIT_PARTIAL)
            self.assertFalse(outcome.wrote_file)
            self.assertFalse(output.exists())
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "tencent")
            self.assertEqual(outcome.facts_pack["quote"]["open"], 123.17)
            self.assertEqual(outcome.facts_pack["quote"]["close"], 114.79)
            fallback.assert_not_called()

    def test_primary_failure_fallback_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="auto")
            outcome = gdf.run(
                args,
                fetch_primary=make_error_fetcher("network_error", "dns fail"),
                fetch_fallback=make_fetcher(load_fixture("eastmoney_quote_0710.json")),
            )
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "eastmoney")
            self.assertEqual(outcome.exit_code, gdf.EXIT_PARTIAL)
            self.assertFalse(outcome.wrote_file)
            self.assertFalse(output.exists())
            self.assertTrue(outcome.facts_pack["run"]["errors"])
            self.assertEqual(outcome.facts_pack["run"]["errors"][0]["error_type"], "network_error")

    def test_source_tencent_only_calls_primary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="tencent", no_write=True)
            primary = make_fetcher(load_fixture("tencent_quote_0710.json"))
            fallback = mock.Mock(side_effect=AssertionError("fallback should not be called"))
            outcome = gdf.run(args, fetch_primary=primary, fetch_fallback=fallback)
            self.assertEqual(outcome.facts_pack["run"]["requested_source"], "tencent")
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "tencent")
            fallback.assert_not_called()

    def test_source_eastmoney_only_calls_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="eastmoney", no_write=True)
            primary = mock.Mock(side_effect=AssertionError("primary should not be called"))
            fallback = make_fetcher(load_fixture("eastmoney_quote_0710.json"))
            outcome = gdf.run(args, fetch_primary=primary, fetch_fallback=fallback)
            self.assertEqual(outcome.facts_pack["run"]["requested_source"], "eastmoney")
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "eastmoney")
            primary.assert_not_called()

    def test_source_ignores_row_without_date_when_valid_target_row_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="tencent", no_write=True)
            client = make_table_client(
                daily_rows=[
                    {"open": 1.0, "close": 1.1},
                    {
                        "date": "2026-07-09",
                        "open": 122.0,
                        "high": 123.0,
                        "low": 121.0,
                        "close": 122.5,
                        "prev_close": 121.5,
                        "amount": 99.0,
                        "turnover_rate": 1.0,
                    },
                    {
                        "date": "2026-07-10",
                        "open": 123.17,
                        "high": 123.8,
                        "low": 114.0,
                        "close": 114.79,
                        "prev_close": 124.01,
                        "amount": 111.28,
                        "turnover_rate": 5.92,
                    },
                ]
            )
            outcome = gdf.run(
                args,
                ak_client=client,
                fetch_primary=gdf.fetch_primary_quote,
                fetch_fallback=gdf.fetch_fallback_quote,
            )
            self.assertEqual(outcome.facts_pack["quote"]["open"], 123.17)
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "tencent")
            self.assertEqual(outcome.facts_pack["run"]["status"], "partial")

    def test_source_with_only_unparseable_date_rows_returns_source_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="tencent")
            client = make_table_client(
                daily_rows=[
                    {"open": 1.0, "close": 1.1},
                    {"date": "", "open": 2.0, "close": 2.1},
                ]
            )
            outcome = gdf.run(
                args,
                ak_client=client,
                fetch_primary=gdf.fetch_primary_quote,
                fetch_fallback=gdf.fetch_fallback_quote,
            )
            self.assertEqual(outcome.status, "source_error")
            self.assertEqual(outcome.exit_code, gdf.EXIT_SOURCE_ERROR)
            self.assertFalse(output.exists())
            self.assertIsNone(outcome.facts_pack)

    def test_auto_falls_back_after_primary_unparseable_date_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = make_context_complete_pack()
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), source="auto")
            client = make_table_client(
                daily_rows=[
                    {"open": 1.0, "close": 1.1},
                    {"date": "", "open": 2.0, "close": 2.1},
                ],
                hist_rows=[
                    {
                        "date": "2026-07-09",
                        "close": 124.01,
                    },
                    {
                        "date": "2026-07-10",
                        "open": 123.17,
                        "high": 123.8,
                        "low": 114.0,
                        "close": 114.79,
                        "prev_close": 124.01,
                        "amount": 111.28,
                        "turnover_rate": 5.92,
                    },
                ],
            )
            outcome = gdf.run(
                args,
                ak_client=client,
                fetch_primary=gdf.fetch_primary_quote,
                fetch_fallback=gdf.fetch_fallback_quote,
                volume_ratio_candidate_provider=lambda *_args: None,
            )
            self.assertEqual(outcome.status, "success")
            self.assertEqual(outcome.exit_code, gdf.EXIT_SUCCESS)
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "eastmoney")
            self.assertEqual(outcome.facts_pack["quote"]["open"], 123.17)
            self.assertEqual(outcome.facts_pack["run"]["errors"][0]["error_type"], "source_error")
            self.assertTrue(outcome.facts_pack["run"]["errors"][0]["recovered"])

    def test_parseable_wrong_date_still_returns_date_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="tencent")
            client = make_table_client(
                daily_rows=[
                    {
                        "date": "2026-07-09",
                        "open": 122.0,
                        "high": 123.0,
                        "low": 121.0,
                        "close": 122.5,
                        "prev_close": 121.5,
                        "amount": 99.0,
                        "turnover_rate": 1.0,
                    }
                ]
            )
            outcome = gdf.run(
                args,
                ak_client=client,
                fetch_primary=gdf.fetch_primary_quote,
                fetch_fallback=gdf.fetch_fallback_quote,
            )
            self.assertEqual(outcome.status, "date_mismatch")
            self.assertEqual(outcome.exit_code, gdf.EXIT_DATE_MISMATCH)
            self.assertFalse(output.exists())

    def test_auto_continues_after_primary_date_mismatch_and_uses_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="auto")
            primary = make_fetcher(
                make_quote_result(
                    status="date_mismatch",
                    source="tencent",
                    source_date="2026-07-09",
                    error_type="date_mismatch",
                    error_message="returned dates do not include target date",
                )
            )
            fallback = make_fetcher(load_fixture("eastmoney_quote_0710.json"))
            outcome = gdf.run(args, fetch_primary=primary, fetch_fallback=fallback)
            self.assertNotEqual(outcome.exit_code, gdf.EXIT_DATE_MISMATCH)
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "eastmoney")
            self.assertEqual(outcome.facts_pack["quote"]["open"], 123.17)
            self.assertTrue(outcome.facts_pack["run"]["errors"])
            self.assertEqual(outcome.facts_pack["run"]["errors"][0]["error_type"], "date_mismatch")
            self.assertTrue(outcome.facts_pack["run"]["errors"][0].get("recovered"))
            self.assertFalse(any(value == 123.0 for value in outcome.facts_pack["quote"].values() if isinstance(value, (int, float))))

    def test_success_path_with_context_complete_pack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = make_context_complete_pack()
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), source="auto")
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
                volume_ratio_candidate_provider=lambda *_args: None,
            )
            self.assertEqual(outcome.status, "success")
            self.assertEqual(outcome.exit_code, gdf.EXIT_SUCCESS)
            self.assertFalse(outcome.wrote_file)
            self.assertEqual(outcome.facts_pack["run"]["status"], "success")
            self.assertEqual(outcome.facts_pack["name"], "阳光电源")

            existing["needs_manual_check"]["news_policy_context"] = True
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            outcome_partial = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
                volume_ratio_candidate_provider=lambda *_args: None,
            )
            self.assertEqual(outcome_partial.status, "partial")
            self.assertEqual(outcome_partial.exit_code, gdf.EXIT_PARTIAL)
            self.assertFalse(outcome_partial.wrote_file)

    def test_auto_continues_after_incomplete_primary_and_uses_complete_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="auto")
            primary = make_fetcher(
                make_quote_result(
                    status="ok",
                    source="tencent",
                    source_date="2026-07-10",
                    quote={
                        "open": 123.17,
                        "high": 123.8,
                        "low": 114.0,
                        "close": 114.79,
                        "prev_close": 124.01,
                        "amount": None,
                        "turnover_rate": None,
                    },
                    source_pct_change=-7.434884283525522,
                )
            )
            fallback = make_fetcher(load_fixture("eastmoney_quote_0710.json"))
            outcome = gdf.run(args, fetch_primary=primary, fetch_fallback=fallback)
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "eastmoney")
            self.assertEqual(outcome.facts_pack["quote"]["amount"], 111.28)
            self.assertEqual(outcome.facts_pack["quote"]["turnover_rate"], 5.92)

    def test_auto_uses_best_partial_when_no_complete_source_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="auto", no_write=True)
            primary = make_fetcher(
                make_quote_result(
                    status="ok",
                    source="tencent",
                    source_date="2026-07-10",
                    quote={
                        "open": 123.17,
                        "high": 123.8,
                        "low": 114.0,
                        "close": 114.79,
                        "prev_close": 124.01,
                        "amount": None,
                        "turnover_rate": None,
                    },
                    source_pct_change=-7.434884283525522,
                )
            )
            fallback = make_fetcher(
                make_quote_result(
                    status="ok",
                    source="eastmoney",
                    source_date="2026-07-10",
                    quote={
                        "open": 123.17,
                        "high": 123.8,
                        "low": 114.0,
                        "close": 114.79,
                        "prev_close": 124.01,
                        "amount": 111.28,
                        "turnover_rate": None,
                    },
                    source_pct_change=-7.434884283525522,
                )
            )
            outcome = gdf.run(args, fetch_primary=primary, fetch_fallback=fallback, volume_ratio_candidate_provider=lambda *_args: None)
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "eastmoney")
            self.assertEqual(outcome.facts_pack["quote"]["amount"], 111.28)
            self.assertIsNone(outcome.facts_pack["quote"]["turnover_rate"])
            self.assertEqual(outcome.status, "partial")

    def test_auto_does_not_downgrade_recovered_fallback_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = make_context_complete_pack()
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), source="auto")
            primary = make_fetcher(
                make_quote_result(
                    status="date_mismatch",
                    source="tencent",
                    source_date="2026-07-09",
                    error_type="date_mismatch",
                    error_message="returned dates do not include target date",
                )
            )
            fallback = make_fetcher(load_fixture("eastmoney_quote_0710.json"))
            outcome = gdf.run(args, fetch_primary=primary, fetch_fallback=fallback, volume_ratio_candidate_provider=lambda *_args: None)
            self.assertEqual(outcome.status, "success")
            self.assertEqual(outcome.exit_code, gdf.EXIT_SUCCESS)
            self.assertEqual(outcome.facts_pack["run"]["status"], "success")
            self.assertTrue(outcome.facts_pack["run"]["errors"][0]["recovered"])

    def test_auto_uses_clean_fallback_after_complete_primary_pct_conflict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="auto", no_write=True)
            fallback = mock.Mock(side_effect=make_fetcher(load_fixture("eastmoney_quote_0710.json")))
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_pct_conflict_0710.json")),
                fetch_fallback=fallback,
                volume_ratio_candidate_provider=lambda *_args: None,
            )
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "eastmoney")
            self.assertEqual(outcome.facts_pack["quote"]["open"], 123.17)
            self.assertTrue(outcome.facts_pack["run"]["errors"][0]["recovered"])
            self.assertEqual(outcome.facts_pack["run"]["errors"][0]["error_type"], "quote_verification_conflict")
            fallback.assert_called()

    def test_auto_keeps_clean_complete_primary_without_unnecessary_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="auto", no_write=True)
            primary = make_fetcher(load_fixture("tencent_quote_0710.json"))
            fallback = mock.Mock(side_effect=AssertionError("fallback should not be called"))
            outcome = gdf.run(
                args,
                fetch_primary=primary,
                fetch_fallback=fallback,
                volume_ratio_candidate_provider=lambda *_args: None,
            )
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "tencent")
            self.assertEqual(outcome.status, "partial")
            fallback.assert_not_called()

    def test_auto_keeps_primary_when_fallback_is_not_better(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="auto", no_write=True)
            primary = make_fetcher(load_fixture("tencent_quote_pct_conflict_0710.json"))
            fallback = mock.Mock(side_effect=make_fetcher(
                make_quote_result(
                    status="ok",
                    source="eastmoney",
                    source_date="2026-07-10",
                    quote={
                        "open": 123.17,
                        "high": 123.8,
                        "low": 114.0,
                        "close": 114.79,
                        "prev_close": 124.01,
                        "amount": 111.28,
                        "turnover_rate": 5.92,
                    },
                    source_pct_change=-7.0,
                )
            ))
            outcome = gdf.run(
                args,
                fetch_primary=primary,
                fetch_fallback=fallback,
                volume_ratio_candidate_provider=lambda *_args: None,
            )
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "tencent")
            self.assertEqual(outcome.facts_pack["quote_verification"]["status"], "conflict")
            fallback.assert_called()

    def test_recovered_quote_conflict_does_not_force_partial(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = make_context_complete_pack()
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), source="auto")
            fallback = mock.Mock(side_effect=make_fetcher(load_fixture("eastmoney_quote_0710.json")))
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_pct_conflict_0710.json")),
                fetch_fallback=fallback,
                volume_ratio_candidate_provider=lambda *_args: None,
            )
            self.assertEqual(outcome.status, "success")
            self.assertEqual(outcome.exit_code, gdf.EXIT_SUCCESS)
            self.assertEqual(outcome.facts_pack["run"]["status"], "success")
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "eastmoney")
            self.assertTrue(outcome.facts_pack["run"]["errors"][0]["recovered"])
            fallback.assert_called()

    def test_timeout_interrupts_akshare_call(self):
        class SleepyClient:
            def stock_zh_a_daily(self, **_kwargs):
                time.sleep(0.2)
                return []

            def stock_zh_a_hist(self, **_kwargs):
                return []

        result = gdf._fetch_records(
            SleepyClient(),
            source="tencent",
            symbol="300274",
            target_date="2026-07-10",
            timeout=0.05,
        )
        self.assertEqual(result["status"], "network_error")
        self.assertEqual(result["error_type"], "timeout")
        self.assertIn("timed out", result["error_message"])

    def test_primary_timeout_fallback_success_and_all_timeout_network_error(self):
        class TimeoutThenSuccessClient:
            def stock_zh_a_daily(self, **_kwargs):
                time.sleep(0.2)
                return []

            def stock_zh_a_hist(self, **_kwargs):
                return [
                    {"date": "2026-07-09", "close": 124.01},
                    {
                        "date": "2026-07-10",
                        "open": 123.17,
                        "high": 123.8,
                        "low": 114.0,
                        "close": 114.79,
                        "prev_close": 124.01,
                        "amount": 111.28,
                        "turnover_rate": 5.92,
                    },
                ]

        class TimeoutOnlyClient:
            def stock_zh_a_daily(self, **_kwargs):
                time.sleep(0.2)
                return []

            def stock_zh_a_hist(self, **_kwargs):
                time.sleep(0.2)
                return []

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="auto", no_write=True, timeout=0.05)
            outcome = gdf.run(
                args,
                ak_client=TimeoutThenSuccessClient(),
                fetch_primary=gdf.fetch_primary_quote,
                fetch_fallback=gdf.fetch_fallback_quote,
                volume_ratio_candidate_provider=lambda *_args: None,
            )
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "eastmoney")
            self.assertEqual(outcome.facts_pack["run"]["errors"][0]["error_type"], "timeout")
            self.assertEqual(outcome.facts_pack["run"]["errors"][0]["source"], "tencent")
            self.assertEqual(outcome.status, "partial")

            timeout_outcome = gdf.run(
                args,
                ak_client=TimeoutOnlyClient(),
                fetch_primary=gdf.fetch_primary_quote,
                fetch_fallback=gdf.fetch_fallback_quote,
            )
            self.assertEqual(timeout_outcome.status, "network_error")
            self.assertEqual(timeout_outcome.exit_code, gdf.EXIT_NETWORK_ERROR)
            self.assertIsNone(timeout_outcome.facts_pack)
            self.assertFalse(output.exists())

    def test_dry_run_and_no_write_skip_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dry_output = Path(tmpdir) / "dry.json"
            args_dry = make_args(output=str(dry_output), source="tencent", dry_run=True)
            dry_outcome = gdf.run(
                args_dry,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
            )
            self.assertFalse(dry_output.exists())
            self.assertIsNotNone(dry_outcome.facts_pack)

            no_write_output = Path(tmpdir) / "nowrap.json"
            args_no_write = make_args(output=str(no_write_output), source="tencent", no_write=True)
            no_write_outcome = gdf.run(
                args_no_write,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
            )
            self.assertFalse(no_write_output.exists())
            self.assertIsNotNone(no_write_outcome.facts_pack)
            self.assertFalse(no_write_outcome.wrote_file)

    def test_dry_run_and_no_write_cli_formatting(self):
        sample_pack = make_context_complete_pack()
        sample_outcome = gdf.RunOutcome(
            exit_code=gdf.EXIT_SUCCESS,
            facts_pack=sample_pack,
            wrote_file=False,
            output_path="/tmp/facts.json",
            status="success",
        )
        exit_code, stdout = run_main(["--symbol", "300274", "--date", "2026-07-10", "--output", "/tmp/facts.json", "--dry-run"], sample_outcome)
        self.assertEqual(exit_code, gdf.EXIT_SUCCESS)
        self.assertIn('"quote"', stdout)
        self.assertIn('"volume_ratio"', stdout)
        self.assertNotIn(gdf.CANDIDATE_STDOUT_MARKER, stdout)

        exit_code, stdout = run_main(
            [
                "--symbol",
                "300274",
                "--date",
                "2026-07-10",
                "--output",
                "/tmp/facts.json",
                "--dry-run",
                "--emit-runner-marker",
            ],
            sample_outcome,
        )
        marker_lines = [line for line in stdout.splitlines() if line.startswith(gdf.CANDIDATE_STDOUT_MARKER)]
        self.assertEqual(exit_code, gdf.EXIT_SUCCESS)
        self.assertEqual(len(marker_lines), 1)
        self.assertEqual(json.loads(marker_lines[0][len(gdf.CANDIDATE_STDOUT_MARKER) :]), sample_pack)

        exit_code, stdout = run_main(["--symbol", "300274", "--date", "2026-07-10", "--output", "/tmp/facts.json", "--no-write"], sample_outcome)
        self.assertEqual(exit_code, gdf.EXIT_SUCCESS)
        self.assertIn('"status"', stdout)
        self.assertIn('"exit_code"', stdout)
        self.assertNotIn('"quote"', stdout)

    def test_partial_missing_volume_ratio(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="tencent", write_partial=True)
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_partial_missing_amount_turnover.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
                volume_ratio_candidate_provider=lambda *_args: None,
            )
            self.assertEqual(outcome.status, "partial")
            self.assertEqual(outcome.exit_code, gdf.EXIT_PARTIAL)
            self.assertFalse(outcome.wrote_file)
            self.assertFalse(output.exists())
            self.assertTrue(outcome.facts_pack["needs_manual_check"]["volume_ratio"])

    def test_pct_change_conflict_uses_derived_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="tencent")
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_pct_conflict_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
            )
            self.assertEqual(outcome.status, "partial")
            self.assertEqual(outcome.facts_pack["quote_verification"]["status"], "conflict")
            self.assertAlmostEqual(
                outcome.facts_pack["quote"]["pct_change"],
                gdf.derive_pct_change(114.79, 124.01),
                places=12,
            )

    def test_zero_source_pct_change_is_preserved(self):
        quote_result = make_quote_result(
            status="ok",
            source="tencent",
            source_date="2026-07-10",
            quote={
                "open": 100,
                "high": 100,
                "low": 100,
                "close": 100,
                "prev_close": 100,
                "amount": 10,
                "turnover_rate": 1,
            },
            source_pct_change=0.0,
        )
        quote, verification, complete = gdf.normalize_quote(quote_result)
        self.assertTrue(complete)
        self.assertEqual(verification["source_pct_change"], 0.0)
        self.assertEqual(verification["derived_pct_change"], 0.0)
        self.assertEqual(verification["delta"], 0.0)
        self.assertEqual(verification["status"], "confirmed")
        self.assertNotEqual(verification["status"], "conflict")
        self.assertEqual(quote["pct_change"], 0.0)

    def test_zero_amount_and_turnover_rate_are_preserved(self):
        result = gdf._fetch_records(
            make_table_client(
                daily_rows=[
                    {"date": "2026-07-09", "close": 100},
                    {
                        "date": "2026-07-10",
                        "open": 100,
                        "high": 101,
                        "low": 99,
                        "close": 100,
                        "amount": 0,
                        "turnover_rate": 0.0,
                    },
                ]
            ),
            source="tencent",
            symbol="300274",
            target_date="2026-07-10",
            timeout=5,
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["quote"]["amount"], 0.0)
        self.assertEqual(result["quote"]["turnover_rate"], 0.0)

    def test_first_not_none_does_not_treat_zero_as_missing(self):
        self.assertEqual(gdf.first_not_none(0, 1), 0)
        self.assertEqual(gdf.first_not_none(0.0, 1.0), 0.0)
        self.assertEqual(gdf.first_not_none("0", "1"), "0")
        self.assertEqual(gdf.first_not_none("", "0"), "0")
        self.assertEqual(gdf.first_not_none(None, "", 7), 7)

    def test_historical_trade_date_mismatch_exit_6(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="tencent")
            outcome = gdf.run(
                args,
                fetch_primary=make_error_fetcher("date_mismatch", "returned dates do not include target date"),
                fetch_fallback=make_fetcher(load_fixture("eastmoney_quote_0710.json")),
            )
            self.assertEqual(outcome.exit_code, gdf.EXIT_DATE_MISMATCH)
            self.assertFalse(output.exists())
            self.assertEqual(outcome.status, "date_mismatch")

    def test_volume_ratio_source_date_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="tencent")
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
                volume_ratio_candidate_provider=lambda *_args: load_fixture("volume_ratio_candidate_wrong_day.json"),
            )
            self.assertEqual(outcome.status, "partial")
            self.assertEqual(outcome.facts_pack["volume_ratio"]["verification"]["status"], "rejected")
            self.assertEqual(outcome.facts_pack["volume_ratio"]["verification"]["source_date"], "2026-07-09")
            self.assertEqual(outcome.facts_pack["quote"]["close"], 114.79)

    def test_existing_manual_confirmed_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = load_fixture("existing_manual_confirmed_status.json")
            existing["volume_ratio"]["manual_verification"] = {
                "decided_by": "test",
                "decided_at": "2026-07-10T16:00:00Z",
                "source": "test fixture",
                "reason": "manual fixture value",
            }
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), source="auto")
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
                volume_ratio_candidate_provider=lambda *_args: load_fixture("volume_ratio_candidate_wrong_day.json"),
            )
            self.assertEqual(outcome.exit_code, gdf.EXIT_PARTIAL)
            written = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(written["volume_ratio"]["confirmed_value"], 1.79)
            self.assertEqual(written["volume_ratio"]["verification"]["status"], "manual_confirmed")

    def test_manual_confirmation_variants_are_locked(self):
        for fixture_name in (
            "existing_manual_confirmed_status.json",
            "existing_confirmed_manual_method.json",
            "existing_confirmed_manual_check.json",
        ):
            with self.subTest(fixture=fixture_name):
                existing = load_fixture(fixture_name)
                self.assertTrue(gdf.is_manual_lock(existing["volume_ratio"]))

    def test_manual_volume_ratio_metadata_is_preserved_byte_for_byte(self):
        for fixture_name in (
            "existing_manual_confirmed_status.json",
            "existing_confirmed_manual_method.json",
            "existing_confirmed_manual_check.json",
        ):
            with self.subTest(fixture=fixture_name):
                existing = load_fixture(fixture_name)
                existing["volume_ratio"]["verification"]["human_ticket"] = "T-123"
                existing["volume_ratio"]["verification"]["reviewer_note"] = {"source": "manual"}
                existing["volume_ratio"]["custom_extension"] = {"foo": "bar"}
                before_verification = copy.deepcopy(existing["volume_ratio"]["verification"])
                before_top_level = copy.deepcopy(existing["volume_ratio"])
                with tempfile.TemporaryDirectory() as tmpdir:
                    output = Path(tmpdir) / "facts.json"
                    output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    args = make_args(output=str(output), source="auto", no_write=True)
                    candidate = load_fixture("volume_ratio_candidate_wrong_day.json")
                    candidate["candidate_value"] = 2.34
                    outcome = gdf.run(
                        args,
                        fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                        fetch_fallback=make_error_fetcher("source_error", "unused"),
                        volume_ratio_candidate_provider=lambda *_args: candidate,
                    )
                    after = outcome.facts_pack["volume_ratio"]
                    self.assertEqual(after["confirmed_value"], before_top_level["confirmed_value"])
                    self.assertEqual(after["verification"], before_verification)
                    self.assertEqual(after["custom_extension"], before_top_level["custom_extension"])
                    self.assertIn("automation_evidence", after)
                    self.assertEqual(after["automation_evidence"]["status"], "conflict")

    def test_manual_locked_volume_ratio_preserves_candidate_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = load_fixture("existing_manual_confirmed_status.json")
            original_candidate = existing["volume_ratio"]["candidate_value"]
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), source="auto", no_write=True)
            candidate = load_fixture("volume_ratio_candidate_wrong_day.json")
            candidate["candidate_value"] = 2.34
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
                volume_ratio_candidate_provider=lambda *_args: candidate,
            )
            self.assertEqual(outcome.facts_pack["volume_ratio"]["candidate_value"], original_candidate)
            self.assertEqual(outcome.facts_pack["volume_ratio"]["confirmed_value"], existing["volume_ratio"]["confirmed_value"])
            self.assertEqual(outcome.facts_pack["volume_ratio"]["automation_evidence"]["status"], "conflict")
            self.assertEqual(outcome.facts_pack["volume_ratio"]["automation_evidence"]["latest_candidate_value"], 2.34)

    def test_manual_locked_volume_ratio_preserves_entire_original_record(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = load_fixture("existing_confirmed_manual_method.json")
            existing["volume_ratio"]["verification"]["human_ticket"] = "T-123"
            existing["volume_ratio"]["verification"]["reviewer_note"] = {"source": "manual"}
            existing["volume_ratio"]["custom_extension"] = {"foo": "bar"}
            before = copy.deepcopy(existing["volume_ratio"])
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), source="auto", no_write=True)
            candidate = load_fixture("volume_ratio_candidate_wrong_day.json")
            candidate["candidate_value"] = 2.34
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
                volume_ratio_candidate_provider=lambda *_args: candidate,
            )
            after = outcome.facts_pack["volume_ratio"]
            self.assertEqual(after["candidate_value"], before["candidate_value"])
            self.assertEqual(after["confirmed_value"], before["confirmed_value"])
            self.assertEqual(after["verification"], before["verification"])
            self.assertEqual(after["custom_extension"], before["custom_extension"])
            self.assertEqual(after["source"], before["source"])

    def test_manual_locked_conflicting_candidate_goes_to_automation_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = load_fixture("existing_manual_confirmed_status.json")
            existing["volume_ratio"]["manual_verification"] = {
                "decided_by": "test",
                "decided_at": "2026-07-10T16:00:00Z",
                "source": "test fixture",
                "reason": "manual fixture value",
            }
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), source="auto", no_write=True)
            candidate = load_fixture("volume_ratio_candidate_wrong_day.json")
            candidate["candidate_value"] = 2.34
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
                volume_ratio_candidate_provider=lambda *_args: candidate,
            )
            after = outcome.facts_pack["volume_ratio"]
            self.assertEqual(after["confirmed_value"], existing["volume_ratio"]["confirmed_value"])
            self.assertEqual(after["candidate_value"], existing["volume_ratio"]["candidate_value"])
            self.assertEqual(after["verification"], existing["volume_ratio"]["verification"])
            self.assertEqual(after["automation_evidence"]["status"], "conflict")
            self.assertEqual(after["automation_evidence"]["latest_candidate_value"], 2.34)

    def test_manual_locked_matching_candidate_does_not_rewrite_original_candidate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = load_fixture("existing_manual_confirmed_status.json")
            existing["volume_ratio"]["manual_verification"] = {
                "decided_by": "test",
                "decided_at": "2026-07-10T16:00:00Z",
                "source": "test fixture",
                "reason": "manual fixture value",
            }
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), source="auto", no_write=True)
            candidate = load_fixture("volume_ratio_candidate_same_day.json")
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
                volume_ratio_candidate_provider=lambda *_args: candidate,
            )
            after = outcome.facts_pack["volume_ratio"]
            self.assertEqual(after["candidate_value"], existing["volume_ratio"]["candidate_value"])
            self.assertEqual(after["confirmed_value"], existing["volume_ratio"]["confirmed_value"])
            self.assertEqual(after["verification"], existing["volume_ratio"]["verification"])
            self.assertEqual(after["automation_evidence"]["status"], "matches_manual_confirmation")

    def test_same_value_wrong_source_date_not_matches_manual_confirmation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = load_fixture("existing_manual_confirmed_status.json")
            existing["volume_ratio"]["manual_verification"] = {
                "decided_by": "test",
                "decided_at": "2026-07-10T16:00:00Z",
                "source": "test fixture",
                "reason": "manual fixture value",
            }
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), source="auto", no_write=True)
            candidate = load_fixture("volume_ratio_candidate_wrong_day.json")
            candidate["candidate_value"] = existing["volume_ratio"]["confirmed_value"]
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
                volume_ratio_candidate_provider=lambda *_args: candidate,
            )
            after = outcome.facts_pack["volume_ratio"]
            self.assertNotEqual(after["automation_evidence"]["status"], "matches_manual_confirmation")
            self.assertEqual(after["automation_evidence"]["status"], "source_date_mismatch_same_value")
            self.assertEqual(after["automation_evidence"]["latest_candidate_value"], existing["volume_ratio"]["confirmed_value"])
            self.assertEqual(after["automation_evidence"]["source_date"], "2026-07-09")

    def test_same_value_correct_source_date_matches_manual_confirmation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = load_fixture("existing_manual_confirmed_status.json")
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), source="auto", no_write=True)
            candidate = load_fixture("volume_ratio_candidate_same_day.json")
            candidate["candidate_value"] = existing["volume_ratio"]["confirmed_value"]
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
                volume_ratio_candidate_provider=lambda *_args: candidate,
            )
            after = outcome.facts_pack["volume_ratio"]
            self.assertEqual(after["automation_evidence"]["status"], "matches_manual_confirmation")
            self.assertEqual(after["automation_evidence"]["latest_candidate_value"], existing["volume_ratio"]["confirmed_value"])
            self.assertEqual(after["automation_evidence"]["source_date"], "2026-07-10")

    def test_name_source_preference_and_fallbacks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="tencent", no_write=True)
            payload_with_name = load_fixture("tencent_quote_0710.json")
            payload_with_name["source_name"] = "来自来源名称"
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(payload_with_name),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
            )
            self.assertEqual(outcome.facts_pack["name"], "来自来源名称")
            self.assertEqual(outcome.facts_pack["run"]["name_source"], "source")

            existing = load_fixture("existing_manual_confirmed_status.json")
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            outcome_existing = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
            )
            self.assertEqual(outcome_existing.facts_pack["name"], existing["name"])
            self.assertEqual(outcome_existing.facts_pack["run"]["name_source"], "existing_pack")

            output = Path(tmpdir) / "facts_symbol.json"
            args_symbol = make_args(output=str(output), source="tencent", no_write=True)
            outcome_symbol = gdf.run(
                args_symbol,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
            )
            self.assertEqual(outcome_symbol.facts_pack["name"], "300274")
            self.assertEqual(outcome_symbol.facts_pack["run"]["name_source"], "symbol_fallback")

    def test_fully_empty_data_does_not_write_even_with_write_partial(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="auto", write_partial=True)
            outcome = gdf.run(
                args,
                fetch_primary=make_error_fetcher("source_error", "empty"),
                fetch_fallback=make_error_fetcher("source_error", "empty"),
                volume_ratio_candidate_provider=lambda *_args: None,
            )
            self.assertFalse(output.exists())
            self.assertNotEqual(outcome.exit_code, gdf.EXIT_SUCCESS)
            self.assertIsNone(outcome.facts_pack)

    def test_invalid_existing_json_symbol_and_date_mismatch_are_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            original_text = "not valid json\n"
            output.write_text(original_text, encoding="utf-8")
            args = make_args(output=str(output), source="tencent")
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
            )
            self.assertEqual(outcome.status, "schema_error")
            self.assertEqual(outcome.exit_code, gdf.EXIT_SCHEMA_ERROR)
            self.assertEqual(output.read_text(encoding="utf-8"), original_text)

            output.write_text(json.dumps({"symbol": "999999", "trade_date": "2026-07-10"}, ensure_ascii=False) + "\n", encoding="utf-8")
            outcome_symbol = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
            )
            self.assertEqual(outcome_symbol.status, "schema_error")
            self.assertEqual(outcome_symbol.exit_code, gdf.EXIT_SCHEMA_ERROR)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["symbol"], "999999")

            output.write_text(json.dumps({"symbol": "300274", "trade_date": "2026-07-09"}, ensure_ascii=False) + "\n", encoding="utf-8")
            outcome_date = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
            )
            self.assertEqual(outcome_date.status, "schema_error")
            self.assertEqual(outcome_date.exit_code, gdf.EXIT_SCHEMA_ERROR)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["trade_date"], "2026-07-09")

    def test_non_object_json_root_schema_error(self):
        root_payloads = [
            "[]",
            '"hello"',
            "123",
            "true",
            "null",
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            original_text = '{"symbol":"300274","trade_date":"2026-07-10"}\n'
            for payload in root_payloads:
                with self.subTest(payload=payload):
                    output.write_text(original_text, encoding="utf-8")
                    output.write_text(payload + "\n", encoding="utf-8")
                    args = make_args(output=str(output), source="tencent")
                    outcome = gdf.run(
                        args,
                        fetch_primary=mock.Mock(side_effect=AssertionError("fetch_primary should not be called")),
                        fetch_fallback=mock.Mock(side_effect=AssertionError("fetch_fallback should not be called")),
                    )
                    self.assertEqual(outcome.status, "schema_error")
                    self.assertEqual(outcome.exit_code, gdf.EXIT_SCHEMA_ERROR)
                    self.assertEqual(output.read_text(encoding="utf-8"), payload + "\n")
                    self.assertIsNone(outcome.facts_pack)

    def test_atomic_write_failure_keeps_original_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = load_fixture("existing_manual_confirmed_status.json")
            original = json.dumps(existing, ensure_ascii=False, indent=2) + "\n"
            output.write_text(original, encoding="utf-8")
            args = make_args(output=str(output), source="tencent")
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
            )
            self.assertFalse(outcome.wrote_file)
            self.assertEqual(output.read_text(encoding="utf-8"), original)
            self.assertEqual(list(output.parent.glob("*.tmp")), [])

    def test_timeout_argument_rejected_when_non_positive(self):
        with self.assertRaises(SystemExit):
            gdf.parse_args([
                "--symbol",
                "300274",
                "--date",
                "2026-07-10",
                "--output",
                "/tmp/facts.json",
                "--timeout",
                "0",
            ])

    def test_formal_generator_write_transaction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            args = make_args(output=str(output), source="tencent", write_partial=True)
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
            )
            self.assertFalse(output.exists())
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "tencent")
            self.assertEqual(outcome.facts_pack["trade_date"], "2026-07-10")
            self.assertFalse(outcome.wrote_file)
            self.assertIsNone(outcome.output_sha256)
            tmp_residuals = list(output.parent.glob("*.tmp"))
            self.assertEqual(tmp_residuals, [])

    def test_generator_output_without_write_official_never_writes_official(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            official = repo / "data" / "daily" / "300274_2026-07-10_facts.json"
            candidate_output = Path(tmpdir) / "candidate.json"
            args = make_args(output=str(candidate_output), source="tencent", write_partial=True)
            with mock.patch.object(gdf, "REPO_ROOT", repo):
                outcome = gdf.run(
                    args,
                    fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                    fetch_fallback=make_error_fetcher("source_error", "unused"),
                    volume_ratio_candidate_provider=lambda *_args: load_fixture("volume_ratio_candidate_same_day.json"),
                )
            self.assertIn(outcome.status, {"success", "partial"})
            self.assertFalse(outcome.wrote_file)
            self.assertFalse(official.exists())
            self.assertFalse(candidate_output.exists())

    def test_generator_output_to_real_official_path_without_write_official_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            official = repo / "data" / "daily" / "300274_2026-07-10_facts.json"
            official.parent.mkdir(parents=True)
            args = make_args(output=str(official), source="tencent", write_partial=True)
            with mock.patch.object(gdf, "REPO_ROOT", repo):
                outcome = gdf.run(
                    args,
                    fetch_primary=mock.Mock(side_effect=AssertionError("fetch must not run")),
                    fetch_fallback=mock.Mock(side_effect=AssertionError("fallback must not run")),
                )
            self.assertEqual(outcome.status, "schema_error")
            self.assertFalse(outcome.wrote_file)
            self.assertFalse(official.exists())

    def test_write_official_cli_rejects_custom_output(self):
        with self.assertRaises(SystemExit):
            gdf.parse_args([
                "--symbol",
                "300274",
                "--date",
                "2026-07-10",
                "--write-official",
                "--output",
                "/tmp/not-official.json",
            ])

    def test_write_official_creates_canonical_official_in_temp_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            args = make_args(output=None, source="tencent", write_partial=True, write_official=True)
            volume_candidate = {
                "candidate_value": 1.79,
                "source": "pytest",
                "source_date": "2026-07-10",
                "fetched_at": "2026-07-13T00:00:00Z",
                "method": "historical_five_day_volume_cross_check",
                "verification_status": "confirmed",
                "confirmed_by": "pytest",
            }
            with (
                mock.patch.object(gdf, "REPO_ROOT", repo),
                mock.patch.object(gdf, "validate_generated_facts_pack", lambda *_args, **_kwargs: None),
                mock.patch.object(gdf.oft, "_validator_summary", lambda *_args, **_kwargs: {"status": "passed"}),
            ):
                outcome = gdf.run(
                    args,
                    fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                    fetch_fallback=make_error_fetcher("source_error", "unused"),
                    volume_ratio_candidate_provider=lambda *_args: volume_candidate,
                )
            official = repo / "data" / "daily" / "300274_2026-07-10_facts.json"
            self.assertEqual(Path(outcome.output_path).resolve(), official.resolve())
            self.assertTrue(outcome.wrote_file)
            self.assertTrue(official.exists())
            self.assertEqual(outcome.output_sha256, gdf.ofl.sha256_file(official))

    def test_write_official_wrote_file_tracks_actual_official_change(self):
        volume_candidate = {
            "candidate_value": 1.79,
            "source": "pytest",
            "source_date": "2026-07-10",
            "fetched_at": "2026-07-13T00:00:00Z",
            "method": "historical_five_day_volume_cross_check",
            "verification_status": "confirmed",
            "confirmed_by": "pytest",
        }
        cases = (
            ("created", True, True),
            ("created_postcheck_failed", True, True),
            ("identical_noop", False, False),
            ("semantic_noop", False, False),
        )
        for write_action, official_changed, expected_wrote_file in cases:
            with self.subTest(write_action=write_action), tempfile.TemporaryDirectory() as tmpdir:
                repo = Path(tmpdir) / "repo"
                args = make_args(output=None, source="tencent", write_partial=True, write_official=True)
                result = mock.Mock(
                    write_action=write_action,
                    official_changed=official_changed,
                    official_sha256_after="a" * 64,
                )
                with (
                    mock.patch.object(gdf, "REPO_ROOT", repo),
                    mock.patch.object(gdf, "validate_generated_facts_pack", lambda *_args, **_kwargs: None),
                    mock.patch.object(gdf.oft, "promote_candidate_to_official", return_value=result),
                ):
                    outcome = gdf.run(
                        args,
                        fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                        fetch_fallback=make_error_fetcher("source_error", "unused"),
                        volume_ratio_candidate_provider=lambda *_args: volume_candidate,
                    )
                self.assertIs(outcome.wrote_file, expected_wrote_file)

    def test_write_official_rejects_noncanonical_symbol_and_date(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            cases = [
                make_args(output=None, symbol="../300274", write_official=True),
                make_args(output=None, date="../2026-07-10", write_official=True),
            ]
            for args in cases:
                with self.subTest(args=args), mock.patch.object(gdf, "REPO_ROOT", repo):
                    outcome = gdf.run(
                        args,
                        fetch_primary=mock.Mock(side_effect=AssertionError("fetch must not run")),
                        fetch_fallback=mock.Mock(side_effect=AssertionError("fallback must not run")),
                    )
                    self.assertEqual(outcome.status, "schema_error")
                    self.assertFalse(outcome.wrote_file)

    def test_write_official_rejects_symlink_escape_in_temp_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            outside = Path(tmpdir) / "outside"
            outside.mkdir()
            (repo / "data").mkdir(parents=True)
            (repo / "data" / "daily").symlink_to(outside, target_is_directory=True)
            args = make_args(output=None, source="tencent", write_official=True)
            with mock.patch.object(gdf, "REPO_ROOT", repo):
                outcome = gdf.run(
                    args,
                    fetch_primary=mock.Mock(side_effect=AssertionError("fetch must not run")),
                    fetch_fallback=mock.Mock(side_effect=AssertionError("fallback must not run")),
                )
            self.assertEqual(outcome.status, "schema_error")
            self.assertFalse(outcome.wrote_file)

    def test_07_10_gold_sample_preserves_manual_volume_ratio(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = load_fixture("existing_manual_confirmed_status.json")
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), source="auto")
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
                volume_ratio_candidate_provider=lambda *_args: load_fixture("volume_ratio_candidate_wrong_day.json"),
            )
            self.assertEqual(outcome.facts_pack["quote"]["prev_close"], 124.01)
            self.assertEqual(outcome.facts_pack["quote"]["open"], 123.17)
            self.assertEqual(outcome.facts_pack["quote"]["high"], 123.8)
            self.assertEqual(outcome.facts_pack["quote"]["low"], 114.0)
            self.assertEqual(outcome.facts_pack["quote"]["close"], 114.79)
            self.assertAlmostEqual(outcome.facts_pack["quote"]["pct_change"], -7.434884283525522, places=12)
            self.assertEqual(outcome.facts_pack["quote"]["amount"], 111.28)
            self.assertEqual(outcome.facts_pack["quote"]["turnover_rate"], 5.92)
            self.assertEqual(outcome.facts_pack["volume_ratio"]["confirmed_value"], 1.79)
            self.assertEqual(outcome.facts_pack["volume_ratio"]["verification"]["status"], "manual_confirmed")
            self.assertEqual(outcome.exit_code, gdf.EXIT_PARTIAL)
            written = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(written["volume_ratio"]["confirmed_value"], 1.79)

    def test_validator_accepts_temp_facts_pack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            existing = load_fixture("existing_manual_confirmed_status.json")
            existing["volume_ratio"]["manual_verification"] = {
                "decided_by": "test",
                "decided_at": "2026-07-10T16:00:00Z",
                "source": "test fixture",
                "reason": "manual fixture value",
            }
            output.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            args = make_args(output=str(output), source="auto")
            outcome = gdf.run(
                args,
                fetch_primary=make_fetcher(load_fixture("tencent_quote_0710.json")),
                fetch_fallback=make_error_fetcher("source_error", "unused"),
                volume_ratio_candidate_provider=lambda *_args: load_fixture("volume_ratio_candidate_wrong_day.json"),
            )
            self.assertTrue(output.exists())
            cmd = [
                "python3",
                str(VALIDATOR),
                "--files",
                str(REVIEW_0710),
                "--date",
                "2026-07-10",
                "--previous-date",
                "2026-07-09",
                "--key-levels",
                "114.00,114.79,118.06,123.17,123.80,124.01,124.49,126.00,126.16,127.18,127.30,127.53,128.18",
                "--facts-pack",
                str(output),
                "--no-fail",
            ]
            result = subprocess.run(
                cmd,
                cwd=REPO_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + "\n" + result.stderr)
            self.assertIn("validate_review_chain: PASS", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
