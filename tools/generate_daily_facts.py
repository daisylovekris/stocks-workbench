#!/usr/bin/env python3
"""Generate daily facts packs for stock review workflows.

This module keeps the fetch / normalize / merge / write steps separate so that
the data-source calls can be monkeypatched in tests.
"""

from __future__ import annotations

import argparse
import copy
import math
import json
import os
import signal
import sys
import tempfile
from dataclasses import dataclass
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import official_facts_lock as ofl
from tools import validate_review_chain as vrc
from tools import volume_ratio_evidence as vre


SCHEMA_VERSION = "facts_pack_v0.2"
UTC = timezone.utc

EXIT_SUCCESS = 0
EXIT_PARTIAL = 2
EXIT_NETWORK_ERROR = 3
EXIT_SOURCE_ERROR = 4
EXIT_SCHEMA_ERROR = 5
EXIT_DATE_MISMATCH = 6
CANDIDATE_STDOUT_MARKER = "STOCKS_FACTS_CANDIDATE_JSON="

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

FETCH_CORE_QUOTE_FIELDS = (
    "open",
    "high",
    "low",
    "close",
    "prev_close",
    "amount",
    "turnover_rate",
)

CONTEXT_MANUAL_CHECK_KEYS = (
    "market_indices",
    "sector_context",
    "disclosure_status",
    "news_policy_context",
)

LOCKED_MANUAL_CONFIRMATION_STATUSES = {
    "manual_confirmed",
    "confirmed",
}

MANUAL_CONFIRMED_BY_VALUES = {
    "manual_check",
    "user_manual_check",
}

TENCENT_KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
TENCENT_QUOTE_URL = "https://qt.gtimg.cn/q={code}"
SOHU_HISTORY_URL = "https://q.stock.sohu.com/hisHq"
HTTP_USER_AGENT = "Mozilla/5.0 (stocks-workbench facts generator)"
VOLUME_RATIO_CONFIRM_TOLERANCE = vre.SAME_DAY_VOLUME_RATIO_TOLERANCE
HISTORICAL_VOLUME_RATIO_CONFIRM_TOLERANCE = vre.HISTORICAL_VOLUME_RATIO_TOLERANCE
OHLC_FIELDS = vre.OHLC_FIELDS


@dataclass
class RunOutcome:
    exit_code: int
    facts_pack: dict[str, Any] | None
    wrote_file: bool
    output_path: str | None
    status: str
    output_sha256: str | None = None


class SourceTimeoutError(TimeoutError):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_iso_z() -> str:
    return utc_now().isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_date(date_text: str) -> datetime:
    return datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=UTC)


def normalize_date_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    text = str(value).strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text:
        text = text.split(" ", 1)[0]
    try:
        if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
            return datetime.strptime(text[:10], "%Y-%m-%d").date().isoformat()
        digits = "".join(ch for ch in text if ch.isdigit())
        if len(digits) == 8:
            return datetime.strptime(digits, "%Y%m%d").date().isoformat()
    except ValueError:
        return None
    return None


def normalize_name_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def first_not_none(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        return value
    return None


def record_date_text(record: dict[str, Any]) -> str | None:
    if not isinstance(record, dict):
        return None
    return normalize_date_text(first_not_none(record.get("date"), record.get("日期"), record.get("trade_date")))


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_float_or_none(value: Any) -> float | None:
    return to_float(value)


def positive_timeout(value: str) -> float:
    timeout = float(value)
    if timeout <= 0:
        raise argparse.ArgumentTypeError("--timeout must be greater than 0")
    return timeout


def is_manual_lock(volume_ratio: dict[str, Any] | None) -> bool:
    if not volume_ratio:
        return False
    verification = volume_ratio.get("verification")
    if not isinstance(verification, dict):
        return False
    status = str(verification.get("status") or "").strip()
    method = str(verification.get("method") or "").strip().lower()
    confirmed_by = str(verification.get("confirmed_by") or "").strip()
    if status in LOCKED_MANUAL_CONFIRMATION_STATUSES and method == "manual":
        return True
    if status == "manual_confirmed":
        return True
    return confirmed_by in MANUAL_CONFIRMED_BY_VALUES


def _mapping_value(mapping: Any, key: str, default: Any = None) -> Any:
    if not isinstance(mapping, dict) or key not in mapping:
        return default
    value = mapping.get(key)
    return default if value is None else value


def _mapping_bool(mapping: Any, key: str, default: bool) -> bool:
    value = _mapping_value(mapping, key, default=default)
    if value is default:
        return default
    if isinstance(value, bool):
        return value
    return bool(value)


@contextmanager
def _hard_timeout(seconds: float, source: str):
    if seconds <= 0:
        raise ValueError("timeout must be greater than 0")
    if not hasattr(signal, "setitimer") or not hasattr(signal, "SIGALRM"):
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)
    def _raise_timeout(signum, frame):  # noqa: ARG001
        raise SourceTimeoutError(f"{source} timed out after {seconds:.3f}s")

    signal.signal(signal.SIGALRM, _raise_timeout)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, previous_timer[0], previous_timer[1])
        signal.signal(signal.SIGALRM, previous_handler)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate daily facts packs for review workflows",
    )
    parser.add_argument("--symbol", required=True, help="Stock symbol, e.g. 300274")
    parser.add_argument("--date", required=True, help="Target trade date in YYYY-MM-DD")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--source",
        choices=("auto", "tencent", "eastmoney"),
        default="auto",
        help="Historical quote source route",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print JSON and status without writing")
    parser.add_argument(
        "--emit-runner-marker",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--no-write", action="store_true", help="Do not write output file")
    parser.add_argument(
        "--write-partial",
        action="store_true",
        help="Allow writing partial facts when core quote is incomplete",
    )
    parser.add_argument(
        "--timeout",
        type=positive_timeout,
        default=15.0,
        help="Network timeout in seconds",
    )
    parser.add_argument(
        "--lock-dir",
        help="Override the shared official-facts lock directory (tests only)",
    )
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_existing_pack(pack: Any, symbol: str, target_date: str) -> dict[str, Any]:
    if not isinstance(pack, dict):
        raise ValueError(
            f"schema_error: existing output root must be an object, got {type(pack).__name__}"
        )
    if str(pack.get("symbol")) != str(symbol):
        raise ValueError(
            f"schema_error: existing output symbol {pack.get('symbol')} does not match {symbol}"
        )
    if str(pack.get("trade_date")) != str(target_date):
        raise ValueError(
            f"schema_error: existing output date {pack.get('trade_date')} does not match {target_date}"
        )
    return pack


def _record_list_from_table(table: Any) -> list[dict[str, Any]]:
    if table is None:
        return []
    if isinstance(table, list):
        return [dict(row) for row in table if isinstance(row, dict)]
    if hasattr(table, "to_dict"):
        try:
            records = table.to_dict(orient="records")
            return [dict(row) for row in records if isinstance(row, dict)]
        except TypeError:
            pass
    if hasattr(table, "iterrows"):
        return [dict(row) for _, row in table.iterrows()]
    return []


def _sort_records_by_date(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda row: record_date_text(row) or "")


def _partition_records_by_date(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    valid_records: list[dict[str, Any]] = []
    invalid_count = 0
    for record in records:
        if record_date_text(record) is None:
            invalid_count += 1
            continue
        valid_records.append(record)
    return _sort_records_by_date(valid_records), invalid_count


def _classify_exception(exc: Exception) -> str:
    message = f"{type(exc).__name__}: {exc}".lower()
    network_markers = (
        "timeout",
        "timed out",
        "dns",
        "name resolution",
        "connection refused",
        "connection reset",
        "network",
        "name or service not known",
        "temporary failure",
        "urlopen error",
        "ssl",
        "unexpected_eof",
        "remote end closed",
    )
    if any(marker in message for marker in network_markers):
        return "network_error"
    return "source_error"


def _market_code(symbol: str) -> str:
    prefix = "sz" if symbol.startswith(("0", "3")) else "sh"
    return f"{prefix}{symbol}"


def _http_get_text_direct(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: float,
    encoding: str = "utf-8",
) -> str:
    if params:
        url = f"{url}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": HTTP_USER_AGENT})
    opener = build_opener(ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        return response.read().decode(encoding, errors="replace")


def _error_fetch_result(
    *,
    source: str,
    target_date: str,
    fetched_at: str,
    exc: Exception,
) -> dict[str, Any]:
    status = _classify_exception(exc)
    return {
        "status": status,
        "source": source,
        "target_date": target_date,
        "source_date": None,
        "rows": [],
        "raw_record": None,
        "previous_record": None,
        "source_pct_change": None,
        "source_name": None,
        "quote": None,
        "fetched_at": fetched_at,
        "error_type": status,
        "error_message": f"{type(exc).__name__}: {exc}",
    }


def _strip_percent(value: Any) -> Any:
    return value.rstrip("%") if isinstance(value, str) else value


def parse_tencent_snapshot(fields: list[Any]) -> dict[str, Any] | None:
    if len(fields) <= 49:
        return None
    timestamp = str(fields[30] or "").strip()
    source_date = normalize_date_text(timestamp[:8]) if len(timestamp) >= 8 else None
    amount = None
    compound = str(fields[35] or "")
    compound_parts = compound.split("/")
    if len(compound_parts) >= 3:
        amount_yuan = to_float_or_none(compound_parts[2])
        if amount_yuan is not None:
            amount = amount_yuan / 1e8
    if amount is None:
        amount_wan = to_float_or_none(fields[37])
        if amount_wan is not None:
            amount = amount_wan / 10000
    return {
        "source_date": source_date,
        "source_timestamp": timestamp or None,
        "is_closed": len(timestamp) >= 14 and timestamp[8:14] >= "150000",
        "name": normalize_name_text(fields[1]),
        "open": to_float_or_none(fields[5]),
        "high": to_float_or_none(fields[33]),
        "low": to_float_or_none(fields[34]),
        "close": to_float_or_none(fields[3]),
        "prev_close": to_float_or_none(fields[4]),
        "pct_change": to_float_or_none(fields[32]),
        "volume": to_float_or_none(fields[36]),
        "amount": amount,
        "turnover_rate": to_float_or_none(fields[38]),
        "volume_ratio": to_float_or_none(fields[49]),
    }


def _parse_tencent_quote_text(text: str) -> list[str]:
    if '="' not in text:
        raise ValueError("Tencent quote payload missing field delimiter")
    payload = text.split('="', 1)[1].rsplit('";', 1)[0]
    return payload.split("~")


def _quote_values_match(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    fields: tuple[str, ...] = OHLC_FIELDS,
    tolerance: float = vre.OHLC_ABS_TOLERANCE,
) -> bool:
    try:
        left_ohlc = {field: left.get(field) for field in fields}
        right_ohlc = {field: right.get(field) for field in fields}
        vre.validate_ohlc_match(left_ohlc, right_ohlc, tolerance=tolerance)
    except vre.EvidenceError:
        return False
    return True


def _tencent_kline_records(payload: dict[str, Any], code: str) -> tuple[list[dict[str, Any]], list[Any] | None]:
    stock_data = payload.get("data", {}).get(code)
    if not isinstance(stock_data, dict):
        raise ValueError(f"Tencent kline payload missing {code}")
    raw_rows = stock_data.get("day") or stock_data.get("qfqday") or []
    records = []
    for row in raw_rows:
        if not isinstance(row, list) or len(row) < 6:
            continue
        records.append(
            {
                "date": row[0],
                "open": row[1],
                "close": row[2],
                "high": row[3],
                "low": row[4],
                "volume": row[5],
            }
        )
    qt = stock_data.get("qt", {}).get(code)
    return _sort_records_by_date(records), qt if isinstance(qt, list) else None


def derive_five_day_volume_ratio(records: list[dict[str, Any]], target_date: str) -> float | None:
    window = _six_day_volume_window(records, target_date)
    if window is None:
        return None
    try:
        return vre.calculate_volume_ratio_from_window([item["volume"] for item in window])
    except vre.EvidenceError:
        return None


def _six_day_volume_window(records: list[dict[str, Any]], target_date: str) -> list[dict[str, Any]] | None:
    dated_records = []
    try:
        target = vre.parse_trade_date(target_date)
    except vre.EvidenceError:
        return None
    for row in records:
        date_text = record_date_text(row)
        if date_text is None:
            continue
        try:
            dated_records.append((vre.parse_trade_date(date_text), row))
        except vre.EvidenceError:
            continue
    if sum(1 for date_value, _row in dated_records if date_value == target) != 1:
        return None
    sorted_records = [row for _date_text, row in sorted(dated_records, key=lambda item: item[0])]
    target_index = next(
        (index for index, row in enumerate(sorted_records) if record_date_text(row) == target_date),
        None,
    )
    if target_index is None or target_index < 5:
        return None
    window_dates = [
        record_date_text(row)
        for row in sorted_records[target_index - 5 : target_index + 1]
    ]
    if any(date_text is None for date_text in window_dates):
        return None
    volumes = [to_float_or_none(row.get("volume")) for row in sorted_records[target_index - 5 : target_index + 1]]
    try:
        vre.validate_six_day_window(window_dates, volumes, target_date=target_date)
    except vre.EvidenceError:
        return None
    return [
        {
            "date": date_text,
            "volume": volume,
        }
        for date_text, volume in zip(window_dates, volumes)
    ]


def _five_day_volume_check_from_records(
    records: list[dict[str, Any]],
    target_date: str,
    *,
    source: str,
    expected_value: Any,
    tolerance: float,
    fetched_at: str | None = None,
) -> dict[str, Any] | None:
    window = _six_day_volume_window(records, target_date)
    if window is None:
        return None
    try:
        return vre.build_five_day_volume_check(
            source=source,
            trade_dates=[row["date"] for row in window],
            volumes=[row["volume"] for row in window],
            target_date=target_date,
            expected_value=expected_value,
            tolerance=tolerance,
            fetched_at=fetched_at,
        )
    except vre.EvidenceError:
        return None


def _quote_from_tencent_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "open": to_float_or_none(record.get("open")),
        "high": to_float_or_none(record.get("high")),
        "low": to_float_or_none(record.get("low")),
        "close": to_float_or_none(record.get("close")),
    }


