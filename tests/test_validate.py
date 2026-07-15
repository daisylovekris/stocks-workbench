import json
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "tools" / "validate_review_chain.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures"
DEFAULT_DATE = "2026-01-16"
DEFAULT_PREVIOUS_DATE = "2026-01-15"
DEFAULT_KEY_LEVELS = "126.10,127.18,138.61"


def run_validator(
    fixture_path: Path,
    facts_pack: Path | None = None,
    no_facts: bool = False,
    migration_base_facts: Path | None = None,
) -> str:
    cmd = [
        "python3",
        str(VALIDATOR),
        "--files",
        str(fixture_path),
        "--date",
        DEFAULT_DATE,
        "--previous-date",
        DEFAULT_PREVIOUS_DATE,
        "--key-levels",
        DEFAULT_KEY_LEVELS,
        "--verbose",
        "--no-fail",
    ]
    if facts_pack is not None and not no_facts:
        cmd.extend(["--facts-pack", str(facts_pack)])
    if migration_base_facts is not None:
        cmd.extend(["--migration-base-facts", str(migration_base_facts)])
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout


def extract_findings(report: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in report.splitlines():
        stripped = line.strip()
        if stripped.startswith("- File: "):
            if current:
                findings.append(current)
            current = {"file": stripped}
            continue
        if current is None:
            continue
        for key, prefix in (
            ("line", "- Line: "),
            ("rule_id", "- Rule: "),
            ("severity", "- Severity: "),
            ("matched", "- Matched: "),
        ):
            if stripped.startswith(prefix):
                current[key] = stripped.removeprefix(prefix).strip("`")
                break
    if current:
        findings.append(current)
    return [finding for finding in findings if "rule_id" in finding]


def write_current_markdown(tmp_path: Path) -> Path:
    path = tmp_path / "review.md"
    path.write_text("## 当前结论\n仅作观察，不输出买卖动作。\n", encoding="utf-8")
    return path


def base_volume_ratio_facts(method: str = "archived_tencent_snapshot_plus_sohu_historical_reverification") -> dict:
    return {
        "schema_version": "facts_pack_v0.2",
        "trade_date": DEFAULT_DATE,
        "symbol": "300274",
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
        "quote_verification": {"status": "confirmed", "source_date": DEFAULT_DATE},
        "volume_ratio": {
            "candidate_value": 1.49,
            "confirmed_value": 1.49,
            "source": "archived_tencent_snapshot+sohu_history",
            "verification": {
                "status": "confirmed",
                "method": method,
                "source_date": DEFAULT_DATE,
                "source": "archived_tencent_snapshot+sohu_history",
            },
            "legacy_verification": {
                "status": "confirmed",
                "method": "same_day_snapshot_plus_sohu_five_day_cross_check",
                "source": "tencent_qt_direct_index_49+sohu_five_day_volume",
                "source_date": DEFAULT_DATE,
                "fetched_at": "2026-01-16T07:05:00Z",
            },
            "cross_check": {
                "value": 1.49,
                "source": "sohu_five_day_volume_derived",
                "source_date": DEFAULT_DATE,
                "formula": "target_day_volume / mean(prior_5_trading_day_volume)",
                "tolerance": 0.05,
                "delta": 0.0,
            },
            "snapshot_ohlc_check": {
                "status": "matched",
                "fields": ["open", "high", "low", "close"],
                "snapshot_source": "tencent_qt_direct_index_49",
                "matched_to": "sohu_history",
                "source_date": DEFAULT_DATE,
                "tolerance": 0.02,
                "snapshot_ohlc": {"open": 108.0, "high": 109.26, "low": 100.73, "close": 108.29},
                "matched_ohlc": {"open": 108.0, "high": 109.26, "low": 100.73, "close": 108.29},
            },
            "archived_snapshot_source": {
                "source": "tencent_qt_direct_index_49",
                "source_date": DEFAULT_DATE,
                "ohlc": {"open": 108.0, "high": 109.26, "low": 100.73, "close": 108.29},
                "previous_close": 108.0,
                "pct_change": 0.2685185185185235,
                "amount": 100.65149576,
                "turnover_rate": 6.05,
                "volume_ratio": 1.49,
                "original_fetched_at": "2026-01-16T07:05:00Z",
                "source_pack_paths": [
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
                ],
            },
            "historical_ohlc_check": {
                "status": "passed",
                "archived_source": "tencent_qt_direct_index_49",
                "archived_source_date": DEFAULT_DATE,
                "historical_source": "sohu_history",
                "historical_source_date": DEFAULT_DATE,
                "ohlc": {"open": 108.0, "high": 109.26, "low": 100.73, "close": 108.29},
                "archived_ohlc": {"open": 108.0, "high": 109.26, "low": 100.73, "close": 108.29},
                "tolerance": 0.02,
                "compared_fields": ["open", "high", "low", "close"],
                "field_results": {
                    "open": {"left": 108.0, "right": 108.0, "delta": 0.0, "matched": True},
                    "high": {"left": 109.26, "right": 109.26, "delta": 0.0, "matched": True},
                    "low": {"left": 100.73, "right": 100.73, "delta": 0.0, "matched": True},
                    "close": {"left": 108.29, "right": 108.29, "delta": 0.0, "matched": True},
                },
                "fetched_at": "2026-07-15T08:00:00Z",
                "source": "sohu_history",
                "source_date": DEFAULT_DATE,
            },
            "five_day_volume_check": {
                "status": "passed",
                "source": "sohu_history",
                "trade_dates": ["2026-01-09", "2026-01-12", "2026-01-13", "2026-01-14", DEFAULT_PREVIOUS_DATE, DEFAULT_DATE],
                "volumes": [100.0, 110.0, 120.0, 130.0, 144.3322147651007, 180.0],
                "target_volume": 180.0,
                "calculated_value": 1.49,
                "expected_value": 1.49,
                "formula": "target_day_volume / mean(prior_5_trading_day_volume)",
                "tolerance": 0.02,
                "fetched_at": "2026-07-15T08:00:00Z",
            },
            "migration": {
                "old_file_sha256": "a" * 64,
                "migrated_at": "2026-07-15T12:00:00Z",
                "tool_version": "test",
                "tool": "tools/migrate_legacy_volume_ratio_evidence.py",
                "migration_type": "legacy_archived_tencent_snapshot_reverification",
            },
        },
        "needs_manual_check": {"volume_ratio": False, "disclosure_status": True},
        "missing": {"disclosure_status": None},
        "run": {"status": "partial"},
    }


def write_facts(tmp_path: Path, facts: dict, name: str = "facts.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(facts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


SHOULD_FLAG_CASES = [
    ("F01_R003_hard_bottom_claim.md", None, "R003_SUPPORT_OR_BOTTOM_MISLABEL", None),
    ("F02_R003_broad_support_upgrade.md", None, "R003_SUPPORT_OR_BOTTOM_MISLABEL", None),
    ("F03_R003_heading_key_level.md", None, "R003_SUPPORT_OR_BOTTOM_MISLABEL", None),
    ("F04_R004_stale_full_date.md", None, "R004_CURRENT_SECTION_STALE_DATE", None),
    ("F05_R004_stale_short_date.md", None, "R004_CURRENT_SECTION_STALE_DATE", None),
    ("F06_R005_stale_level_identity.md", None, "R005_CURRENT_SECTION_STALE_LEVEL", None),
    ("F07_R006_needs_check_announcement.md", "needs_check.json", "R006_DISCLOSURE_NEEDS_MANUAL_CHECK", "P2"),
    ("F08_R006_no_facts_safe_default.md", None, "R006_DISCLOSURE_NEEDS_MANUAL_CHECK", "P2"),
    ("F09_R008_pending_sync.md", None, "R008_INDEX_OR_ASSOCIATED_FILES_STATUS", None),
    ("F10_R006_no_announcement_variant.md", "needs_check.json", "R006_DISCLOSURE_NEEDS_MANUAL_CHECK", "P2"),
    ("F11_R003_support_label_with_observation_tail.md", None, "R003_SUPPORT_OR_BOTTOM_MISLABEL", None),
    ("F12_R003_mixed_negative_positive_support.md", None, "R003_SUPPORT_OR_BOTTOM_MISLABEL", None),
    ("F13_R004_table_current_stale_date.md", None, "R004_CURRENT_SECTION_STALE_DATE", None),
    ("F14_R003_mixed_comma_support_claim.md", None, "R003_SUPPORT_OR_BOTTOM_MISLABEL", None),
    ("F15_R006_empty_facts_pack_incomplete.md", "empty.json", "R006_DISCLOSURE_NEEDS_MANUAL_CHECK", "P2"),
    ("F16_R004_short_date_before_chinese.md", None, "R004_CURRENT_SECTION_STALE_DATE", None),
    ("F17_R004_prior_date_label_current_line.md", None, "R004_CURRENT_SECTION_STALE_DATE", None),
    ("F18_R004_older_stale_date.md", None, "R004_CURRENT_SECTION_STALE_DATE", None),
    ("F19_R004_stale_date_with_unrelated_comparison.md", None, "R004_CURRENT_SECTION_STALE_DATE", None),
    ("F20_R003_inherited_predicate_support_claim.md", None, "R003_SUPPORT_OR_BOTTOM_MISLABEL", None),
    ("F21_R003_prior_caution_does_not_suppress_next_claim.md", None, "R003_SUPPORT_OR_BOTTOM_MISLABEL", None),
]


@pytest.mark.parametrize("filename,facts_filename,expected_rule,expected_severity", SHOULD_FLAG_CASES)
def test_should_flag_fixture(filename: str, facts_filename: str | None, expected_rule: str, expected_severity: str | None) -> None:
    fixture_path = FIXTURES / "should_flag" / filename
    facts_pack = FIXTURES / "facts" / facts_filename if facts_filename else None
    report = run_validator(fixture_path, facts_pack=facts_pack)
    findings = extract_findings(report)
    matching = [finding for finding in findings if finding.get("rule_id") == expected_rule]
    assert matching, report
    if expected_severity:
        assert any(finding.get("severity") == expected_severity for finding in matching), report
    if filename == "F03_R003_heading_key_level.md":
        assert any("section heading:" in finding.get("matched", "") for finding in matching), report


SHOULD_PASS_CASES = [
    ("P01_downgrade_just_observation.md", None),
    ("P02_negative_intro_list.md", None),
    ("P03_teaching_write_as_context.md", None),
    ("P04_history_hard_bottom_claim.md", None),
    ("P05_old_date_current_like_subheading.md", None),
    ("P06_comparison_old_date.md", None),
    ("P07_path_recap_lines.md", None),
    ("P08_observation_key_level_discussion.md", None),
    ("P09_confirmed_facts_announcement.md", "confirmed.json"),
    ("P10_double_negative_risk_note.md", "confirmed.json"),
    ("P11_history_scope_current_child_heading.md", None),
    ("P12_fresh_price_action_observation.md", None),
    ("P13_observation_bottom_confirmation_question.md", None),
    ("P14_unrelated_segment_support_claim.md", None),
    ("P15_current_date_nested_history_heading.md", None),
    ("P16_phrase_first_support_observation_question.md", None),
    ("P17_support_question_with_is.md", None),
    ("P18_hedged_support_observation.md", None),
]


@pytest.mark.parametrize("filename,facts_filename", SHOULD_PASS_CASES)
def test_should_pass_fixture_has_zero_findings(filename: str, facts_filename: str | None) -> None:
    fixture_path = FIXTURES / "should_pass" / filename
    facts_pack = FIXTURES / "facts" / facts_filename if facts_filename else None
    report = run_validator(fixture_path, facts_pack=facts_pack)
    findings = extract_findings(report)
    assert findings == [], report


def assert_volume_ratio_evidence_p2(report: str) -> None:
    findings = extract_findings(report)
    matching = [finding for finding in findings if finding.get("rule_id") == "R009_VOLUME_RATIO_EVIDENCE_CONSISTENCY"]
    assert matching, report
    assert any(finding.get("severity") == "P2" for finding in matching), report


def test_same_day_snapshot_method_missing_snapshot_ohlc_check_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts("same_day_snapshot_plus_sohu_five_day_cross_check")
    facts["volume_ratio"].pop("snapshot_ohlc_check")
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_same_day_snapshot_method_missing_five_day_volume_check_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts("same_day_snapshot_plus_sohu_five_day_cross_check")
    facts["volume_ratio"].pop("five_day_volume_check")
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_same_day_snapshot_method_wrong_snapshot_date_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts("same_day_snapshot_plus_sohu_five_day_cross_check")
    facts["volume_ratio"]["snapshot_ohlc_check"]["source_date"] = DEFAULT_PREVIOUS_DATE
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_same_day_snapshot_method_non_finite_ohlc_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts("same_day_snapshot_plus_sohu_five_day_cross_check")
    facts["volume_ratio"]["snapshot_ohlc_check"]["snapshot_ohlc"]["open"] = "nan"
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_same_day_snapshot_method_ohlc_mismatch_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts("same_day_snapshot_plus_sohu_five_day_cross_check")
    facts["volume_ratio"]["snapshot_ohlc_check"]["matched_ohlc"]["close"] = 109.0
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_missing_archived_source_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"].pop("archived_snapshot_source")
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_missing_historical_ohlc_check_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"].pop("historical_ohlc_check")
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_missing_migration_metadata_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"].pop("migration")
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_close_999_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["historical_ohlc_check"]["ohlc"]["close"] = 999
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_authoritative_archived_ohlc_close_999_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["archived_snapshot_source"]["ohlc"]["close"] = 999
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_redundant_archived_ohlc_conflict_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["historical_ohlc_check"]["archived_ohlc"] = {
        "open": 108.0,
        "high": 109.26,
        "low": 100.73,
        "close": 999,
    }
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_archived_volume_ratio_conflict_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["archived_snapshot_source"]["volume_ratio"] = 999
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_super_tolerances_are_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["historical_ohlc_check"]["tolerance"] = 1e9
    facts["volume_ratio"]["five_day_volume_check"]["tolerance"] = 1e9
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_non_finite_archived_ohlc_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["archived_snapshot_source"]["ohlc"]["open"] = "inf"
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_duplicate_five_day_trade_dates_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["five_day_volume_check"]["trade_dates"][2] = facts["volume_ratio"]["five_day_volume_check"]["trade_dates"][1]
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_disordered_five_day_trade_dates_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    dates = facts["volume_ratio"]["five_day_volume_check"]["trade_dates"]
    dates[1], dates[2] = dates[2], dates[1]
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_final_trade_date_must_be_target_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["five_day_volume_check"]["trade_dates"][-1] = "2026-01-17"
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_prior_dates_must_precede_target_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["five_day_volume_check"]["trade_dates"][4] = DEFAULT_DATE
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


@pytest.mark.parametrize("bad_volume", [0, -1, "nan", "inf"])
def test_archived_reverification_bad_volume_values_are_p2(tmp_path: Path, bad_volume) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["five_day_volume_check"]["volumes"][3] = bad_volume
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_changed_volumes_with_stale_declared_value_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["five_day_volume_check"]["volumes"] = [1, 1, 1, 1, 1, 999]
    facts["volume_ratio"]["five_day_volume_check"]["calculated_value"] = 1.49
    facts["volume_ratio"]["five_day_volume_check"]["expected_value"] = 1.49
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_fake_ancient_trade_dates_are_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["five_day_volume_check"]["trade_dates"] = [
        "0001-01-01",
        "0001-01-02",
        "0001-01-03",
        "0001-01-04",
        "0001-01-05",
        DEFAULT_DATE,
    ]
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_unable_to_recalculate_confirmed_value_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["five_day_volume_check"]["calculated_value"] = 1.42
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_formal_value_mismatch_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["confirmed_value"] = 1.42
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_reverification_five_day_source_must_be_sohu_history_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["five_day_volume_check"]["source"] = "tencent_history"
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


@pytest.mark.parametrize("method", ["unknown_method", "archived_tencent_snapshot_plus_sohu_historical_reverificaton"])
def test_unknown_or_misspelled_volume_ratio_method_is_p2(tmp_path: Path, method: str) -> None:
    facts = base_volume_ratio_facts(method)
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_same_day_cross_check_value_and_delta_are_recomputed(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts("same_day_snapshot_plus_sohu_five_day_cross_check")
    facts["volume_ratio"]["cross_check"]["value"] = 99
    facts["volume_ratio"]["cross_check"]["delta"] = 97.51
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_same_day_cross_check_formula_must_match_authoritative_id(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts("same_day_snapshot_plus_sohu_five_day_cross_check")
    facts["volume_ratio"]["cross_check"]["formula"] = "target / average"
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_historical_five_day_method_with_complete_cross_check_passes(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts("historical_five_day_volume_cross_check")
    facts["volume_ratio"] = {
        "candidate_value": 1.25,
        "confirmed_value": 1.25,
        "source": "sohu_five_day_volume+tencent_five_day_volume",
        "verification": {
            "status": "confirmed",
            "method": "historical_five_day_volume_cross_check",
            "source": "sohu_five_day_volume+tencent_five_day_volume",
            "source_date": DEFAULT_DATE,
        },
        "cross_check": {
            "value": 1.25,
            "source": "tencent_five_day_volume_derived",
            "source_date": DEFAULT_DATE,
            "formula": "target_day_volume / mean(prior_5_trading_day_volume)",
            "tolerance": 0.01,
            "delta": 0.0,
        },
        "source_volume_checks": {
            "sohu_history": {
                "status": "passed",
                "source": "sohu_history",
                "trade_dates": ["2026-01-09", "2026-01-12", "2026-01-13", "2026-01-14", DEFAULT_PREVIOUS_DATE, DEFAULT_DATE],
                "volumes": [100.0, 110.0, 120.0, 130.0, 260.0, 180.0],
                "target_volume": 180.0,
                "calculated_value": 1.25,
                "expected_value": 1.25,
                "formula": "target_day_volume / mean(prior_5_trading_day_volume)",
                "tolerance": 0.01,
            },
            "tencent_history": {
                "status": "passed",
                "source": "tencent_history",
                "trade_dates": ["2026-01-09", "2026-01-12", "2026-01-13", "2026-01-14", DEFAULT_PREVIOUS_DATE, DEFAULT_DATE],
                "volumes": [100.0, 110.0, 120.0, 130.0, 260.0, 180.0],
                "target_volume": 180.0,
                "calculated_value": 1.25,
                "expected_value": 1.25,
                "formula": "target_day_volume / mean(prior_5_trading_day_volume)",
                "tolerance": 0.01,
            },
        },
    }
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert extract_findings(report) == [], report


def test_historical_five_day_method_missing_source_windows_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts("historical_five_day_volume_cross_check")
    facts["volume_ratio"] = {
        "candidate_value": 1.25,
        "confirmed_value": 1.25,
        "source": "sohu_five_day_volume+tencent_five_day_volume",
        "verification": {
            "status": "confirmed",
            "method": "historical_five_day_volume_cross_check",
            "source_date": DEFAULT_DATE,
        },
        "cross_check": {
            "value": 1.25,
            "source": "tencent_five_day_volume_derived",
            "source_date": DEFAULT_DATE,
            "formula": "target_day_volume / mean(prior_5_trading_day_volume)",
            "tolerance": 0.01,
            "delta": 0.0,
        },
    }
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_legacy_manual_requires_manual_confirmed_status(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts("legacy_manual_confirmation")
    facts["volume_ratio"] = {
        "candidate_value": 1.25,
        "confirmed_value": 1.25,
        "source": "manual_check",
        "verification": {"status": "confirmed", "method": "legacy_manual_confirmation"},
        "manual_verification": {
            "decided_by": "analyst",
            "decided_at": DEFAULT_DATE,
            "source": "ticket",
            "reason": "manual legacy backfill",
        },
    }
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_legacy_manual_complete_metadata_passes(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts("legacy_manual_confirmation")
    facts["volume_ratio"] = {
        "candidate_value": 1.25,
        "confirmed_value": 1.25,
        "source": "manual_check",
        "verification": {"status": "manual_confirmed", "method": "legacy_manual_confirmation"},
        "manual_verification": {
            "decided_by": "analyst",
            "decided_at": DEFAULT_DATE,
            "source": "ticket",
            "reason": "manual legacy backfill",
        },
    }
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert extract_findings(report) == [], report


def test_archived_reverification_complete_evidence_passes(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    findings = extract_findings(report)
    assert findings == [], report


@pytest.mark.parametrize("status", ["unverified", "unknown_status", "", "derived_confirmed"])
def test_archived_reverification_rejects_non_profile_status(tmp_path: Path, status: str) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["verification"]["status"] = status
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_formal_volume_ratio_missing_status_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["verification"].pop("status")
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_formal_manual_volume_ratio_missing_method_is_p2(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    facts["volume_ratio"]["source"] = "manual_check"
    facts["volume_ratio"]["verification"] = {"status": "manual_confirmed"}
    facts["volume_ratio"]["manual_verification"] = {
        "decided_by": "analyst",
        "decided_at": DEFAULT_DATE,
        "source": "ticket",
        "reason": "manual legacy backfill",
    }
    report = run_validator(write_current_markdown(tmp_path), facts_pack=write_facts(tmp_path, facts))
    assert_volume_ratio_evidence_p2(report)


def test_archived_legacy_verification_must_equal_migration_base(tmp_path: Path) -> None:
    facts = base_volume_ratio_facts()
    base = base_volume_ratio_facts("same_day_snapshot_plus_sohu_five_day_cross_check")
    base["volume_ratio"]["verification"] = dict(facts["volume_ratio"]["legacy_verification"])
    facts["volume_ratio"]["legacy_verification"]["method"] = "unexpected_method"
    report = run_validator(
        write_current_markdown(tmp_path),
        facts_pack=write_facts(tmp_path, facts),
        migration_base_facts=write_facts(tmp_path, base, "base.json"),
    )
    assert_volume_ratio_evidence_p2(report)
