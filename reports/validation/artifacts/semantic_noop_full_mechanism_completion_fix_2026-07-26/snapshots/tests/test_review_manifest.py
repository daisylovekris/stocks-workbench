from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from tools import review_manifest as rm


SYMBOL = "300274"
TRADE_DATE = "2026-07-16"
FIXED_NOW = datetime(2026, 7, 16, 16, 30, tzinfo=ZoneInfo("Asia/Shanghai"))


def facts_payload(*, status: str = "success", missing=None, needs=None) -> dict:
    return {
        "schema_version": "facts_pack_v0.2",
        "symbol": SYMBOL,
        "trade_date": TRADE_DATE,
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
        "quote_verification": {"status": "confirmed", "source": "pytest", "source_date": TRADE_DATE},
        "run": {"status": status},
        "volume_ratio": {
            "confirmed_value": 1.1,
            "verification": {"status": "confirmed", "method": "pytest", "source_date": TRADE_DATE},
        },
        "missing": {} if missing is None else missing,
        "needs_manual_check": {} if needs is None else needs,
    }


def payload_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def setup_repo(tmp_path: Path, *, official_bytes: bytes | None = None) -> tuple[Path, Path, str]:
    repo = tmp_path / "repo"
    official = repo / "data" / "daily" / f"{SYMBOL}_{TRADE_DATE}_facts.json"
    official.parent.mkdir(parents=True)
    data = official_bytes if official_bytes is not None else payload_bytes(facts_payload())
    official.write_bytes(data)
    return repo, official, hashlib.sha256(data).hexdigest()


def write_runner(
    path: Path,
    *,
    official: Path,
    official_sha: str,
    mode: str = "today_after_close",
    **overrides,
) -> Path:
    manifest = {
        "schema_version": "runner_manifest_v0.2_phase_b",
        "run_id": str(uuid.uuid4()),
        "symbol": SYMBOL,
        "target_date": TRADE_DATE,
        "mode": mode,
        "write_official": True,
        "dry_run": False,
        "stage": "finished",
        "finished_at": "2026-07-16T16:00:00+08:00",
        "manifest_path": str(path.resolve(strict=False)),
        "official_path": str(official),
        "official_sha256_before": None,
        "official_sha256_after": official_sha,
        "candidate_sha256": official_sha,
        "official_changed": True,
        "official_bytes_equal_candidate": True,
        "write_action": "created",
        "outcome": "success",
        "reason_code": "official_written",
        "official_validator_after": {"status": "passed"},
        "official_post_write_error": None,
        "partial_write_policy": {"eligible": True},
    }
    manifest.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return path


def semantic_facts_pair(*, status: str = "partial") -> tuple[dict, dict]:
    official = facts_payload(status=status, needs={"market_indices": True})
    official["generated_at"] = "2026-07-16T08:00:00Z"
    official["quote_verification"]["fetched_at"] = "2026-07-16T08:00:01Z"
    official["run"]["fetched_at"] = "2026-07-16T08:00:02Z"
    official["volume_ratio"]["five_day_volume_check"] = {"fetched_at": "2026-07-16T08:00:03Z"}
    official["volume_ratio"]["snapshot_ohlc_check"] = {"fetched_at": "2026-07-16T08:00:04Z"}
    official["volume_ratio"]["verification"]["fetched_at"] = "2026-07-16T08:00:05Z"
    candidate = json.loads(json.dumps(official))
    candidate["generated_at"] = "2026-07-16T09:00:00Z"
    candidate["quote_verification"]["fetched_at"] = "2026-07-16T09:00:01Z"
    candidate["run"]["fetched_at"] = "2026-07-16T09:00:02Z"
    candidate["volume_ratio"]["five_day_volume_check"]["fetched_at"] = "2026-07-16T09:00:03Z"
    candidate["volume_ratio"]["snapshot_ohlc_check"]["fetched_at"] = "2026-07-16T09:00:04Z"
    candidate["volume_ratio"]["verification"]["fetched_at"] = "2026-07-16T09:00:05Z"
    return official, candidate


def write_semantic_runner(path: Path, *, official: Path, official_payload: dict, candidate: dict, **overrides) -> Path:
    official_bytes = payload_bytes(official_payload)
    candidate_bytes = payload_bytes(candidate)
    candidate_path = path.parent / "candidate.json"
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_bytes(candidate_bytes)
    official_sha = hashlib.sha256(official_bytes).hexdigest()
    comparison = rm.oft.build_semantic_comparison(
        candidate=candidate,
        official=official_payload,
        candidate_bytes=candidate_bytes,
        official_bytes=official_bytes,
        symbol=SYMBOL,
        target_date=TRADE_DATE,
    )
    manifest_overrides = {
        "official_sha256_before": official_sha,
        "official_sha256_after": official_sha,
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "candidate_path": str(candidate_path),
        "official_changed": False,
        "official_bytes_equal_candidate": False,
        "write_action": "semantic_noop",
        "outcome": "official_unchanged",
        "reason_code": "official_semantically_identical",
        "comparison": comparison,
    }
    manifest_overrides.update(overrides)
    return write_runner(
        path,
        official=official,
        official_sha=official_sha,
        **manifest_overrides,
    )


def options(tmp_path: Path, repo: Path, runner: Path | None, **overrides) -> rm.ReviewOptions:
    values = {
        "runtime_dir": tmp_path / "runtime",
        "runner_runtime_dir": tmp_path,
        "symbol": SYMBOL,
        "trade_date": TRADE_DATE,
        "runner_manifest_path": runner,
        "repo_root": repo,
        "official_lock_dir": tmp_path / "official-locks",
        "now": lambda: FIXED_NOW,
    }
    values.update(overrides)
    return rm.ReviewOptions(**values)