def _target_quote_from_records(records: list[dict[str, Any]], target_date: str) -> dict[str, Any] | None:
    target = next((row for row in records if record_date_text(row) == target_date), None)
    return _quote_from_tencent_record(target) if target else None


def _same_day_snapshot_ohlc_matched(
    *,
    snapshot: dict[str, Any] | None,
    target_quote: dict[str, Any] | None,
    target_date: str,
) -> bool:
    return bool(
        snapshot
        and target_quote
        and snapshot.get("source_date") == target_date
        and snapshot.get("is_closed")
        and snapshot.get("volume_ratio") is not None
        and _quote_values_match(target_quote, snapshot)
    )


def _snapshot_ohlc_evidence(
    *,
    snapshot_source: str | None,
    target_date: str,
    snapshot: dict[str, Any],
    historical_source: str,
    historical_ohlc: dict[str, Any],
    fetched_at: str | None = None,
) -> dict[str, Any]:
    evidence = vre.build_ohlc_check(
        archived_source=snapshot_source or "unknown_tencent_snapshot",
        archived_source_date=target_date,
        archived_ohlc={field: snapshot.get(field) for field in OHLC_FIELDS},
        historical_source=historical_source,
        historical_source_date=target_date,
        historical_ohlc=historical_ohlc,
        tolerance=vre.OHLC_TOLERANCE,
        fetched_at=fetched_at,
    )
    evidence.update(
        {
            "snapshot_source": snapshot_source,
            "source_date": target_date,
            "matched_to": historical_source,
            "snapshot_ohlc": evidence["archived_ohlc"],
            "historical_ohlc": evidence["ohlc"],
        }
    )
    return evidence


