"""Deterministic Phase C review manifests derived from official facts.

The review layer is a read model.  It never changes repository-owned review,
card, index, weekly, facts, or Git files.  Runtime artifacts are committed by
an append-only index record after an official-SHA recheck under the shared
official facts lock.
"""

from __future__ import annotations

import contextlib
import copy
import fcntl
import hashlib
import json
import os
import re
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterator
from zoneinfo import ZoneInfo

try:
    from tools import official_facts_lock as ofl
    from tools import official_facts_transaction as oft
    from tools import phase_b_completion as pbc
    from tools import safe_file_read as sfr
    from tools import validate_review_chain as vrc
except ModuleNotFoundError:  # pragma: no cover - direct execution fallback
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools import official_facts_lock as ofl
    from tools import official_facts_transaction as oft
    from tools import phase_b_completion as pbc
    from tools import safe_file_read as sfr
    from tools import validate_review_chain as vrc


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_DIR = Path("~/Library/Application Support/Mimo-Lab/stocks-runtime").expanduser()
SCHEMA_VERSION = "review_manifest_v0.2_phase_c"
INDEX_SCHEMA_VERSION = "review_index_v0.2_phase_c"
GENERATOR_VERSION = "phase_c_v0.2"
BUSINESS_TIMEZONE = "Asia/Shanghai"
RUNNER_SCHEMA_VERSION = "runner_manifest_v0.2_phase_b"
ALLOWED_MODES = {"today_after_close", "historical_backfill", "rebuild_from_official"}
ALLOWED_REVIEW_STATES = {"ready_for_human_review", "needs_manual_review"}
DOWNSTREAM_PERMISSIONS = {
    "review": False,
    "current_cards": False,
    "index": False,
    "weekly": False,
    "git": False,
    "trading": False,
}
FORBIDDEN_MANIFEST_KEYS = {"human_decision", "human_notes", "approved", "rejected"}
FORBIDDEN_MANIFEST_VALUES = {"approved", "rejected"}
SHA_RE = re.compile(r"[0-9a-f]{64}")
SYMBOL_RE = re.compile(r"\d{6}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
SENSITIVE_PATTERNS = (
    re.compile(r"(?i)(\bauthorization\s*[:=]\s*)(?:(?:bearer|basic)\s+)?[^\s,;]+"),
    re.compile(r"(?i)(\bproxy-authorization\s*[:=]\s*)(?:(?:bearer|basic)\s+)?[^\s,;]+"),
    re.compile(r"(?i)(\b(?:set-cookie|cookie)\s*[:=]\s*)[^\r\n,;]+"),
    re.compile(r"(?i)(\bx-api-key\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(\bheader\s*[:=]\s*(?:bearer|basic)[-\s]*)([^\s,;]+)"),
    re.compile(r"(?i)([?&](?:token|access_token|api[_-]?key|apikey|key|password|secret|signature)=)[^&\s#]+"),
    re.compile(
        r"(?i)\b((?:OPENAI_API_KEY|GITHUB_TOKEN|AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|"
        r"[A-Z][A-Z0-9_]*(?:_TOKEN|_SECRET|_PASSWORD|_API_KEY))\s*[:=]\s*)[^\s,;]+"
    ),
    re.compile(
        r"(?i)\b((?:token|access_token|api[_-]?key|apikey|key|password|secret|signature)\s*[:=]\s*)[^\s,;]+"
    ),
    re.compile(r"(sk-)[A-Za-z0-9_-]{12,}"),
)
SENSITIVE_KEY_RE = re.compile(
    r"(?i)^(?:authorization|proxy-authorization|cookie|set-cookie|x-api-key|token|access_token|"
    r"api[_-]?key|apikey|key|password|secret|signature|OPENAI_API_KEY|GITHUB_TOKEN|"
    r"AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|[A-Z][A-Z0-9_]*(?:_TOKEN|_SECRET|_PASSWORD|_API_KEY))$"
)
INCIDENT_WRITE_ACTIONS = {
    "conflict_blocked",
    "created_postcheck_failed",
    "sealed_blocked",
    "manual_blocked",
}
INCIDENT_REASON_CODES = {
    "official_conflict",
    "official_written_manifest_failed",
    "official_written_postcheck_failed",
    "official_written_bytes_mismatch",
    "official_snapshot_failed",
}
REQUIRED_MANIFEST_FIELDS = {
    "schema_version",
    "artifact_type",
    "review_id",
    "run_id",
    "symbol",
    "trade_date",
    "mode",
    "official_path",
    "official_sha256",
    "candidate_sha256",
    "runner_manifest_path",
    "runner_manifest_sha256",
    "official_sha256_before",
    "official_changed",
    "official_sha_match",
    "write_action",
    "write_reason_code",
    "postcheck_status",
    "incident_reason_code",
    "facts_status",
    "validator_result",
    "missing",
    "needs_manual_check",
    "confirmed_fields",
    "unresolved_fields",
    "partial_write_policy",
    "evidence_summary",
    "source_refs",
    "generated_at",
    "generator_version",
    "review_state",
    "downstream_permissions",
    "provenance",
}


class ReviewError(Exception):
    """Expected fail-closed Phase C error with a stable reason code."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class IndexCorruptError(ReviewError):
    """The append-only index cannot be safely extended."""


@dataclass(frozen=True)
class RunnerEvidence:
    path: Path | None
    sha256: str | None
    manifest: dict[str, Any] | None
    error_type: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class ReviewOptions:
    runtime_dir: Path
    symbol: str
    trade_date: str
    runner_manifest_path: Path | None = None
    runner_runtime_dir: Path | None = None
    rebuild_from_official: bool = False
    repo_root: Path = REPO_ROOT
    official_lock_dir: Path | None = None
    now: Callable[[], datetime] | None = None
    before_final_recheck: Callable[[], None] | None = None


@dataclass(frozen=True)
class ReviewResult:
    status: str
    review_id: str | None
    manifest_path: Path | None
    index_path: Path | None
    review_state: str | None
    reason_code: str | None = None


PHASE_B_WRITE_SEMANTICS = pbc.PHASE_B_WRITE_SEMANTICS


def sanitize_text(value: object, *, limit: int = 1000) -> str:
    text = str(value)
    for pattern in SENSITIVE_PATTERNS:
        text = pattern.sub(lambda match: match.group(1) + "[REDACTED]", text)
    return text[:limit]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def canonical_json_line(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is not allowed: {value}")


def parse_json_object(data: bytes, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"), parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ReviewError(f"{label}_invalid", f"{label} JSON is invalid: {sanitize_text(exc)}") from exc
    if not isinstance(value, dict):
        raise ReviewError(f"{label}_invalid", f"{label} root must be an object")
    return value


def _inside(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def normalize_runtime_dir(value: str | os.PathLike[str], *, repo_root: Path = REPO_ROOT) -> Path:
    raw = Path(value).expanduser()
    resolved = raw.resolve(strict=False)
    repo = repo_root.expanduser().resolve(strict=False)
    if _inside(resolved, repo):
        raise ReviewError("runtime_inside_repository", "runtime directory must resolve outside the repository")
    current = raw if raw.is_absolute() else (Path.cwd() / raw)
    for candidate in (current, *current.parents):
        if candidate.exists() and candidate.is_symlink():
            target = candidate.resolve(strict=False)
            if _inside(target, repo):
                raise ReviewError("runtime_symlink_into_repository", "runtime symlink resolves into the repository")
    return resolved


def prepare_runtime_dir(runtime_dir: Path, *, repo_root: Path) -> None:
    runtime_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    checked = normalize_runtime_dir(runtime_dir, repo_root=repo_root)
    if checked != runtime_dir:
        raise ReviewError("runtime_path_changed", "runtime path changed after creation")
    probe = runtime_dir / ".phase_c_write_probe"
    try:
        atomic_write_bytes(probe, b"ok\n")
        probe.unlink()
    except OSError as exc:
        raise ReviewError("runtime_unwritable", f"runtime directory is not writable: {sanitize_text(exc)}") from exc


def validate_identity(symbol: str, trade_date: str) -> None:
    if not SYMBOL_RE.fullmatch(symbol):
        raise ReviewError("symbol_invalid", "symbol must be a six-digit A-share code")
    if not DATE_RE.fullmatch(trade_date):
        raise ReviewError("trade_date_invalid", "trade_date must use canonical YYYY-MM-DD")
    try:
        if datetime.fromisoformat(trade_date).date().isoformat() != trade_date:
            raise ValueError
    except ValueError as exc:
        raise ReviewError("trade_date_invalid", "trade_date must be a real canonical date") from exc


def canonical_official_path(repo_root: Path, symbol: str, trade_date: str) -> Path:
    try:
        return oft.canonical_official_path(repo_root, symbol, trade_date)
    except ValueError as exc:
        raise ReviewError("official_path_invalid", sanitize_text(exc)) from exc


def review_id_for(symbol: str, trade_date: str, official_sha256: str, *, suffix: str | None = None) -> str:
    if not SHA_RE.fullmatch(official_sha256):
        raise ReviewError("official_sha_invalid", "official SHA must be 64 lowercase hexadecimal characters")
    value = f"rev_{symbol}_{trade_date}_{official_sha256[:16]}"
    if suffix:
        if not re.fullmatch(r"[a-z0-9_]+", suffix):
            raise ReviewError("review_id_suffix_invalid", "review ID suffix is invalid")
        value += f"_{suffix}"
    return value


def review_lock_path(runtime_dir: Path, symbol: str, trade_date: str) -> Path:
    digest = hashlib.sha256(f"{symbol}_{trade_date}".encode("utf-8")).hexdigest()
    return runtime_dir / "locks" / f"review_{digest}.lock"


@contextlib.contextmanager
def review_lock(path: Path) -> Iterator[bool]:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("a+b") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            offset = 0
            while offset < len(payload):
                written = handle.write(payload[offset:])
                if written is None or written <= 0:
                    raise OSError("short write while creating review artifact")
                offset += written
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _absolute_lexical_path(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _read_regular_file_beneath(
    path: Path,
    *,
    root: Path,
    reason_code: str,
    label: str,
    missing_ok: bool = False,
) -> tuple[bytes | None, Path]:
    """Read one regular file through the shared no-follow fd helper."""

    try:
        return sfr.read_regular_file_beneath(path, root=root, label=label, missing_ok=missing_ok)
    except sfr.SafeFileReadError as exc:
        raise ReviewError(reason_code, sanitize_text(exc)) from exc


def _read_locked_official(
    official_path: Path,
    *,
    repo_root: Path,
    lock_state: ofl.OfficialFactsLockState,
) -> tuple[bytes | None, str | None]:
    """Read official facts from one no-follow fd while the matching lock is held."""

    try:
        lock_state.assert_held_for(official_path)
    except RuntimeError as exc:
        raise ReviewError("official_path_invalid", sanitize_text(exc)) from exc
    data, _path = _read_regular_file_beneath(
        official_path,
        root=repo_root,
        reason_code="official_path_invalid",
        label="official facts path",
        missing_ok=True,
    )
    if data is None:
        return None, None
    return data, sha256_bytes(data)


def load_runner_evidence(
    path: Path | None,
    *,
    allowed_runtime_root: Path,
    symbol: str,
    trade_date: str,
    official_path: Path,
    official_bytes: bytes,
    official_sha256: str,
    required: bool,
    expected_sha256: str | None = None,
) -> RunnerEvidence:
    if path is None:
        if required:
            raise ReviewError("runner_manifest_required", "a Phase B runner manifest is required")
        return RunnerEvidence(path=None, sha256=None, manifest=None)
    try:
        raw, resolved = _read_regular_file_beneath(
            path,
            root=allowed_runtime_root,
            reason_code="runner_manifest_path_invalid",
            label="runner manifest path",
        )
        assert raw is not None
    except ReviewError as exc:
        return RunnerEvidence(
            path=_absolute_lexical_path(path),
            sha256=None,
            manifest=None,
            error_type=exc.reason_code,
            error_message=sanitize_text(exc),
        )
    observed_sha256 = sha256_bytes(raw)
    if expected_sha256 is not None and observed_sha256 != expected_sha256:
        return RunnerEvidence(
            path=resolved,
            sha256=observed_sha256,
            manifest=None,
            error_type="runner_manifest_changed",
            error_message="runner manifest SHA changed after the review manifest was created",
        )
    try:
        manifest = parse_json_object(raw, label="runner_manifest")
        validate_runner_manifest(
            manifest,
            symbol=symbol,
            trade_date=trade_date,
            official_path=official_path,
            runner_manifest_path=resolved,
        )
        if manifest.get("write_action") == "semantic_noop":
            validate_semantic_noop_evidence(
                manifest,
                runner_manifest_path=resolved,
                official_bytes=official_bytes,
                official_sha256=official_sha256,
                symbol=symbol,
                trade_date=trade_date,
                allowed_runtime_root=allowed_runtime_root,
            )
    except ReviewError as exc:
        return RunnerEvidence(
            path=resolved,
            sha256=observed_sha256,
            manifest=None,
            error_type=exc.reason_code,
            error_message=sanitize_text(exc),
        )
    return RunnerEvidence(path=resolved, sha256=observed_sha256, manifest=manifest)


def validate_runner_manifest(
    manifest: dict[str, Any],
    *,
    symbol: str,
    trade_date: str,
    official_path: Path,
    runner_manifest_path: Path,
) -> None:
    if manifest.get("schema_version") != RUNNER_SCHEMA_VERSION:
        raise ReviewError("runner_manifest_schema_invalid", "runner manifest schema_version is not Phase B v0.2")
    if str(manifest.get("symbol")) != symbol or str(manifest.get("target_date")) != trade_date:
        raise ReviewError("runner_manifest_identity_mismatch", "runner manifest identity does not match symbol and trade_date")
    if manifest.get("mode") not in {"today_after_close", "historical_backfill"}:
        raise ReviewError("runner_manifest_mode_invalid", "runner manifest mode is invalid")
    if manifest.get("write_official") is not True or manifest.get("dry_run") is not False:
        raise ReviewError("runner_manifest_not_official", "runner manifest is not an explicit official-write run")
    if manifest.get("stage") != "finished" or not isinstance(manifest.get("finished_at"), str):
        raise ReviewError("runner_manifest_not_committed", "runner manifest must be a finished Phase B commit marker")
    recorded_manifest_path = manifest.get("manifest_path")
    if (
        not isinstance(recorded_manifest_path, str)
        or Path(recorded_manifest_path).expanduser().resolve(strict=False) != runner_manifest_path
    ):
        raise ReviewError("runner_manifest_path_mismatch", "runner manifest path does not match its committed path")
    value = manifest.get("official_path")
    if not isinstance(value, str) or Path(value).expanduser().resolve(strict=False) != official_path.resolve(strict=False):
        raise ReviewError("runner_manifest_official_path_mismatch", "runner manifest official_path is not canonical")
    run_id = manifest.get("run_id")
    try:
        uuid.UUID(str(run_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ReviewError("runner_manifest_run_id_invalid", "runner manifest run_id must be a UUID") from exc
    write_action = manifest.get("write_action")
    if not isinstance(write_action, str) or not write_action.strip():
        raise ReviewError(
            "runner_manifest_write_action_invalid",
            "runner manifest write_action must be a known non-empty Phase B action",
        )
    allowed_actions = {action for action, _reason in PHASE_B_WRITE_SEMANTICS}
    if write_action not in allowed_actions:
        raise ReviewError(
            "runner_manifest_write_action_invalid",
            "runner manifest write_action is not a known Phase B action",
        )
    reason_code = manifest.get("reason_code")
    if not isinstance(reason_code, str) or not reason_code.strip():
        raise ReviewError(
            "runner_manifest_reason_code_invalid",
            "runner manifest reason_code must be a known non-empty Phase B reason",
        )
    allowed_reasons = {reason for _action, reason in PHASE_B_WRITE_SEMANTICS}
    if reason_code not in allowed_reasons:
        raise ReviewError(
            "runner_manifest_reason_code_invalid",
            "runner manifest reason_code is not a known Phase B reason",
        )
    semantic = PHASE_B_WRITE_SEMANTICS.get((write_action, reason_code))
    if semantic is None:
        raise ReviewError(
            "runner_manifest_action_reason_mismatch",
            "runner manifest write_action and reason_code are not a valid Phase B combination",
        )
    outcome = manifest.get("outcome")
    if not isinstance(outcome, str) or not outcome.strip():
        raise ReviewError(
            "runner_manifest_outcome_invalid",
            "runner manifest outcome must be a non-empty Phase B outcome",
        )
    if outcome not in semantic.outcomes:
        raise ReviewError(
            "runner_manifest_outcome_mismatch",
            "runner manifest outcome conflicts with its Phase B action and reason",
        )
    official_changed = manifest.get("official_changed")
    if type(official_changed) is not bool or official_changed is not semantic.official_changed:
        raise ReviewError(
            "runner_manifest_official_changed_mismatch",
            "runner manifest official_changed conflicts with its Phase B action and reason",
        )
    for key in ("official_sha256_before", "official_sha256_after", "candidate_sha256"):
        value = manifest.get(key)
        if value is not None and not (isinstance(value, str) and SHA_RE.fullmatch(value)):
            raise ReviewError("runner_manifest_sha_invalid", f"runner manifest {key} is invalid")
    before_sha = manifest.get("official_sha256_before")
    after_sha = manifest.get("official_sha256_after")
    if semantic.after_sha_required and after_sha is None:
        raise ReviewError(
            "runner_manifest_after_sha_mismatch",
            "runner manifest action and reason require official_sha256_after",
        )
    if not official_changed and (
        (before_sha is None) != (after_sha is None)
        or (before_sha is not None and after_sha is not None and before_sha != after_sha)
    ):
        raise ReviewError(
            "runner_manifest_after_sha_mismatch",
            "runner manifest no-change transaction has inconsistent before and after SHAs",
        )
    if write_action in {"created", "identical_noop"} and after_sha != manifest.get("candidate_sha256"):
        raise ReviewError(
            "runner_manifest_after_sha_mismatch",
            "runner manifest completed transaction has inconsistent candidate and after SHAs",
        )
    if write_action == "semantic_noop":
        comparison = manifest.get("comparison")
        candidate_path = manifest.get("candidate_path")
        if not isinstance(candidate_path, str) or not candidate_path:
            raise ReviewError(
                "runner_manifest_semantic_evidence_invalid",
                "semantic_noop requires a candidate_path",
            )
        expected_candidate = runner_manifest_path.parent / "candidate.json"
        if Path(candidate_path).expanduser().resolve(strict=False) != expected_candidate.resolve(strict=False):
            raise ReviewError(
                "runner_manifest_semantic_evidence_invalid",
                "semantic_noop candidate_path must be the committed runner candidate",
            )
        if manifest.get("official_bytes_equal_candidate") is not False:
            raise ReviewError(
                "runner_manifest_semantic_evidence_invalid",
                "semantic_noop requires raw candidate and official bytes to differ",
            )
        if not isinstance(comparison, dict):
            raise ReviewError(
                "runner_manifest_semantic_evidence_invalid",
                "semantic_noop requires a comparison evidence object",
            )
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
        if set(comparison) != required_comparison:
            raise ReviewError(
                "runner_manifest_semantic_evidence_invalid",
                "semantic_noop comparison fields are incomplete or unknown",
            )
        if (
            comparison.get("comparison_mode") != oft.SEMANTIC_COMPARISON_MODE
            or comparison.get("excluded_json_paths") != list(oft.SEMANTIC_NOOP_EXCLUDED_JSON_PATHS)
            or comparison.get("candidate_raw_sha256") != manifest.get("candidate_sha256")
            or comparison.get("official_raw_sha256") != after_sha
            or comparison.get("candidate_raw_sha256") == comparison.get("official_raw_sha256")
            or comparison.get("semantic_equal") is not True
            or comparison.get("official_changed") is not False
            or comparison.get("candidate_semantic_sha256") != comparison.get("official_semantic_sha256")
            or not isinstance(comparison.get("candidate_semantic_sha256"), str)
            or not SHA_RE.fullmatch(comparison.get("candidate_semantic_sha256"))
        ):
            raise ReviewError(
                "runner_manifest_semantic_evidence_invalid",
                "semantic_noop comparison evidence is inconsistent",
            )


def validate_semantic_noop_evidence(
    manifest: dict[str, Any],
    *,
    runner_manifest_path: Path,
    official_bytes: bytes,
    official_sha256: str,
    symbol: str,
    trade_date: str,
    allowed_runtime_root: Path,
) -> None:
    """Recompute semantic_noop evidence from the committed candidate and official."""

    candidate_bytes, candidate_path = _read_regular_file_beneath(
        Path(str(manifest["candidate_path"])),
        root=allowed_runtime_root,
        reason_code="runner_manifest_semantic_candidate_missing",
        label="semantic_noop candidate path",
    )
    assert candidate_bytes is not None
    if sha256_bytes(candidate_bytes) != manifest.get("candidate_sha256"):
        raise ReviewError(
            "runner_manifest_semantic_candidate_sha_mismatch",
            "semantic_noop candidate raw SHA does not match the runner manifest",
        )
    if sha256_bytes(official_bytes) != official_sha256 or official_sha256 != manifest.get("official_sha256_after"):
        raise ReviewError(
            "runner_manifest_semantic_official_sha_mismatch",
            "semantic_noop current official SHA does not match the runner manifest",
        )
    candidate = parse_json_object(candidate_bytes, label="semantic_candidate")
    official = parse_json_object(official_bytes, label="semantic_official")
    try:
        vrc.assert_facts_pack_valid(candidate, facts_pack_path=str(candidate_path), date=trade_date)
        vrc.assert_facts_pack_valid(official, facts_pack_path=str(manifest.get("official_path")), date=trade_date)
    except Exception as exc:  # noqa: BLE001 - semantic evidence fails closed
        raise ReviewError(
            "runner_manifest_semantic_validator_failed",
            f"semantic_noop facts Validator failed: {sanitize_text(exc)}",
        ) from exc
    recomputed = oft.build_semantic_comparison(
        candidate=candidate,
        official=official,
        candidate_bytes=candidate_bytes,
        official_bytes=official_bytes,
        symbol=symbol,
        target_date=trade_date,
    )
    if recomputed.get("semantic_equal") is not True or manifest.get("comparison") != recomputed:
        raise ReviewError(
            "runner_manifest_semantic_comparison_mismatch",
            "semantic_noop comparison evidence does not match the live recomputation",
        )


def _validator_result(facts: dict[str, Any], *, official_path: Path, trade_date: str) -> dict[str, Any]:
    try:
        vrc.assert_facts_pack_valid(facts, facts_pack_path=str(official_path), date=trade_date)
    except Exception as exc:  # noqa: BLE001 - validator evidence is recorded fail-closed
        return {
            "status": "failed",
            "exception_type": type(exc).__name__,
            "message": sanitize_text(exc),
        }
    return {"status": "passed"}


def _active_entries(value: object, source: str) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [
            {"source": source, "field": str(key), "value": copy.deepcopy(item)}
            for key, item in value.items()
            if item not in (None, False, "", [], {})
        ]
    if isinstance(value, list):
        return [
            {"source": source, "field": str(index), "value": copy.deepcopy(item)}
            for index, item in enumerate(value)
        ]
    if value not in (None, False, ""):
        return [{"source": source, "field": "value", "value": copy.deepcopy(value)}]
    return []


def unresolved_fields(missing: object, needs_manual_check: object) -> list[dict[str, Any]]:
    return _active_entries(missing, "missing") + _active_entries(needs_manual_check, "needs_manual_check")


def confirmed_fields(facts: dict[str, Any]) -> list[str]:
    confirmed: list[str] = []
    quote = facts.get("quote") if isinstance(facts.get("quote"), dict) else {}
    for field in ("open", "high", "low", "close", "prev_close", "pct_change", "amount", "turnover_rate"):
        if field in quote and quote[field] is not None:
            confirmed.append(f"quote.{field}")
    volume = facts.get("volume_ratio") if isinstance(facts.get("volume_ratio"), dict) else {}
    verification = volume.get("verification") if isinstance(volume.get("verification"), dict) else {}
    if verification.get("status") in {"confirmed", "derived_confirmed", "manual_confirmed"}:
        confirmed.append("volume_ratio")
    return confirmed


def _source_refs(facts: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    allowed_keys = {"source", "source_url", "url", "evidence_ref", "raw_url", "method", "source_date"}

    def walk(value: object, prefix: str = "") -> None:
        if isinstance(value, dict):
            for key in sorted(value):
                child = value[key]
                path = f"{prefix}.{key}" if prefix else str(key)
                if str(key) in allowed_keys and isinstance(child, (str, int, float)) and not isinstance(child, bool):
                    refs.append({"field": path, "value": sanitize_text(child, limit=500)})
                elif isinstance(child, (dict, list)):
                    walk(child, path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{prefix}[{index}]")

    walk(facts)
    return refs


def _postcheck_status(runner: dict[str, Any] | None) -> str:
    if runner is None:
        return "unknown"
    if runner.get("official_post_write_error") or runner.get("write_action") == "created_postcheck_failed":
        return "failed"
    after = runner.get("official_validator_after")
    if isinstance(after, dict) and after.get("status") == "failed":
        return "failed"
    if isinstance(after, dict) and after.get("status") == "passed":
        return "passed"
    if runner.get("write_action") in {"created", "identical_noop", "semantic_noop", "conflict_blocked", "sealed_blocked", "manual_blocked"}:
        return "passed"
    return "unknown"


def _incident_reason(
    *,
    parse_error: str | None,
    identity_error: str | None,
    validator: dict[str, Any],
    runner: dict[str, Any] | None,
    runner_error_type: str | None,
    official_sha_match: bool | None,
) -> str | None:
    if runner_error_type:
        return "runner_manifest_invalid"
    if parse_error:
        return "official_json_invalid"
    if identity_error:
        return "official_identity_mismatch"
    if validator.get("status") == "failed":
        return "validator_failed"
    if official_sha_match is False:
        return "runner_official_sha_mismatch"
    if runner is not None:
        reason = runner.get("reason_code")
        action = runner.get("write_action")
        candidate_sha = runner.get("candidate_sha256")
        candidate_mismatch = (
            isinstance(candidate_sha, str)
            and candidate_sha != runner.get("official_sha256_after")
            and action in {"created", "identical_noop", "created_postcheck_failed"}
        )
        if (
            reason == "official_written_bytes_mismatch"
            or (
                runner.get("official_bytes_equal_candidate") is False
                and action != "semantic_noop"
            )
            or candidate_mismatch
        ):
            return "official_bytes_mismatch"
        if reason == "official_written_postcheck_failed" or action == "created_postcheck_failed" or _postcheck_status(runner) == "failed":
            return "post_write_failure"
        if reason == "official_written_manifest_failed":
            return "official_written_manifest_failed"
        if reason in INCIDENT_REASON_CODES or action in INCIDENT_WRITE_ACTIONS:
            return "official_conflict"
    return None


def build_review_manifest(
    *,
    review_id: str,
    official_bytes: bytes,
    official_sha256: str,
    official_path: Path,
    symbol: str,
    trade_date: str,
    runner_evidence: RunnerEvidence,
    rebuild_from_official: bool,
    generated_at: datetime,
    invalid_prior: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runner = runner_evidence.manifest
    parse_error: str | None = None
    identity_error: str | None = None
    facts: dict[str, Any] | None = None
    try:
        facts = parse_json_object(official_bytes, label="official")
    except ReviewError as exc:
        parse_error = sanitize_text(exc)
    if facts is not None and (str(facts.get("symbol")) != symbol or str(facts.get("trade_date")) != trade_date):
        identity_error = "official symbol or trade_date does not match the canonical path"
    validator = _sanitized_copy(
        _validator_result(facts, official_path=official_path, trade_date=trade_date)
        if facts is not None and identity_error is None
        else {"status": "not_run", "reason_code": "official_unparseable_or_identity_mismatch"}
    )
    if not isinstance(validator, dict):
        validator = {"status": "failed", "reason_code": "validator_result_invalid"}
    runner_after = runner.get("official_sha256_after") if runner else None
    official_sha_match: bool | None = (runner_after == official_sha256) if runner is not None else None
    incident_reason = _incident_reason(
        parse_error=parse_error,
        identity_error=identity_error,
        validator=validator,
        runner=runner,
        runner_error_type=runner_evidence.error_type,
        official_sha_match=official_sha_match,
    )
    artifact_type = "incident_review" if incident_reason else "facts_review"
    safe_facts = facts if artifact_type == "facts_review" and facts is not None else {}
    missing = _sanitized_copy(safe_facts.get("missing", {}))
    needs = _sanitized_copy(safe_facts.get("needs_manual_check", {}))
    unresolved = unresolved_fields(missing, needs)
    facts_status = (
        safe_facts.get("run", {}).get("status")
        if isinstance(safe_facts.get("run"), dict)
        else None
    )
    complete = facts_status == "success" and not unresolved
    completed_official_transaction = (
        runner is not None
        and runner.get("write_action") in {"created", "identical_noop", "semantic_noop"}
        and runner.get("outcome") in {"success", "partial", "official_unchanged"}
    )
    review_state = "ready_for_human_review"
    if (
        rebuild_from_official
        or invalid_prior is not None
        or artifact_type == "incident_review"
        or not complete
        or validator.get("status") != "passed"
        or official_sha_match is not True
        or not completed_official_transaction
    ):
        review_state = "needs_manual_review"
    mode = "rebuild_from_official" if rebuild_from_official or runner_evidence.error_type else (runner.get("mode") if runner else None)
    write_action = sanitize_text(runner.get("write_action")) if runner and runner.get("write_action") is not None else None
    reason_code = sanitize_text(runner.get("reason_code")) if runner and runner.get("reason_code") is not None else None
    candidate_sha = runner.get("candidate_sha256") if runner else None
    official_before = runner.get("official_sha256_before") if runner else None
    official_changed = runner.get("official_changed") if runner else None
    postcheck = _postcheck_status(runner)
    evidence_summary = {
        "official_bytes_sha256": official_sha256,
        "official_parse_error": parse_error,
        "official_identity_error": identity_error,
        "runner_manifest_sha256": runner_evidence.sha256,
        "runner_manifest_error": (
            {
                "error_type": runner_evidence.error_type,
                "message": runner_evidence.error_message,
            }
            if runner_evidence.error_type
            else None
        ),
        "runner_official_sha256_after": runner_after,
        "candidate_sha256": candidate_sha,
        "official_bytes_equal_candidate": runner.get("official_bytes_equal_candidate") if runner else None,
        "official_post_write_error": _sanitized_copy(runner.get("official_post_write_error")) if runner else None,
        "runner_official_validator_after": _sanitized_copy(runner.get("official_validator_after")) if runner else None,
        "semantic_comparison": _sanitized_copy(runner.get("comparison")) if runner else None,
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": artifact_type,
        "review_id": review_id,
        "run_id": None if rebuild_from_official else (runner.get("run_id") if runner else None),
        "symbol": symbol,
        "trade_date": trade_date,
        "mode": mode,
        "official_path": str(official_path),
        "official_sha256": official_sha256,
        "candidate_sha256": candidate_sha,
        "runner_manifest_path": str(runner_evidence.path) if runner_evidence.path else None,
        "runner_manifest_sha256": runner_evidence.sha256,
        "official_sha256_before": official_before,
        "official_changed": official_changed,
        "official_sha_match": official_sha_match,
        "write_action": write_action,
        "write_reason_code": reason_code,
        "postcheck_status": postcheck,
        "incident_reason_code": incident_reason,
        "facts_status": facts_status,
        "validator_result": validator,
        "missing": missing,
        "needs_manual_check": needs,
        "confirmed_fields": confirmed_fields(safe_facts) if artifact_type == "facts_review" else [],
        "unresolved_fields": unresolved,
        "partial_write_policy": _sanitized_copy(runner.get("partial_write_policy")) if runner else None,
        "evidence_summary": evidence_summary,
        "source_refs": _source_refs(safe_facts) if artifact_type == "facts_review" else [],
        "generated_at": generated_at.astimezone(ZoneInfo(BUSINESS_TIMEZONE)).isoformat(),
        "generator_version": GENERATOR_VERSION,
        "review_state": review_state,
        "downstream_permissions": dict(DOWNSTREAM_PERMISSIONS),
        "provenance": {
            "authoritative_inputs": [
                "official_locked_bytes",
                *( ["runner_manifest_schema_valid"] if runner else [] ),
                *( ["facts_validator_live"] if validator.get("status") != "not_run" else [] ),
            ],
            "rebuilt_from_official": rebuild_from_official,
            "runner_manifest_used": runner is not None,
            "runner_manifest_invalid": runner_evidence.error_type is not None,
            "official_sha_rechecked_before_commit": True,
            "invalid_prior_manifest": invalid_prior,
        },
    }
    validate_review_manifest(manifest)
    return manifest


def _sanitized_copy(value: object, *, key_hint: str | None = None) -> object:
    if key_hint is not None and SENSITIVE_KEY_RE.fullmatch(key_hint):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            str(key): _sanitized_copy(child, key_hint=str(key))
            for key, child in value.items()
            if str(key) not in FORBIDDEN_MANIFEST_KEYS
        }
    if isinstance(value, list):
        return [_sanitized_copy(child) for child in value]
    if isinstance(value, str):
        return sanitize_text(value)
    return copy.deepcopy(value)


def _walk_manifest(value: object) -> Iterator[tuple[str | None, object]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from _walk_manifest(child)
    elif isinstance(value, list):
        for child in value:
            yield None, child
            yield from _walk_manifest(child)


def validate_review_manifest(manifest: dict[str, Any]) -> None:
    missing_fields = REQUIRED_MANIFEST_FIELDS - set(manifest)
    if missing_fields:
        raise ReviewError("review_manifest_schema_invalid", f"review manifest is missing fields: {sorted(missing_fields)}")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ReviewError("review_manifest_schema_invalid", "review manifest schema_version is invalid")
    if manifest.get("artifact_type") not in {"facts_review", "incident_review"}:
        raise ReviewError("review_manifest_schema_invalid", "artifact_type is invalid")
    if manifest.get("review_state") not in ALLOWED_REVIEW_STATES:
        raise ReviewError("review_manifest_state_invalid", "machine review state exceeds the human boundary")
    if manifest.get("downstream_permissions") != DOWNSTREAM_PERMISSIONS:
        raise ReviewError("downstream_permissions_invalid", "all downstream permissions must remain false")
    if manifest.get("mode") not in ALLOWED_MODES:
        raise ReviewError("review_manifest_mode_invalid", "review manifest mode is invalid")
    if not SHA_RE.fullmatch(str(manifest.get("official_sha256") or "")):
        raise ReviewError("review_manifest_sha_invalid", "official_sha256 is invalid")
    for key, value in _walk_manifest(manifest):
        if key in FORBIDDEN_MANIFEST_KEYS:
            raise ReviewError("forbidden_human_field", f"manifest contains forbidden field {key}")
        if isinstance(value, str) and value.lower() in FORBIDDEN_MANIFEST_VALUES:
            raise ReviewError("forbidden_human_state", "manifest contains a machine-forbidden human decision")


def render_summary(manifest: dict[str, Any]) -> str:
    validate_review_manifest(manifest)
    warning = (
        "⚠️ 固定警示：本记录存在未决事项或事务异常，必须人工逐项核验；禁止弱化、推断或启用任何下游权限。"
        if manifest["review_state"] == "needs_manual_review"
        else "⚠️ 固定警示：本记录仅已具备人工审查条件，尚未批准；全部下游权限保持关闭。"
    )

    def lines_for(value: object) -> list[str]:
        if isinstance(value, dict):
            return [f"- `{key}`: `{json.dumps(item, ensure_ascii=False, sort_keys=True)}`" for key, item in value.items()] or ["- （无）"]
        if isinstance(value, list):
            return [f"- `{json.dumps(item, ensure_ascii=False, sort_keys=True)}`" for item in value] or ["- （无）"]
        return [f"- `{json.dumps(value, ensure_ascii=False)}`"]

    unresolved = manifest["unresolved_fields"]
    todo = [
        f"- 核验 `{item.get('source')}.{item.get('field')}`，保持原值 `{json.dumps(item.get('value'), ensure_ascii=False, sort_keys=True)}`"
        for item in unresolved
        if isinstance(item, dict)
    ]
    if manifest["artifact_type"] == "incident_review":
        todo.insert(0, f"- 核验事故原因 `{manifest.get('incident_reason_code')}` 及 Phase B 事务证据")
    if not todo:
        todo = ["- 人工核对 manifest 与 official facts 后再作任何后续决定"]
    return "\n".join(
        [
            "# Phase C Deterministic Review Summary",
            "",
            warning,
            "",
            f"- artifact type: `{manifest['artifact_type']}`",
            f"- review state: `{manifest['review_state']}`",
            f"- official SHA: `{manifest['official_sha256']}`",
            f"- runner SHA 核验: `{manifest['official_sha_match']}`",
            f"- Validator 结果: `{manifest['validator_result'].get('status')}`",
            f"- write action / reason: `{manifest.get('write_action')}` / `{manifest.get('write_reason_code')}`",
            "",
            "## missing",
            "",
            *lines_for(manifest["missing"]),
            "",
            "## needs_manual_check",
            "",
            *lines_for(manifest["needs_manual_check"]),
            "",
            "## unresolved_fields",
            "",
            *lines_for(manifest["unresolved_fields"]),
            "",
            "## 人工待核清单",
            "",
            *todo,
            "",
            "## 下游权限",
            "",
            "review/current_cards/index/weekly/git/trading 全部为 false；本摘要不含交易判断、趋势观点或正式复盘结论。",
            "",
        ]
    )


def _index_runtime_and_trade_date(index_path: Path) -> tuple[Path, str]:
    if index_path.name != "review_index.jsonl" or index_path.parent.parent.name != "reviews":
        raise IndexCorruptError("index_manifest_path_invalid", "review index path is not canonical")
    return index_path.parent.parent.parent.resolve(strict=False), index_path.parent.name


def _canonical_index_manifest_path(entry: dict[str, Any], *, runtime_dir: Path, index_trade_date: str) -> Path:
    trade_date = entry.get("trade_date")
    review_id = entry.get("review_id")
    value = entry.get("manifest_path")
    if trade_date != index_trade_date or not isinstance(review_id, str) or not isinstance(value, str):
        raise IndexCorruptError("index_manifest_path_invalid", "index manifest identity or path is invalid")
    if review_id in {"", ".", ".."} or Path(review_id).name != review_id:
        raise IndexCorruptError("index_manifest_path_invalid", "index review ID is not a single canonical directory name")
    raw = Path(value).expanduser()
    if not raw.is_absolute() or raw.name != "review_manifest.json":
        raise IndexCorruptError("index_manifest_path_invalid", "index manifest path must be absolute and canonical")
    expected_dir = runtime_dir / "reviews" / trade_date / review_id
    expected = expected_dir / "review_manifest.json"
    lexical = Path(os.path.abspath(raw))
    expected_lexical = Path(os.path.abspath(expected))
    if lexical != expected_lexical:
        raise IndexCorruptError("index_manifest_path_invalid", "index manifest path is outside its canonical review directory")
    resolved = raw.resolve(strict=False)
    expected_resolved = expected.resolve(strict=False)
    reviews_root = (runtime_dir / "reviews").resolve(strict=False)
    if resolved != expected_resolved or not _inside(resolved, reviews_root) or not _inside(resolved, expected_dir.resolve(strict=False)):
        raise IndexCorruptError("index_manifest_path_invalid", "index manifest path resolves outside its canonical review directory")
    return resolved


def read_index(index_path: Path) -> list[dict[str, Any]]:
    if not index_path.exists():
        return []
    raw = index_path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise IndexCorruptError("review_index_truncated_tail", "review index has a partial trailing line")
    parsed: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line:
            raise IndexCorruptError("review_index_corrupt", f"review index line {line_number} is empty")
        try:
            entry = json.loads(line.decode("utf-8"), parse_constant=_reject_json_constant)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise IndexCorruptError("review_index_corrupt", f"review index line {line_number} is invalid: {sanitize_text(exc)}") from exc
        validate_index_entry(entry, line_number=line_number)
        parsed.append(entry)

    entries: list[dict[str, Any]] = []
    by_review_id: dict[str, dict[str, Any]] = {}
    path_owners: dict[str, str] = {}
    for entry in parsed:
        review_id = str(entry["review_id"])
        manifest_path = str(entry["manifest_path"])
        prior_owner = path_owners.get(manifest_path)
        if prior_owner is not None and prior_owner != review_id:
            raise IndexCorruptError(
                "index_manifest_alias_conflict",
                "one manifest path is referenced by multiple review IDs",
            )
        path_owners[manifest_path] = review_id
        prior = by_review_id.get(review_id)
        if prior is not None:
            if prior == entry:
                continue
            raise IndexCorruptError(
                "index_duplicate_review_conflict",
                "duplicate review ID has conflicting index records",
            )
        by_review_id[review_id] = entry
        entries.append(entry)

    runtime_dir, index_trade_date = _index_runtime_and_trade_date(index_path)
    for entry in entries:
        _canonical_index_manifest_path(entry, runtime_dir=runtime_dir, index_trade_date=index_trade_date)
    return entries


def validate_index_entry(entry: object, *, line_number: int | None = None) -> None:
    label = f"line {line_number}" if line_number is not None else "entry"
    required = {
        "schema_version",
        "review_id",
        "symbol",
        "trade_date",
        "official_sha256",
        "manifest_path",
        "manifest_sha256",
        "review_state",
        "created_at",
        "supersedes_review_id",
    }
    if not isinstance(entry, dict) or required - set(entry):
        raise IndexCorruptError("review_index_corrupt", f"review index {label} is missing required fields")
    if entry.get("schema_version") != INDEX_SCHEMA_VERSION:
        raise IndexCorruptError("review_index_corrupt", f"review index {label} schema is invalid")
    if entry.get("review_state") not in ALLOWED_REVIEW_STATES:
        raise IndexCorruptError("review_index_corrupt", f"review index {label} state is invalid")
    if not isinstance(entry.get("review_id"), str) or not isinstance(entry.get("manifest_path"), str):
        raise IndexCorruptError("review_index_corrupt", f"review index {label} identity path is invalid")
    if not SYMBOL_RE.fullmatch(str(entry.get("symbol") or "")) or not DATE_RE.fullmatch(str(entry.get("trade_date") or "")):
        raise IndexCorruptError("review_index_corrupt", f"review index {label} symbol or date is invalid")
    if not SHA_RE.fullmatch(str(entry.get("official_sha256") or "")) or not SHA_RE.fullmatch(str(entry.get("manifest_sha256") or "")):
        raise IndexCorruptError("review_index_corrupt", f"review index {label} SHA is invalid")


def inspect_index_entry(entry: dict[str, Any], *, runtime_dir: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    try:
        path = _canonical_index_manifest_path(
            entry,
            runtime_dir=runtime_dir,
            index_trade_date=str(entry.get("trade_date")),
        )
    except IndexCorruptError as exc:
        raise exc
    try:
        raw = path.read_bytes()
        if sha256_bytes(raw) != entry["manifest_sha256"]:
            raise ReviewError("manifest_sha_mismatch", "indexed manifest SHA mismatch")
        manifest = parse_json_object(raw, label="review_manifest")
        validate_review_manifest(manifest)
        if any(
            manifest.get(key) != entry.get(key)
            for key in ("review_id", "symbol", "trade_date", "official_sha256", "review_state")
        ):
            raise ReviewError("manifest_index_mismatch", "manifest and index identity mismatch")
        return manifest, None
    except (OSError, ReviewError) as exc:
        observed_sha = None
        missing = not path.exists()
        if not missing:
            try:
                observed_sha = sha256_bytes(path.read_bytes())
            except OSError:
                observed_sha = None
        return None, {
            "review_id": entry.get("review_id"),
            "path": str(path),
            "reason_code": getattr(exc, "reason_code", "indexed_manifest_unreadable"),
            "message": sanitize_text(exc),
            "observed_manifest_sha256": observed_sha,
            "manifest_missing": missing,
        }


def load_existing_manifest(path: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if not path.exists():
        return None, None
    try:
        raw = path.read_bytes()
        manifest = parse_json_object(raw, label="review_manifest")
        validate_review_manifest(manifest)
        return manifest, None
    except (OSError, ReviewError) as exc:
        observed_sha = None
        try:
            observed_sha = sha256_bytes(path.read_bytes())
        except OSError:
            pass
        return None, {
            "path": str(path),
            "reason_code": getattr(exc, "reason_code", "review_manifest_unreadable"),
            "message": sanitize_text(exc),
            "observed_manifest_sha256": observed_sha,
            "manifest_missing": not path.exists(),
        }


def invalid_diagnostic_fingerprint(
    *,
    canonical_review_id: str,
    canonical_manifest_path: Path,
    diagnostic: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    missing = bool(diagnostic.get("manifest_missing"))
    observed_sha = diagnostic.get("observed_manifest_sha256")
    observation = "missing" if missing else (observed_sha if isinstance(observed_sha, str) else "unreadable")
    normalized = {
        "canonical_review_id": canonical_review_id,
        "invalid_reason": str(diagnostic.get("reason_code") or "review_manifest_invalid"),
        "canonical_manifest_path": str(canonical_manifest_path.resolve(strict=False)),
        "observed_manifest_sha256": observation,
    }
    fingerprint = sha256_bytes(canonical_json_line(normalized).rstrip(b"\n"))
    return fingerprint, {
        **normalized,
        "diagnostic_fingerprint": fingerprint,
        "message": sanitize_text(diagnostic.get("message", "invalid canonical manifest")),
    }


def verify_uncommitted_manifest(
    manifest: dict[str, Any],
    *,
    official_bytes: bytes,
    official_sha256: str,
    official_path: Path,
    runner_runtime_dir: Path,
    symbol: str,
    trade_date: str,
) -> None:
    """Re-derive an unindexed manifest before allowing index recovery."""

    rebuilt = bool(
        isinstance(manifest.get("provenance"), dict)
        and manifest["provenance"].get("rebuilt_from_official") is True
    )
    runner_value = manifest.get("runner_manifest_path")
    runner_path = Path(runner_value) if isinstance(runner_value, str) else None
    runner_evidence = load_runner_evidence(
        runner_path,
        allowed_runtime_root=runner_runtime_dir,
        symbol=symbol,
        trade_date=trade_date,
        official_path=official_path,
        official_bytes=official_bytes,
        official_sha256=official_sha256,
        required=not rebuilt,
        expected_sha256=(
            str(manifest.get("runner_manifest_sha256"))
            if manifest.get("runner_manifest_sha256") is not None
            else None
        ),
    )
    if runner_evidence.error_type == "runner_manifest_changed":
        raise ReviewError(
            "runner_manifest_changed",
            "runner manifest SHA changed after the uncommitted review manifest was created",
        )
    try:
        generated_at = datetime.fromisoformat(str(manifest.get("generated_at")))
    except ValueError as exc:
        raise ReviewError("review_manifest_generated_at_invalid", "uncommitted manifest generated_at is invalid") from exc
    expected = build_review_manifest(
        review_id=str(manifest.get("review_id")),
        official_bytes=official_bytes,
        official_sha256=official_sha256,
        official_path=official_path,
        symbol=symbol,
        trade_date=trade_date,
        runner_evidence=runner_evidence,
        rebuild_from_official=rebuilt,
        generated_at=generated_at,
        invalid_prior=manifest.get("provenance", {}).get("invalid_prior_manifest"),
    )
    if expected != manifest:
        raise ReviewError("uncommitted_manifest_authority_mismatch", "uncommitted manifest does not match current authoritative inputs")


def make_index_entry(manifest: dict[str, Any], manifest_path: Path, manifest_bytes: bytes, *, supersedes_review_id: str | None) -> dict[str, Any]:
    return {
        "schema_version": INDEX_SCHEMA_VERSION,
        "review_id": manifest["review_id"],
        "symbol": manifest["symbol"],
        "trade_date": manifest["trade_date"],
        "official_sha256": manifest["official_sha256"],
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "review_state": manifest["review_state"],
        "created_at": manifest["generated_at"],
        "supersedes_review_id": supersedes_review_id,
    }


def append_index_entry(index_path: Path, entry: dict[str, Any]) -> None:
    validate_index_entry(entry)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_line(entry)
    descriptor = os.open(index_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise OSError("short append to review index")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    fsync_directory(index_path.parent)


def _commit_new_directory(temp_dir: Path, final_dir: Path) -> None:
    os.rename(temp_dir, final_dir)
    fsync_directory(final_dir.parent)


def _commit_into_summary_orphan(temp_dir: Path, final_dir: Path) -> None:
    final_dir.mkdir(parents=True, exist_ok=True)
    os.replace(temp_dir / "review_summary.md", final_dir / "review_summary.md")
    os.replace(temp_dir / "review_manifest.json", final_dir / "review_manifest.json")
    fsync_directory(final_dir)
    fsync_directory(final_dir.parent)
    temp_dir.rmdir()


def _write_temp_artifacts(trade_dir: Path, manifest: dict[str, Any]) -> tuple[Path, bytes]:
    trade_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=".review_tmp_", dir=trade_dir))
    manifest_payload = json_bytes(manifest)
    try:
        atomic_write_bytes(temp_dir / "review_summary.md", render_summary(manifest).encode("utf-8"))
        atomic_write_bytes(temp_dir / "review_manifest.json", manifest_payload)
        fsync_directory(temp_dir)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    return temp_dir, manifest_payload


def _current_time(options: ReviewOptions) -> datetime:
    value = options.now() if options.now else datetime.now(ZoneInfo(BUSINESS_TIMEZONE))
    if value.tzinfo is None or value.utcoffset() is None:
        value = value.replace(tzinfo=ZoneInfo(BUSINESS_TIMEZONE))
    return value.astimezone(ZoneInfo(BUSINESS_TIMEZONE))


def _latest_superseded(entries: list[dict[str, Any]], valid_manifests: dict[str, dict[str, Any]], *, symbol: str, trade_date: str, official_sha: str) -> str | None:
    for entry in reversed(entries):
        if (
            entry.get("symbol") == symbol
            and entry.get("trade_date") == trade_date
            and entry.get("official_sha256") != official_sha
            and entry.get("review_id") in valid_manifests
        ):
            return str(entry["review_id"])
    return None


def generate_review(options: ReviewOptions) -> ReviewResult:
    validate_identity(options.symbol, options.trade_date)
    runtime = normalize_runtime_dir(options.runtime_dir, repo_root=options.repo_root)
    prepare_runtime_dir(runtime, repo_root=options.repo_root)
    runner_runtime = normalize_runtime_dir(
        options.runner_runtime_dir or runtime,
        repo_root=options.repo_root,
    )
    official_path = canonical_official_path(options.repo_root, options.symbol, options.trade_date)
    if official_path.is_symlink() or official_path.parent.is_symlink():
        raise ReviewError("official_path_invalid", "official facts path must not be a symlink")
    lock_path = review_lock_path(runtime, options.symbol, options.trade_date)
    with review_lock(lock_path) as acquired:
        if not acquired:
            return ReviewResult("review_generator_already_active", None, None, None, None, "review_generator_already_active")
        with ofl.official_facts_lock(official_path, lock_dir=options.official_lock_dir) as official_lock:
            initial_bytes, initial_sha = _read_locked_official(
                official_path,
                repo_root=options.repo_root,
                lock_state=official_lock,
            )
        if initial_bytes is None or initial_sha is None:
            raise ReviewError("official_facts_missing", "canonical official facts do not exist")
        runner_evidence = load_runner_evidence(
            options.runner_manifest_path,
            allowed_runtime_root=runner_runtime,
            symbol=options.symbol,
            trade_date=options.trade_date,
            official_path=official_path,
            official_bytes=initial_bytes,
            official_sha256=initial_sha,
            required=not options.rebuild_from_official,
        )
        trade_dir = runtime / "reviews" / options.trade_date
        index_path = trade_dir / "review_index.jsonl"
        entries = read_index(index_path)
        valid_index: dict[str, dict[str, Any]] = {}
        invalid_diagnostics: list[dict[str, Any]] = []
        for entry in entries:
            manifest, diagnostic = inspect_index_entry(entry, runtime_dir=runtime)
            if manifest is not None:
                valid_index[str(entry["review_id"])] = manifest
            elif diagnostic is not None:
                invalid_diagnostics.append(diagnostic)

        canonical_id = review_id_for(options.symbol, options.trade_date, initial_sha)
        canonical_dir = trade_dir / canonical_id
        canonical_manifest_path = canonical_dir / "review_manifest.json"
        existing_manifest, existing_diagnostic = load_existing_manifest(canonical_manifest_path)
        invalid_prior: dict[str, Any] | None = existing_diagnostic
        relevant_bad_index = [
            item for item in invalid_diagnostics if any(
                entry.get("review_id") == item.get("review_id") and entry.get("official_sha256") == initial_sha
                for entry in entries
            )
        ]
        if relevant_bad_index:
            invalid_prior = relevant_bad_index[0]

        if existing_manifest is not None:
            if (
                existing_manifest.get("official_sha256") != initial_sha
                or existing_manifest.get("review_id") != canonical_id
                or existing_manifest.get("symbol") != options.symbol
                or existing_manifest.get("trade_date") != options.trade_date
                or Path(str(existing_manifest.get("official_path"))).resolve(strict=False) != official_path.resolve(strict=False)
            ):
                invalid_prior = {
                    "path": str(canonical_manifest_path),
                    "reason_code": "existing_manifest_identity_mismatch",
                    "observed_manifest_sha256": sha256_bytes(canonical_manifest_path.read_bytes()),
                    "manifest_missing": False,
                }
                existing_manifest = None
            elif canonical_id in valid_index:
                if options.before_final_recheck:
                    options.before_final_recheck()
                with ofl.official_facts_lock(official_path, lock_dir=options.official_lock_dir) as official_lock:
                    _bytes, final_sha = _read_locked_official(
                        official_path,
                        repo_root=options.repo_root,
                        lock_state=official_lock,
                    )
                    if final_sha != initial_sha:
                        return ReviewResult("official_changed_during_generation", None, None, index_path, None, "official_sha_changed")
                return ReviewResult("review_already_exists", canonical_id, canonical_manifest_path, index_path, existing_manifest["review_state"])
            else:
                try:
                    verify_uncommitted_manifest(
                        existing_manifest,
                        official_bytes=initial_bytes,
                        official_sha256=initial_sha,
                        official_path=official_path,
                        runner_runtime_dir=runner_runtime,
                        symbol=options.symbol,
                        trade_date=options.trade_date,
                    )
                except ReviewError as exc:
                    invalid_prior = {
                        "path": str(canonical_manifest_path),
                        "reason_code": exc.reason_code,
                        "message": sanitize_text(exc),
                    }
                    existing_manifest = None
            if existing_manifest is not None and canonical_id not in valid_index:
                existing_payload = canonical_manifest_path.read_bytes()
                if options.before_final_recheck:
                    options.before_final_recheck()
                with ofl.official_facts_lock(official_path, lock_dir=options.official_lock_dir) as official_lock:
                    _bytes, final_sha = _read_locked_official(
                        official_path,
                        repo_root=options.repo_root,
                        lock_state=official_lock,
                    )
                    if final_sha != initial_sha:
                        return ReviewResult("official_changed_during_generation", None, None, index_path, None, "official_sha_changed")
                    entry = make_index_entry(
                        existing_manifest,
                        canonical_manifest_path,
                        existing_payload,
                        supersedes_review_id=_latest_superseded(entries, valid_index, symbol=options.symbol, trade_date=options.trade_date, official_sha=initial_sha),
                    )
                    append_index_entry(index_path, entry)
                return ReviewResult("review_index_recovered", canonical_id, canonical_manifest_path, index_path, existing_manifest["review_state"])

        review_id = canonical_id
        final_dir = canonical_dir
        summary_orphan = canonical_dir.exists() and not canonical_manifest_path.exists() and not invalid_prior
        if invalid_prior is not None:
            fingerprint, invalid_prior = invalid_diagnostic_fingerprint(
                canonical_review_id=canonical_id,
                canonical_manifest_path=canonical_manifest_path,
                diagnostic=invalid_prior,
            )
            suffix = f"invalid_{fingerprint[:16]}"
            review_id = review_id_for(options.symbol, options.trade_date, initial_sha, suffix=suffix)
            final_dir = trade_dir / review_id
            if review_id in valid_index:
                if options.before_final_recheck:
                    options.before_final_recheck()
                with ofl.official_facts_lock(official_path, lock_dir=options.official_lock_dir) as official_lock:
                    _bytes, final_sha = _read_locked_official(
                        official_path,
                        repo_root=options.repo_root,
                        lock_state=official_lock,
                    )
                    if final_sha != initial_sha:
                        return ReviewResult("official_changed_during_generation", None, None, index_path, None, "official_sha_changed")
                diagnostic_manifest = valid_index[review_id]
                return ReviewResult(
                    "invalid_diagnostic_already_recorded",
                    review_id,
                    final_dir / "review_manifest.json",
                    index_path,
                    diagnostic_manifest["review_state"],
                    "invalid_diagnostic_already_recorded",
                )

        manifest = build_review_manifest(
            review_id=review_id,
            official_bytes=initial_bytes,
            official_sha256=initial_sha,
            official_path=official_path,
            symbol=options.symbol,
            trade_date=options.trade_date,
            runner_evidence=runner_evidence,
            rebuild_from_official=options.rebuild_from_official,
            generated_at=_current_time(options),
            invalid_prior=invalid_prior,
        )
        temp_dir, manifest_payload = _write_temp_artifacts(trade_dir, manifest)
        try:
            if options.before_final_recheck:
                options.before_final_recheck()
            with ofl.official_facts_lock(official_path, lock_dir=options.official_lock_dir) as official_lock:
                _final_bytes, final_sha = _read_locked_official(
                    official_path,
                    repo_root=options.repo_root,
                    lock_state=official_lock,
                )
                if final_sha != initial_sha:
                    return ReviewResult("official_changed_during_generation", None, None, index_path, None, "official_sha_changed")
                if summary_orphan and final_dir == canonical_dir:
                    _commit_into_summary_orphan(temp_dir, final_dir)
                else:
                    _commit_new_directory(temp_dir, final_dir)
                temp_dir = Path("")
                manifest_path = final_dir / "review_manifest.json"
                supersedes = _latest_superseded(
                    entries,
                    valid_index,
                    symbol=options.symbol,
                    trade_date=options.trade_date,
                    official_sha=initial_sha,
                )
                append_index_entry(
                    index_path,
                    make_index_entry(manifest, manifest_path, manifest_payload, supersedes_review_id=supersedes),
                )
            status = "review_created_after_invalid" if invalid_prior is not None else "review_created"
            if summary_orphan:
                status = "review_summary_orphan_recovered"
            return ReviewResult(status, review_id, manifest_path, index_path, manifest["review_state"])
        finally:
            if temp_dir and temp_dir.exists() and temp_dir.name.startswith(".review_tmp_"):
                shutil.rmtree(temp_dir, ignore_errors=True)
