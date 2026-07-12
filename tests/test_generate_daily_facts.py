import contextlib
import copy
import io
import json
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


class GenerateDailyFactsTests(unittest.TestCase):
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
            self.assertTrue(outcome.wrote_file)
            self.assertEqual(outcome.facts_pack["run"]["source_used"], "tencent")
            self.assertEqual(outcome.facts_pack["quote"]["open"], 123.17)
            self.assertEqual(outcome.facts_pack["quote"]["close"], 114.79)
            self.assertTrue(output.exists())
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
            self.assertTrue(outcome.wrote_file)
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
            self.assertTrue(outcome.wrote_file)
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
            self.assertTrue(outcome.wrote_file)
            self.assertTrue(output.exists())
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
            original = "{\"original\": true}\n"
            output.write_text(original, encoding="utf-8")
            payload = load_fixture("tencent_quote_0710.json")
            with mock.patch.object(gdf.os, "replace", side_effect=OSError("replace failed")):
                with self.assertRaises(OSError):
                    gdf.atomic_write_json(output, payload)
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

    def test_atomic_write_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "facts.json"
            payload = load_fixture("tencent_quote_0710.json")
            gdf.atomic_write_json(output, payload)
            self.assertTrue(output.exists())
            written = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(written["source"], "tencent")
            self.assertEqual(written["source_date"], "2026-07-10")
            tmp_residuals = list(output.parent.glob("*.tmp"))
            self.assertEqual(tmp_residuals, [])

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