def fetch_sohu_quote(_client: Any, symbol: str, target_date: str, timeout: float) -> dict[str, Any]:
    fetched_at = utc_now_iso_z()
    start_date = (parse_date(target_date) - timedelta(days=45)).strftime("%Y%m%d")
    end_date = parse_date(target_date).strftime("%Y%m%d")
    try:
        text = _http_get_text_direct(
            SOHU_HISTORY_URL,
            params={
                "code": f"cn_{symbol}",
                "start": start_date,
                "end": end_date,
                "stat": "1",
                "order": "D",
                "period": "d",
                "callback": "historySearchHandler",
                "rt": "jsonp",
            },
            timeout=timeout,
            encoding="gb18030",
        )
        start = text.find("(")
        end = text.rfind(")")
        if start < 0 or end <= start:
            raise ValueError("Sohu payload missing JSONP wrapper")
        payload = json.loads(text[start + 1 : end])
        hq = payload[0].get("hq", []) if isinstance(payload, list) and payload else []
        records = []
        for row in hq:
            if not isinstance(row, list) or len(row) < 10:
                continue
            records.append(
                {
                    "date": row[0],
                    "open": row[1],
                    "close": row[2],
                    "change": row[3],
                    "pct_change": _strip_percent(row[4]),
                    "low": row[5],
                    "high": row[6],
                    "volume": row[7],
                    "amount_wan": row[8],
                    "turnover_rate": _strip_percent(row[9]),
                }
            )
        records = _sort_records_by_date(records)
    except Exception as exc:  # noqa: BLE001
        return _error_fetch_result(source="sohu", target_date=target_date, fetched_at=fetched_at, exc=exc)

    target_index = next((index for index, row in enumerate(records) if record_date_text(row) == target_date), None)
    if target_index is None:
        return {
            **_error_fetch_result(
                source="sohu",
                target_date=target_date,
                fetched_at=fetched_at,
                exc=ValueError(f"returned dates do not include target date {target_date}"),
            ),
            "status": "date_mismatch",
            "error_type": "date_mismatch",
            "source_date": record_date_text(records[-1]) if records else None,
            "rows": records,
        }

    raw_record = records[target_index]
    previous_record = records[target_index - 1] if target_index > 0 else None
    close_value = to_float_or_none(raw_record.get("close"))
    change_value = to_float_or_none(raw_record.get("change"))
    prev_close = to_float_or_none(previous_record.get("close")) if previous_record else None
    if prev_close is None and close_value is not None and change_value is not None:
        prev_close = close_value - change_value
    amount_wan = to_float_or_none(raw_record.get("amount_wan"))
    return {
        "status": "ok",
        "source": "sohu",
        "target_date": target_date,
        "source_date": target_date,
        "rows": records,
        "raw_record": raw_record,
        "previous_record": previous_record,
        "source_pct_change": to_float_or_none(raw_record.get("pct_change")),
        "source_name": None,
        "quote": {
            "open": to_float_or_none(raw_record.get("open")),
            "high": to_float_or_none(raw_record.get("high")),
            "low": to_float_or_none(raw_record.get("low")),
            "close": close_value,
            "prev_close": prev_close,
            "amount": amount_wan / 10000 if amount_wan is not None else None,
            "turnover_rate": to_float_or_none(raw_record.get("turnover_rate")),
        },
        "field_sources": {
            field: "sohu_history"
            for field in ("open", "high", "low", "close", "prev_close", "amount", "turnover_rate")
        },
        "fetched_at": fetched_at,
        "error_type": None,
        "error_message": None,
    }


def fetch_tencent_direct_quote(_client: Any, symbol: str, target_date: str, timeout: float) -> dict[str, Any]:
    fetched_at = utc_now_iso_z()
    code = _market_code(symbol)
    start_date = (parse_date(target_date) - timedelta(days=45)).date().isoformat()
    try:
        text = _http_get_text_direct(
            TENCENT_KLINE_URL,
            params={"param": f"{code},day,{start_date},{target_date},80,"},
            timeout=timeout,
        )
        payload = json.loads(text)
        records, qt_fields = _tencent_kline_records(payload, code)
    except Exception as exc:  # noqa: BLE001
        return _error_fetch_result(source="tencent", target_date=target_date, fetched_at=fetched_at, exc=exc)

    target_index = next((index for index, row in enumerate(records) if record_date_text(row) == target_date), None)
    if target_index is None:
        return {
            **_error_fetch_result(
                source="tencent",
                target_date=target_date,
                fetched_at=fetched_at,
                exc=ValueError(f"returned dates do not include target date {target_date}"),
            ),
            "status": "date_mismatch",
            "error_type": "date_mismatch",
            "source_date": record_date_text(records[-1]) if records else None,
            "rows": records,
        }

    raw_record = records[target_index]
    previous_record = records[target_index - 1] if target_index > 0 else None
    quote = {
        "open": to_float_or_none(raw_record.get("open")),
        "high": to_float_or_none(raw_record.get("high")),
        "low": to_float_or_none(raw_record.get("low")),
        "close": to_float_or_none(raw_record.get("close")),
        "prev_close": to_float_or_none(previous_record.get("close")) if previous_record else None,
        "amount": None,
        "turnover_rate": None,
    }
    field_sources = {
        field: "tencent_fqkline"
        for field in ("open", "high", "low", "close", "prev_close")
    }
    snapshot = parse_tencent_snapshot(qt_fields) if qt_fields else None
    source_name = snapshot.get("name") if snapshot else None
    source_pct_change = None
    if snapshot and snapshot.get("source_date") == target_date and snapshot.get("is_closed"):
        if _quote_values_match(quote, snapshot):
            quote["amount"] = snapshot.get("amount")
            quote["turnover_rate"] = snapshot.get("turnover_rate")
            field_sources["amount"] = "tencent_qt_snapshot"
            field_sources["turnover_rate"] = "tencent_qt_snapshot"
            source_pct_change = snapshot.get("pct_change")

    errors = []
    if quote["amount"] is None or quote["turnover_rate"] is None:
        sohu = fetch_sohu_quote(None, symbol, target_date, timeout)
        if sohu.get("status") == "ok" and _quote_values_match(quote, sohu.get("quote") or {}):
            sohu_quote = sohu.get("quote") or {}
            source_pct_change = sohu.get("source_pct_change")
            for field in ("amount", "turnover_rate"):
                if quote[field] is None and sohu_quote.get(field) is not None:
                    quote[field] = sohu_quote[field]
                    field_sources[field] = "sohu_history"
        elif sohu.get("status") not in {"ok", "date_mismatch"}:
            errors.append(
                {
                    "source": "sohu",
                    "error_type": sohu.get("error_type") or sohu.get("status"),
                    "error_message": sohu.get("error_message"),
                    "fetched_at": sohu.get("fetched_at"),
                    "recovered": quote["amount"] is not None and quote["turnover_rate"] is not None,
                }
            )
        elif sohu.get("status") == "ok":
            errors.append(
                {
                    "source": "sohu",
                    "error_type": "quote_enrichment_conflict",
                    "error_message": "Sohu quote does not match Tencent historical quote",
                    "fetched_at": sohu.get("fetched_at"),
                    "recovered": False,
                }
            )

    return {
        "status": "ok",
        "source": "tencent",
        "target_date": target_date,
        "source_date": target_date,
        "rows": records,
        "raw_record": raw_record,
        "previous_record": previous_record,
        "source_pct_change": source_pct_change,
        "source_name": source_name,
        "quote": quote,
        "field_sources": field_sources,
        "fetched_at": fetched_at,
        "error_type": None,
        "error_message": None,
        "errors": errors,
    }


