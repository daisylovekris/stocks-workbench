#!/usr/bin/env python3
"""Phase B after-close runner for controlled daily facts generation.

The default mode remains non-official: it only gates a generator dry-run,
captures evidence, and writes runtime artifacts outside the repository.  Formal
official facts writes require explicit ``--write-official``.  This runner still
does not install or enable launchd, and it does not automatically modify review,
current card, index, or weekly documents.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time as dt_time, timedelta
from pathlib import Path
from typing import Any, Iterator
from zoneinfo import ZoneInfo

try:
    from tools import official_facts_lock as ofl
    from tools import official_facts_transaction as oft
    from tools import phase_b_completion as pbc
    from tools import safe_file_read as sfr
    from tools import validate_review_chain as vrc
except ModuleNotFoundError:  # pragma: no cover - direct execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools import official_facts_lock as ofl
    from tools import official_facts_transaction as oft
    from tools import phase_b_completion as pbc
    from tools import safe_file_read as sfr
    from tools import validate_review_chain as vrc


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_DIR = Path("~/Library/Application Support/Mimo-Lab/stocks-runtime").expanduser()
DEFAULT_CALENDAR = REPO_ROOT / "config" / "a_share_trading_calendar_2026.json"
DEFAULT_CUTOFF = "15:20"
BUSINESS_TIMEZONE = "Asia/Shanghai"
SCHEMA_VERSION = "runner_manifest_v0.2_phase_b"
SUMMARY_SCHEMA_VERSION = "runner_summary_v0.2_phase_b"
GENERATOR = REPO_ROOT / "tools" / "generate_daily_facts.py"
CANDIDATE_STDOUT_MARKER = "STOCKS_FACTS_CANDIDATE_JSON="
ALLOWED_FACTS_SCHEMAS = {"facts_pack_v0.2"}
REQUIRED_TOP_LEVEL_OBJECTS = (
    "quote",
    "quote_verification",
    "run",
    "volume_ratio",
    "missing",
    "needs_manual_check",
)
REQUIRED_QUOTE_FIELDS = (
    "open",
    "high",
    "low",
    "close",
    "prev_close",
    "pct_change",
    "amount",
    "turnover_rate",
)
KNOWN_GENERATOR_STATUSES = {
    "success",
    "partial",
    "date_mismatch",
    "network_error",
    "source_error",
    "schema_error",
    "failed",
    "error",
    "unknown",
}
SENSITIVE_CANDIDATE_KEYS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "token",
    "access_token",
    "api_key",
    "apikey",
    "key",
    "password",
    "secret",
    "signature",
    "aws_secret_access_key",
    "aws_access_key_id",
}
SENSITIVE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(
        r"(?im)^(\s*(?:Authorization|Proxy-Authorization|Cookie|Set-Cookie|X-API-Key)\s*:\s*)[^\n\r]*"
    ),
    re.compile(
        r"(?i)([?&](?:token|access_token|api_key|apikey|key|password|secret|signature)=)[^&\s#]*"
    ),
    re.compile(
        r"(?i)([\"'](?:[A-Z][A-Z0-9_]*(?:_TOKEN|_SECRET|_PASSWORD|_API_KEY)|"
        r"AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|authorization|proxy-authorization|cookie|set-cookie|"
        r"x-api-key|token|access_token|api_key|apikey|key|password|secret|signature)[\"']\s*:\s*)"
        r"(?:\"[^\"]*\"|'[^']*'|[^,}\]\s]+)"
    ),
    re.compile(
        r"(?i)\b((?:[A-Z][A-Z0-9_]*(?:_TOKEN|_SECRET|_PASSWORD|_API_KEY)|"
        r"AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|password|secret|api[_-]?key|apikey|token)\s*=\s*)"
        r"(?:\"[^\"]*\"|'[^']*'|[^\s&;,]+)"
    ),
)


class RunnerError(Exception):
    """Expected runner failure with a stable reason code."""

    def __init__(self, reason_code: str, message: str, *, stage: str = "gate") -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.stage = stage


@dataclass(frozen=True)
class TradingCalendar:
    path: Path
    schema_version: str
    timezone: str
    source: str
    calendar_version: str
    coverage_start: date
    coverage_end: date
    trading_days: tuple[date, ...]
    sha256: str

    def is_trading_day(self, value: date) -> bool:
        return value in set(self.trading_days)

    def metadata(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "source": self.source,
            "version": self.calendar_version,
            "sha256": self.sha256,
            "coverage_start": self.coverage_start.isoformat(),
            "coverage_end": self.coverage_end.isoformat(),
        }


@dataclass
class RunContext:
    args: argparse.Namespace
    runtime_dir: Path
    run_id: str
    run_dir: Path
    alerts_dir: Path
    manifest_path: Path
    summary_path: Path
    stdout_path: Path
    stderr_path: Path
    candidate_path: Path
    lock_path: Path


def parse_trade_date(value: object, *, field: str = "date") -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date string")
    parsed = date.fromisoformat(value)
    if value != parsed.isoformat():
        raise ValueError(f"{field} must be canonical ISO date")
    return parsed


def parse_now(value: str | None) -> datetime:
    if value is None:
        return datetime.now(ZoneInfo(BUSINESS_TIMEZONE))
    if value.endswith(("Z", "z")):
        raise RunnerError("invalid_now", "--now must use the explicit +08:00 offset")
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise RunnerError("invalid_now", "--now must be a valid ISO datetime with +08:00 offset") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RunnerError("invalid_now", "--now must include timezone offset +08:00")
    if parsed.utcoffset() != timedelta(hours=8):
        raise RunnerError("invalid_now", "--now timezone offset must be exactly +08:00")
    return parsed.astimezone(ZoneInfo(BUSINESS_TIMEZONE))


def parse_cutoff(value: str) -> dt_time:
    match = re.fullmatch(r"(\d{2}):(\d{2})", value)
    if not match:
        raise argparse.ArgumentTypeError("--cutoff must use HH:MM")
    hour = int(match.group(1))
    minute = int(match.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise argparse.ArgumentTypeError("--cutoff must be a real local time")
    return dt_time(hour=hour, minute=minute)


def sanitize_text(text: str) -> str:
    sanitized = text
    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(lambda m: (m.group(1) if m.groups() else "") + "[REDACTED]", sanitized)
    return sanitized


def normalize_runtime_dir(value: str | os.PathLike[str]) -> Path:
    runtime_dir = Path(value).expanduser().resolve(strict=False)
    repo_root = REPO_ROOT.resolve()
    if runtime_dir == repo_root or repo_root in runtime_dir.parents:
        raise RunnerError(
            "runtime_inside_repository",
            "runtime directory must be outside the repository",
            stage="gate",
        )
    return runtime_dir


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            tmp_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def load_calendar(path: Path) -> TradingCalendar:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RunnerError("calendar_invalid", f"calendar file is not readable: {exc}") from exc
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RunnerError("calendar_invalid", f"calendar JSON is invalid: {exc}") from exc
    if not isinstance(data, dict):
        raise RunnerError("calendar_invalid", "calendar root must be an object")
    if data.get("schema_version") != "0.1":
        raise RunnerError("calendar_invalid", "calendar schema_version must be 0.1")
    if data.get("timezone") != BUSINESS_TIMEZONE:
        raise RunnerError("calendar_invalid", "calendar timezone must be Asia/Shanghai")
    try:
        coverage_start = parse_trade_date(data.get("coverage_start"), field="coverage_start")
        coverage_end = parse_trade_date(data.get("coverage_end"), field="coverage_end")
    except ValueError as exc:
        raise RunnerError("calendar_invalid", str(exc)) from exc
    if coverage_start > coverage_end:
        raise RunnerError("calendar_invalid", "calendar coverage_start is after coverage_end")
    raw_days = data.get("trading_days")
    if not isinstance(raw_days, list) or not raw_days:
        raise RunnerError("calendar_invalid", "calendar trading_days must be a non-empty list")
    parsed_days: list[date] = []
    previous: date | None = None
    seen: set[date] = set()
    for index, item in enumerate(raw_days):
        try:
            current = parse_trade_date(item, field=f"trading_days[{index}]")
        except ValueError as exc:
            raise RunnerError("calendar_invalid", str(exc)) from exc
        if current in seen:
            raise RunnerError("calendar_invalid", f"duplicate trading day: {current.isoformat()}")
        if previous is not None and current <= previous:
            raise RunnerError("calendar_invalid", "trading_days must be strictly increasing")
        if current < coverage_start or current > coverage_end:
            raise RunnerError("calendar_invalid", f"trading day outside coverage: {current.isoformat()}")
        seen.add(current)
        parsed_days.append(current)
        previous = current
    return TradingCalendar(
        path=path,
        schema_version=str(data.get("schema_version")),
        timezone=str(data.get("timezone")),
        source=str(data.get("source") or ""),
        calendar_version=str(data.get("calendar_version") or ""),
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        trading_days=tuple(parsed_days),
        sha256=sha256_bytes(raw),
    )


def resolve_target(args: argparse.Namespace, now: datetime) -> tuple[str, date]:
    if args.mode == "today_after_close":
        if args.date:
            raise RunnerError("calendar_invalid", "--date is only accepted with historical_backfill")
        return args.mode, now.date()
    if args.mode == "historical_backfill":
        if not args.date:
            raise RunnerError("calendar_invalid", "historical_backfill requires --date")
        if not args.reason or not args.reason.strip():
            raise RunnerError("calendar_invalid", "historical_backfill requires non-empty --reason")
        try:
            return args.mode, parse_trade_date(args.date, field="--date")
        except ValueError as exc:
            raise RunnerError("calendar_invalid", str(exc)) from exc
    raise RunnerError("calendar_invalid", f"unknown mode: {args.mode}")


def official_path_for(symbol: str, target_date: date) -> Path:
    try:
        return oft.canonical_official_path(REPO_ROOT, symbol, target_date.isoformat())
    except ValueError as exc:
        raise RunnerError("official_path_invalid", str(exc), stage="gate") from exc


def is_sealed_facts(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return oft.is_sealed_official(data if isinstance(data, dict) else None)


def _manifest_timestamp(manifest: dict[str, Any]) -> datetime | None:
    for field in ("finished_at", "started_at"):
        value = manifest.get(field)
        if not isinstance(value, str):
            continue
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            continue
        if parsed.tzinfo is not None and parsed.utcoffset() is not None:
            return parsed
    return None


def scan_previous_runs(
    runtime_dir: Path,
    target_date: date,
    *,
    symbol: str,
    mode: str,
    write_official: bool = True,
    repo_root: Path | None = None,
    official_path: Path | None = None,
    official_lock_dir: Path | None = None,
) -> tuple[str | None, str | None, list[dict[str, str]]]:
    runs_dir = runtime_dir / "runs" / target_date.isoformat()
    diagnostics: list[dict[str, str]] = []
    if not runs_dir.exists():
        return None, None, diagnostics
    matching: list[tuple[datetime, str, dict[str, Any], Path]] = []
    for manifest_path in sorted(runs_dir.glob("*/manifest.json")):
        try:
            raw, safe_manifest_path = sfr.read_regular_file_beneath(
                manifest_path,
                root=runtime_dir,
                label="previous runner manifest",
            )
            assert raw is not None
            manifest = json.loads(raw.decode("utf-8"))
        except (sfr.SafeFileReadError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            diagnostics.append(
                {
                    "path": str(manifest_path),
                    "reason": sanitize_text(f"invalid manifest skipped: {type(exc).__name__}"),
                }
            )
            continue
        if not isinstance(manifest, dict):
            diagnostics.append({"path": str(manifest_path), "reason": "non-object manifest skipped"})
            continue
        if (
            manifest.get("target_date") != target_date.isoformat()
            or manifest.get("symbol") != symbol
            or manifest.get("mode") != mode
        ):
            if write_official:
                diagnostics.append(
                    {
                        "path": str(manifest_path),
                        "reason": "completion invalid: completion_identity_mismatch",
                    }
                )
            continue
        current_id = manifest.get("run_id")
        timestamp = _manifest_timestamp(manifest)
        if not isinstance(current_id, str) or not current_id or timestamp is None:
            diagnostics.append({"path": str(manifest_path), "reason": "incomplete matching manifest skipped"})
            continue
        matching.append((timestamp, current_id, manifest, safe_manifest_path))
    if not matching:
        return None, None, diagnostics
    matching.sort(key=lambda item: (item[0], item[1]))
    previous_run_id = matching[-1][1]
    if not write_official:
        return None, previous_run_id, diagnostics

    effective_repo_root = repo_root or REPO_ROOT
    effective_official_path = official_path or official_path_for(symbol, target_date)
    try:
        with ofl.official_facts_lock(effective_official_path, lock_dir=official_lock_dir) as lock_state:
            try:
                official_bytes, _safe_path = sfr.read_regular_file_beneath(
                    effective_official_path,
                    root=effective_repo_root,
                    label="completion official facts",
                    missing_ok=True,
                )
            except sfr.SafeFileReadError as exc:
                official_bytes = None
                official_read_error = sanitize_text(exc)
            else:
                official_read_error = None
            lock_state.assert_held_for(effective_official_path)
            official_sha = sha256_bytes(official_bytes) if official_bytes is not None else None
            completed = False
            for _, _, manifest, manifest_path in matching:
                try:
                    if official_read_error is not None:
                        raise pbc.CompletionValidationError(
                            "completion_official_unreadable",
                            official_read_error,
                        )
                    pbc.validate_completion_manifest(
                        manifest,
                        manifest_path=manifest_path,
                        runtime_dir=runtime_dir,
                        repo_root=effective_repo_root,
                        symbol=symbol,
                        target_date=target_date.isoformat(),
                        mode=mode,
                        official_path=effective_official_path,
                        official_bytes=official_bytes,
                        official_sha256=official_sha,
                    )
                except pbc.CompletionValidationError as exc:
                    diagnostics.append(
                        {
                            "path": str(manifest_path),
                            "reason": f"completion invalid: {exc.reason_code}",
                        }
                    )
                else:
                    completed = True
    except Exception as exc:  # noqa: BLE001 - completion evidence fails open to a safe rerun
        diagnostics.append(
            {
                "path": str(effective_official_path),
                "reason": sanitize_text(f"completion official lock/read failed: {type(exc).__name__}"),
            }
        )
        completed = False
    return ("already_completed" if completed else None), previous_run_id, diagnostics


def build_context(args: argparse.Namespace, runtime_dir: Path, target_date: date, mode: str) -> RunContext:
    run_id = str(uuid.uuid4())
    run_dir = runtime_dir / "runs" / target_date.isoformat() / run_id
    alerts_dir = runtime_dir / "alerts" / target_date.isoformat()
    lock_key = f"{args.symbol}_{target_date.isoformat()}_{mode}"
    digest = hashlib.sha256(lock_key.encode("utf-8")).hexdigest()
    return RunContext(
        args=args,
        runtime_dir=runtime_dir,
        run_id=run_id,
        run_dir=run_dir,
        alerts_dir=alerts_dir,
        manifest_path=run_dir / "manifest.json",
        summary_path=run_dir / "summary.md",
        stdout_path=run_dir / "generator_stdout.txt",
        stderr_path=run_dir / "generator_stderr.txt",
        candidate_path=run_dir / "candidate.json",
        lock_path=runtime_dir / "locks" / f"{digest}.lock",
    )


@contextlib.contextmanager
def runner_lock(ctx: RunContext) -> Iterator[bool]:
    ctx.lock_path.parent.mkdir(parents=True, exist_ok=True)
    with ctx.lock_path.open("a+b") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def generator_command(args: argparse.Namespace, target_date: date, candidate_path: Path) -> list[str]:
    return [
        sys.executable,
        "-B",
        str(GENERATOR),
        "--symbol",
        args.symbol,
        "--date",
        target_date.isoformat(),
        "--output",
        str(candidate_path),
        "--dry-run",
        "--emit-runner-marker",
        "--timeout",
        str(args.generator_timeout),
    ]


def run_generator(command: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(REPO_ROOT)
        if not existing_pythonpath
        else str(REPO_ROOT) + os.pathsep + existing_pythonpath
    )
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is not allowed: {value}")


def _sensitive_candidate_key(value: object) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if (
                normalized in {item.replace("-", "_") for item in SENSITIVE_CANDIDATE_KEYS}
                or normalized.endswith(("_token", "_secret", "_password", "_api_key"))
            ):
                return str(key)
            nested = _sensitive_candidate_key(child)
            if nested:
                return nested
    elif isinstance(value, list):
        for child in value:
            nested = _sensitive_candidate_key(child)
            if nested:
                return nested
    return None


def parse_generator_stdout(stdout: str) -> dict[str, Any]:
    candidates = [
        line[len(CANDIDATE_STDOUT_MARKER) :]
        for line in stdout.splitlines()
        if line.startswith(CANDIDATE_STDOUT_MARKER)
    ]
    if not candidates:
        raise RunnerError(
            "stdout_candidate_missing",
            "generator stdout did not contain a candidate marker",
            stage="fetch",
        )
    if len(candidates) != 1:
        raise RunnerError(
            "stdout_candidate_ambiguous",
            "generator stdout contained more than one candidate marker",
            stage="fetch",
        )
    try:
        parsed = json.loads(candidates[0], parse_constant=_reject_json_constant)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RunnerError(
            "stdout_parse_failed",
            f"candidate marker JSON is invalid: {sanitize_text(str(exc))}",
            stage="fetch",
        ) from exc
    if not isinstance(parsed, dict):
        raise RunnerError("stdout_parse_failed", "candidate marker must contain a JSON object", stage="fetch")
    sensitive_key = _sensitive_candidate_key(parsed)
    if sensitive_key:
        raise RunnerError(
            "stdout_parse_failed",
            f"candidate contains forbidden sensitive key: {sensitive_key}",
            stage="fetch",
        )
    return parsed


def _finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_candidate_identity(candidate: dict[str, Any], *, symbol: str, target_date: date) -> str:
    target = target_date.isoformat()
    if candidate.get("schema_version") not in ALLOWED_FACTS_SCHEMAS:
        raise RunnerError("candidate_schema_invalid", "candidate schema_version is not allowed", stage="validate")
    if candidate.get("symbol") != symbol:
        raise RunnerError("candidate_identity_mismatch", "candidate symbol does not match runner symbol", stage="validate")
    if candidate.get("trade_date") != target:
        raise RunnerError("source_date_mismatch", "candidate trade_date does not match target date", stage="validate")
    for field in REQUIRED_TOP_LEVEL_OBJECTS:
        if not isinstance(candidate.get(field), dict):
            raise RunnerError("candidate_schema_invalid", f"candidate {field} must be an object", stage="validate")
    source_date = candidate["quote_verification"].get("source_date")
    if source_date != target:
        raise RunnerError("source_date_mismatch", "candidate source_date does not match target date", stage="validate")
    quote = candidate["quote"]
    for field in REQUIRED_QUOTE_FIELDS:
        if field not in quote or not _finite_number(quote.get(field)):
            raise RunnerError(
                "candidate_schema_invalid",
                f"candidate quote.{field} must be a finite number",
                stage="validate",
            )
    status = candidate["run"].get("status")
    if not isinstance(status, str) or not status.strip():
        raise RunnerError("generator_failed", "candidate run.status is missing", stage="fetch")
    if status not in KNOWN_GENERATOR_STATUSES:
        raise RunnerError(
            "unknown_generator_status",
            f"candidate run.status is unknown: {sanitize_text(status)}",
            stage="fetch",
        )
    return status


def validator_summary(candidate: dict[str, Any] | None, candidate_path: Path, target_date: date) -> dict[str, Any]:
    if candidate is None:
        return {"status": "not_run", "message": "no parseable candidate"}
    try:
        vrc.assert_facts_pack_valid(
            candidate,
            facts_pack_path=str(candidate_path),
            date=target_date.isoformat(),
        )
    except Exception as exc:  # noqa: BLE001 - recorded as sanitized manifest evidence
        return {
            "status": "failed",
            "exception_type": type(exc).__name__,
            "message": sanitize_text(str(exc))[:500],
        }
    return {"status": "passed"}


def classify_generator(
    *,
    exit_code: int | None,
    candidate: dict[str, Any] | None,
    validator: dict[str, Any],
    target_date: date,
) -> tuple[str, str, str]:
    if validator.get("status") == "failed":
        return "validate", "failed", "validator_failed"
    result_status = None
    if isinstance(candidate, dict):
        run = candidate.get("run") if isinstance(candidate.get("run"), dict) else {}
        result_status = run.get("status")
    if result_status == "partial" or exit_code == 2:
        return "fetch", "needs_manual_review", "generator_partial"
    if result_status == "date_mismatch":
        return "fetch", "failed", "source_date_mismatch"
    if result_status != "success":
        return "fetch", "failed", "generator_failed"
    if exit_code not in (0, None):
        return "fetch", "failed", "generator_failed"
    if candidate is None:
        return "fetch", "failed", "generator_failed"
    return "validate", "success", None  # type: ignore[return-value]


def generator_exit_matches_status(exit_code: int | None, status: str) -> bool:
    if status == "success":
        return exit_code == 0
    if status == "partial":
        return exit_code == 2
    if status == "date_mismatch":
        return exit_code not in (0, 2, None)
    return exit_code not in (0, 2, None)


def manifest_base(
    *,
    ctx: RunContext,
    calendar: TradingCalendar | None,
    mode: str | None,
    target_date: date | None,
    now: datetime | None,
    started_at: datetime,
    official_path: Path | None,
    previous_run_id: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": ctx.run_id,
        "pid": os.getpid(),
        "mode": mode,
        "reason": ctx.args.reason,
        "symbol": ctx.args.symbol,
        "target_date": target_date.isoformat() if target_date else None,
        "timezone": BUSINESS_TIMEZONE,
        "calendar": calendar.metadata() if calendar else None,
        "scheduled_cutoff": ctx.args.cutoff,
        "now": now.isoformat() if now else None,
        "started_at": started_at.isoformat(),
        "finished_at": None,
        "duration_ms": None,
        "stage": "running",
        "last_stage": "gate",
        "outcome": "failed",
        "reason_code": None,
        "needs_manual_review": False,
        "dry_run": not bool(getattr(ctx.args, "write_official", False)),
        "write_official": bool(getattr(ctx.args, "write_official", False)),
        "generator": {
            "command": None,
            "exit_code": None,
            "result_status": None,
            "protocol_reason": None,
            "stdout_path": str(ctx.stdout_path),
            "stderr_path": str(ctx.stderr_path),
        },
        "candidate_path": str(ctx.candidate_path),
        "candidate_sha256": None,
        "official_path": str(official_path) if official_path else None,
        "official_exists_before": None,
        "official_sha256_before": None,
        "official_sha256_after": None,
        "write_action": None,
        "partial_write_policy": None,
        "official_validator_before": {"status": "not_run"},
        "official_validator_after": {"status": "not_run"},
        "official_changed": False,
        "official_bytes_equal_candidate": None,
        "official_post_write_error": None,
        "comparison": None,
        "validator": {"status": "not_run"},
        "retry_count": 0,
        "alerts": [],
        "exception": None,
        "previous_run_id": previous_run_id,
        "scan_diagnostics": [],
        "manifest_bundle_failed": False,
        "manifest_bundle_reason_code": None,
        "runtime_dir": str(ctx.runtime_dir),
        "manifest_path": str(ctx.manifest_path),
    }


def finish_manifest(
    manifest: dict[str, Any],
    *,
    started_monotonic: float,
    last_stage: str,
    outcome: str,
    reason_code: str | None,
) -> None:
    manifest["finished_at"] = datetime.now(ZoneInfo(BUSINESS_TIMEZONE)).isoformat()
    manifest["duration_ms"] = int((time.monotonic() - started_monotonic) * 1000)
    manifest["stage"] = "finished"
    manifest["last_stage"] = last_stage
    manifest["outcome"] = outcome
    manifest["reason_code"] = reason_code
    manifest["needs_manual_review"] = outcome in {"partial", "needs_manual_review"}


def write_alert(ctx: RunContext, manifest: dict[str, Any]) -> str:
    alert = {
        "schema_version": "runner_alert_v0.2_phase_a",
        "run_id": ctx.run_id,
        "symbol": manifest.get("symbol"),
        "target_date": manifest.get("target_date"),
        "outcome": manifest.get("outcome"),
        "reason_code": manifest.get("reason_code"),
        "write_action": manifest.get("write_action"),
        "official_path": manifest.get("official_path"),
        "official_sha256_after": manifest.get("official_sha256_after"),
        "official_changed": manifest.get("official_changed"),
        "manifest_path": str(ctx.manifest_path),
    }
    alert_path = ctx.alerts_dir / f"{ctx.run_id}.json"
    atomic_write_json(alert_path, alert)
    return str(alert_path)


def summary_markdown(manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Daily Facts After-Close Runner Summary",
            "",
            f"- schema_version: `{SUMMARY_SCHEMA_VERSION}`",
            f"- run_id: `{manifest.get('run_id')}`",
            f"- mode: `{manifest.get('mode')}`",
            f"- symbol: `{manifest.get('symbol')}`",
            f"- target_date: `{manifest.get('target_date')}`",
            f"- outcome: `{manifest.get('outcome')}`",
            f"- reason_code: `{manifest.get('reason_code')}`",
            f"- stage: `{manifest.get('stage')}`",
            f"- last_stage: `{manifest.get('last_stage')}`",
            f"- dry_run: `{manifest.get('dry_run')}`",
            f"- write_official: `{manifest.get('write_official')}`",
            f"- candidate_sha256: `{manifest.get('candidate_sha256')}`",
            f"- write_action: `{manifest.get('write_action')}`",
            f"- official_sha256_before: `{manifest.get('official_sha256_before')}`",
            f"- official_sha256_after: `{manifest.get('official_sha256_after')}`",
            f"- official_changed: `{manifest.get('official_changed')}`",
            f"- official_bytes_equal_candidate: `{manifest.get('official_bytes_equal_candidate')}`",
            f"- comparison_mode: `{(manifest.get('comparison') or {}).get('comparison_mode')}`",
            f"- generator_exit_code: `{manifest.get('generator', {}).get('exit_code')}`",
            f"- generator_result_status: `{manifest.get('generator', {}).get('result_status')}`",
            f"- validator_status: `{manifest.get('validator', {}).get('status')}`",
            "",
            "Phase B writes official facts only when --write-official is explicitly selected; review, current card, index, and weekly files are never written by this runner.",
            (
                "Post-write check failed after official facts changed; manual verification is required before treating the official file as usable."
                if manifest.get("official_changed")
                and manifest.get("reason_code") in {"official_written_postcheck_failed", "official_written_bytes_mismatch"}
                else ""
            ),
            "",
        ]
    )


def _json_payload(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_manifest_bundle(
    ctx: RunContext,
    manifest: dict[str, Any],
    *,
    stdout: str,
    stderr: str,
    candidate: dict[str, Any] | None,
    include_alert: bool,
) -> None:
    atomic_write_text(ctx.stdout_path, stdout)
    atomic_write_text(ctx.stderr_path, stderr)
    if candidate is not None:
        candidate_payload = _json_payload(candidate)
        atomic_write_bytes(ctx.candidate_path, candidate_payload)
        manifest["candidate_sha256"] = sha256_bytes(candidate_payload)
    atomic_write_text(ctx.summary_path, summary_markdown(manifest))
    if include_alert:
        alert_path = write_alert(ctx, manifest)
        manifest["alerts"] = [alert_path]
    atomic_write_json(ctx.manifest_path, manifest)


def persist_terminal_bundle(
    ctx: RunContext,
    manifest: dict[str, Any],
    *,
    started_monotonic: float,
    stdout: str = "",
    stderr: str = "",
    candidate: dict[str, Any] | None = None,
    include_alert: bool,
) -> bool:
    try:
        write_manifest_bundle(
            ctx,
            manifest,
            stdout=stdout,
            stderr=stderr,
            candidate=candidate,
            include_alert=include_alert,
        )
        return True
    except Exception as exc:  # noqa: BLE001 - terminal bundle must fail closed
        official_was_written = (
            manifest.get("write_action") in {"created", "identical_noop", "created_postcheck_failed"}
            or manifest.get("official_changed") is True
        ) and bool(manifest.get("official_sha256_after") or manifest.get("official_changed"))
        previous_reason_code = manifest.get("reason_code")
        manifest["exception"] = {
            "type": type(exc).__name__,
            "message": sanitize_text(str(exc))[:500],
        }
        manifest["manifest_bundle_failed"] = True
        manifest["manifest_bundle_reason_code"] = "official_written_manifest_failed" if official_was_written else "manifest_write_failed"
        finish_manifest(
            manifest,
            started_monotonic=started_monotonic,
            last_stage="manifest",
            outcome="failed" if not official_was_written else manifest.get("outcome", "failed"),
            reason_code=(
                previous_reason_code
                if official_was_written
                and previous_reason_code in {"official_written_postcheck_failed", "official_written_bytes_mismatch"}
                else "official_written_manifest_failed" if official_was_written else "manifest_write_failed"
            ),
        )
        try:
            atomic_write_json(ctx.manifest_path, manifest)
        except Exception as manifest_exc:  # noqa: BLE001 - stderr becomes the final machine record
            manifest["exception"] = {
                "type": type(manifest_exc).__name__,
                "message": sanitize_text(str(manifest_exc))[:500],
            }
            manifest["manifest_path"] = None
        return False


def prepare_runtime_dir(runtime_dir: Path) -> None:
    try:
        runtime_dir.mkdir(parents=True, exist_ok=True)
        probe = runtime_dir / ".write_probe"
        atomic_write_text(probe, "ok\n")
        probe.unlink(missing_ok=True)
    except OSError as exc:
        raise RunnerError("manifest_write_failed", f"runtime directory is not writable: {exc}", stage="manifest") from exc


def execute(args: argparse.Namespace) -> tuple[int, dict[str, Any] | None]:
    if bool(args.dry_run) == bool(args.write_official):
        raise RunnerError("run_mode_required", "choose exactly one of --dry-run or --write-official", stage="gate")
    if args.write_official and args.now:
        raise RunnerError("invalid_now", "--now is only allowed with --dry-run", stage="gate")
    if args.write_official and args.mode == "historical_backfill" and (not args.date or not args.reason or not args.reason.strip()):
        raise RunnerError(
            "historical_backfill_requires_reason",
            "--write-official historical_backfill requires --date and non-empty --reason",
            stage="gate",
        )
    runtime_dir = normalize_runtime_dir(
        args.runtime_dir or os.environ.get("STOCKS_RUNTIME_DIR") or DEFAULT_RUNTIME_DIR
    )
    started_monotonic = time.monotonic()
    started_at = datetime.now(ZoneInfo(BUSINESS_TIMEZONE))
    now = parse_now(args.now if args.dry_run else None)
    try:
        fallback_target = parse_trade_date(args.date, field="--date") if args.date else now.date()
    except ValueError:
        fallback_target = now.date()
    ctx = build_context(args, runtime_dir, fallback_target, args.mode)
    calendar: TradingCalendar | None = None
    previous_run_id: str | None = None
    mode: str | None = None
    target_date: date | None = None
    manifest_target_date: date | None = fallback_target
    official_path: Path | None = None
    manifest: dict[str, Any] | None = None
    stdout = ""
    stderr = ""
    candidate: dict[str, Any] | None = None
    current_stage = "gate"
    try:
        prepare_runtime_dir(runtime_dir)
        mode, target_date = resolve_target(args, now)
        manifest_target_date = target_date
        if target_date != fallback_target:
            ctx = build_context(args, runtime_dir, target_date, mode)
        official_path = official_path_for(args.symbol, target_date)
        calendar = load_calendar(Path(args.calendar))
        manifest = manifest_base(
            ctx=ctx,
            calendar=calendar,
            mode=mode,
            target_date=target_date,
            now=now,
            started_at=started_at,
            official_path=official_path,
            previous_run_id=None,
        )
        if target_date < calendar.coverage_start or target_date > calendar.coverage_end:
            finish_manifest(manifest, started_monotonic=started_monotonic, last_stage="gate", outcome="skipped", reason_code="calendar_uncovered")
            persisted = persist_terminal_bundle(ctx, manifest, started_monotonic=started_monotonic, include_alert=False)
            return (0 if persisted else 1), manifest
        if not calendar.is_trading_day(target_date):
            finish_manifest(manifest, started_monotonic=started_monotonic, last_stage="gate", outcome="skipped", reason_code="non_trading_day")
            persisted = persist_terminal_bundle(ctx, manifest, started_monotonic=started_monotonic, include_alert=False)
            return (0 if persisted else 1), manifest
        if mode == "today_after_close" and now.time() < parse_cutoff(args.cutoff):
            finish_manifest(manifest, started_monotonic=started_monotonic, last_stage="gate", outcome="skipped", reason_code="before_close")
            persisted = persist_terminal_bundle(ctx, manifest, started_monotonic=started_monotonic, include_alert=False)
            return (0 if persisted else 1), manifest
        expected_official_sha = None
        official_exists_before = False
        try:
            with ofl.official_facts_lock(official_path) as lock_state:
                official_bytes, expected_official_sha = ofl.read_current_official(
                    official_path,
                    lock_state=lock_state,
                )
                official_exists_before = official_bytes is not None
        except Exception as exc:  # noqa: BLE001
            raise RunnerError("official_snapshot_failed", sanitize_text(str(exc)), stage="gate") from exc
        manifest["official_exists_before"] = official_exists_before
        manifest["official_sha256_before"] = expected_official_sha
        if args.dry_run and is_sealed_facts(official_path):
            finish_manifest(manifest, started_monotonic=started_monotonic, last_stage="gate", outcome="skipped", reason_code="sealed_exists")
            persisted = persist_terminal_bundle(ctx, manifest, started_monotonic=started_monotonic, include_alert=True)
            return (0 if persisted else 1), manifest
        with runner_lock(ctx) as acquired:
            if not acquired:
                finish_manifest(manifest, started_monotonic=started_monotonic, last_stage="gate", outcome="skipped", reason_code="runner_already_active")
                persisted = persist_terminal_bundle(ctx, manifest, started_monotonic=started_monotonic, include_alert=True)
                return (0 if persisted else 1), manifest
            previous_reason, previous_run_id, scan_diagnostics = scan_previous_runs(
                runtime_dir,
                target_date,
                symbol=args.symbol,
                mode=mode,
                write_official=args.write_official,
                repo_root=REPO_ROOT,
                official_path=official_path,
            )
            manifest["previous_run_id"] = previous_run_id
            manifest["scan_diagnostics"] = scan_diagnostics
            if previous_reason == "already_completed":
                finish_manifest(
                    manifest,
                    started_monotonic=started_monotonic,
                    last_stage="gate",
                    outcome="skipped",
                    reason_code="already_completed",
                )
                persisted = persist_terminal_bundle(
                    ctx,
                    manifest,
                    started_monotonic=started_monotonic,
                    include_alert=False,
                )
                return (0 if persisted else 1), manifest
            command = generator_command(args, target_date, ctx.candidate_path)
            manifest["generator"]["command"] = command
            current_stage = "fetch"
            result = run_generator(command)
            raw_stdout = result.stdout or ""
            stdout = sanitize_text(raw_stdout)
            stderr = sanitize_text(result.stderr or "")
            manifest["generator"]["exit_code"] = result.returncode
            try:
                candidate = parse_generator_stdout(raw_stdout)
            except RunnerError as exc:
                manifest["generator"]["protocol_reason"] = exc.reason_code
                manifest["exception"] = {
                    "type": type(exc).__name__,
                    "message": sanitize_text(str(exc))[:500],
                }
                finish_manifest(
                    manifest,
                    started_monotonic=started_monotonic,
                    last_stage="fetch",
                    outcome="failed",
                    reason_code=exc.reason_code,
                )
                persisted = persist_terminal_bundle(
                    ctx,
                    manifest,
                    started_monotonic=started_monotonic,
                    stdout=stdout,
                    stderr=stderr,
                    include_alert=True,
                )
                return 1, manifest
            try:
                run_status = validate_candidate_identity(
                    candidate,
                    symbol=args.symbol,
                    target_date=target_date,
                )
            except RunnerError as exc:
                manifest["generator"]["result_status"] = (
                    candidate.get("run", {}).get("status")
                    if isinstance(candidate.get("run"), dict)
                    else None
                )
                manifest["exception"] = {
                    "type": type(exc).__name__,
                    "message": sanitize_text(str(exc))[:500],
                }
                finish_manifest(
                    manifest,
                    started_monotonic=started_monotonic,
                    last_stage=exc.stage,
                    outcome="failed",
                    reason_code=exc.reason_code,
                )
                persisted = persist_terminal_bundle(
                    ctx,
                    manifest,
                    started_monotonic=started_monotonic,
                    stdout=stdout,
                    stderr=stderr,
                    candidate=candidate,
                    include_alert=True,
                )
                return 1, manifest
            current_stage = "validate"
            validator = validator_summary(candidate, ctx.candidate_path, target_date)
            manifest["generator"]["result_status"] = run_status
            manifest["validator"] = validator
            last_stage, outcome, reason_code = classify_generator(
                exit_code=result.returncode,
                candidate=candidate,
                validator=validator,
                target_date=target_date,
            )
            if outcome in {"success", "needs_manual_review"} and not generator_exit_matches_status(result.returncode, run_status):
                last_stage, outcome, reason_code = "fetch", "failed", "generator_status_exit_mismatch"
            if args.write_official and outcome in {"success", "needs_manual_review"} and run_status in {"success", "partial"}:
                current_stage = "official"
                if validator.get("status") != "passed":
                    last_stage, outcome, reason_code = "validate", "failed", "validator_failed"
                else:
                    candidate_bytes = _json_payload(candidate)
                    manifest["candidate_sha256"] = sha256_bytes(candidate_bytes)
                    if run_status == "partial":
                        partial_policy = oft.evaluate_partial_write_policy(candidate)
                        manifest["partial_write_policy"] = {**partial_policy.__dict__}
                        if not partial_policy.eligible:
                            manifest["write_action"] = "not_eligible"
                            last_stage, outcome, reason_code = (
                                "official",
                                "needs_manual_review",
                                "partial_not_eligible_for_official",
                            )
                        else:
                            write_result = oft.promote_candidate_to_official(
                                repo_root=REPO_ROOT,
                                official_path=official_path,
                                candidate=candidate,
                                candidate_bytes=candidate_bytes,
                                symbol=args.symbol,
                                target_date=target_date.isoformat(),
                                expected_sha256=expected_official_sha,
                            )
                            manifest["official_path"] = str(write_result.official_path)
                            manifest["official_exists_before"] = write_result.official_exists_before
                            manifest["official_sha256_before"] = write_result.official_sha256_before
                            manifest["official_sha256_after"] = write_result.official_sha256_after
                            manifest["write_action"] = write_result.write_action
                            manifest["partial_write_policy"] = write_result.partial_write_policy
                            manifest["official_validator_before"] = write_result.official_validator_before
                            manifest["official_validator_after"] = write_result.official_validator_after
                            manifest["official_changed"] = write_result.official_changed
                            manifest["official_bytes_equal_candidate"] = write_result.official_bytes_equal_candidate
                            manifest["official_post_write_error"] = write_result.post_write_error
                            manifest["comparison"] = write_result.comparison
                            last_stage = (
                                "validate"
                                if write_result.reason_code in {"official_written_postcheck_failed", "official_written_bytes_mismatch"}
                                else "official"
                            )
                            outcome = write_result.outcome
                            reason_code = write_result.reason_code
                    else:
                        write_result = oft.promote_candidate_to_official(
                            repo_root=REPO_ROOT,
                            official_path=official_path,
                            candidate=candidate,
                            candidate_bytes=candidate_bytes,
                            symbol=args.symbol,
                            target_date=target_date.isoformat(),
                            expected_sha256=expected_official_sha,
                        )
                        manifest["official_path"] = str(write_result.official_path)
                        manifest["official_exists_before"] = write_result.official_exists_before
                        manifest["official_sha256_before"] = write_result.official_sha256_before
                        manifest["official_sha256_after"] = write_result.official_sha256_after
                        manifest["write_action"] = write_result.write_action
                        manifest["partial_write_policy"] = write_result.partial_write_policy
                        manifest["official_validator_before"] = write_result.official_validator_before
                        manifest["official_validator_after"] = write_result.official_validator_after
                        manifest["official_changed"] = write_result.official_changed
                        manifest["official_bytes_equal_candidate"] = write_result.official_bytes_equal_candidate
                        manifest["official_post_write_error"] = write_result.post_write_error
                        manifest["comparison"] = write_result.comparison
                        last_stage = (
                            "validate"
                            if write_result.reason_code in {"official_written_postcheck_failed", "official_written_bytes_mismatch"}
                            else "official"
                        )
                        outcome = write_result.outcome
                        reason_code = write_result.reason_code
            finish_manifest(manifest, started_monotonic=started_monotonic, last_stage=last_stage, outcome=outcome, reason_code=reason_code)
            persisted = persist_terminal_bundle(
                ctx,
                manifest,
                started_monotonic=started_monotonic,
                stdout=stdout,
                stderr=stderr,
                candidate=candidate,
                include_alert=outcome in {"failed", "needs_manual_review"},
            )
            if not persisted:
                return 1, manifest
            if outcome == "failed":
                return 1, manifest
            if outcome == "needs_manual_review":
                return 2, manifest
            return 0, manifest
    except RunnerError as exc:
        if manifest is None:
            manifest = manifest_base(
                ctx=ctx,
                calendar=calendar,
                mode=mode if mode is not None else args.mode,
                target_date=target_date if target_date is not None else manifest_target_date,
                now=now,
                started_at=started_at,
                official_path=official_path,
                previous_run_id=previous_run_id,
            )
        manifest["exception"] = {"type": type(exc).__name__, "message": sanitize_text(str(exc))[:500]}
        finish_manifest(manifest, started_monotonic=started_monotonic, last_stage=exc.stage, outcome="failed", reason_code=exc.reason_code)
        persist_terminal_bundle(
            ctx,
            manifest,
            started_monotonic=started_monotonic,
            stdout=stdout,
            stderr=stderr,
            candidate=candidate,
            include_alert=True,
        )
        return 1, manifest
    except Exception as exc:  # noqa: BLE001 - fail-closed runner boundary
        if manifest is None:
            manifest = manifest_base(
                ctx=ctx,
                calendar=calendar,
                mode=mode,
                target_date=target_date,
                now=now,
                started_at=started_at,
                official_path=official_path,
                previous_run_id=previous_run_id,
            )
        manifest["exception"] = {"type": type(exc).__name__, "message": sanitize_text(str(exc))[:500]}
        finish_manifest(
            manifest,
            started_monotonic=started_monotonic,
            last_stage=current_stage,
            outcome="failed",
            reason_code="runner_unexpected_error",
        )
        persist_terminal_bundle(
            ctx,
            manifest,
            started_monotonic=started_monotonic,
            stdout=stdout,
            stderr=stderr,
            candidate=candidate,
            include_alert=True,
        )
        return 1, manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase B after-close daily facts runner")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--dry-run", action="store_true", help="Generate and validate candidate only")
    mode_group.add_argument("--write-official", action="store_true", help="Explicitly promote eligible candidate to official facts")
    parser.add_argument("--symbol", default="300274")
    parser.add_argument("--mode", choices=("today_after_close", "historical_backfill"), default="today_after_close")
    parser.add_argument("--date", help="Target date for historical_backfill only")
    parser.add_argument("--reason", help="Required non-empty reason for historical_backfill")
    parser.add_argument("--now", help="Dry-run/test-only current time with exact +08:00 offset")
    parser.add_argument("--cutoff", default=DEFAULT_CUTOFF)
    parser.add_argument("--calendar", default=str(DEFAULT_CALENDAR))
    parser.add_argument("--runtime-dir", default=None)
    parser.add_argument("--generator-timeout", type=float, default=15.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        code, manifest = execute(args)
    except RunnerError as exc:
        print(
            json.dumps(
                {
                    "outcome": "failed",
                    "reason_code": exc.reason_code,
                    "message": sanitize_text(str(exc)),
                    "manifest": None,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    if manifest is not None:
        payload = {
            "run_id": manifest.get("run_id"),
            "outcome": manifest.get("outcome"),
            "reason_code": manifest.get("reason_code"),
            "manifest": manifest.get("manifest_path"),
            "official_path": manifest.get("official_path"),
            "official_sha256_after": manifest.get("official_sha256_after"),
            "write_action": manifest.get("write_action"),
            "official_changed": manifest.get("official_changed"),
            "manifest_bundle_reason_code": manifest.get("manifest_bundle_reason_code"),
        }
        stream = sys.stderr if (
            (manifest.get("outcome") == "failed" and not manifest.get("manifest_path"))
            or manifest.get("manifest_bundle_failed") is True
        ) else sys.stdout
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), file=stream)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
