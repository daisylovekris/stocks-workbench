import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "tools" / "validate_review_chain.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures"
DEFAULT_DATE = "2026-01-16"
DEFAULT_PREVIOUS_DATE = "2026-01-15"
DEFAULT_KEY_LEVELS = "126.10,127.18,138.61"


def run_validator(fixture_path: Path, facts_pack: Path | None = None, no_facts: bool = False) -> str:
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
