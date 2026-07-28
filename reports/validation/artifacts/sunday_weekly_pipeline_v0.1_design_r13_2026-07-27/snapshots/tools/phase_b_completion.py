"""Phase B completed-run semantics and live evidence validation."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

try:
    from tools import official_facts_transaction as oft
    from tools import safe_file_read as sfr
    from tools import validate_review_chain as vrc
except ModuleNotFoundError:  # pragma: no cover - direct execution fallback
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools import official_facts_transaction as oft
    from tools import safe_file_read as sfr
    from tools import validate_review_chain as vrc


RUNNER_SCHEMA_VERSION = "runner_manifest_v0.2_phase_b"
SHA_RE = re.compile(r"[0-9a-f]{64}")
COMPLETION_ACTIONS = frozenset({"created", "identical_noop", "semantic_noop"})


@dataclass(frozen=True)
class PhaseBWriteSemantic:
    outcomes: frozenset[str]
    official_changed: bool
    after_sha_required: bool


# Shared by Phase B completion validation and the Phase C runner-evidence gate.
PHASE_B_WRITE_SEMANTICS = {
    ("created", "official_written"): PhaseBWriteSemantic(frozenset({"success"}), True, True),
    ("created", "official_written_partial"): PhaseBWriteSemantic(frozenset({"partial"}), True, True),
    ("created", "official_written_manifest_failed"): PhaseBWriteSemantic(
        frozenset({"success", "partial"}), True, True
    ),
    ("identical_noop", "official_already_identical"): PhaseBWriteSemantic(
        frozenset({"success", "partial"}), False, True
    ),
    ("identical_noop", "official_written_manifest_failed"): PhaseBWriteSemantic(
        frozenset({"success", "partial"}), False, True
    ),
    ("semantic_noop", "official_semantically_identical"): PhaseBWriteSemantic(
        frozenset({"official_unchanged"}), False, True
    ),
    ("conflict_blocked", "official_conflict"): PhaseBWriteSemantic(
        frozenset({"needs_manual_review"}), False, False
    ),
    ("conflict_blocked", "official_invalid"): PhaseBWriteSemantic(
        frozenset({"needs_manual_review"}), False, False
    ),
    ("sealed_blocked", "sealed_exists"): PhaseBWriteSemantic(frozenset({"skipped"}), False, True),
    ("manual_blocked", "manual_exists"): PhaseBWriteSemantic(frozenset({"skipped"}), False, True),
    ("not_eligible", "partial_not_eligible_for_official"): PhaseBWriteSemantic(
        frozenset({"needs_manual_review"}), False, False
    ),
    ("not_eligible", "validator_failed"): PhaseBWriteSemantic(
        frozenset({"needs_manual_review"}), False, False
    ),
    ("not_eligible", "candidate_not_eligible_for_official"): PhaseBWriteSemantic(
        frozenset({"needs_manual_review"}), False, False
    ),
    ("created_postcheck_failed", "official_written_postcheck_failed"): PhaseBWriteSemantic(
        frozenset({"needs_manual_review"}), True, False
    ),
    ("created_postcheck_failed", "official_written_bytes_mismatch"): PhaseBWriteSemantic(
        frozenset({"needs_manual_review"}), True, False
    ),
}


class CompletionValidationError(ValueError):
    """A matching prior manifest is not a live, complete Phase B success."""

    def __init__(self, reason_code: str, message: str):
        super().__init__(message)
        self.reason_code = reason_code


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_json_object(raw: bytes, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CompletionValidationError(f"{label}_json_invalid", f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise CompletionValidationError(f"{label}_json_invalid", f"{label} must be a JSON object")
    return value


def _aware_datetime(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _require_sha(manifest: dict[str, Any], key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        raise CompletionValidationError("completion_sha_invalid", f"{key} must be a lowercase SHA-256")
    return value


def _require_validator_passed(manifest: dict[str, Any], key: str) -> None:
    value = manifest.get(key)
    if not isinstance(value, dict) or value.get("status") != "passed":
        raise CompletionValidationError("completion_validator_invalid", f"{key} must record status=passed")


def _validate_facts(
    payload: dict[str, Any],
    *,
    path: Path,
    target_date: str,
    validator: Callable[..., None] | None,
) -> None:
    try:
        check = validator or vrc.assert_facts_pack_valid
        check(payload, facts_pack_path=str(path), date=target_date)
    except Exception as exc:  # noqa: BLE001 - invalid evidence never counts as completion
        raise CompletionValidationError(
            "completion_facts_validator_failed",
            f"facts Validator rejected {path.name}: {type(exc).__name__}",
        ) from exc


def validate_completion_manifest(
    manifest: dict[str, Any],
    *,
    manifest_path: Path,
    runtime_dir: Path,
    repo_root: Path,
    symbol: str,
    target_date: str,
    mode: str,
    official_path: Path,
    official_bytes: bytes | None,
    official_sha256: str | None,
    validator: Callable[..., None] | None = None,
) -> str:
    """Return the completed action only when every committed/live proof passes."""

    if manifest.get("schema_version") != RUNNER_SCHEMA_VERSION:
        raise CompletionValidationError("completion_schema_invalid", "runner schema is not Phase B v0.2")
    if manifest.get("stage") != "finished" or not _aware_datetime(manifest.get("finished_at")):
        raise CompletionValidationError("completion_stage_invalid", "runner manifest is not a finished terminal record")
    if manifest.get("outcome") == "failed":
        raise CompletionValidationError("completion_outcome_failed", "failed runner outcome cannot complete a task")
    if manifest.get("manifest_bundle_failed") is True:
        raise CompletionValidationError("completion_bundle_failed", "failed runtime bundle cannot complete a task")
    if manifest.get("write_official") is not True or manifest.get("dry_run") is not False:
        raise CompletionValidationError("completion_run_mode_invalid", "completion requires write_official=true and dry_run=false")
    if (
        manifest.get("symbol") != symbol
        or manifest.get("target_date") != target_date
        or manifest.get("mode") != mode
    ):
        raise CompletionValidationError("completion_identity_mismatch", "runner task identity does not match the scan")

    run_id = manifest.get("run_id")
    try:
        uuid.UUID(str(run_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise CompletionValidationError("completion_run_id_invalid", "run_id must be a UUID") from exc
    expected_manifest = runtime_dir / "runs" / target_date / str(run_id) / "manifest.json"
    if manifest_path.absolute() != expected_manifest.absolute() or manifest_path.parent.name != run_id:
        raise CompletionValidationError("completion_run_id_mismatch", "run_id does not identify the manifest directory")
    manifest_identity = manifest.get("manifest_path")
    if not isinstance(manifest_identity, str) or Path(manifest_identity).absolute() != manifest_path.absolute():
        raise CompletionValidationError("completion_manifest_path_invalid", "manifest_path does not identify this manifest")

    expected_official = oft.canonical_official_path(repo_root, symbol, target_date)
    recorded_official = manifest.get("official_path")
    if (
        expected_official.resolve(strict=False) != official_path.resolve(strict=False)
        or not isinstance(recorded_official, str)
        or Path(recorded_official).resolve(strict=False) != expected_official.resolve(strict=False)
    ):
        raise CompletionValidationError("completion_official_path_invalid", "official_path is not canonical")
    if official_bytes is None or official_sha256 is None:
        raise CompletionValidationError("completion_official_missing", "current official facts are missing")
    if sha256_bytes(official_bytes) != official_sha256:
        raise CompletionValidationError("completion_official_read_invalid", "official SHA is not derived from its read bytes")

    action = manifest.get("write_action")
    reason_code = manifest.get("reason_code")
    if action not in COMPLETION_ACTIONS:
        raise CompletionValidationError("completion_action_invalid", "write_action is not a completed Phase B action")
    semantic = PHASE_B_WRITE_SEMANTICS.get((action, reason_code))
    if semantic is None or reason_code == "official_written_manifest_failed":
        raise CompletionValidationError("completion_action_reason_invalid", "action and reason are not a successful completion pair")
    if manifest.get("outcome") not in semantic.outcomes:
        raise CompletionValidationError("completion_action_outcome_invalid", "outcome conflicts with action and reason")
    if type(manifest.get("official_changed")) is not bool or manifest.get("official_changed") is not semantic.official_changed:
        raise CompletionValidationError("completion_official_changed_invalid", "official_changed conflicts with action and reason")

    before_sha = manifest.get("official_sha256_before")
    after_sha = _require_sha(manifest, "official_sha256_after")
    candidate_sha = _require_sha(manifest, "candidate_sha256")
    if official_sha256 != after_sha:
        raise CompletionValidationError("completion_official_drift", "current official SHA differs from recorded after SHA")
    if before_sha is not None and (not isinstance(before_sha, str) or SHA_RE.fullmatch(before_sha) is None):
        raise CompletionValidationError("completion_sha_invalid", "official_sha256_before is invalid")

    candidate_identity = manifest.get("candidate_path")
    expected_candidate = manifest_path.parent / "candidate.json"
    if not isinstance(candidate_identity, str) or Path(candidate_identity).absolute() != expected_candidate.absolute():
        raise CompletionValidationError("completion_candidate_path_invalid", "candidate_path is not the committed run candidate")
    try:
        candidate_bytes, candidate_path = sfr.read_regular_file_beneath(
            expected_candidate,
            root=runtime_dir,
            label="completion candidate",
        )
    except sfr.SafeFileReadError as exc:
        raise CompletionValidationError("completion_candidate_unreadable", str(exc)) from exc
    assert candidate_bytes is not None
    if sha256_bytes(candidate_bytes) != candidate_sha:
        raise CompletionValidationError("completion_candidate_drift", "candidate bytes differ from candidate_sha256")
    candidate = parse_json_object(candidate_bytes, label="completion_candidate")
    official = parse_json_object(official_bytes, label="completion_official")
    _validate_facts(candidate, path=candidate_path, target_date=target_date, validator=validator)
    _validate_facts(official, path=official_path, target_date=target_date, validator=validator)
    _require_validator_passed(manifest, "validator")
    _require_validator_passed(manifest, "official_validator_before")
    _require_validator_passed(manifest, "official_validator_after")

    candidate_status = (candidate.get("run") or {}).get("status") if isinstance(candidate.get("run"), dict) else None
    if action == "created":
        expected_pair = (
            ("partial", "official_written_partial", "partial")
            if candidate_status == "partial"
            else ("success", "official_written", "success")
        )
        if (candidate_status, reason_code, manifest.get("outcome")) != expected_pair:
            raise CompletionValidationError("completion_created_status_invalid", "created status, reason, and outcome disagree")
        if (
            before_sha is not None
            or manifest.get("official_exists_before") is not False
            or manifest.get("official_bytes_equal_candidate") is not True
            or after_sha != candidate_sha
            or manifest.get("comparison") is not None
        ):
            raise CompletionValidationError("completion_created_evidence_invalid", "created SHA or byte evidence is inconsistent")
    elif action == "identical_noop":
        if candidate_status not in {"success", "partial"} or manifest.get("outcome") != candidate_status:
            raise CompletionValidationError("completion_identical_status_invalid", "identical_noop outcome must match candidate status")
        if (
            manifest.get("official_exists_before") is not True
            or manifest.get("official_bytes_equal_candidate") is not True
            or before_sha != after_sha
            or after_sha != candidate_sha
            or manifest.get("comparison") is not None
        ):
            raise CompletionValidationError("completion_identical_evidence_invalid", "identical_noop SHA or byte evidence is inconsistent")
    else:
        comparison = manifest.get("comparison")
        required_comparison = {
            "comparison_mode",
            "candidate_raw_sha256",
            "official_raw_sha256",
            "candidate_semantic_sha256",
            "official_semantic_sha256",
            "excluded_json_paths",
            "excluded_values",
            "semantic_equal",
            "official_changed",
        }
        if (
            manifest.get("official_exists_before") is not True
            or manifest.get("official_bytes_equal_candidate") is not False
            or before_sha != after_sha
            or candidate_sha == after_sha
            or not isinstance(comparison, dict)
            or set(comparison) != required_comparison
            or comparison.get("comparison_mode") != oft.SEMANTIC_COMPARISON_MODE
            or comparison.get("excluded_json_paths") != list(oft.SEMANTIC_NOOP_EXCLUDED_JSON_PATHS)
            or comparison.get("candidate_raw_sha256") != candidate_sha
            or comparison.get("official_raw_sha256") != after_sha
            or comparison.get("semantic_equal") is not True
            or comparison.get("official_changed") is not False
            or comparison.get("candidate_semantic_sha256") != comparison.get("official_semantic_sha256")
            or not isinstance(comparison.get("candidate_semantic_sha256"), str)
            or SHA_RE.fullmatch(comparison.get("candidate_semantic_sha256")) is None
        ):
            raise CompletionValidationError("completion_semantic_evidence_invalid", "semantic_noop evidence is incomplete or inconsistent")
        recomputed = oft.build_semantic_comparison(
            candidate=candidate,
            official=official,
            candidate_bytes=candidate_bytes,
            official_bytes=official_bytes,
            symbol=symbol,
            target_date=target_date,
        )
        if recomputed.get("semantic_equal") is not True or comparison != recomputed:
            raise CompletionValidationError("completion_semantic_recompute_mismatch", "live semantic comparison differs from manifest evidence")
    return str(action)
