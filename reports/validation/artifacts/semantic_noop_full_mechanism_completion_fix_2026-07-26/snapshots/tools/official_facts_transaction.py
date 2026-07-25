"""Shared transaction policy for controlled official daily facts writes."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from tools import official_facts_lock as ofl
from tools import validate_review_chain as vrc
from tools import volume_ratio_evidence as vre


OFFICIAL_DAILY_DIR = Path("data") / "daily"
PARTIAL_MISSING_WHITELIST = frozenset(
    {
        "market_indices",
        "sector_context",
        "disclosure_status",
        "news_policy_context",
    }
)
CORE_QUOTE_FIELDS = (
    "open",
    "high",
    "low",
    "close",
    "prev_close",
    "pct_change",
    "amount",
    "turnover_rate",
)
VOLUME_RATIO_ALLOWED_STATUSES = {"confirmed", "derived_confirmed"}
VOLUME_RATIO_BLOCKED_STATUSES = {"candidate", "conflict", "stale", "unavailable", "rejected", "needs_manual_check"}
SEMANTIC_NOOP_EXCLUDED_JSON_PATHS = (
    "generated_at",
    "quote_verification.fetched_at",
    "run.fetched_at",
    "volume_ratio.five_day_volume_check.fetched_at",
    "volume_ratio.snapshot_ohlc_check.fetched_at",
    "volume_ratio.verification.fetched_at",
)
SEMANTIC_COMPARISON_MODE = "approved_timestamp_paths_v1"


@dataclass(frozen=True)
class PartialPolicyResult:
    eligible: bool
    reason_code: str
    missing_keys: tuple[str, ...]
    needs_manual_review: bool


@dataclass(frozen=True)
class OfficialWriteResult:
    write_action: str
    outcome: str
    reason_code: str
    official_path: Path
    official_exists_before: bool
    official_sha256_before: str | None
    official_sha256_after: str | None
    candidate_sha256: str
    partial_write_policy: dict[str, Any]
    official_validator_before: dict[str, Any]
    official_validator_after: dict[str, Any]
    official_changed: bool = False
    official_bytes_equal_candidate: bool | None = None
    post_write_error: dict[str, Any] | None = None
    comparison: dict[str, Any] | None = None


def semantic_json_bytes(payload: dict[str, Any]) -> bytes:
    """Serialize normalized facts deterministically for semantic hashing."""

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _pop_exact_json_path(payload: dict[str, Any], path: str) -> tuple[bool, object]:
    parts = path.split(".")
    current: object = payload
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    if not isinstance(current, dict) or parts[-1] not in current:
        return False, None
    return True, current.pop(parts[-1])


def build_semantic_comparison(
    *,
    candidate: dict[str, Any],
    official: dict[str, Any],
    candidate_bytes: bytes,
    official_bytes: bytes,
    symbol: str,
    target_date: str,
) -> dict[str, Any]:
    """Compare facts while excluding only the six approved timestamp paths."""

    candidate_raw_sha = hashlib.sha256(candidate_bytes).hexdigest()
    official_raw_sha = hashlib.sha256(official_bytes).hexdigest()
    result: dict[str, Any] = {
        "comparison_mode": SEMANTIC_COMPARISON_MODE,
        "candidate_raw_sha256": candidate_raw_sha,
        "official_raw_sha256": official_raw_sha,
        "candidate_semantic_sha256": None,
        "official_semantic_sha256": None,
        "excluded_json_paths": list(SEMANTIC_NOOP_EXCLUDED_JSON_PATHS),
        "excluded_values": {
            "candidate_types": {},
            "official_types": {},
            "all_paths_present": False,
            "all_strings": False,
            "all_valid_iso_datetime": False,
        },
        "semantic_equal": False,
        "official_changed": False,
    }
    candidate_schema = candidate.get("schema_version")
    identity_equal = (
        candidate.get("symbol") == official.get("symbol") == symbol
        and candidate.get("trade_date") == official.get("trade_date") == target_date
        and isinstance(candidate_schema, str)
        and candidate_schema == official.get("schema_version")
    )
    if not identity_equal:
        return result

    candidate_semantic = copy.deepcopy(candidate)
    official_semantic = copy.deepcopy(official)
    all_present = True
    all_strings = True
    all_valid_iso = True
    for path in SEMANTIC_NOOP_EXCLUDED_JSON_PATHS:
        candidate_present, candidate_value = _pop_exact_json_path(candidate_semantic, path)
        official_present, official_value = _pop_exact_json_path(official_semantic, path)
        all_present = all_present and candidate_present and official_present
        candidate_type = type(candidate_value).__name__ if candidate_present else "missing"
        official_type = type(official_value).__name__ if official_present else "missing"
        result["excluded_values"]["candidate_types"][path] = candidate_type
        result["excluded_values"]["official_types"][path] = official_type
        values_are_strings = (
            candidate_present
            and official_present
            and isinstance(candidate_value, str)
            and isinstance(official_value, str)
        )
        all_strings = all_strings and values_are_strings
        if values_are_strings:
            try:
                vre.parse_timezone_datetime(candidate_value, field=f"candidate.{path}")
                vre.parse_timezone_datetime(official_value, field=f"official.{path}")
            except vre.EvidenceError:
                all_valid_iso = False
        else:
            all_valid_iso = False
    result["excluded_values"]["all_paths_present"] = all_present
    result["excluded_values"]["all_strings"] = all_strings
    result["excluded_values"]["all_valid_iso_datetime"] = all_valid_iso
    if not (all_present and all_strings and all_valid_iso):
        return result

    try:
        candidate_semantic_sha = hashlib.sha256(semantic_json_bytes(candidate_semantic)).hexdigest()
        official_semantic_sha = hashlib.sha256(semantic_json_bytes(official_semantic)).hexdigest()
    except (TypeError, ValueError):
        return result
    result["candidate_semantic_sha256"] = candidate_semantic_sha
    result["official_semantic_sha256"] = official_semantic_sha
    result["semantic_equal"] = (
        candidate_semantic == official_semantic
        and candidate_semantic_sha == official_semantic_sha
    )
    return result


def canonical_official_path(repo_root: Path, symbol: str, target_date: str) -> Path:
    if not re.fullmatch(r"\d{6}", str(symbol)):
        raise ValueError("official symbol must be a six-digit A-share code")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(target_date)):
        raise ValueError("official target_date must use YYYY-MM-DD")
    canonical_dir = (repo_root / OFFICIAL_DAILY_DIR).resolve(strict=False)
    path = canonical_dir / f"{symbol}_{target_date}_facts.json"
    if path.name != f"{symbol}_{target_date}_facts.json":
        raise ValueError("official filename is not canonical")
    resolved_parent = path.parent.resolve(strict=False)
    if resolved_parent != canonical_dir:
        raise ValueError("official path parent is not canonical data/daily")
    repo_resolved = repo_root.resolve(strict=False)
    if repo_resolved not in path.resolve(strict=False).parents:
        raise ValueError("official path escapes repository")
    return path


def validate_official_path(path: Path, repo_root: Path, symbol: str, target_date: str) -> Path:
    canonical = canonical_official_path(repo_root, symbol, target_date)
    if path.resolve(strict=False) != canonical.resolve(strict=False):
        raise ValueError("official path must be derived from symbol and target_date")
    if path.exists() and path.is_symlink():
        raise ValueError("official path must not be a symlink")
    parent = path.parent
    if parent.exists() and parent.is_symlink():
        raise ValueError("official parent must not be a symlink")
    return canonical


def json_bytes(payload: dict[str, Any], *, sort_keys: bool = False) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=sort_keys) + "\n").encode("utf-8")


def _validator_summary(
    facts_pack: dict[str, Any],
    *,
    official_path: Path,
    target_date: str,
    validator: Callable[..., None] | None = None,
) -> dict[str, Any]:
    try:
        (validator or vrc.assert_facts_pack_valid)(
            facts_pack,
            facts_pack_path=str(official_path),
            date=target_date,
        )
    except Exception as exc:  # noqa: BLE001 - transaction records fail-closed validator evidence
        return {"status": "failed", "exception_type": type(exc).__name__, "message": str(exc)[:500]}
    return {"status": "passed"}


def parse_official_bytes(data: bytes | None, *, symbol: str, target_date: str) -> dict[str, Any] | None:
    if data is None:
        return None
    try:
        parsed = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"official JSON is invalid: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("official root must be an object")
    if str(parsed.get("symbol")) != str(symbol):
        raise ValueError("official symbol mismatch")
    if str(parsed.get("trade_date")) != str(target_date):
        raise ValueError("official trade_date mismatch")
    return parsed


def is_sealed_official(facts_pack: dict[str, Any] | None) -> bool:
    if not isinstance(facts_pack, dict):
        return False
    run = facts_pack.get("run") if isinstance(facts_pack.get("run"), dict) else {}
    return bool(facts_pack.get("sealed") is True or run.get("sealed") is True or run.get("status") == "sealed")


def is_manual_official(facts_pack: dict[str, Any] | None) -> bool:
    if not isinstance(facts_pack, dict):
        return False
    run = facts_pack.get("run") if isinstance(facts_pack.get("run"), dict) else {}
    return bool(
        facts_pack.get("manual") is True
        or facts_pack.get("official_manual") is True
        or run.get("manual") is True
        or run.get("official_write") == "manual"
        or run.get("status") == "manual"
    )


def _finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _truthy_missing(value: object) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, (list, tuple, set, dict, str)):
        return bool(value)
    return True


def evaluate_partial_write_policy(candidate: dict[str, Any]) -> PartialPolicyResult:
    quote = candidate.get("quote") if isinstance(candidate.get("quote"), dict) else {}
    quote_verification = (
        candidate.get("quote_verification") if isinstance(candidate.get("quote_verification"), dict) else {}
    )
    volume_ratio = candidate.get("volume_ratio") if isinstance(candidate.get("volume_ratio"), dict) else {}
    volume_verification = (
        volume_ratio.get("verification") if isinstance(volume_ratio.get("verification"), dict) else {}
    )
    missing = candidate.get("missing") if isinstance(candidate.get("missing"), dict) else {}
    needs = candidate.get("needs_manual_check") if isinstance(candidate.get("needs_manual_check"), dict) else {}

    missing_keys = {
        key
        for key, value in missing.items()
        if _truthy_missing(value)
    } | {
        key
        for key, value in needs.items()
        if _truthy_missing(value)
    }

    core_complete = all(_finite_number(quote.get(field)) for field in CORE_QUOTE_FIELDS)
    quote_ok = quote_verification.get("source_date") == candidate.get("trade_date") and quote_verification.get("status") not in {
        "conflict",
        "needs_manual_check",
        "date_mismatch",
    }
    turnover_ok = _finite_number(quote.get("turnover_rate")) and not _truthy_missing(needs.get("turnover_rate"))
    volume_status = volume_verification.get("status")
    volume_ok = (
        volume_status in VOLUME_RATIO_ALLOWED_STATUSES
        and volume_status not in VOLUME_RATIO_BLOCKED_STATUSES
        and volume_verification.get("method") not in (None, "")
        and not _truthy_missing(needs.get("volume_ratio"))
    )
    whitelist_only = missing_keys <= PARTIAL_MISSING_WHITELIST
    eligible = core_complete and quote_ok and turnover_ok and volume_ok and whitelist_only
    return PartialPolicyResult(
        eligible=eligible,
        reason_code="eligible_partial_official" if eligible else "partial_not_eligible_for_official",
        missing_keys=tuple(sorted(missing_keys)),
        needs_manual_review=bool(missing_keys),
    )


def _write_bytes_locked(
    output_path: Path,
    payload_bytes: bytes,
    *,
    lock_state: ofl.OfficialFactsLockState,
) -> tuple[bytes | None, str | None, dict[str, Any] | None]:
    lock_state.assert_held_for(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_file: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=str(output_path.parent),
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_file = Path(handle.name)
            handle.write(payload_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_file, output_path)
        post_write_error: dict[str, Any] | None = None
        dir_fd: int | None = None
        try:
            dir_fd = os.open(str(output_path.parent), os.O_DIRECTORY)
            os.fsync(dir_fd)
        except OSError as exc:
            post_write_error = {
                "type": type(exc).__name__,
                "message": str(exc)[:500],
                "stage": "directory_fsync",
            }
        finally:
            if dir_fd is not None:
                os.close(dir_fd)
        try:
            final_bytes, final_sha = ofl.read_current_official(output_path, lock_state=lock_state)
        except Exception as exc:  # noqa: BLE001 - official already changed; preserve structured evidence
            error = {
                "type": type(exc).__name__,
                "message": str(exc)[:500],
                "stage": "post_write_read",
            }
            if post_write_error is not None:
                error["previous_error"] = post_write_error
            return None, None, error
        return final_bytes, final_sha, post_write_error
    finally:
        if tmp_file is not None:
            tmp_file.unlink(missing_ok=True)


def promote_candidate_to_official(
    *,
    repo_root: Path,
    official_path: Path,
    candidate: dict[str, Any],
    candidate_bytes: bytes,
    symbol: str,
    target_date: str,
    expected_sha256: str | None,
    lock_dir: Path | None = None,
    validator: Callable[..., None] | None = None,
    enforce_canonical_path: bool = True,
) -> OfficialWriteResult:
    if enforce_canonical_path:
        official_path = validate_official_path(official_path, repo_root, symbol, target_date)
    elif official_path.exists() and official_path.is_symlink():
        raise ValueError("official path must not be a symlink")
    candidate_sha = ofl.sha256_bytes(candidate_bytes)
    partial_policy = evaluate_partial_write_policy(candidate)
    run = candidate.get("run") if isinstance(candidate.get("run"), dict) else {}
    candidate_status = run.get("status")

    with ofl.official_facts_lock(official_path, lock_dir=lock_dir) as lock_state:
        try:
            official_bytes, before_sha = ofl.read_locked_official(
                official_path,
                expected_sha256=expected_sha256,
                lock_state=lock_state,
            )
            existing = parse_official_bytes(official_bytes, symbol=symbol, target_date=target_date)
        except Exception as exc:  # noqa: BLE001
            return OfficialWriteResult(
                write_action="conflict_blocked",
                outcome="needs_manual_review",
                reason_code="official_conflict" if isinstance(exc, ofl.OfficialFactsChangedError) else "official_invalid",
                official_path=official_path,
                official_exists_before=expected_sha256 is not None,
                official_sha256_before=expected_sha256,
                official_sha256_after=expected_sha256,
                candidate_sha256=candidate_sha,
                partial_write_policy={**partial_policy.__dict__},
                official_validator_before={"status": "not_run", "message": str(exc)[:500]},
                official_validator_after={"status": "not_run"},
            )
        exists_before = official_bytes is not None
        if is_sealed_official(existing):
            return OfficialWriteResult(
                "sealed_blocked",
                "skipped",
                "sealed_exists",
                official_path,
                exists_before,
                before_sha,
                before_sha,
                candidate_sha,
                {**partial_policy.__dict__},
                {"status": "not_run"},
                {"status": "not_run"},
            )
        if is_manual_official(existing):
            return OfficialWriteResult(
                "manual_blocked",
                "skipped",
                "manual_exists",
                official_path,
                exists_before,
                before_sha,
                before_sha,
                candidate_sha,
                {**partial_policy.__dict__},
                {"status": "not_run"},
                {"status": "not_run"},
            )
        validator_before = _validator_summary(
            candidate,
            official_path=official_path,
            target_date=target_date,
            validator=validator,
        )
        if validator_before.get("status") != "passed":
            return OfficialWriteResult(
                "not_eligible",
                "needs_manual_review",
                "validator_failed",
                official_path,
                exists_before,
                before_sha,
                before_sha,
                candidate_sha,
                {**partial_policy.__dict__},
                validator_before,
                {"status": "not_run"},
            )
        if candidate_status == "partial" and not partial_policy.eligible:
            return OfficialWriteResult(
                "not_eligible",
                "needs_manual_review",
                "partial_not_eligible_for_official",
                official_path,
                exists_before,
                before_sha,
                before_sha,
                candidate_sha,
                {**partial_policy.__dict__},
                validator_before,
                {"status": "not_run"},
            )
        if candidate_status not in {"success", "partial"}:
            return OfficialWriteResult(
                "not_eligible",
                "needs_manual_review",
                "candidate_not_eligible_for_official",
                official_path,
                exists_before,
                before_sha,
                before_sha,
                candidate_sha,
                {**partial_policy.__dict__},
                validator_before,
                {"status": "not_run"},
            )
        if official_bytes == candidate_bytes:
            return OfficialWriteResult(
                "identical_noop",
                "partial" if candidate_status == "partial" else "success",
                "official_already_identical",
                official_path,
                exists_before,
                before_sha,
                before_sha,
                candidate_sha,
                {**partial_policy.__dict__},
                validator_before,
                validator_before,
                False,
                True,
            )
        if official_bytes is not None:
            official_validator = _validator_summary(
                existing,
                official_path=official_path,
                target_date=target_date,
                validator=validator,
            )
            comparison = build_semantic_comparison(
                candidate=candidate,
                official=existing,
                candidate_bytes=candidate_bytes,
                official_bytes=official_bytes,
                symbol=symbol,
                target_date=target_date,
            )
            if (
                official_validator.get("status") == "passed"
                and comparison.get("semantic_equal") is True
            ):
                return OfficialWriteResult(
                    "semantic_noop",
                    "official_unchanged",
                    "official_semantically_identical",
                    official_path,
                    exists_before,
                    before_sha,
                    before_sha,
                    candidate_sha,
                    {**partial_policy.__dict__},
                    validator_before,
                    official_validator,
                    False,
                    False,
                    None,
                    comparison,
                )
            return OfficialWriteResult(
                "conflict_blocked",
                "needs_manual_review",
                "official_conflict",
                official_path,
                exists_before,
                before_sha,
                before_sha,
                candidate_sha,
                {**partial_policy.__dict__},
                validator_before,
                official_validator,
                comparison=comparison,
            )
        final_bytes, after_sha, post_write_error = _write_bytes_locked(
            official_path,
            candidate_bytes,
            lock_state=lock_state,
        )
        official_changed = True
        bytes_equal = final_bytes == candidate_bytes if final_bytes is not None else False
        if post_write_error is not None:
            return OfficialWriteResult(
                "created_postcheck_failed",
                "needs_manual_review",
                "official_written_postcheck_failed",
                official_path,
                exists_before,
                before_sha,
                after_sha,
                candidate_sha,
                {**partial_policy.__dict__},
                validator_before,
                {"status": "not_run", "message": post_write_error.get("message")},
                official_changed,
                bytes_equal,
                post_write_error,
            )
        if not bytes_equal or after_sha is None:
            return OfficialWriteResult(
                "created_postcheck_failed",
                "needs_manual_review",
                "official_written_bytes_mismatch",
                official_path,
                exists_before,
                before_sha,
                after_sha,
                candidate_sha,
                {**partial_policy.__dict__},
                validator_before,
                {"status": "not_run"},
                official_changed,
                False,
                {
                    "type": "OfficialBytesMismatch",
                    "message": "written official facts do not match candidate bytes",
                    "stage": "post_write_bytes_check",
                },
            )
        try:
            final_pack = parse_official_bytes(final_bytes, symbol=symbol, target_date=target_date)
        except Exception as exc:  # noqa: BLE001 - official already changed; preserve structured evidence
            validator_after = {
                "status": "failed",
                "exception_type": type(exc).__name__,
                "message": str(exc)[:500],
            }
            return OfficialWriteResult(
                "created_postcheck_failed",
                "needs_manual_review",
                "official_written_postcheck_failed",
                official_path,
                exists_before,
                before_sha,
                after_sha,
                candidate_sha,
                {**partial_policy.__dict__},
                validator_before,
                validator_after,
                official_changed,
                bytes_equal,
                {
                    "type": type(exc).__name__,
                    "message": str(exc)[:500],
                    "stage": "post_write_parse",
                },
            )
        validator_after = _validator_summary(
            final_pack or {},
            official_path=official_path,
            target_date=target_date,
            validator=validator,
        )
        if validator_after.get("status") != "passed":
            return OfficialWriteResult(
                "created_postcheck_failed",
                "needs_manual_review",
                "official_written_postcheck_failed",
                official_path,
                exists_before,
                before_sha,
                after_sha,
                candidate_sha,
                {**partial_policy.__dict__},
                validator_before,
                validator_after,
                official_changed,
                bytes_equal,
                {
                    "type": str(validator_after.get("exception_type") or "ValidatorError"),
                    "message": str(validator_after.get("message") or "post-write official validator failed")[:500],
                    "stage": "post_write_validator",
                },
            )
        return OfficialWriteResult(
            "created",
            "partial" if candidate_status == "partial" else "success",
            "official_written_partial" if candidate_status == "partial" else "official_written",
            official_path,
            exists_before,
            before_sha,
            after_sha,
            candidate_sha,
            {**partial_policy.__dict__},
            validator_before,
            validator_after,
            official_changed,
            bytes_equal,
            None,
        )
