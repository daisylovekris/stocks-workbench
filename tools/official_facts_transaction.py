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
SEMANTIC_COMPARISON_V1_MODE = "approved_timestamp_paths_v1"
SEMANTIC_COMPARISON_V2_MODE = "symmetric_timestamp_leaf_paths_v2"
SEMANTIC_COMPARISON_V3_MODE = "method_profile_timestamp_paths_v3"
SEMANTIC_COMPARISON_MODE = SEMANTIC_COMPARISON_V3_MODE
TIMESTAMP_LEAF_NAMES = frozenset({"generated_at", "fetched_at"})
REQUIRED_V2_TIMESTAMP_PATHS = frozenset(
    {
        "generated_at",
        "quote_verification.fetched_at",
        "run.fetched_at",
        "volume_ratio.five_day_volume_check.fetched_at",
        "volume_ratio.verification.fetched_at",
    }
)
METHOD_PROFILE_SCHEMA_VERSION = "semantic_noop_timestamp_profiles_v0.3"
METHOD_PROFILE_REGISTRY_SCHEMA_VERSION = "semantic_noop_timestamp_profile_registry_v0.1"
REPO_ROOT = Path(__file__).resolve().parents[1]
METHOD_PROFILE_CONFIG_PATH = REPO_ROOT / "rules" / "semantic_noop_timestamp_profiles_v0.3.json"
METHOD_PROFILE_REGISTRY_PATH = REPO_ROOT / "rules" / "semantic_noop_timestamp_profile_registry_v0.1.json"
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
PROFILE_CONFIG_TOP_LEVEL_FIELDS = frozenset(
    {
        "schema_version",
        "profile_version",
        "comparison_mode",
        "common_required_paths",
        "allow_list_index_paths",
        "profiles",
    }
)
ACTIVE_PROFILE_FIELDS = frozenset(
    {
        "required_paths",
        "optional_paths",
        "optional_presence_conditions",
        "allow_list_index_paths",
    }
)
BLOCKED_PROFILE_FIELDS = frozenset(
    {
        "profile_status",
        "reason",
        "required_paths",
        "optional_paths",
        "optional_presence_conditions",
        "allow_list_index_paths",
    }
)
PROFILE_CONDITION_FIELDS = frozenset({"present_when_parent"})
REGISTRY_TOP_LEVEL_FIELDS = frozenset({"schema_version", "active_profile_version", "profiles"})
REGISTRY_ENTRY_FIELDS = frozenset({"path", "comparison_mode", "profile_sha256", "status"})
PROFILE_STATUS_ALLOWED = frozenset({"active", "frozen"})


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    """Deterministic canonical JSON bytes used for profile identity hashing."""

    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class MethodProfileConfig:
    profile_version: str
    comparison_mode: str
    common_required_paths: tuple[str, ...]
    allow_list_index_paths: bool
    profiles: dict[str, dict[str, Any]]
    sha256: str


def _validate_profile_path_list(paths: object, *, label: str) -> list[str]:
    if not isinstance(paths, list) or len(paths) != len(set(paths)):
        raise ValueError(f"{label} must be a duplicate-free list")
    for path in paths:
        if not isinstance(path, str) or not path:
            raise ValueError(f"{label} entries must be non-empty strings")
        if "[" in path or "]" in path:
            raise ValueError(f"{label} must not contain list index paths: {path}")
    return list(paths)


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is not allowed: {value}")


def _parse_strict_json_object(raw: bytes, *, label: str) -> dict[str, Any]:
    """Parse JSON with duplicate-key rejection at every nesting level."""

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{label}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        parsed = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{label} JSON is invalid: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} root must be an object")
    return parsed


@dataclass(frozen=True)
class MethodProfileRegistryEntry:
    version: str
    path: Path
    comparison_mode: str
    profile_sha256: str
    status: str


@dataclass(frozen=True)
class MethodProfileRegistry:
    schema_version: str
    active_profile_version: str
    entries: dict[str, MethodProfileRegistryEntry]
    path: Path