def fetch_volume_ratio_candidate(symbol: str, target_date: str, timeout: float) -> dict[str, Any] | None:
    fetched_at = utc_now_iso_z()
    code = _market_code(symbol)
    snapshot_source = None
    try:
        text = _http_get_text_direct(
            TENCENT_QUOTE_URL.format(code=code),
            timeout=timeout,
            encoding="gb18030",
        )
        snapshot = parse_tencent_snapshot(_parse_tencent_quote_text(text))
        snapshot_source = "tencent_qt_direct_index_49"
    except Exception as exc:  # noqa: BLE001
        snapshot = None
        snapshot_error = exc
    else:
        snapshot_error = None

    sohu = fetch_sohu_quote(None, symbol, target_date, timeout)
    sohu_derived = (
        derive_five_day_volume_ratio(sohu.get("rows") or [], target_date)
        if sohu.get("status") == "ok"
        else None
    )
    tencent_derived = None
    tencent_history_error = None
    target_quote = None
    embedded_snapshot = None
    try:
        start_date = (parse_date(target_date) - timedelta(days=45)).date().isoformat()
        text = _http_get_text_direct(
            TENCENT_KLINE_URL,
            params={"param": f"{code},day,{start_date},{target_date},80,"},
            timeout=timeout,
        )
        records, embedded_qt_fields = _tencent_kline_records(json.loads(text), code)
        tencent_derived = derive_five_day_volume_ratio(records, target_date)
        target_quote = _target_quote_from_records(records, target_date)
        embedded_snapshot = parse_tencent_snapshot(embedded_qt_fields) if embedded_qt_fields else None
    except Exception as exc:  # noqa: BLE001
        tencent_history_error = exc

    usable_snapshot = None
    usable_snapshot_source = None
    if _same_day_snapshot_ohlc_matched(
        snapshot=snapshot,
        target_quote=target_quote,
        target_date=target_date,
    ):
        usable_snapshot = snapshot
        usable_snapshot_source = snapshot_source
    elif _same_day_snapshot_ohlc_matched(
        snapshot=embedded_snapshot,
        target_quote=target_quote,
        target_date=target_date,
    ):
        usable_snapshot = embedded_snapshot
        usable_snapshot_source = "tencent_kline_embedded_qt_index_49"

    if usable_snapshot:
        snapshot = usable_snapshot
        snapshot_source = usable_snapshot_source
        snapshot_value = to_float_or_none(snapshot.get("volume_ratio"))
        sohu_quote = sohu.get("quote") if isinstance(sohu.get("quote"), dict) else None
        snapshot_ohlc_check = None
        five_day_volume_check = None
        if sohu.get("status") == "ok" and sohu_quote is not None:
            try:
                snapshot_ohlc_check = _snapshot_ohlc_evidence(
                    snapshot_source=snapshot_source,
                    target_date=target_date,
                    snapshot=snapshot,
                    historical_source=vre.SOHU_HISTORY_SOURCE,
                    historical_ohlc=sohu_quote,
                    fetched_at=sohu.get("fetched_at"),
                )
            except vre.EvidenceError:
                snapshot_ohlc_check = None
        if sohu_derived is not None:
            five_day_volume_check = _five_day_volume_check_from_records(
                sohu.get("rows") or [],
                target_date,
                source=vre.SOHU_HISTORY_SOURCE,
                expected_value=snapshot_value,
            tolerance=VOLUME_RATIO_CONFIRM_TOLERANCE,
            fetched_at=sohu.get("fetched_at"),
        )
        cross_check = {
            "value": sohu_derived,
            "source": "sohu_five_day_volume_derived" if sohu_derived is not None else None,
            "source_date": target_date if sohu_derived is not None else None,
            "formula": vre.VOLUME_RATIO_FORMULA_ID,
            "tolerance": VOLUME_RATIO_CONFIRM_TOLERANCE,
            "delta": abs(snapshot_value - sohu_derived)
            if snapshot_value is not None and sohu_derived is not None
            else None,
        }
        auto_confirmed = (
            snapshot_value is not None
            and sohu_derived is not None
            and snapshot_ohlc_check is not None
            and five_day_volume_check is not None
            and cross_check["delta"] <= VOLUME_RATIO_CONFIRM_TOLERANCE
        )
        conflict = snapshot_value is not None and sohu_derived is not None and not auto_confirmed
        verification_status = "confirmed" if auto_confirmed else "conflict" if conflict else "candidate"
        result = {
            "candidate_value": snapshot_value,
            "source": (
                f"{snapshot_source}+sohu_five_day_volume"
                if sohu_derived is not None
                else snapshot_source
            ),
            "source_date": target_date,
            "fetched_at": fetched_at,
            "method": (
                "same_day_snapshot_plus_sohu_five_day_cross_check"
                if sohu_derived is not None
                else "same_day_close_snapshot"
            ),
            "confirmed_by": "automation_cross_check" if auto_confirmed else "none",
            "verification_status": verification_status,
            "cross_check": cross_check,
            "notes": (
                "same-day Tencent close snapshot confirmed by Sohu five-day volume calculation"
                if auto_confirmed
                else "Tencent snapshot conflicts with Sohu five-day volume calculation"
                if conflict
                else "same-day Tencent close snapshot candidate; independent cross-check unavailable"
            ),
            "error_type": None,
            "error_message": None,
        }
        if snapshot_ohlc_check is not None:
            result["snapshot_ohlc_check"] = snapshot_ohlc_check
        if five_day_volume_check is not None:
            result["five_day_volume_check"] = five_day_volume_check
        return result

    if sohu_derived is not None and tencent_derived is not None:
        delta = abs(sohu_derived - tencent_derived)
        auto_confirmed = delta <= HISTORICAL_VOLUME_RATIO_CONFIRM_TOLERANCE
        sohu_five_day_check = _five_day_volume_check_from_records(
            sohu.get("rows") or [],
            target_date,
            source=vre.SOHU_HISTORY_SOURCE,
            expected_value=sohu_derived,
            tolerance=HISTORICAL_VOLUME_RATIO_CONFIRM_TOLERANCE,
            fetched_at=sohu.get("fetched_at"),
        )
        tencent_five_day_check = _five_day_volume_check_from_records(
            records if "records" in locals() else [],
            target_date,
            source=vre.TENCENT_HISTORY_SOURCE,
            expected_value=tencent_derived,
            tolerance=HISTORICAL_VOLUME_RATIO_CONFIRM_TOLERANCE,
            fetched_at=fetched_at,
        )
        return {
            "candidate_value": sohu_derived,
            "source": "sohu_five_day_volume+tencent_five_day_volume",
            "source_date": target_date,
            "fetched_at": fetched_at,
            "method": "historical_five_day_volume_cross_check",
            "confirmed_by": "automation_cross_check" if auto_confirmed else "none",
            "verification_status": "confirmed" if auto_confirmed else "conflict",
            "cross_check": {
                "value": tencent_derived,
                "source": "tencent_five_day_volume_derived",
                "source_date": target_date,
                "formula": vre.VOLUME_RATIO_FORMULA_ID,
                "tolerance": HISTORICAL_VOLUME_RATIO_CONFIRM_TOLERANCE,
                "delta": delta,
            },
            **(
                {
                    "source_volume_checks": {
                        "sohu_history": sohu_five_day_check,
                        "tencent_history": tencent_five_day_check,
                    }
                }
                if sohu_five_day_check is not None and tencent_five_day_check is not None
                else {}
            ),
            **({"five_day_volume_check": tencent_five_day_check} if tencent_five_day_check is not None else {}),
            "notes": (
                "historical volume ratio confirmed from Sohu and Tencent daily volume; "
                "amount-based ratios are not accepted"
                if auto_confirmed
                else "Sohu and Tencent historical volume-derived ratios conflict"
            ),
            "error_type": None,
            "error_message": None,
        }

    if sohu_derived is not None:
        return {
            "candidate_value": sohu_derived,
            "source": "sohu_five_day_volume_derived",
            "source_date": target_date,
            "fetched_at": fetched_at,
            "method": "derived_candidate",
            "confirmed_by": "none",
            "verification_status": "candidate",
            "notes": (
                "derived from Sohu target-day volume divided by prior five trading-day average; "
                "single-source candidate only; amount-based ratios are not accepted"
            ),
            "error_type": type(snapshot_error).__name__ if snapshot_error else None,
            "error_message": str(snapshot_error) if snapshot_error else None,
        }

    if tencent_derived is not None:
        return {
            "candidate_value": tencent_derived,
            "source": "tencent_five_day_volume_derived",
            "source_date": target_date,
            "fetched_at": fetched_at,
            "method": "derived_candidate",
            "confirmed_by": "none",
            "verification_status": "candidate",
            "notes": (
                "derived from Tencent target-day volume divided by prior five trading-day average; "
                "single-source candidate only; amount-based ratios are not accepted"
            ),
            "error_type": type(snapshot_error).__name__ if snapshot_error else None,
            "error_message": str(snapshot_error) if snapshot_error else None,
        }

    final_error = tencent_history_error or snapshot_error or ValueError(
        "same-day snapshot and five-day volume history unavailable"
    )
    return {
        "candidate_value": None,
        "source": "tencent_volume_ratio_chain",
        "source_date": None,
        "fetched_at": fetched_at,
        "method": "unavailable",
        "notes": "same-day snapshot and derived candidate unavailable",
        "error_type": _classify_exception(final_error),
        "error_message": f"{type(final_error).__name__}: {final_error}",
    }