def load_manifest(result: rm.ReviewResult) -> dict:
    assert result.manifest_path is not None
    return json.loads(result.manifest_path.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def pass_validator(monkeypatch):
    monkeypatch.setattr(rm, "_validator_result", lambda facts, official_path, trade_date: {"status": "passed"})
    monkeypatch.setattr(rm.vrc, "assert_facts_pack_valid", lambda *args, **kwargs: None)


def test_complete_is_ready_for_human_review(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    result = rm.generate_review(options(tmp_path, repo, runner))
    manifest = load_manifest(result)
    assert result.status == "review_created"
    assert manifest["artifact_type"] == "facts_review"
    assert manifest["review_state"] == "ready_for_human_review"
    assert manifest["review_id"] == f"rev_{SYMBOL}_{TRADE_DATE}_{sha[:16]}"


def test_partial_is_needs_manual_review(tmp_path):
    data = payload_bytes(facts_payload(status="partial", needs={"market_indices": True}))
    repo, official, sha = setup_repo(tmp_path, official_bytes=data)
    runner = write_runner(
        tmp_path / "runner.json",
        official=official,
        official_sha=sha,
        outcome="partial",
        reason_code="official_written_partial",
    )
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    assert manifest["review_state"] == "needs_manual_review"
    assert "固定警示：本记录存在未决事项" in Path(manifest_path(tmp_path, manifest)).with_name("review_summary.md").read_text()


def test_phase_c_accepts_valid_semantic_noop_and_is_idempotent(tmp_path):
    official_payload, candidate = semantic_facts_pair()
    official_bytes = payload_bytes(official_payload)
    repo, official, sha = setup_repo(tmp_path, official_bytes=official_bytes)
    runner = write_semantic_runner(
        tmp_path / "runner-bundle" / "manifest.json",
        official=official,
        official_payload=official_payload,
        candidate=candidate,
    )

    first = rm.generate_review(options(tmp_path, repo, runner))
    manifest = load_manifest(first)
    first_index = first.index_path.read_bytes()
    second = rm.generate_review(options(tmp_path, repo, runner))

    assert hashlib.sha256(official.read_bytes()).hexdigest() == sha
    assert manifest["artifact_type"] == "facts_review"
    assert manifest["review_state"] == "needs_manual_review"
    assert manifest["write_action"] == "semantic_noop"
    assert manifest["write_reason_code"] == "official_semantically_identical"
    assert manifest["evidence_summary"]["semantic_comparison"]["semantic_equal"] is True
    assert manifest["downstream_permissions"] == rm.DOWNSTREAM_PERMISSIONS
    assert second.status == "review_already_exists"
    assert second.index_path.read_bytes() == first_index
    assert len(rm.read_index(second.index_path)) == 1


def test_phase_c_rejects_tampered_semantic_sha(tmp_path):
    official_payload, candidate = semantic_facts_pair()
    repo, official, _sha = setup_repo(tmp_path, official_bytes=payload_bytes(official_payload))
    runner = write_semantic_runner(
        tmp_path / "runner-bundle" / "manifest.json",
        official=official,
        official_payload=official_payload,
        candidate=candidate,
    )
    payload = json.loads(runner.read_text(encoding="utf-8"))
    payload["comparison"]["candidate_semantic_sha256"] = "f" * 64
    runner.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    assert manifest["artifact_type"] == "incident_review"
    assert manifest["incident_reason_code"] == "runner_manifest_invalid"
    assert manifest["write_action"] is None


def test_phase_c_rejects_missing_semantic_candidate(tmp_path):
    official_payload, candidate = semantic_facts_pair()
    repo, official, _sha = setup_repo(tmp_path, official_bytes=payload_bytes(official_payload))
    runner = write_semantic_runner(
        tmp_path / "runner-bundle" / "manifest.json",
        official=official,
        official_payload=official_payload,
        candidate=candidate,
    )
    (runner.parent / "candidate.json").unlink()

    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    assert manifest["artifact_type"] == "incident_review"
    assert manifest["incident_reason_code"] == "runner_manifest_invalid"
    assert manifest["write_action"] is None


def test_phase_c_rejects_candidate_replaced_by_symlink_before_fd_open(tmp_path, monkeypatch):
    official_payload, candidate = semantic_facts_pair()
    repo, official, _sha = setup_repo(tmp_path, official_bytes=payload_bytes(official_payload))
    runner = write_semantic_runner(
        tmp_path / "runner-bundle" / "manifest.json",
        official=official,
        official_payload=official_payload,
        candidate=candidate,
    )
    candidate_path = runner.parent / "candidate.json"
    outside = tmp_path / "outside-candidate.json"
    outside.write_bytes(candidate_path.read_bytes())
    original_open = rm.os.open
    replaced = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal replaced
        if path == "candidate.json" and dir_fd is not None and not replaced:
            replaced = True
            candidate_path.unlink()
            candidate_path.symlink_to(outside)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(rm.os, "open", racing_open)
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))

    assert replaced is True
    assert manifest["artifact_type"] == "incident_review"
    assert manifest["evidence_summary"]["runner_manifest_error"]["error_type"] == (
        "runner_manifest_semantic_candidate_missing"
    )
    assert manifest["write_action"] is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"outcome": "partial"},
        {"reason_code": "official_already_identical"},
        {"official_changed": True},
    ],
)
def test_phase_c_rejects_semantic_action_outcome_reason_mismatch(tmp_path, overrides):
    official_payload, candidate = semantic_facts_pair()
    repo, official, _sha = setup_repo(tmp_path, official_bytes=payload_bytes(official_payload))
    runner = write_semantic_runner(
        tmp_path / "runner-bundle" / "manifest.json",
        official=official,
        official_payload=official_payload,
        candidate=candidate,
        **overrides,
    )

    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    assert manifest["artifact_type"] == "incident_review"
    assert manifest["incident_reason_code"] == "runner_manifest_invalid"
    assert manifest["write_action"] is None


def manifest_path(tmp_path: Path, manifest: dict) -> Path:
    return tmp_path / "runtime" / "reviews" / TRADE_DATE / manifest["review_id"] / "review_manifest.json"


def test_missing_and_needs_manual_check_are_preserved_and_combined(tmp_path):
    missing = {"sector_context": "缺失", "market_indices": None}
    needs = {"volume_ratio": False, "news_policy_context": {"status": "needs_manual_check"}}
    repo, official, sha = setup_repo(tmp_path, official_bytes=payload_bytes(facts_payload(status="partial", missing=missing, needs=needs)))
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    assert manifest["missing"] == missing
    assert manifest["needs_manual_check"] == needs
    assert manifest["unresolved_fields"] == [
        {"source": "missing", "field": "sector_context", "value": "缺失"},
        {"source": "needs_manual_check", "field": "news_policy_context", "value": {"status": "needs_manual_check"}},
    ]