def _validate_registry_config_path(value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("registry profile path must be a non-empty string")
    raw = Path(value)
    if raw.is_absolute():
        raise ValueError("registry profile path must be relative")
    if raw.parts != ("rules", raw.name) or raw.suffix != ".json":
        raise ValueError("registry profile path must be rules/<file>.json without traversal")
    rules_dir = (REPO_ROOT / "rules").resolve(strict=False)
    resolved = (REPO_ROOT / raw).resolve(strict=False)
    if resolved.parent != rules_dir:
        raise ValueError("registry profile path must resolve inside rules/ without symlink escape")
    return resolved


def load_method_profile_config(path: Path | None = None) -> MethodProfileConfig:
    """Load and strictly validate a v3 method profile config."""

    config_path = Path(path).resolve(strict=False) if path is not None else METHOD_PROFILE_CONFIG_PATH
    try:
        raw = config_path.read_bytes()
    except OSError as exc:
        raise ValueError(f"method profile config is not readable: {exc}") from exc
    parsed = _parse_strict_json_object(raw, label="method profile config")
    unknown_top = set(parsed) - PROFILE_CONFIG_TOP_LEVEL_FIELDS
    if unknown_top:
        raise ValueError(f"method profile config has unknown top-level fields: {sorted(unknown_top)}")
    if parsed.get("schema_version") != METHOD_PROFILE_SCHEMA_VERSION:
        raise ValueError("method profile config schema_version is invalid")
    profile_version = parsed.get("profile_version")
    if not isinstance(profile_version, str) or not profile_version:
        raise ValueError("method profile config profile_version is invalid")
    if parsed.get("comparison_mode") != SEMANTIC_COMPARISON_V3_MODE:
        raise ValueError("method profile config comparison_mode is invalid")
    common = _validate_profile_path_list(parsed.get("common_required_paths"), label="common_required_paths")
    if not common:
        raise ValueError("common_required_paths must not be empty")
    if parsed.get("allow_list_index_paths") is not False:
        raise ValueError("method profile config allow_list_index_paths must be boolean false")
    raw_profiles = parsed.get("profiles")
    if not isinstance(raw_profiles, dict) or not raw_profiles:
        raise ValueError("method profile config profiles must be a non-empty object")
    profiles: dict[str, dict[str, Any]] = {}
    for method, profile in raw_profiles.items():
        if not isinstance(method, str) or not method or not isinstance(profile, dict):
            raise ValueError(f"profile entry for {method!r} must be an object")
        profile_status = profile.get("profile_status", "active")
        if profile_status == "active":
            allowed_fields = ACTIVE_PROFILE_FIELDS
        elif profile_status == "blocked":
            allowed_fields = BLOCKED_PROFILE_FIELDS
        else:
            raise ValueError(f"profile {method} profile_status must be active or blocked")
        unknown_profile = set(profile) - allowed_fields
        if unknown_profile:
            raise ValueError(f"profile {method} has unknown fields: {sorted(unknown_profile)}")
        required = _validate_profile_path_list(profile.get("required_paths"), label=f"{method}.required_paths")
        optional = _validate_profile_path_list(profile.get("optional_paths"), label=f"{method}.optional_paths")
        if set(required) & set(optional):
            raise ValueError(f"profile {method} required and optional paths overlap")
        conditions = profile.get("optional_presence_conditions")
        if not isinstance(conditions, dict):
            raise ValueError(f"profile {method} optional_presence_conditions must be an object")
        if set(conditions) != set(optional):
            raise ValueError(f"profile {method} optional_presence_conditions must cover exactly optional_paths")
        for condition_path, condition in conditions.items():
            if not isinstance(condition, dict) or set(condition) != PROFILE_CONDITION_FIELDS:
                raise ValueError(
                    f"profile {method} condition for {condition_path} must contain exactly present_when_parent"
                )
            parent = condition.get("present_when_parent")
            if not isinstance(parent, str) or not parent:
                raise ValueError(
                    f"profile {method} condition {condition_path} present_when_parent must be a non-empty string"
                )
        if profile.get("allow_list_index_paths") is not False:
            raise ValueError(f"profile {method} allow_list_index_paths must be boolean false")
        if profile_status == "active":
            missing_common = sorted(set(common) - set(required))
            if missing_common:
                raise ValueError(
                    f"profile {method} required_paths must include common_required_paths; missing: {missing_common}"
                )
            if not required:
                raise ValueError(f"active profile {method} required_paths must not be empty")
            normalized: dict[str, Any] = {
                "profile_status": "active",
                "required_paths": required,
                "optional_paths": optional,
                "optional_presence_conditions": {key: conditions[key] for key in sorted(conditions)},
                "allow_list_index_paths": False,
            }
        else:
            if required:
                raise ValueError(f"blocked profile {method} required_paths must be empty")
            if optional:
                raise ValueError(f"blocked profile {method} optional_paths must be empty")
            if conditions:
                raise ValueError(f"blocked profile {method} optional_presence_conditions must be empty")
            reason = profile.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError(f"blocked profile {method} requires a non-empty string reason")
            normalized = {
                "profile_status": "blocked",
                "required_paths": [],
                "optional_paths": [],
                "optional_presence_conditions": {},
                "allow_list_index_paths": False,
                "reason": reason,
            }
        profiles[method] = normalized
    sha256 = hashlib.sha256(canonical_json_bytes(parsed)).hexdigest()
    return MethodProfileConfig(
        profile_version=profile_version,
        comparison_mode=str(parsed.get("comparison_mode")),
        common_required_paths=tuple(common),
        allow_list_index_paths=False,
        profiles=profiles,
        sha256=sha256,
    )


def load_method_profile_registry(path: Path | None = None) -> MethodProfileRegistry:
    """Load and strictly validate the method profile version registry."""

    registry_path = Path(path).resolve(strict=False) if path is not None else METHOD_PROFILE_REGISTRY_PATH
    try:
        raw = registry_path.read_bytes()
    except OSError as exc:
        raise ValueError(f"method profile registry is not readable: {exc}") from exc
    parsed = _parse_strict_json_object(raw, label="method profile registry")
    unknown_top = set(parsed) - REGISTRY_TOP_LEVEL_FIELDS
    if unknown_top:
        raise ValueError(f"method profile registry has unknown top-level fields: {sorted(unknown_top)}")
    if parsed.get("schema_version") != METHOD_PROFILE_REGISTRY_SCHEMA_VERSION:
        raise ValueError("method profile registry schema_version is invalid")
    active_version = parsed.get("active_profile_version")
    if not isinstance(active_version, str) or not active_version:
        raise ValueError("method profile registry active_profile_version is invalid")
    raw_entries = parsed.get("profiles")
    if not isinstance(raw_entries, dict) or not raw_entries:
        raise ValueError("method profile registry profiles must be a non-empty object")
    entries: dict[str, MethodProfileRegistryEntry] = {}
    seen_sha: dict[str, str] = {}
    for version, entry in raw_entries.items():
        if not isinstance(version, str) or not version or not isinstance(entry, dict):
            raise ValueError(f"registry entry for {version!r} must be an object")
        unknown_entry = set(entry) - REGISTRY_ENTRY_FIELDS
        if unknown_entry:
            raise ValueError(f"registry entry {version} has unknown fields: {sorted(unknown_entry)}")
        config_path = _validate_registry_config_path(entry.get("path"))
        comparison_mode = entry.get("comparison_mode")
        if comparison_mode != SEMANTIC_COMPARISON_V3_MODE:
            raise ValueError(f"registry entry {version} comparison_mode is invalid")
        profile_sha256 = entry.get("profile_sha256")
        if not isinstance(profile_sha256, str) or _SHA256_RE.fullmatch(profile_sha256) is None:
            raise ValueError(f"registry entry {version} profile_sha256 is invalid")
        status = entry.get("status")
        if status not in PROFILE_STATUS_ALLOWED:
            raise ValueError(f"registry entry {version} status must be active or frozen")
        if profile_sha256 in seen_sha:
            raise ValueError(f"registry profile SHA {profile_sha256} maps to multiple versions")
        seen_sha[profile_sha256] = version
        entries[version] = MethodProfileRegistryEntry(
            version=version,
            path=config_path,
            comparison_mode=comparison_mode,
            profile_sha256=profile_sha256,
            status=status,
        )
    if active_version not in entries:
        raise ValueError(f"method profile registry active_profile_version {active_version} is not registered")
    if entries[active_version].status != "active":
        raise ValueError("method profile registry active_profile_version must have status active")
    for version, entry in entries.items():
        config = load_method_profile_config(entry.path)
        if config.profile_version != version:
            raise ValueError(f"registry entry {version} profile_version does not match config")
        if config.comparison_mode != entry.comparison_mode:
            raise ValueError(f"registry entry {version} comparison_mode does not match config")
        if config.sha256 != entry.profile_sha256:
            raise ValueError(f"registry entry {version} profile_sha256 does not match canonical config SHA")
    return MethodProfileRegistry(
        schema_version=str(parsed.get("schema_version")),
        active_profile_version=active_version,
        entries=entries,
        path=registry_path,
    )


def resolve_profile_for_version(
    version: object,
    *,
    registry_path: Path | None = None,
    for_new_write: bool = False,
) -> tuple[MethodProfileConfig, MethodProfileRegistryEntry]:
    """Resolve a profile config by version from the registry.

    Historical recompute resolves the recorded ``profile_version`` (active or
    frozen); new writes require the registry's active version with status
    ``active``.
    """

    if not isinstance(version, str) or not version:
        raise ValueError("profile_version must be a non-empty string")
    registry = load_method_profile_registry(registry_path)
    entry = registry.entries.get(version)
    if entry is None:
        raise ValueError(f"unknown profile_version: {version}")
    if for_new_write and entry.status != "active":
        raise ValueError(f"profile_version {version} is {entry.status}; new writes require an active profile")
    config = load_method_profile_config(entry.path)
    if config.profile_version != version or config.sha256 != entry.profile_sha256:
        raise ValueError(f"profile_version {version} config identity mismatch")
    return config, entry


def active_method_profile_config(
    registry_path: Path | None = None,
) -> tuple[MethodProfileConfig, MethodProfileRegistryEntry]:
    """Resolve the registry's active profile version for new Phase B writes."""

    registry = load_method_profile_registry(registry_path)
    return resolve_profile_for_version(
        registry.active_profile_version,
        registry_path=registry_path,
        for_new_write=True,
    )


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


def _json_path_segments(path: str) -> list[str]:
    """Split a JSON path into segments, supporting ``a.b[0].c`` notation."""

    segments: list[str] = []
    buffer = ""
    index = 0
    while index < len(path):
        char = path[index]
        if char == ".":
            if buffer:
                segments.append(buffer)
                buffer = ""
            index += 1
        elif char == "[":
            if buffer:
                segments.append(buffer)
                buffer = ""
            end = path.find("]", index + 1)
            if end < 0:
                raise ValueError(f"invalid JSON path bracket: {path}")
            segments.append(path[index + 1 : end])
            index = end + 1
        else:
            buffer += char
            index += 1
    if buffer:
        segments.append(buffer)
    return segments


def _get_json_path_value(payload: dict[str, Any], path: str) -> object:
    current: object = payload
    for segment in _json_path_segments(path):
        if isinstance(current, dict):
            if segment not in current:
                raise KeyError(path)
            current = current[segment]
        elif isinstance(current, list):
            try:
                current = current[int(segment)]
            except (ValueError, IndexError) as exc:
                raise KeyError(path) from exc
        else:
            raise KeyError(path)
    return current


def _pop_json_path(payload: dict[str, Any], path: str) -> bool:
    segments = _json_path_segments(path)
    current: object = payload
    for segment in segments[:-1]:
        if isinstance(current, dict):
            if segment not in current:
                return False
            current = current[segment]
        elif isinstance(current, list):
            try:
                current = current[int(segment)]
            except (ValueError, IndexError):
                return False
        else:
            return False
    last = segments[-1]
    if isinstance(current, dict):
        if last not in current:
            return False
        current.pop(last)
        return True
    if isinstance(current, list):
        try:
            del current[int(last)]
            return True
        except (ValueError, IndexError):
            return False
    return False


def discover_timestamp_leaf_paths(payload: dict[str, Any]) -> list[str]:
    """Return the sorted unique JSON paths of timestamp leaves in ``payload``.

    A timestamp leaf is any key named ``generated_at`` or ``fetched_at``,
    discovered recursively through nested objects and lists.
    """

    paths: set[str] = set()

    def walk(node: object, prefix: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                if key in TIMESTAMP_LEAF_NAMES:
                    paths.add(path)
                else:
                    walk(value, path)
        elif isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{prefix}[{index}]")

    walk(payload, "")
    return sorted(paths)


def build_semantic_comparison_v1(
    *,
    candidate: dict[str, Any],
    official: dict[str, Any],
    candidate_bytes: bytes,
    official_bytes: bytes,
    symbol: str,
    target_date: str,
) -> dict[str, Any]:
    """Legacy v1 comparison: exclude only the fixed six approved timestamp paths."""

    candidate_raw_sha = hashlib.sha256(candidate_bytes).hexdigest()
    official_raw_sha = hashlib.sha256(official_bytes).hexdigest()
    result: dict[str, Any] = {
        "comparison_mode": SEMANTIC_COMPARISON_V1_MODE,
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


def build_semantic_comparison_v2(
    *,
    candidate: dict[str, Any],
    official: dict[str, Any],
    candidate_bytes: bytes,
    official_bytes: bytes,
    symbol: str,
    target_date: str,
) -> dict[str, Any]:
    """Symmetric timestamp-leaf comparison used by new Phase B writes.

    Both payloads must contain exactly the same sorted set of timestamp leaf
    paths (keys named ``generated_at`` or ``fetched_at``); every value must be
    a timezone-aware datetime string.  Those symmetric paths are then removed
    before the semantic payloads are hashed, so any non-timestamp difference
    still fails the comparison.
    """

    candidate_raw_sha = hashlib.sha256(candidate_bytes).hexdigest()
    official_raw_sha = hashlib.sha256(official_bytes).hexdigest()
    result: dict[str, Any] = {
        "comparison_mode": SEMANTIC_COMPARISON_V2_MODE,
        "candidate_raw_sha256": candidate_raw_sha,
        "official_raw_sha256": official_raw_sha,
        "candidate_semantic_sha256": None,
        "official_semantic_sha256": None,
        "excluded_json_paths": [],
        "excluded_values": {
            "candidate_paths": [],
            "official_paths": [],
            "candidate_types": {},
            "official_types": {},
            "path_sets_equal": False,
            "required_paths_present": False,
            "candidate_missing_required_paths": [],
            "official_missing_required_paths": [],
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

    candidate_paths = discover_timestamp_leaf_paths(candidate)
    official_paths = discover_timestamp_leaf_paths(official)
    result["excluded_values"]["candidate_paths"] = candidate_paths
    result["excluded_values"]["official_paths"] = official_paths
    result["excluded_values"]["candidate_types"] = {
        path: type(_get_json_path_value(candidate, path)).__name__ for path in candidate_paths
    }
    result["excluded_values"]["official_types"] = {
        path: type(_get_json_path_value(official, path)).__name__ for path in official_paths
    }
    candidate_missing_required = sorted(REQUIRED_V2_TIMESTAMP_PATHS - set(candidate_paths))
    official_missing_required = sorted(REQUIRED_V2_TIMESTAMP_PATHS - set(official_paths))
    result["excluded_values"]["candidate_missing_required_paths"] = candidate_missing_required
    result["excluded_values"]["official_missing_required_paths"] = official_missing_required
    result["excluded_values"]["required_paths_present"] = (
        not candidate_missing_required and not official_missing_required
    )
    if candidate_paths != official_paths:
        return result
    if not result["excluded_values"]["required_paths_present"]:
        return result
    result["excluded_values"]["path_sets_equal"] = True
    result["excluded_json_paths"] = candidate_paths

    all_strings = True
    for path in candidate_paths:
        if not isinstance(_get_json_path_value(candidate, path), str) or not isinstance(
            _get_json_path_value(official, path), str
        ):
            all_strings = False
            break
    result["excluded_values"]["all_strings"] = all_strings
    if not all_strings:
        return result

    all_valid_iso = True
    for path in candidate_paths:
        try:
            vre.parse_timezone_datetime(_get_json_path_value(candidate, path), field=f"candidate.{path}")
            vre.parse_timezone_datetime(_get_json_path_value(official, path), field=f"official.{path}")
        except vre.EvidenceError:
            all_valid_iso = False
            break
    result["excluded_values"]["all_valid_iso_datetime"] = all_valid_iso
    if not all_valid_iso:
        return result

    candidate_semantic = copy.deepcopy(candidate)
    official_semantic = copy.deepcopy(official)
    for path in candidate_paths:
        if not (_pop_json_path(candidate_semantic, path) and _pop_json_path(official_semantic, path)):
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


def build_semantic_comparison_v3(
    *,
    candidate: dict[str, Any],
    official: dict[str, Any],
    candidate_bytes: bytes,
    official_bytes: bytes,
    symbol: str,
    target_date: str,
    profile_version: str | None = None,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    """Method-aware profile comparison used by new Phase B writes.

    The legal timestamp exclusion set is derived exclusively from the
    version-controlled profile config for the payloads' shared
    ``volume_ratio.verification.method``.  A missing required path, any
    timestamp leaf outside the authorized profile (including list-index
    paths), asymmetric discovered sets, or invalid datetime values all fail
    closed with ``semantic_equal=false`` and no valid semantic SHA.
    """

    if profile_version is None:
        config, _entry = active_method_profile_config(registry_path)
    else:
        config, _entry = resolve_profile_for_version(
            profile_version,
            registry_path=registry_path,
            for_new_write=False,
        )
    candidate_raw_sha = hashlib.sha256(candidate_bytes).hexdigest()
    official_raw_sha = hashlib.sha256(official_bytes).hexdigest()
    result: dict[str, Any] = {
        "comparison_mode": SEMANTIC_COMPARISON_V3_MODE,
        "profile_version": config.profile_version,
        "profile_sha256": config.sha256,
        "verification_method": None,
        "required_paths": [],
        "optional_paths": [],
        "candidate_discovered_paths": [],
        "official_discovered_paths": [],
        "candidate_missing_required_paths": [],
        "official_missing_required_paths": [],
        "candidate_extra_paths": [],
        "official_extra_paths": [],
        "all_values_valid_timezone_datetime": False,
        "candidate_raw_sha256": candidate_raw_sha,
        "official_raw_sha256": official_raw_sha,
        "candidate_semantic_sha256": None,
        "official_semantic_sha256": None,
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

    candidate_vr = candidate.get("volume_ratio") if isinstance(candidate.get("volume_ratio"), dict) else {}
    official_vr = official.get("volume_ratio") if isinstance(official.get("volume_ratio"), dict) else {}
    candidate_verification = (
        candidate_vr.get("verification") if isinstance(candidate_vr.get("verification"), dict) else {}
    )
    official_verification = (
        official_vr.get("verification") if isinstance(official_vr.get("verification"), dict) else {}
    )
    candidate_method = candidate_verification.get("method")
    official_method = official_verification.get("method")
    if not isinstance(candidate_method, str) or candidate_method != official_method:
        if isinstance(candidate_method, str):
            result["verification_method"] = candidate_method
        return result
    result["verification_method"] = candidate_method

    profile = config.profiles.get(candidate_method)
    if profile is None or profile.get("profile_status") != "active":
        return result
    required = profile["required_paths"]
    optional = profile["optional_paths"]
    conditions = profile["optional_presence_conditions"]
    result["required_paths"] = list(required)
    result["optional_paths"] = list(optional)

    candidate_paths = discover_timestamp_leaf_paths(candidate)
    official_paths = discover_timestamp_leaf_paths(official)
    result["candidate_discovered_paths"] = candidate_paths
    result["official_discovered_paths"] = official_paths
    if any("[" in path for path in candidate_paths) or any("[" in path for path in official_paths):
        return result

    candidate_missing = sorted(set(required) - set(candidate_paths))
    official_missing = sorted(set(required) - set(official_paths))
    result["candidate_missing_required_paths"] = candidate_missing
    result["official_missing_required_paths"] = official_missing
    if candidate_missing or official_missing:
        return result

    def legal_set(payload: dict[str, Any]) -> set[str]:
        legal = set(required)
        for opt in optional:
            condition = conditions.get(opt)
            if not isinstance(condition, dict):
                continue
            parent = condition.get("present_when_parent")
            if isinstance(parent, str):
                try:
                    if isinstance(_get_json_path_value(payload, parent), dict):
                        legal.add(opt)
                except KeyError:
                    pass
        return legal

    candidate_legal = legal_set(candidate)
    official_legal = legal_set(official)
    candidate_extra = sorted(set(candidate_paths) - candidate_legal)
    official_extra = sorted(set(official_paths) - official_legal)
    result["candidate_extra_paths"] = candidate_extra
    result["official_extra_paths"] = official_extra
    if (
        candidate_extra
        or official_extra
        or candidate_paths != official_paths
        or candidate_legal != official_legal
    ):
        return result

    all_valid = True
    for path in candidate_paths:
        try:
            vre.parse_timezone_datetime(_get_json_path_value(candidate, path), field=f"candidate.{path}")
            vre.parse_timezone_datetime(_get_json_path_value(official, path), field=f"official.{path}")
        except vre.EvidenceError:
            all_valid = False
            break
    result["all_values_valid_timezone_datetime"] = all_valid
    if not all_valid:
        return result

    candidate_semantic = copy.deepcopy(candidate)
    official_semantic = copy.deepcopy(official)
    for path in candidate_paths:
        if not (_pop_json_path(candidate_semantic, path) and _pop_json_path(official_semantic, path)):
            return result
    try:
        candidate_semantic_sha = hashlib.sha256(semantic_json_bytes(candidate_semantic)).hexdigest()
        official_semantic_sha = hashlib.sha256(semantic_json_bytes(official_semantic)).hexdigest()
    except (TypeError, ValueError):
        return result
    result["candidate_semantic_sha256"] = candidate_semantic_sha
    result["official_semantic_sha256"] = official_semantic_sha
    result["semantic_equal"] = (
        candidate_semantic == official_semantic and candidate_semantic_sha == official_semantic_sha
    )
    return result


def build_semantic_comparison(
    *,
    candidate: dict[str, Any],
    official: dict[str, Any],
    candidate_bytes: bytes,
    official_bytes: bytes,
    symbol: str,
    target_date: str,
    comparison_mode: str | None = None,
    profile_version: str | None = None,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    """Dispatch semantic comparison to an explicit v1/v2/v3 mode.

    New Phase B writes default to ``SEMANTIC_COMPARISON_MODE`` (v3).  Historical
    v1 and v2 evidence is always recomputed with their recorded modes so legacy
    manifests are never reinterpreted with newer rules.
    """

    mode = comparison_mode or SEMANTIC_COMPARISON_MODE
    if mode == SEMANTIC_COMPARISON_V1_MODE:
        return build_semantic_comparison_v1(
            candidate=candidate,
            official=official,
            candidate_bytes=candidate_bytes,
            official_bytes=official_bytes,
            symbol=symbol,
            target_date=target_date,
        )
    if mode == SEMANTIC_COMPARISON_V2_MODE:
        return build_semantic_comparison_v2(
            candidate=candidate,
            official=official,
            candidate_bytes=candidate_bytes,
            official_bytes=official_bytes,
            symbol=symbol,
            target_date=target_date,
        )
    if mode == SEMANTIC_COMPARISON_V3_MODE:
        return build_semantic_comparison_v3(
            candidate=candidate,
            official=official,
            candidate_bytes=candidate_bytes,
            official_bytes=official_bytes,
            symbol=symbol,
            target_date=target_date,
            profile_version=profile_version,
            registry_path=registry_path,
        )
    raise ValueError(f"unknown semantic comparison mode: {mode}")


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