def _fetch_records(
    ak_client: Any,
    *,
    source: str,
    symbol: str,
    target_date: str,
    timeout: float,
) -> dict[str, Any]:
    start_date = (parse_date(target_date) - timedelta(days=14)).strftime("%Y%m%d")
    end_date = parse_date(target_date).strftime("%Y%m%d")
    fetched_at = utc_now_iso_z()

    try:
        with _hard_timeout(timeout, source):
            if source == "tencent":
                prefix = "sz" if symbol.startswith(("0", "3")) else "sh"
                table = ak_client.stock_zh_a_daily(
                    symbol=f"{prefix}{symbol}",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="",
                )
            elif source == "eastmoney":
                table = ak_client.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="",
                )
            else:
                raise ValueError(f"unknown source route: {source}")
    except SourceTimeoutError as exc:
        return {
            "status": "network_error",
            "source": source,
            "target_date": target_date,
            "source_date": None,
            "rows": [],
            "raw_record": None,
            "previous_record": None,
            "source_pct_change": None,
            "source_name": None,
            "quote": None,
            "fetched_at": fetched_at,
            "error_type": "timeout",
            "error_message": str(exc),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": _classify_exception(exc),
            "source": source,
            "target_date": target_date,
            "source_date": None,
            "rows": [],
            "raw_record": None,
            "previous_record": None,
            "source_pct_change": None,
            "source_name": None,
            "quote": None,
            "fetched_at": fetched_at,
            "error_type": _classify_exception(exc),
            "error_message": f"{type(exc).__name__}: {exc}",
        }

    records, invalid_date_row_count = _partition_records_by_date(_record_list_from_table(table))
    if not records:
        invalid_date_message = "no parseable date rows in result set" if invalid_date_row_count else "empty result set"
        return {
            "status": "source_error",
            "source": source,
            "target_date": target_date,
            "source_date": None,
            "rows": [],
            "raw_record": None,
            "previous_record": None,
            "source_pct_change": None,
            "source_name": None,
            "quote": None,
            "fetched_at": fetched_at,
            "error_type": "source_error",
            "error_message": invalid_date_message,
            "invalid_date_row_count": invalid_date_row_count,
        }

    target_index = None
    for index, record in enumerate(records):
        row_date = record_date_text(record)
        if row_date == target_date:
            target_index = index
            break

    if target_index is None:
        return {
            "status": "date_mismatch",
            "source": source,
            "target_date": target_date,
            "source_date": record_date_text(records[-1]),
            "rows": records,
            "raw_record": records[-1],
            "previous_record": records[-2] if len(records) > 1 else None,
            "source_pct_change": to_float_or_none(
                first_not_none(records[-1].get("pct_change"), records[-1].get("涨跌幅"))
            ),
            "source_name": normalize_name_text(
                records[-1].get("name")
                or records[-1].get("名称")
                or records[-1].get("证券简称")
                or records[-1].get("股票简称")
            ),
            "quote": None,
            "fetched_at": fetched_at,
            "error_type": "date_mismatch",
            "error_message": f"returned dates do not include target date {target_date}",
            "invalid_date_row_count": invalid_date_row_count,
        }

    raw_record = records[target_index]
    previous_record = records[target_index - 1] if target_index > 0 else None
    source_date = record_date_text(raw_record)
    source_pct_change = to_float_or_none(first_not_none(raw_record.get("pct_change"), raw_record.get("涨跌幅")))
    source_name = normalize_name_text(
        first_not_none(raw_record.get("name"), raw_record.get("名称"), raw_record.get("证券简称"), raw_record.get("股票简称"))
    )
    if source == "tencent":
        source_pct_change = source_pct_change if source_pct_change is not None else None
    quote = {
        "open": to_float_or_none(first_not_none(raw_record.get("open"), raw_record.get("开盘"))),
        "high": to_float_or_none(first_not_none(raw_record.get("high"), raw_record.get("最高"))),
        "low": to_float_or_none(first_not_none(raw_record.get("low"), raw_record.get("最低"))),
        "close": to_float_or_none(first_not_none(raw_record.get("close"), raw_record.get("收盘"))),
        "prev_close": to_float_or_none(
            first_not_none(
                raw_record.get("prev_close"),
                raw_record.get("昨收"),
                previous_record.get("close") if previous_record else None,
                previous_record.get("收盘") if previous_record else None,
            )
        ),
        "amount": to_float_or_none(first_not_none(raw_record.get("amount"), raw_record.get("成交额"))),
        "turnover_rate": to_float_or_none(first_not_none(raw_record.get("turnover_rate"), raw_record.get("换手率"))),
    }

    if source == "tencent":
        if quote["turnover_rate"] is not None and quote["turnover_rate"] <= 1:
            quote["turnover_rate"] = quote["turnover_rate"] * 100
        if quote["amount"] is not None and quote["amount"] > 100000:
            quote["amount"] = quote["amount"] / 1e8
    elif source == "eastmoney":
        if quote["amount"] is not None and quote["amount"] > 100000:
            quote["amount"] = quote["amount"] / 1e8
    return {
        "status": "ok",
        "source": source,
        "target_date": target_date,
        "source_date": source_date,
        "rows": records,
        "raw_record": raw_record,
        "previous_record": previous_record,
        "quote": quote,
        "source_pct_change": source_pct_change,
        "source_name": source_name,
        "fetched_at": fetched_at,
        "error_type": None,
        "error_message": None,
        "invalid_date_row_count": invalid_date_row_count,
    }


def fetch_primary_quote(ak_client: Any, symbol: str, target_date: str, timeout: float) -> dict[str, Any]:
    if ak_client is None:
        ak_client = _load_akshare_client()
    return _fetch_records(ak_client, source="tencent", symbol=symbol, target_date=target_date, timeout=timeout)


def fetch_fallback_quote(ak_client: Any, symbol: str, target_date: str, timeout: float) -> dict[str, Any]:
    if ak_client is None:
        ak_client = _load_akshare_client()
    return _fetch_records(ak_client, source="eastmoney", symbol=symbol, target_date=target_date, timeout=timeout)


def derive_pct_change(close: float | None, prev_close: float | None) -> float | None:
    if close is None or prev_close in (None, 0):
        return None
    return (close / prev_close - 1.0) * 100.0


def normalize_quote(fetch_result: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], bool]:
    quote_data = fetch_result.get("quote") or {}
    open_value = to_float_or_none(quote_data.get("open"))
    high_value = to_float_or_none(quote_data.get("high"))
    low_value = to_float_or_none(quote_data.get("low"))
    close_value = to_float_or_none(quote_data.get("close"))
    prev_close_value = to_float_or_none(quote_data.get("prev_close"))
    amount_value = to_float_or_none(quote_data.get("amount"))
    turnover_value = to_float_or_none(quote_data.get("turnover_rate"))
    derived_pct = derive_pct_change(close_value, prev_close_value)
    source_pct = to_float_or_none(fetch_result.get("source_pct_change"))
    quote = {
        "open": open_value,
        "high": high_value,
        "low": low_value,
        "close": close_value,
        "prev_close": prev_close_value,
        "pct_change": derived_pct,
        "amount": amount_value,
        "turnover_rate": turnover_value,
    }
    quote_verification: dict[str, Any] = {
        "status": "confirmed" if derived_pct is not None else "needs_manual_check",
        "source_pct_change": source_pct,
        "derived_pct_change": derived_pct,
        "delta": None,
        "source": fetch_result.get("source"),
        "source_date": fetch_result.get("source_date"),
        "fetched_at": fetch_result.get("fetched_at"),
        "notes": None,
        "error_type": fetch_result.get("error_type"),
        "error_message": fetch_result.get("error_message"),
        "field_sources": copy.deepcopy(fetch_result.get("field_sources") or {}),
    }
    if source_pct is not None and derived_pct is not None:
        quote_verification["delta"] = derived_pct - source_pct
        if abs(derived_pct - source_pct) > 0.05:
            quote_verification["status"] = "conflict"
            quote_verification["notes"] = "source pct_change conflicts with derived value"
    elif derived_pct is None:
        quote_verification["status"] = "needs_manual_check"
        quote_verification["notes"] = "derived pct_change unavailable"
    else:
        quote_verification["notes"] = "source pct_change unavailable"
    complete = all(quote.get(field) is not None for field in ("open", "high", "low", "close", "prev_close", "amount", "turnover_rate"))
    return quote, quote_verification, complete