def test_downstream_permissions_are_permanently_false(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    assert load_manifest(rm.generate_review(options(tmp_path, repo, runner)))["downstream_permissions"] == rm.DOWNSTREAM_PERMISSIONS


@pytest.mark.parametrize("field", ["human_decision", "human_notes", "approved", "rejected"])
def test_human_or_model_decision_fields_are_rejected(field):
    manifest = {key: None for key in rm.REQUIRED_MANIFEST_FIELDS}
    manifest.update(
        schema_version=rm.SCHEMA_VERSION,
        artifact_type="facts_review",
        review_id="rev_300274_2026-07-16_" + "a" * 16,
        symbol=SYMBOL,
        trade_date=TRADE_DATE,
        mode="rebuild_from_official",
        official_sha256="a" * 64,
        review_state="needs_manual_review",
        downstream_permissions=dict(rm.DOWNSTREAM_PERMISSIONS),
    )
    manifest[field] = "approved"
    with pytest.raises(rm.ReviewError, match="forbidden"):
        rm.validate_review_manifest(manifest)


@pytest.mark.parametrize("broken", [b"{", b'{"symbol":"300274"'])
def test_incident_review_for_damaged_or_truncated_json(tmp_path, broken):
    repo, official, sha = setup_repo(tmp_path, official_bytes=broken)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    assert manifest["artifact_type"] == "incident_review"
    assert manifest["incident_reason_code"] == "official_json_invalid"
    assert manifest["review_state"] == "needs_manual_review"
    assert manifest["missing"] == {}
    assert manifest["confirmed_fields"] == []
    assert manifest["evidence_summary"]["official_parse_error"]


def test_incident_review_for_validator_failure(tmp_path, monkeypatch):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    monkeypatch.setattr(rm, "_validator_result", lambda facts, official_path, trade_date: {"status": "failed", "message": "P1 failed"})
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    assert manifest["artifact_type"] == "incident_review"
    assert manifest["incident_reason_code"] == "validator_failed"


@pytest.mark.parametrize(
    "runner_bytes",
    [
        b"{broken",
        b"[]\n",
        b'{"schema_version":"unknown","symbol":"999999","target_date":"2099-01-01"}\n',
        b'{"schema_version":"runner_manifest_v0.2_phase_b","symbol":123}\n',
    ],
)
@pytest.mark.parametrize("official_valid", [True, False])
def test_invalid_runner_manifest_creates_minimal_incident(tmp_path, runner_bytes, official_valid):
    official_bytes = None if official_valid else b"{damaged-official"
    repo, _official, _sha = setup_repo(tmp_path, official_bytes=official_bytes)
    runner = tmp_path / "runner.json"
    runner.write_bytes(runner_bytes)
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    assert manifest["artifact_type"] == "incident_review"
    assert manifest["review_state"] == "needs_manual_review"
    assert manifest["incident_reason_code"] == "runner_manifest_invalid"
    assert manifest["downstream_permissions"] == rm.DOWNSTREAM_PERMISSIONS
    assert manifest["run_id"] is None
    assert manifest["write_action"] is None
    assert manifest["write_reason_code"] is None
    assert manifest["facts_status"] is None
    assert manifest["confirmed_fields"] == []
    assert manifest["missing"] == {}
    assert manifest["needs_manual_check"] == {}
    assert manifest["source_refs"] == []
    assert manifest["evidence_summary"]["runner_manifest_error"]["error_type"]
    assert manifest["runner_manifest_sha256"] == hashlib.sha256(runner_bytes).hexdigest()


def test_invalid_runner_cannot_spoof_identity_or_leak_raw_sensitive_text(tmp_path):
    repo, _official, _sha = setup_repo(tmp_path)
    runner = tmp_path / "runner.json"
    runner.write_text(
        json.dumps(
            {
                "schema_version": "unknown",
                "symbol": "999999",
                "target_date": "2099-01-01",
                "write_action": "Authorization: Bearer forged-action-secret",
                "reason_code": "OPENAI_API_KEY=forged-key-secret",
                "source_refs": {"Cookie": "session-cookie-secret"},
            }
        ),
        encoding="utf-8",
    )
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    serialized = json.dumps(manifest, ensure_ascii=False)
    assert manifest["symbol"] == SYMBOL
    assert manifest["trade_date"] == TRADE_DATE
    assert "999999" not in serialized
    assert "2099-01-01" not in serialized
    assert "forged-action-secret" not in serialized
    assert "forged-key-secret" not in serialized
    assert "session-cookie-secret" not in serialized


@pytest.mark.parametrize(
    ("write_action", "reason_code", "outcome", "official_changed", "after_sha_required"),
    [
        ("created", "official_written", "success", True, True),
        ("created", "official_written_partial", "partial", True, True),
        ("created", "official_written_manifest_failed", "success", True, True),
        ("created", "official_written_manifest_failed", "partial", True, True),
        ("identical_noop", "official_already_identical", "success", False, True),
        ("identical_noop", "official_already_identical", "partial", False, True),
        ("identical_noop", "official_written_manifest_failed", "success", False, True),
        ("identical_noop", "official_written_manifest_failed", "partial", False, True),
        ("conflict_blocked", "official_conflict", "needs_manual_review", False, False),
        ("conflict_blocked", "official_invalid", "needs_manual_review", False, False),
        ("sealed_blocked", "sealed_exists", "skipped", False, True),
        ("manual_blocked", "manual_exists", "skipped", False, True),
        ("not_eligible", "partial_not_eligible_for_official", "needs_manual_review", False, False),
        ("not_eligible", "validator_failed", "needs_manual_review", False, False),
        ("not_eligible", "candidate_not_eligible_for_official", "needs_manual_review", False, False),
        ("created_postcheck_failed", "official_written_postcheck_failed", "needs_manual_review", True, False),
        ("created_postcheck_failed", "official_written_bytes_mismatch", "needs_manual_review", True, False),
    ],
)
def test_phase_b_authoritative_action_reason_matrix(
    tmp_path,
    write_action,
    reason_code,
    outcome,
    official_changed,
    after_sha_required,
):
    repo, official, sha = setup_repo(tmp_path)
    before_sha = sha if not official_changed and after_sha_required else None
    after_sha = sha if after_sha_required else None
    runner_path = write_runner(
        tmp_path / "runner.json",
        official=official,
        official_sha=sha,
        write_action=write_action,
        reason_code=reason_code,
        outcome=outcome,
        official_changed=official_changed,
        official_sha256_before=before_sha,
        official_sha256_after=after_sha,
    )
    manifest = json.loads(runner_path.read_text(encoding="utf-8"))
    rm.validate_runner_manifest(
        manifest,
        symbol=SYMBOL,
        trade_date=TRADE_DATE,
        official_path=official,
        runner_manifest_path=runner_path.resolve(),
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"write_action": "conflict_blocked", "reason_code": "official_conflict", "outcome": "needs_manual_review", "official_changed": False},
        {"write_action": "sealed_blocked", "reason_code": "sealed_exists", "outcome": "skipped", "official_changed": False},
        {"write_action": "manual_blocked", "reason_code": "manual_exists", "outcome": "skipped", "official_changed": False},
        {"write_action": "not_eligible", "reason_code": "partial_not_eligible_for_official", "outcome": "needs_manual_review", "official_changed": False},
        {"write_action": "created_postcheck_failed", "reason_code": "official_written_postcheck_failed", "outcome": "needs_manual_review", "official_changed": True},
    ],
)
def test_noncompleted_phase_b_transactions_never_become_ready(tmp_path, overrides):
    repo, official, sha = setup_repo(tmp_path)
    if not overrides["official_changed"]:
        overrides = {**overrides, "official_sha256_before": sha, "official_sha256_after": sha}
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha, **overrides)
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    assert manifest["review_state"] == "needs_manual_review"


@pytest.mark.parametrize(
    ("overrides", "forged_value"),
    [
        ({"write_action": "forged_write_action"}, "forged_write_action"),
        ({"reason_code": "forged_reason_code"}, "forged_reason_code"),
        ({"write_action": "Authorization: Bearer forged-action-secret"}, "forged-action-secret"),
        ({"reason_code": "OPENAI_API_KEY=forged-reason-secret"}, "forged-reason-secret"),
        ({"write_action": "created", "reason_code": "official_conflict"}, None),
        ({"official_changed": False}, None),
        ({"official_sha256_after": None}, None),
        ({"candidate_sha256": "e" * 64}, None),
        ({"write_action": "conflict_blocked", "reason_code": "official_conflict", "outcome": "success", "official_changed": False}, None),
        ({"write_action": "created_postcheck_failed", "reason_code": "official_written_postcheck_failed", "outcome": "success"}, None),
        ({"write_action": None}, None),
        ({"write_action": ["created"]}, None),
        ({"reason_code": {"value": "official_written"}}, None),
        ({"write_action": ""}, None),
        ({"reason_code": ""}, None),
    ],
)
def test_invalid_action_reason_semantics_fail_closed_to_minimal_incident(tmp_path, overrides, forged_value):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha, **overrides)
    result = rm.generate_review(options(tmp_path, repo, runner))
    manifest = load_manifest(result)
    assert manifest["artifact_type"] == "incident_review"
    assert manifest["review_state"] == "needs_manual_review"
    assert manifest["incident_reason_code"] == "runner_manifest_invalid"
    assert manifest["downstream_permissions"] == rm.DOWNSTREAM_PERMISSIONS
    assert manifest["write_action"] is None
    assert manifest["write_reason_code"] is None
    assert manifest["facts_status"] is None
    assert manifest["confirmed_fields"] == []
    assert manifest["missing"] == {}
    assert manifest["source_refs"] == []
    if forged_value:
        runtime_files = [path for path in (tmp_path / "runtime").rglob("*") if path.is_file()]
        runtime_text = "\n".join(path.read_text(encoding="utf-8") for path in runtime_files)
        assert forged_value not in runtime_text
        assert all(forged_value not in str(path) for path in runtime_files)


@pytest.mark.parametrize(
    ("overrides", "incident"),
    [
        ({"write_action": "conflict_blocked", "outcome": "needs_manual_review", "reason_code": "official_conflict", "official_changed": False}, "official_conflict"),
        ({"write_action": "created", "outcome": "success", "reason_code": "official_written_manifest_failed", "official_changed": True}, "official_written_manifest_failed"),
        ({"write_action": "created_postcheck_failed", "outcome": "needs_manual_review", "reason_code": "official_written_postcheck_failed", "official_post_write_error": {"stage": "post_write_read"}}, "post_write_failure"),
        ({"write_action": "created_postcheck_failed", "outcome": "needs_manual_review", "official_bytes_equal_candidate": False, "reason_code": "official_written_bytes_mismatch", "candidate_sha256": "b" * 64}, "official_bytes_mismatch"),
    ],
)
def test_transaction_incidents_are_preserved(tmp_path, overrides, incident):
    repo, official, sha = setup_repo(tmp_path)
    if overrides.get("official_changed") is False:
        overrides = {**overrides, "official_sha256_before": sha, "official_sha256_after": sha}
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha, **overrides)
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    assert manifest["artifact_type"] == "incident_review"
    assert manifest["incident_reason_code"] == incident
    assert manifest["write_action"] == overrides.get("write_action", "created")


def test_runner_sha_mismatch_forces_incident_and_manual_state(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha="a" * 64)
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    assert manifest["official_sha256"] == sha
    assert manifest["official_sha_match"] is False
    assert manifest["incident_reason_code"] == "runner_official_sha_mismatch"
    assert manifest["review_state"] == "needs_manual_review"