def build_volume_ratio_block(
    *,
    existing_volume_ratio: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
    target_date: str,
    fetched_at: str,
) -> dict[str, Any]:
    locked = is_manual_lock(existing_volume_ratio)
    if locked:
        candidate_value = to_float_or_none(candidate.get("candidate_value")) if candidate and candidate.get("candidate_value") is not None else None
        return merge_preserving_manual_confirmation(
            existing_volume_ratio=existing_volume_ratio,
            fresh_volume_ratio={
                "candidate_value": candidate_value,
                "confirmed_value": None,
                "source": candidate.get("source") if candidate else None,
                "verification": {
                    "status": "manual_confirmed",
                    "method": candidate.get("method") if candidate and candidate.get("method") else "manual",
                    "confirmed_by": candidate.get("confirmed_by") if candidate else None,
                    "source": candidate.get("source") if candidate else None,
                    "source_date": normalize_date_text(candidate.get("source_date")) if candidate else None,
                    "fetched_at": candidate.get("fetched_at") if candidate and candidate.get("fetched_at") else fetched_at,
                    "notes": candidate.get("notes") if candidate else None,
                    "error_type": candidate.get("error_type") if candidate else None,
                    "error_message": candidate.get("error_message") if candidate else None,
                },
                "automation_evidence": {
                    "status": "conflict" if candidate_value is not None else "candidate",
                    "candidate_value": candidate_value,
                    "source": candidate.get("source") if candidate else None,
                    "source_date": normalize_date_text(candidate.get("source_date")) if candidate else None,
                    "fetched_at": candidate.get("fetched_at") if candidate and candidate.get("fetched_at") else fetched_at,
                    "notes": candidate.get("notes") if candidate else None,
                    "error_type": candidate.get("error_type") if candidate else None,
                    "error_message": candidate.get("error_message") if candidate else None,
                },
            },
            target_date=target_date,
            fetched_at=fetched_at,
        )

    merged = {
        "candidate_value": None,
        "confirmed_value": None,
        "source": None,
        "verification": {
            "status": "needs_manual_check",
            "method": "manual" if locked else "source",
            "confirmed_by": "manual_check" if locked else "none",
            "source": None,
            "source_date": None,
            "fetched_at": fetched_at,
            "notes": "volume_ratio requires manual confirmation for historical dates",
            "error_type": None,
            "error_message": None,
        },
    }

    if candidate and candidate.get("candidate_value") is not None:
        candidate_source_date = normalize_date_text(candidate.get("source_date"))
        if candidate_source_date == target_date:
            candidate_value = to_float_or_none(candidate.get("candidate_value"))
            candidate_status = str(candidate.get("verification_status") or "candidate")
            if candidate_status not in {"candidate", "confirmed", "conflict"}:
                candidate_status = "candidate"
            merged["candidate_value"] = candidate_value
            if candidate_status == "confirmed":
                merged["confirmed_value"] = candidate_value
            merged["source"] = candidate.get("source")
            if isinstance(candidate.get("cross_check"), dict):
                merged["cross_check"] = copy.deepcopy(candidate["cross_check"])
            if isinstance(candidate.get("snapshot_ohlc_check"), dict):
                merged["snapshot_ohlc_check"] = copy.deepcopy(candidate["snapshot_ohlc_check"])
            if isinstance(candidate.get("five_day_volume_check"), dict):
                merged["five_day_volume_check"] = copy.deepcopy(candidate["five_day_volume_check"])
            if isinstance(candidate.get("source_volume_checks"), dict):
                merged["source_volume_checks"] = copy.deepcopy(candidate["source_volume_checks"])
            merged["verification"].update(
                {
                    "status": candidate_status,
                    "method": candidate.get("method") or "source",
                    "confirmed_by": candidate.get("confirmed_by") or "none",
                    "source": candidate.get("source"),
                    "source_date": candidate_source_date,
                    "fetched_at": candidate.get("fetched_at") or fetched_at,
                    "notes": candidate.get("notes") or "candidate volume_ratio requires confirmation",
                    "error_type": candidate.get("error_type"),
                    "error_message": candidate.get("error_message"),
                }
            )
        else:
            merged["verification"].update(
                {
                    "status": "rejected" if candidate_source_date else "needs_manual_check",
                    "method": candidate.get("method") or "source_date_check",
                    "confirmed_by": "none",
                    "source": candidate.get("source"),
                    "source_date": candidate_source_date,
                    "fetched_at": candidate.get("fetched_at") or fetched_at,
                    "notes": "volume_ratio source_date does not match target date",
                    "error_type": candidate.get("error_type") or "date_mismatch",
                    "error_message": candidate.get("error_message") or "volume_ratio source_date mismatch",
                }
            )
    else:
        merged["verification"].update(
            {
                "status": "needs_manual_check",
                "method": "unavailable",
                "confirmed_by": "none",
                "source": candidate.get("source") if candidate else None,
                "source_date": normalize_date_text(candidate.get("source_date")) if candidate else None,
                "fetched_at": candidate.get("fetched_at") if candidate and candidate.get("fetched_at") else fetched_at,
                "notes": "volume_ratio unavailable; requires manual confirmation",
                "error_type": candidate.get("error_type") if candidate else None,
                "error_message": candidate.get("error_message") if candidate else None,
            }
        )
    return merged


def merge_preserving_manual_confirmation(
    *,
    existing_volume_ratio: dict[str, Any] | None,
    fresh_volume_ratio: dict[str, Any],
    target_date: str,
    fetched_at: str,
) -> dict[str, Any]:
    if not is_manual_lock(existing_volume_ratio):
        return fresh_volume_ratio
    locked = copy.deepcopy(existing_volume_ratio)
    locked.setdefault("verification", {})
    if not isinstance(locked["verification"], dict):
        locked["verification"] = {}
    locked["verification"] = copy.deepcopy(locked["verification"])
    fresh_candidate = fresh_volume_ratio.get("candidate_value") if isinstance(fresh_volume_ratio, dict) else None
    auto_evidence = copy.deepcopy(fresh_volume_ratio.get("automation_evidence")) if isinstance(fresh_volume_ratio, dict) and isinstance(fresh_volume_ratio.get("automation_evidence"), dict) else {}
    if fresh_candidate is not None:
        fresh_verification = fresh_volume_ratio.get("verification") if isinstance(fresh_volume_ratio, dict) else None
        source_date = fresh_verification.get("source_date") if isinstance(fresh_verification, dict) else None
        fetched_at_value = fresh_verification.get("fetched_at") if isinstance(fresh_verification, dict) else fetched_at
        notes_value = fresh_verification.get("notes") if isinstance(fresh_verification, dict) else None
        error_type_value = fresh_verification.get("error_type") if isinstance(fresh_verification, dict) else None
        error_message_value = fresh_verification.get("error_message") if isinstance(fresh_verification, dict) else None
        source_date_matches_target = source_date == target_date
        status_value = (
            "conflict"
            if locked.get("confirmed_value") is not None and fresh_candidate != locked.get("confirmed_value")
            else "matches_manual_confirmation"
            if source_date_matches_target
            else "source_date_mismatch_same_value"
        )
        locked["automation_evidence"] = auto_evidence
        locked["automation_evidence"].update(
            {
                "status": status_value,
                "latest_candidate_value": fresh_candidate,
                "source": fresh_volume_ratio.get("source") if isinstance(fresh_volume_ratio, dict) else None,
                "source_date": source_date,
                "fetched_at": fetched_at_value,
                "notes": (
                    notes_value
                    if source_date_matches_target or status_value == "conflict"
                    else "same value but source_date does not corroborate target trade_date"
                ),
                "error_type": error_type_value,
                "error_message": error_message_value,
            }
        )
    return locked


def count_core_fields(quote: dict[str, Any]) -> int:
    return sum(1 for field in FETCH_CORE_QUOTE_FIELDS if quote.get(field) is not None)


def is_complete_core_quote(quote: dict[str, Any]) -> bool:
    return count_core_fields(quote) == len(FETCH_CORE_QUOTE_FIELDS)


def quote_verification_is_clean(quote_verification: dict[str, Any] | None) -> bool:
    if not isinstance(quote_verification, dict):
        return False
    return quote_verification.get("status") == "confirmed"


def candidate_quality_score(candidate: dict[str, Any]) -> tuple[int, int, int, int, int]:
    quote = candidate.get("quote") or {}
    quote_verification = candidate.get("quote_verification") if isinstance(candidate, dict) else {}
    source = candidate.get("source") if isinstance(candidate, dict) else None
    return (
        1 if candidate.get("status") == "ok" else 0,
        1 if is_complete_core_quote(quote) else 0,
        1 if quote_verification_is_clean(quote_verification) else 0,
        count_core_fields(quote),
        1 if source == "tencent" else 0,
    )


def quote_quality_issue(candidate: dict[str, Any]) -> dict[str, Any] | None:
    quote_verification = candidate.get("quote_verification") if isinstance(candidate, dict) else {}
    if not isinstance(quote_verification, dict):
        return None
    if quote_verification.get("status") != "conflict":
        return None
    return {
        "source": candidate.get("source") if isinstance(candidate, dict) else None,
        "error_type": "quote_verification_conflict",
        "error_message": quote_verification.get("notes") or "source pct_change conflicts with derived value",
        "fetched_at": candidate.get("fetched_at") if isinstance(candidate, dict) else None,
        "source_date": candidate.get("source_date") if isinstance(candidate, dict) else None,
    }


def determine_run_status(
    *,
    quote_complete: bool,
    quote_result_status: str,
    quote_verification_status: str,
    volume_ratio_status: str,
    context_missing: bool,
    errors: list[dict[str, Any]],
    candidate_present: bool,
) -> str:
    if quote_result_status == "date_mismatch":
        return "date_mismatch"
    if any(error.get("error_type") == "schema_error" for error in errors):
        return "schema_error"
    if not quote_complete and quote_result_status in {"network_error", "source_error", "schema_error"}:
        if all(error.get("error_type") == "network_error" for error in errors if error.get("error_type")):
            return "network_error"
        return "source_error"
    if quote_verification_status == "conflict":
        return "partial"
    if volume_ratio_status in {"needs_manual_check", "rejected", "conflict"}:
        return "partial"
    if context_missing:
        return "partial"
    if quote_complete and not errors and not candidate_present:
        return "success"
    if quote_complete:
        return "partial" if errors or context_missing else "success"
    return "partial"


def _runtime_error_code(status: str) -> int:
    return {
        "success": EXIT_SUCCESS,
        "partial": EXIT_PARTIAL,
        "network_error": EXIT_NETWORK_ERROR,
        "source_error": EXIT_SOURCE_ERROR,
        "schema_error": EXIT_SCHEMA_ERROR,
        "date_mismatch": EXIT_DATE_MISMATCH,
    }.get(status, EXIT_SOURCE_ERROR)


def choose_best_result(current: dict[str, Any] | None, candidate: dict[str, Any]) -> dict[str, Any]:
    if current is None:
        return candidate
    current_score = candidate_quality_score(current)
    candidate_score = candidate_quality_score(candidate)
    if candidate_score > current_score:
        return candidate
    return current


def build_facts_pack(
    *,
    args: argparse.Namespace,
    quote_result: dict[str, Any],
    existing_pack: dict[str, Any] | None,
    volume_ratio_candidate: dict[str, Any] | None,
) -> dict[str, Any]:
    quote, quote_verification, quote_complete = normalize_quote(quote_result)
    fetched_at = quote_result.get("fetched_at") or utc_now_iso_z()
    existing_volume_ratio = existing_pack.get("volume_ratio") if isinstance(existing_pack, dict) else None
    volume_ratio = build_volume_ratio_block(
        existing_volume_ratio=existing_volume_ratio,
        candidate=volume_ratio_candidate,
        target_date=args.date,
        fetched_at=fetched_at,
    )
    existing_missing = existing_pack.get("missing") if isinstance(existing_pack, dict) else {}
    existing_needs_manual_check = existing_pack.get("needs_manual_check") if isinstance(existing_pack, dict) else {}
    name_source = "symbol_fallback"
    name = normalize_name_text(quote_result.get("source_name") or quote_result.get("name"))
    if name:
        name_source = "source"
    else:
        name = normalize_name_text(existing_pack.get("name")) if isinstance(existing_pack, dict) else None
        if name:
            name_source = "existing_pack"
        else:
            name = str(args.symbol)
            name_source = "symbol_fallback"
    needs_manual_check = {
        "volume_ratio": volume_ratio.get("verification", {}).get("status") not in {"confirmed", "manual_confirmed"},
        "market_indices": _mapping_bool(existing_needs_manual_check, "market_indices", True),
        "sector_context": _mapping_bool(existing_needs_manual_check, "sector_context", True),
        "disclosure_status": _mapping_bool(existing_needs_manual_check, "disclosure_status", True),
        "news_policy_context": _mapping_bool(existing_needs_manual_check, "news_policy_context", True),
    }
    missing = {
        "market_indices": _mapping_value(existing_missing, "market_indices", None),
        "sector_context": _mapping_value(existing_missing, "sector_context", None),
        "disclosure_status": _mapping_value(existing_missing, "disclosure_status", None),
        "news_policy_context": _mapping_value(existing_missing, "news_policy_context", None),
    }
    run_status = "success" if quote_complete else "partial"
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now_iso_z(),
        "trade_date": args.date,
        "symbol": args.symbol,
        "name": name,
        "quote": quote,
        "quote_verification": quote_verification,
        "volume_ratio": volume_ratio,
        "missing": missing,
        "needs_manual_check": needs_manual_check,
        "run": {
            "status": run_status,
            "requested_source": args.source,
            "source_used": quote_result.get("source"),
            "target_date": args.date,
            "fetched_at": fetched_at,
            "errors": quote_result.get("errors", []),
            "name_source": name_source,
        },
    }


def compute_final_run_status(facts_pack: dict[str, Any]) -> str:
    quote = facts_pack.get("quote") if isinstance(facts_pack, dict) else {}
    if not isinstance(quote, dict):
        return "partial"
    if any(quote.get(field) is None for field in CORE_QUOTE_FIELDS):
        return "partial"
    quote_verification = facts_pack.get("quote_verification") if isinstance(facts_pack, dict) else {}
    if not isinstance(quote_verification, dict):
        return "partial"
    if quote_verification.get("status") in {"conflict", "needs_manual_check"}:
        return "partial"
    volume_ratio = facts_pack.get("volume_ratio") if isinstance(facts_pack, dict) else {}
    verification = volume_ratio.get("verification") if isinstance(volume_ratio, dict) else {}
    if not isinstance(verification, dict):
        return "partial"
    if verification.get("status") not in {"confirmed", "manual_confirmed"}:
        return "partial"
    needs_manual_check = facts_pack.get("needs_manual_check") if isinstance(facts_pack, dict) else {}
    for key in CONTEXT_MANUAL_CHECK_KEYS:
        if _mapping_bool(needs_manual_check, key, True):
            return "partial"
    return "success"


def _has_any_core_field(quote: dict[str, Any]) -> bool:
    return any(quote.get(field) is not None for field in CORE_QUOTE_FIELDS)


def json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def parse_existing_official_bytes(
    data: bytes | None,
    *,
    symbol: str,
    target_date: str,
) -> dict[str, Any] | None:
    if data is None:
        return None
    try:
        pack = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"schema_error: output JSON is invalid: {exc}") from exc
    return _validate_existing_pack(pack, symbol, target_date)


def snapshot_expected_official_sha(
    output_path: Path,
    *,
    symbol: str,
    target_date: str,
    lock_dir: Path | None,
) -> str | None:
    """Take a short locked pre-fetch snapshot without retaining parsed state."""

    with ofl.official_facts_lock(output_path, lock_dir=lock_dir) as lock_state:
        official_bytes, expected_sha256 = ofl.read_current_official(
            output_path,
            lock_state=lock_state,
        )
        parse_existing_official_bytes(
            official_bytes,
            symbol=symbol,
            target_date=target_date,
        )
        return expected_sha256


def validate_generated_facts_pack(
    facts_pack: dict[str, Any],
    *,
    output_path: Path,
    target_date: str,
) -> None:
    """Run the real review-chain facts rules before a formal generator write."""

    vrc.assert_facts_pack_valid(
        facts_pack,
        facts_pack_path=str(output_path),
        date=target_date,
    )


def _write_generated_bytes_locked(
    output_path: Path,
    payload_bytes: bytes,
    *,
    expected_sha256: str | None,
    lock_state: ofl.OfficialFactsLockState,
) -> str:
    """Write, replace, sync, and fingerprint generator output under one lock."""

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
        ofl.read_locked_official(
            output_path,
            expected_sha256=expected_sha256,
            lock_state=lock_state,
        )
        os.replace(tmp_file, output_path)
        try:
            dir_fd = os.open(str(output_path.parent), os.O_DIRECTORY)
        except OSError:
            dir_fd = None
        if dir_fd is not None:
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        final_bytes, final_sha256 = ofl.read_current_official(
            output_path,
            lock_state=lock_state,
        )
        if final_bytes != payload_bytes or final_sha256 is None:
            raise RuntimeError("written official facts do not match generator bytes")
        return final_sha256
    finally:
        if tmp_file is not None:
            tmp_file.unlink(missing_ok=True)


def write_generated_facts_transaction(
    *,
    args: argparse.Namespace,
    output_path: Path,
    quote_result: dict[str, Any],
    volume_ratio_candidate: dict[str, Any] | None,
    expected_sha256: str | None,
    lock_dir: Path | None,
) -> tuple[dict[str, Any], str, bool, str | None]:
    """Build, validate, and write final generator facts under one held lock."""

    with ofl.official_facts_lock(output_path, lock_dir=lock_dir) as lock_state:
        official_bytes, _actual_sha256 = ofl.read_locked_official(
            output_path,
            expected_sha256=expected_sha256,
            lock_state=lock_state,
        )
        existing_pack = parse_existing_official_bytes(
            official_bytes,
            symbol=args.symbol,
            target_date=args.date,
        )
        facts_pack = build_facts_pack(
            args=args,
            quote_result=quote_result,
            existing_pack=existing_pack,
            volume_ratio_candidate=volume_ratio_candidate,
        )
        run_status = compute_final_run_status(facts_pack)
        facts_pack["run"]["status"] = run_status

        quote_complete = all(
            facts_pack["quote"].get(field) is not None
            for field in (
                "open",
                "high",
                "low",
                "close",
                "prev_close",
                "amount",
                "turnover_rate",
            )
        )
        should_write = True
        if args.dry_run or args.no_write:
            should_write = False
        elif run_status in {"network_error", "source_error", "schema_error", "date_mismatch"}:
            should_write = False
        elif not quote_complete and not args.write_partial:
            should_write = False
        elif not _has_any_core_field(facts_pack["quote"]):
            should_write = False

        final_sha256 = None
        if should_write:
            validate_generated_facts_pack(
                facts_pack,
                output_path=output_path,
                target_date=args.date,
            )
            final_sha256 = _write_generated_bytes_locked(
                output_path,
                json_bytes(facts_pack),
                expected_sha256=expected_sha256,
                lock_state=lock_state,
            )
        return facts_pack, run_status, should_write, final_sha256


def _load_akshare_client() -> Any:
    import akshare as ak  # type: ignore[import-not-found]

    return ak