def test_candidate_sha_mismatch_forces_bytes_mismatch_incident(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(
        tmp_path / "runner.json",
        official=official,
        official_sha=sha,
        write_action="created_postcheck_failed",
        outcome="needs_manual_review",
        reason_code="official_written_bytes_mismatch",
        candidate_sha256="e" * 64,
        official_bytes_equal_candidate=None,
    )
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    assert manifest["official_sha_match"] is True
    assert manifest["incident_reason_code"] == "official_bytes_mismatch"


def test_candidate_sha_and_transaction_evidence_are_preserved(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(
        tmp_path / "runner.json",
        official=official,
        official_sha=sha,
        write_action="conflict_blocked",
        outcome="needs_manual_review",
        reason_code="official_conflict",
        candidate_sha256="c" * 64,
        official_sha256_before=sha,
        official_changed=False,
    )
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    assert manifest["candidate_sha256"] == "c" * 64
    assert manifest["official_sha256_before"] == sha
    assert manifest["evidence_summary"]["candidate_sha256"] == "c" * 64


def test_same_sha_complete_record_is_noop(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    first = rm.generate_review(options(tmp_path, repo, runner))
    before = first.manifest_path.read_bytes()
    index_before = first.index_path.read_bytes()
    second = rm.generate_review(options(tmp_path, repo, runner))
    assert second.status == "review_already_exists"
    assert second.manifest_path.read_bytes() == before
    assert second.index_path.read_bytes() == index_before


def test_existing_manifest_without_index_is_recovered(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    first = rm.generate_review(options(tmp_path, repo, runner))
    first.index_path.write_bytes(b"")
    before = first.manifest_path.read_bytes()
    second = rm.generate_review(options(tmp_path, repo, runner))
    assert second.status == "review_index_recovered"
    assert second.manifest_path.read_bytes() == before
    assert len(rm.read_index(second.index_path)) == 1


def test_uncommitted_manifest_runner_sha_change_has_stable_diagnostic(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    first = rm.generate_review(options(tmp_path, repo, runner))
    first.index_path.write_bytes(b"")
    runner_payload = json.loads(runner.read_text(encoding="utf-8"))
    runner_payload["reason"] = "changed after review creation"
    runner.write_text(json.dumps(runner_payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    second = rm.generate_review(options(tmp_path, repo, runner))
    manifest = load_manifest(second)

    assert second.status == "review_created_after_invalid"
    assert manifest["review_state"] == "needs_manual_review"
    assert manifest["provenance"]["invalid_prior_manifest"]["invalid_reason"] == "runner_manifest_changed"
    assert len(rm.read_index(second.index_path)) == 1


@pytest.mark.parametrize("damage", ["missing", "broken"])
def test_indexed_manifest_missing_or_damaged_creates_diagnostic_record(tmp_path, damage):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    first = rm.generate_review(options(tmp_path, repo, runner))
    if damage == "missing":
        first.manifest_path.unlink()
    else:
        first.manifest_path.write_text("{broken", encoding="utf-8")
    second = rm.generate_review(options(tmp_path, repo, runner))
    manifest = load_manifest(second)
    assert second.status == "review_created_after_invalid"
    assert second.review_id.startswith(f"rev_{SYMBOL}_{TRADE_DATE}_{sha[:16]}_invalid_")
    assert manifest["review_state"] == "needs_manual_review"
    assert manifest["provenance"]["invalid_prior_manifest"]["diagnostic_fingerprint"]
    index_after_first_diagnostic = second.index_path.read_bytes()
    third = rm.generate_review(options(tmp_path, repo, runner))
    fourth = rm.generate_review(options(tmp_path, repo, runner))
    assert third.status == "invalid_diagnostic_already_recorded"
    assert fourth.status == "invalid_diagnostic_already_recorded"
    assert third.review_id == second.review_id == fourth.review_id
    assert second.index_path.read_bytes() == index_after_first_diagnostic
    entries = rm.read_index(second.index_path)
    assert len(entries) == 2
    assert sum("_invalid_" in entry["review_id"] for entry in entries) == 1
    assert len(list(second.index_path.parent.glob("*_invalid_*"))) == 1


def test_invalid_manifest_content_change_creates_new_fingerprint(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    first = rm.generate_review(options(tmp_path, repo, runner))
    first.manifest_path.write_text("{broken-one", encoding="utf-8")
    diagnostic_one = rm.generate_review(options(tmp_path, repo, runner))
    first.manifest_path.write_text("{broken-two", encoding="utf-8")
    diagnostic_two = rm.generate_review(options(tmp_path, repo, runner))
    assert diagnostic_one.review_id != diagnostic_two.review_id
    assert diagnostic_two.status == "review_created_after_invalid"
    entries = rm.read_index(diagnostic_two.index_path)
    assert sum("_invalid_" in entry["review_id"] for entry in entries) == 2


def test_invalid_diagnostic_allows_recovery_after_canonical_manifest_is_restored(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    first = rm.generate_review(options(tmp_path, repo, runner))
    original = first.manifest_path.read_bytes()
    first.manifest_path.write_text("{broken", encoding="utf-8")
    diagnostic = rm.generate_review(options(tmp_path, repo, runner))
    first.manifest_path.write_bytes(original)
    recovered = rm.generate_review(options(tmp_path, repo, runner))
    assert diagnostic.status == "review_created_after_invalid"
    assert recovered.status == "review_already_exists"
    assert len(rm.read_index(recovered.index_path)) == 2


def test_summary_orphan_is_overwritten_and_committed(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    review_id = rm.review_id_for(SYMBOL, TRADE_DATE, sha)
    orphan = tmp_path / "runtime" / "reviews" / TRADE_DATE / review_id
    orphan.mkdir(parents=True)
    (orphan / "review_summary.md").write_text("orphan", encoding="utf-8")
    result = rm.generate_review(options(tmp_path, repo, runner))
    assert result.status == "review_summary_orphan_recovered"
    assert (orphan / "review_manifest.json").exists()
    assert "orphan" not in (orphan / "review_summary.md").read_text(encoding="utf-8")


def test_summary_orphan_after_first_replace_recovers_without_index_pollution(tmp_path, monkeypatch):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    review_id = rm.review_id_for(SYMBOL, TRADE_DATE, sha)
    orphan = tmp_path / "runtime" / "reviews" / TRADE_DATE / review_id
    orphan.mkdir(parents=True)
    (orphan / "review_summary.md").write_text("old orphan", encoding="utf-8")
    original_replace = rm.os.replace
    failed = False

    def fail_manifest_replace_once(source, destination):
        nonlocal failed
        if Path(source).name == "review_manifest.json" and not failed:
            failed = True
            raise OSError("injected interruption between summary and manifest replace")
        return original_replace(source, destination)

    monkeypatch.setattr(rm.os, "replace", fail_manifest_replace_once)
    with pytest.raises(OSError, match="injected interruption"):
        rm.generate_review(options(tmp_path, repo, runner))

    index = orphan.parent / "review_index.jsonl"
    assert failed is True
    assert (orphan / "review_summary.md").exists()
    assert not (orphan / "review_manifest.json").exists()
    assert not index.exists()

    recovered = rm.generate_review(options(tmp_path, repo, runner))
    manifest = load_manifest(recovered)
    assert recovered.status == "review_summary_orphan_recovered"
    assert manifest["artifact_type"] == "facts_review"
    assert len(rm.read_index(recovered.index_path)) == 1


def test_official_sha_change_during_generation_cancels_commit(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    changed = payload_bytes(facts_payload(status="partial", needs={"market_indices": True}))
    result = rm.generate_review(options(tmp_path, repo, runner, before_final_recheck=lambda: official.write_bytes(changed)))
    assert result.status == "official_changed_during_generation"
    assert not (tmp_path / "runtime" / "reviews" / TRADE_DATE / rm.review_id_for(SYMBOL, TRADE_DATE, sha)).exists()
    assert not (tmp_path / "runtime" / "reviews" / TRADE_DATE / "review_index.jsonl").exists()


def test_official_symlink_replacement_inside_lock_is_rejected(tmp_path, monkeypatch):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    outside = tmp_path / "outside-official.json"
    outside.write_bytes(official.read_bytes())
    original_open = rm.os.open
    replaced = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal replaced
        if path == official.name and dir_fd is not None and not replaced:
            replaced = True
            official.unlink()
            official.symlink_to(outside)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(rm.os, "open", racing_open)
    with pytest.raises(rm.ReviewError) as error:
        rm.generate_review(options(tmp_path, repo, runner))

    assert replaced is True
    assert error.value.reason_code == "official_path_invalid"
    assert not (tmp_path / "runtime" / "reviews" / TRADE_DATE / "review_index.jsonl").exists()


def _process_worker(opts: rm.ReviewOptions, queue, marker: str | None, delay: float) -> None:
    rm._validator_result = lambda facts, official_path, trade_date: {"status": "passed"}  # type: ignore[assignment]
    callback = None
    if marker:
        def pause() -> None:
            Path(marker).write_text("locked", encoding="utf-8")
            time.sleep(delay)
        callback = pause
    opts = rm.ReviewOptions(**{**opts.__dict__, "before_final_recheck": callback})
    result = rm.generate_review(opts)
    queue.put(result.status)


def test_two_processes_can_commit_only_one_review(tmp_path):
    if "fork" not in multiprocessing.get_all_start_methods():
        pytest.skip("fork multiprocessing context required for deterministic flock test")
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    opts = options(tmp_path, repo, runner, now=None)
    marker = tmp_path / "first-holds-review-lock"
    context = multiprocessing.get_context("fork")
    queue = context.Queue()
    first = context.Process(target=_process_worker, args=(opts, queue, str(marker), 0.4))
    first.start()
    deadline = time.time() + 5
    while not marker.exists() and time.time() < deadline:
        time.sleep(0.01)
    second = context.Process(target=_process_worker, args=(opts, queue, None, 0))
    second.start()
    first.join(5)
    second.join(5)
    statuses = {queue.get(timeout=2), queue.get(timeout=2)}
    assert statuses == {"review_created", "review_generator_already_active"}
    index = tmp_path / "runtime" / "reviews" / TRADE_DATE / "review_index.jsonl"
    assert len(rm.read_index(index)) == 1
    assert len(list((index.parent).glob("rev_*"))) == 1


def test_index_partial_trailing_line_fails_closed(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    index = tmp_path / "runtime" / "reviews" / TRADE_DATE / "review_index.jsonl"
    index.parent.mkdir(parents=True)
    index.write_bytes(b'{"partial":')
    with pytest.raises(rm.IndexCorruptError) as error:
        rm.generate_review(options(tmp_path, repo, runner))
    assert error.value.reason_code == "review_index_truncated_tail"


def test_index_corrupt_middle_line_fails_closed(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    first = rm.generate_review(options(tmp_path, repo, runner))
    valid = first.index_path.read_bytes()
    first.index_path.write_bytes(valid + b"{broken}\n" + valid)
    with pytest.raises(rm.IndexCorruptError) as error:
        rm.generate_review(options(tmp_path, repo, runner))
    assert error.value.reason_code == "review_index_corrupt"


@pytest.mark.parametrize("target", ["locks", "outside_reviews", "traversal"])
def test_index_manifest_path_outside_canonical_review_directory_is_rejected(tmp_path, target):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    result = rm.generate_review(options(tmp_path, repo, runner))
    entry = json.loads(result.index_path.read_text(encoding="utf-8"))
    if target == "locks":
        path = tmp_path / "runtime" / "locks" / "not_a_review_manifest.json"
    elif target == "outside_reviews":
        path = tmp_path / "runtime" / "reviews" / "not_a_review_manifest.json"
    else:
        path = result.manifest_path.parent / ".." / "not_a_review_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(result.manifest_path.read_bytes())
    entry["manifest_path"] = str(path)
    entry["manifest_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    result.index_path.write_bytes(rm.canonical_json_line(entry))
    with pytest.raises(rm.IndexCorruptError) as error:
        rm.read_index(result.index_path)
    assert error.value.reason_code == "index_manifest_path_invalid"


def test_index_manifest_symlink_escape_is_rejected(tmp_path):
    runtime = tmp_path / "runtime"
    trade_dir = runtime / "reviews" / TRADE_DATE
    review_id = f"rev_{SYMBOL}_{TRADE_DATE}_{'a' * 16}"
    outside = tmp_path / "outside" / review_id
    outside.mkdir(parents=True)
    manifest_path = outside / "review_manifest.json"
    manifest_path.write_text("{}\n", encoding="utf-8")
    trade_dir.mkdir(parents=True)
    (trade_dir / review_id).symlink_to(outside, target_is_directory=True)
    entry = {
        "schema_version": rm.INDEX_SCHEMA_VERSION,
        "review_id": review_id,
        "symbol": SYMBOL,
        "trade_date": TRADE_DATE,
        "official_sha256": "a" * 64,
        "manifest_path": str(trade_dir / review_id / "review_manifest.json"),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "review_state": "needs_manual_review",
        "created_at": FIXED_NOW.isoformat(),
        "supersedes_review_id": None,
    }
    index = trade_dir / "review_index.jsonl"
    index.write_bytes(rm.canonical_json_line(entry))
    with pytest.raises(rm.IndexCorruptError) as error:
        rm.read_index(index)
    assert error.value.reason_code == "index_manifest_path_invalid"


@pytest.mark.parametrize("conflict_field", ["manifest_sha256", "manifest_path", "official_sha256", "review_state"])
def test_duplicate_review_id_conflicts_fail_closed(tmp_path, conflict_field):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    result = rm.generate_review(options(tmp_path, repo, runner))
    entry = json.loads(result.index_path.read_text(encoding="utf-8"))
    conflict = dict(entry)
    replacements = {
        "manifest_sha256": "b" * 64,
        "manifest_path": str(tmp_path / "runtime" / "reviews" / TRADE_DATE / entry["review_id"] / "other.json"),
        "official_sha256": "b" * 64,
        "review_state": "needs_manual_review",
    }
    conflict[conflict_field] = replacements[conflict_field]
    result.index_path.write_bytes(rm.canonical_json_line(entry) + rm.canonical_json_line(conflict))
    with pytest.raises(rm.IndexCorruptError) as error:
        rm.read_index(result.index_path)
    assert error.value.reason_code == "index_duplicate_review_conflict"


def test_identical_duplicate_index_rows_are_folded(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    result = rm.generate_review(options(tmp_path, repo, runner))
    line = result.index_path.read_bytes()
    result.index_path.write_bytes(line + line)
    entries = rm.read_index(result.index_path)
    assert len(entries) == 1
    rerun = rm.generate_review(options(tmp_path, repo, runner))
    assert rerun.status == "review_already_exists"
    assert result.index_path.read_bytes() == line + line


def test_manifest_alias_conflict_fails_closed(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    result = rm.generate_review(options(tmp_path, repo, runner))
    entry = json.loads(result.index_path.read_text(encoding="utf-8"))
    alias = dict(entry)
    alias["review_id"] = f"rev_{SYMBOL}_{TRADE_DATE}_{'b' * 16}"
    result.index_path.write_bytes(rm.canonical_json_line(entry) + rm.canonical_json_line(alias))
    with pytest.raises(rm.IndexCorruptError) as error:
        rm.read_index(result.index_path)
    assert error.value.reason_code == "index_manifest_alias_conflict"


def test_index_append_failure_leaves_uncommitted_review_for_recovery(tmp_path, monkeypatch):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    with monkeypatch.context() as patch:
        patch.setattr(rm.os, "write", lambda descriptor, payload: (_ for _ in ()).throw(OSError("append failed")))
        with pytest.raises(OSError, match="append failed"):
            rm.generate_review(options(tmp_path, repo, runner))
    review_dir = tmp_path / "runtime" / "reviews" / TRADE_DATE / rm.review_id_for(SYMBOL, TRADE_DATE, sha)
    assert (review_dir / "review_manifest.json").exists()
    assert not (review_dir.parent / "review_index.jsonl").exists() or not (review_dir.parent / "review_index.jsonl").read_bytes()
    recovered = rm.generate_review(options(tmp_path, repo, runner))
    assert recovered.status == "review_index_recovered"
    assert len(rm.read_index(recovered.index_path)) == 1


def test_index_append_uses_fsync_for_file_and_parent(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(rm.os, "fsync", lambda descriptor: calls.append(("file", descriptor)))
    monkeypatch.setattr(rm, "fsync_directory", lambda path: calls.append(("directory", Path(path))))
    entry = {
        "schema_version": rm.INDEX_SCHEMA_VERSION,
        "review_id": "rev_300274_2026-07-16_" + "a" * 16,
        "symbol": SYMBOL,
        "trade_date": TRADE_DATE,
        "official_sha256": "a" * 64,
        "manifest_path": str(tmp_path / "manifest.json"),
        "manifest_sha256": "b" * 64,
        "review_state": "needs_manual_review",
        "created_at": FIXED_NOW.isoformat(),
        "supersedes_review_id": None,
    }
    rm.append_index_entry(tmp_path / "review_index.jsonl", entry)
    assert any(kind == "file" for kind, _ in calls)
    assert ("directory", tmp_path) in calls


def test_index_fsync_failure_is_reported_after_complete_append(tmp_path, monkeypatch):
    entry = {
        "schema_version": rm.INDEX_SCHEMA_VERSION,
        "review_id": "rev_300274_2026-07-16_" + "a" * 16,
        "symbol": SYMBOL,
        "trade_date": TRADE_DATE,
        "official_sha256": "a" * 64,
        "manifest_path": str(tmp_path / "manifest.json"),
        "manifest_sha256": "b" * 64,
        "review_state": "needs_manual_review",
        "created_at": FIXED_NOW.isoformat(),
        "supersedes_review_id": None,
    }
    monkeypatch.setattr(rm.os, "fsync", lambda descriptor: (_ for _ in ()).throw(OSError("index fsync failed")))
    index = tmp_path / "review_index.jsonl"
    with pytest.raises(OSError, match="index fsync failed"):
        rm.append_index_entry(index, entry)
    assert index.read_bytes().endswith(b"\n")


def test_atomic_directory_commit_failure_has_no_index(tmp_path, monkeypatch):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    monkeypatch.setattr(rm, "_commit_new_directory", lambda source, destination: (_ for _ in ()).throw(OSError("rename failed")))
    with pytest.raises(OSError, match="rename failed"):
        rm.generate_review(options(tmp_path, repo, runner))
    trade_dir = tmp_path / "runtime" / "reviews" / TRADE_DATE
    assert not (trade_dir / rm.review_id_for(SYMBOL, TRADE_DATE, sha)).exists()
    assert not (trade_dir / "review_index.jsonl").exists()


def test_runtime_inside_repository_is_rejected(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    with pytest.raises(rm.ReviewError) as error:
        rm.generate_review(options(tmp_path, repo, runner, runtime_dir=repo / "runtime"))
    assert error.value.reason_code == "runtime_inside_repository"


@pytest.mark.parametrize("case", ["manifest_symlink", "parent_symlink", "root_escape"])
def test_runner_manifest_symlink_chain_or_runtime_escape_is_rejected(tmp_path, case):
    repo, official, sha = setup_repo(tmp_path)
    allowed = tmp_path / "allowed-runner-runtime"
    real_dir = allowed / "runs" / TRADE_DATE / "real"
    runner = write_runner(real_dir / "manifest.json", official=official, official_sha=sha)
    supplied = runner
    if case == "manifest_symlink":
        supplied = allowed / "manifest-link.json"
        supplied.symlink_to(runner)
    elif case == "parent_symlink":
        alias = allowed / "runs" / TRADE_DATE / "alias"
        alias.symlink_to(real_dir, target_is_directory=True)
        supplied = alias / "manifest.json"
    else:
        supplied = write_runner(
            tmp_path / "outside-runner-runtime" / "manifest.json",
            official=official,
            official_sha=sha,
        )

    manifest = load_manifest(
        rm.generate_review(
            options(
                tmp_path,
                repo,
                supplied,
                runner_runtime_dir=allowed,
            )
        )
    )

    assert manifest["artifact_type"] == "incident_review"
    assert manifest["incident_reason_code"] == "runner_manifest_invalid"
    assert manifest["evidence_summary"]["runner_manifest_error"]["error_type"] == "runner_manifest_path_invalid"


def test_runtime_symlink_back_into_repository_is_rejected(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    link = tmp_path / "runtime-link"
    link.symlink_to(repo, target_is_directory=True)
    with pytest.raises(rm.ReviewError) as error:
        rm.generate_review(options(tmp_path, repo, runner, runtime_dir=link))
    assert error.value.reason_code in {"runtime_inside_repository", "runtime_symlink_into_repository"}


def test_today_and_historical_modes_same_sha_do_not_duplicate(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    first_runner = write_runner(tmp_path / "today.json", official=official, official_sha=sha)
    first = rm.generate_review(options(tmp_path, repo, first_runner))
    second_runner = write_runner(tmp_path / "history.json", official=official, official_sha=sha, mode="historical_backfill")
    second = rm.generate_review(options(tmp_path, repo, second_runner))
    assert first.review_id == second.review_id
    assert second.status == "review_already_exists"
    assert len(rm.read_index(first.index_path)) == 1


def test_rebuild_from_official_has_manual_state_and_no_fabricated_transaction(tmp_path):
    repo, _official, _sha = setup_repo(tmp_path)
    result = rm.generate_review(options(tmp_path, repo, None, rebuild_from_official=True))
    manifest = load_manifest(result)
    assert manifest["run_id"] is None
    assert manifest["mode"] == "rebuild_from_official"
    assert manifest["provenance"]["rebuilt_from_official"] is True
    assert manifest["review_state"] == "needs_manual_review"
    assert manifest["write_action"] is None


def test_sensitive_transaction_diagnostics_are_redacted(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(
        tmp_path / "runner.json",
        official=official,
        official_sha=sha,
        write_action="created_postcheck_failed",
        outcome="needs_manual_review",
        reason_code="official_written_postcheck_failed",
        official_post_write_error={"message": "Authorization=secret-token token=abc123456789", "stage": "post_write_read"},
    )
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    serialized = json.dumps(manifest, ensure_ascii=False)
    assert "secret-token" not in serialized
    assert "abc123456789" not in serialized
    assert "[REDACTED]" in serialized


@pytest.mark.parametrize(
    ("label", "secret"),
    [
        ("Authorization: Bearer", "bearer-secret-value"),
        ("Authorization: Basic", "basic-secret-value"),
        ("Cookie:", "cookie-secret-value"),
        ("Set-Cookie:", "set-cookie-secret-value"),
        ("X-API-Key:", "x-api-secret-value"),
        ("Proxy-Authorization: Bearer", "proxy-secret-value"),
        ("token=", "token-secret-value"),
        ("access_token=", "access-token-secret-value"),
        ("api_key=", "api-key-secret-value"),
        ("apikey=", "apikey-secret-value"),
        ("key=", "key-secret-value"),
        ("password=", "password-secret-value"),
        ("secret=", "secret-secret-value"),
        ("signature=", "signature-secret-value"),
        ("OPENAI_API_KEY=", "openai-secret-value"),
        ("GITHUB_TOKEN=", "github-secret-value"),
        ("AWS_SECRET_ACCESS_KEY=", "aws-secret-value"),
        ("AWS_ACCESS_KEY_ID=", "aws-id-secret-value"),
        ("CUSTOM_TOKEN=", "custom-token-secret-value"),
        ("CUSTOM_SECRET=", "custom-secret-value"),
        ("CUSTOM_PASSWORD=", "custom-password-value"),
        ("CUSTOM_API_KEY=", "custom-api-key-value"),
    ],
)
def test_sanitize_text_secret_matrix(label, secret):
    sanitized = rm.sanitize_text(f"prefix {label}{secret} suffix")
    assert secret not in sanitized
    assert label.split(":", 1)[0].split("=", 1)[0] in sanitized
    assert "[REDACTED]" in sanitized


def test_plain_key_token_password_words_are_preserved():
    text = "the key idea uses a token budget and a password policy without assigning values"
    assert rm.sanitize_text(text) == text


def test_nested_sensitive_key_values_are_redacted():
    sanitized = rm._sanitized_copy(
        {
            "outer": {
                "OPENAI_API_KEY": "raw-openai-secret",
                "metadata": {"password": "raw-password-secret"},
            }
        }
    )
    serialized = json.dumps(sanitized)
    assert "raw-openai-secret" not in serialized
    assert "raw-password-secret" not in serialized
    assert sanitized["outer"]["OPENAI_API_KEY"] == "[REDACTED]"


def test_runner_validator_source_ref_and_exception_strings_are_redacted(tmp_path, monkeypatch):
    facts = facts_payload()
    facts["quote_verification"]["source"] = "Authorization: Bearer source-secret"
    repo, official, sha = setup_repo(tmp_path, official_bytes=payload_bytes(facts))
    runner = write_runner(
        tmp_path / "runner.json",
        official=official,
        official_sha=sha,
        write_action="Cookie: write-action-secret",
        reason_code="OPENAI_API_KEY=reason-secret",
        official_post_write_error={"message": "AWS_SECRET_ACCESS_KEY=exception-secret"},
    )
    monkeypatch.setattr(
        rm,
        "_validator_result",
        lambda facts, official_path, trade_date: {
            "status": "failed",
            "message": "X-API-Key: validator-secret",
        },
    )
    result = rm.generate_review(options(tmp_path, repo, runner))
    manifest_text = result.manifest_path.read_text(encoding="utf-8")
    summary_text = result.manifest_path.with_name("review_summary.md").read_text(encoding="utf-8")
    for secret in ("source-secret", "write-action-secret", "reason-secret", "exception-secret", "validator-secret"):
        assert secret not in manifest_text
        assert secret not in summary_text
    assert "[REDACTED]" in manifest_text


def test_source_ref_text_is_redacted_in_facts_review(tmp_path):
    facts = facts_payload()
    facts["quote_verification"]["source"] = "Authorization: Bearer source-ref-secret"
    repo, official, sha = setup_repo(tmp_path, official_bytes=payload_bytes(facts))
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    manifest = load_manifest(rm.generate_review(options(tmp_path, repo, runner)))
    serialized = json.dumps(manifest["source_refs"], ensure_ascii=False)
    assert "source-ref-secret" not in serialized
    assert "[REDACTED]" in serialized


def test_review_generation_does_not_create_decisions_file(tmp_path):
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    result = rm.generate_review(options(tmp_path, repo, runner))
    assert not list((tmp_path / "runtime").rglob("decisions.jsonl"))
    assert result.manifest_path.exists()


def _fingerprints(paths: list[Path]) -> dict[str, str]:
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def test_protected_files_and_git_path_set_do_not_change(tmp_path):
    protected = [
        rm.REPO_ROOT / "sungrow" / "reviews" / "sungrow_review_2026-07-13.md",
        rm.REPO_ROOT / "sungrow" / "reviews" / "sungrow_review_2026-07-14.md",
        rm.REPO_ROOT / "sungrow_test" / "sungrow_position_card_v0.1.1.md",
        rm.REPO_ROOT / "sungrow_test" / "sungrow_low_zone_observation_v0.1.md",
        rm.REPO_ROOT / "sungrow_test" / "sungrow_risk_and_tracking_v0.1.md",
        rm.REPO_ROOT / "sungrow_test" / "sungrow_add_position_analysis_v0.1.md",
        rm.REPO_ROOT / "sungrow_test" / "sungrow_valuation_v0.1.md",
        rm.REPO_ROOT / "stock_workbench_index.md",
        *sorted((rm.REPO_ROOT / "weekly").glob("*")),
    ]
    before_sha = _fingerprints([path for path in protected if path.is_file()])
    before_paths = subprocess.check_output(["git", "status", "--short", "--untracked-files=all"], cwd=rm.REPO_ROOT, text=True)
    repo, official, sha = setup_repo(tmp_path)
    runner = write_runner(tmp_path / "runner.json", official=official, official_sha=sha)
    rm.generate_review(options(tmp_path, repo, runner))
    after_sha = _fingerprints([path for path in protected if path.is_file()])
    after_paths = subprocess.check_output(["git", "status", "--short", "--untracked-files=all"], cwd=rm.REPO_ROOT, text=True)
    assert before_sha == after_sha
    assert before_paths == after_paths