def _normalize_errors(errors: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for error in errors:
        if not isinstance(error, dict):
            continue
        invalid_date_row_count = error.get("invalid_date_row_count")
        normalized.append(
            {
                "source": error.get("source"),
                "error_type": error.get("error_type"),
                "error_message": error.get("error_message"),
                "fetched_at": error.get("fetched_at"),
                "recovered": error.get("recovered"),
                "invalid_date_row_count": invalid_date_row_count,
            }
        )
    return normalized


def _attempt_fetch_chain(
    *,
    ak_client: Any,
    symbol: str,
    target_date: str,
    source: str,
    timeout: float,
    fetch_primary: Callable[[Any, str, str, float], dict[str, Any]],
    fetch_fallback: Callable[[Any, str, str, float], dict[str, Any]],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str]:
    errors: list[dict[str, Any]] = []
    chosen: dict[str, Any] | None = None
    chosen_issue: dict[str, Any] | None = None
    fatal_status = "source_error"
    saw_date_mismatch = False
    saw_non_date_error = False

    chain: list[tuple[str, Callable[[Any, str, str, float], dict[str, Any]]]]
    if source == "tencent":
        chain = [("tencent", fetch_primary)]
    elif source == "eastmoney":
        chain = [("eastmoney", fetch_fallback)]
    else:
        chain = [("tencent", fetch_primary), ("eastmoney", fetch_fallback)]

    for route_name, fetcher in chain:
        result = fetcher(ak_client, symbol, target_date, timeout)
        result = dict(result or {})
        result.setdefault("source", route_name)
        result.setdefault("target_date", target_date)
        result.setdefault("fetched_at", utc_now_iso_z())
        result.setdefault("errors", [])
        if result.get("status") == "date_mismatch":
            saw_date_mismatch = True
            if source != "auto":
                return result, errors, "date_mismatch"
            errors.append(
                {
                    "source": route_name,
                    "error_type": "date_mismatch",
                    "error_message": result.get("error_message"),
                    "fetched_at": result.get("fetched_at"),
                    "invalid_date_row_count": result.get("invalid_date_row_count"),
                }
            )
            continue
        if result.get("status") in {"network_error", "source_error", "schema_error"}:
            saw_non_date_error = True
            errors.append(
                {
                    "source": route_name,
                    "error_type": result.get("error_type") or result.get("status"),
                    "error_message": result.get("error_message"),
                    "fetched_at": result.get("fetched_at"),
                    "invalid_date_row_count": result.get("invalid_date_row_count"),
                }
            )
            fatal_status = result.get("status") or fatal_status
            continue
        if result.get("status") in {"ok", "partial"}:
            quote, quote_verification, _ = normalize_quote(result)
            result["quote"] = quote
            result["quote_verification"] = quote_verification
            chosen = choose_best_result(chosen, result)
            current_issue = quote_quality_issue(result)
            if chosen is result:
                if chosen_issue is not None and chosen_issue is not current_issue:
                    recovered_issue = dict(chosen_issue)
                    recovered_issue["recovered"] = True
                    errors.append(recovered_issue)
                chosen_issue = current_issue
            else:
                if current_issue is not None:
                    recovered_issue = dict(current_issue)
                    recovered_issue["recovered"] = True
                    errors.append(recovered_issue)
            fatal_status = result.get("status") or fatal_status
            if result.get("status") == "ok" and is_complete_core_quote(result.get("quote") or {}) and quote_verification_is_clean(result.get("quote_verification")):
                break

    if chosen is not None:
        if chosen_issue is not None:
            errors.append(chosen_issue)
        if errors:
            recovered_errors = []
            for error in errors:
                recovered_error = dict(error)
                if error is not chosen_issue:
                    recovered_error["recovered"] = True
                recovered_errors.append(recovered_error)
            errors = recovered_errors
        return chosen, errors, chosen.get("status") or fatal_status

    if saw_date_mismatch and not saw_non_date_error:
        return None, errors, "date_mismatch"
    if any(error.get("error_type") == "schema_error" for error in errors):
        return None, errors, "schema_error"
    if saw_non_date_error and all(error.get("error_type") in {"network_error", "timeout"} for error in errors if error.get("error_type")):
        return None, errors, "network_error"
    if saw_non_date_error:
        return None, errors, "source_error"
    if saw_date_mismatch:
        return None, errors, "date_mismatch"
    return None, errors, fatal_status


def run(
    args: argparse.Namespace,
    *,
    fetch_primary: Callable[[Any, str, str, float], dict[str, Any]] = fetch_tencent_direct_quote,
    fetch_fallback: Callable[[Any, str, str, float], dict[str, Any]] = fetch_fallback_quote,
    volume_ratio_candidate_provider: Callable[[str, str, float], dict[str, Any] | None] | None = None,
    ak_client: Any | None = None,
) -> RunOutcome:
    output_path = Path(args.output)
    if getattr(args, "timeout", 0) <= 0:
        return RunOutcome(
            exit_code=EXIT_SCHEMA_ERROR,
            facts_pack=None,
            wrote_file=False,
            output_path=str(output_path),
            status="schema_error",
        )
    lock_dir = Path(args.lock_dir) if getattr(args, "lock_dir", None) else None
    try:
        expected_output_sha256 = snapshot_expected_official_sha(
            output_path,
            symbol=args.symbol,
            target_date=args.date,
            lock_dir=lock_dir,
        )
    except ValueError as exc:
        message = str(exc)
        status = "schema_error" if message.startswith("schema_error") else "date_mismatch"
        return RunOutcome(
            exit_code=_runtime_error_code(status),
            facts_pack=None,
            wrote_file=False,
            output_path=str(output_path),
            status=status,
        )

    client = ak_client
    quote_result, errors, fatal_status = _attempt_fetch_chain(
        ak_client=client,
        symbol=args.symbol,
        target_date=args.date,
        source=args.source,
        timeout=args.timeout,
        fetch_primary=fetch_primary,
        fetch_fallback=fetch_fallback,
    )
    if quote_result is None:
        status = fatal_status if fatal_status in {"network_error", "source_error", "schema_error", "date_mismatch"} else "source_error"
        return RunOutcome(
            exit_code=_runtime_error_code(status),
            facts_pack=None,
            wrote_file=False,
            output_path=str(output_path),
            status=status,
        )
    quote_result = dict(quote_result)
    quote_result["errors"] = _normalize_errors([*(quote_result.get("errors") or []), *errors])
    if quote_result.get("status") == "date_mismatch":
        return RunOutcome(
            exit_code=EXIT_DATE_MISMATCH,
            facts_pack=None,
            wrote_file=False,
            output_path=str(output_path),
            status="date_mismatch",
        )

    volume_ratio_candidate = (
        volume_ratio_candidate_provider(args.symbol, args.date, args.timeout)
        if volume_ratio_candidate_provider
        else None
    )
    try:
        facts_pack, run_status, should_write, output_sha256 = write_generated_facts_transaction(
            args=args,
            output_path=output_path,
            quote_result=quote_result,
            volume_ratio_candidate=volume_ratio_candidate,
            expected_sha256=expected_output_sha256,
            lock_dir=lock_dir,
        )
    except (ofl.OfficialFactsChangedError, ValueError):
        return RunOutcome(
            exit_code=EXIT_SCHEMA_ERROR,
            facts_pack=None,
            wrote_file=False,
            output_path=None,
            status="schema_error",
        )

    exit_code = _runtime_error_code(run_status)
    if run_status == "success":
        exit_code = EXIT_SUCCESS
    elif run_status == "partial":
        exit_code = EXIT_PARTIAL

    return RunOutcome(
        exit_code=exit_code,
        facts_pack=facts_pack,
        wrote_file=should_write,
        output_path=str(output_path) if should_write else None,
        status=run_status,
        output_sha256=output_sha256,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    outcome = run(args, volume_ratio_candidate_provider=fetch_volume_ratio_candidate)
    if args.dry_run:
        print(json.dumps(outcome.facts_pack, ensure_ascii=False, indent=2))
        if args.emit_runner_marker and isinstance(outcome.facts_pack, dict):
            print(
                CANDIDATE_STDOUT_MARKER
                + json.dumps(outcome.facts_pack, ensure_ascii=False, separators=(",", ":"))
            )
    elif args.no_write:
        print(
            json.dumps(
                {
                    "status": outcome.status,
                    "exit_code": outcome.exit_code,
                    "source_used": outcome.facts_pack.get("run", {}).get("source_used") if outcome.facts_pack else None,
                    "output": outcome.output_path,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(
            json.dumps(
                {
                    "status": outcome.status,
                    "exit_code": outcome.exit_code,
                    "source_used": outcome.facts_pack.get("run", {}).get("source_used") if outcome.facts_pack else None,
                    "output": outcome.output_path,
                    "wrote_file": outcome.wrote_file,
                    "output_sha256": outcome.output_sha256,
                },
                ensure_ascii=False,
            )
        )
    return outcome.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
