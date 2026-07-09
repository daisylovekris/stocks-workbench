#!/usr/bin/env python3
"""
validate_review_chain.py

Local-only Markdown validator for review-chain documents.

Scope for v1:
- section-aware linting
- no network access
- no行情源 lookup
- no auto-fix
- no business-document mutation

Implemented first:
- R004_CURRENT_SECTION_STALE_DATE
- R007_CURRENT_SECTION_BOUNDARY
- R005_CURRENT_SECTION_STALE_LEVEL
- R003_SUPPORT_OR_BOTTOM_MISLABEL
- R008_INDEX_OR_ASSOCIATED_FILES_STATUS

Reserved / placeholder hooks:
- R001_ACTION_LANGUAGE
- R002_RISK_RELIEF_OVERCLAIM
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


CURRENT_HEADING_KEYWORDS = [
    "当前",
    "本卡当前结论",
    "本卡结论",
    "底部本卡结论",
    "当前本卡结论",
    "当前观察重心",
    "当前状态",
    "当前判断",
    "当前纪律",
    "当前背景",
    "当前主矛盾",
    "当前不能",
    "可以进入",
    "重新评估",
    "分层观察区间",
    "当前最值得观察",
    "需要补充的数据",
    "关联文件",
    "维护状态",
    "当日结论",
    "今日结论",
    "今日风险结论",
    "风险结论",
    "观察结论",
    "当日判断",
    "今日判断",
    "盘后结论",
    "复盘结论",
    "可以继续观察",
    "继续观察的情况",
    "不能进入",
    "暂不进入",
    "重新评估",
    "观察区间",
    "分层观察",
]

OBSERVATION_HEADING_KEYWORDS = [
    "上周五收盘后的状态摘要",
    "下周一关键价位观察",
    "下周关键价位观察",
    "关键价位观察",
    "下周观察",
    "本周观察",
    "周一观察",
    "盘前观察",
    "盘中观察",
    "盘后观察",
    "状态摘要",
    "观察重点",
    "观察清单",
    "观察计划",
    "周末消息检查清单",
    "消息检查清单",
    "三种情景",
    "风险观察",
    "估值与加仓纪律",
    "盘前需要补充的数据",
    "周一盘前需要补充的数据",
    "本周",
    "下周",
    "下周一",
]

HISTORY_HEADING_KEYWORDS = [
    "历史资料",
    "历史记录",
    "历史回顾",
    "旧复盘",
    "旧观察",
    "归档",
]

ACTION_KEYWORDS = [
    "可以买",
    "可以补",
    "适合补",
    "加仓",
    "卖出",
    "买入",
    "减仓",
    "清仓",
    "补仓",
]

SUPPORT_KEYWORDS = [
    "硬底",
    "新支撑",
    "支撑确认",
    "估值底",
    "底部确认",
    "铁底",
    "必守底",
    "安全区",
]

BROAD_SUPPORT_KEYWORDS = [
    "支撑位",
    "修复支撑",
    "成为支撑",
    "已经成为支撑",
    "形成支撑",
    "支撑成立",
    "结构性支撑",
    "估值支撑",
    "价格支撑",
    "关键支撑",
    "强支撑",
]

BROAD_SUPPORT_ASSERTION_MARKERS = [
    "已经成为",
    "已成为",
    "成为",
    "形成",
    "成立",
    "确认",
    "已经是",
    "已是",
    "就是",
    "即是",
]

BROAD_SUPPORT_OBSERVATION_MARKERS = [
    "能否",
    "是否",
    "观察",
    "需继续",
    "继续作为",
    "尝试",
    "可能",
]

RISK_RELIEF_KEYWORDS = [
    "风险解除",
    "有效修复完成",
    "止跌确认",
    "底部确认",
    "加仓成熟",
    "趋势完全重启",
]

ANNOUNCEMENT_ASSERTION_RE = re.compile(
    r"(?:未见|暂未见|无|没有|不存在).{0,24}公告级.{0,16}(?:利好|利空|爆雷)"
)

CURRENT_FRAME_TOKENS = [
    "当前",
    "当前判断",
    "当前口径",
    "当前主矛盾",
    "当前定性",
    "当前结论",
    "当前背景",
    "当前纪律",
    "当前状态",
    "当前收盘价",
    "当前浮亏",
    "当前低位观察重心",
    "本卡当前结论",
    "本卡结论",
    "分层观察区间",
]


@dataclass
class Finding:
    file: str
    line: int
    section: str
    rule_id: str
    severity: str
    disposition: str
    matched_text: str
    reason: str
    suggested_fix: str


RULE_REGISTRY = {
    "R001_ACTION_LANGUAGE": {
        "enabled": False,
        "severity_default": "P2",
        "notes": "Reserved for second pass; explicit automation / auto-trade forms may later rise to P0.",
    },
    "R002_RISK_RELIEF_OVERCLAIM": {
        "enabled": False,
        "severity_default": "P2",
        "notes": "Reserved for second pass.",
    },
    "R003_SUPPORT_OR_BOTTOM_MISLABEL": {
        "enabled": True,
        "severity_default": "P1",
        "notes": "Flag hard-bottom / support overclaims on key levels in current sections.",
    },
    "R004_CURRENT_SECTION_STALE_DATE": {
        "enabled": True,
        "severity_default": "P2",
        "notes": "Flag stale old-date references in current sections.",
    },
    "R005_CURRENT_SECTION_STALE_LEVEL": {
        "enabled": True,
        "severity_default": "P2",
        "notes": "Flag stale level identity in current sections.",
    },
    "R006_DISCLOSURE_NEEDS_MANUAL_CHECK": {
        "enabled": True,
        "severity_default": "P2",
        "notes": "Lightweight safety gate for announcement-status assertions.",
    },
    "R007_CURRENT_SECTION_BOUNDARY": {
        "enabled": True,
        "severity_default": "P3",
        "notes": "Summarize current-zone not-advanced situations.",
    },
    "R008_INDEX_OR_ASSOCIATED_FILES_STATUS": {
        "enabled": True,
        "severity_default": "P2",
        "notes": "Flag stale workflow ledger text such as 后续待同步 in current sections.",
    },
}


def _strip_heading_markers(line: str) -> str:
    text = line.lstrip("#").strip()
    text = re.sub(r"^\d+(?:、|\.\s+)", "", text)
    return text


def _is_date_heading(line: str) -> bool:
    return bool(re.match(r"^\s*#{1,6}\s*\d{4}-\d{2}-\d{2}\b", line))


def _extract_date_heading(line: str) -> Optional[str]:
    match = re.match(r"^\s*#{1,6}\s*(\d{4}-\d{2}-\d{2})\b", line)
    if not match:
        return None
    return match.group(1)


def _is_heading(line: str) -> bool:
    return bool(re.match(r"^\s*#{1,6}\s+", line))


def _heading_level(line: str) -> Optional[int]:
    match = re.match(r"^\s*(#{1,6})\s+", line)
    if not match:
        return None
    return len(match.group(1))


def _is_current_heading(heading_text: str) -> bool:
    return any(keyword in heading_text for keyword in CURRENT_HEADING_KEYWORDS)


def _is_observation_heading(heading_text: str) -> bool:
    return any(keyword in heading_text for keyword in OBSERVATION_HEADING_KEYWORDS)


def _is_history_heading(heading_text: str) -> bool:
    return any(keyword in heading_text for keyword in HISTORY_HEADING_KEYWORDS)


def _short_date(date_text: Optional[str]) -> Optional[str]:
    if not date_text:
        return None
    m = re.match(r"^\d{4}-(\d{2})-(\d{2})$", date_text)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}"


def _normalize_relative(path: str) -> str:
    return str(Path(path).as_posix())


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _run_git(args: List[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or str(exc)).strip()
        raise SystemExit(f"git command failed: git {' '.join(args)}: {message}") from exc
    return result.stdout


def _get_staged_paths() -> List[str]:
    output = _run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    return [line.strip() for line in output.splitlines() if line.strip()]


def _load_staged_file(path: str) -> Optional[str]:
    try:
        return _run_git(["show", f":{path}"])
    except SystemExit as exc:
        os.write(2, f"warning: skipping staged file without readable blob: {path}\n".encode("utf-8"))
        return None


def _load_facts_pack(path: Optional[str]) -> Optional[dict]:
    if not path:
        return None
    candidate = Path(path)
    if not candidate.exists():
        return None
    try:
        return json.loads(candidate.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_invalid_json": True}


def _is_falseish(value: object) -> bool:
    if value is None or value is False:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {
            "",
            "false",
            "0",
            "none",
            "null",
            "no",
            "off",
            "confirmed",
            "checked",
            "verified",
            "clear",
            "no_missing",
            "complete",
        }
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _is_truthy_manual_check_value(value: object) -> bool:
    if value is True:
        return True
    if _is_falseish(value):
        return False
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "":
            return False
        if lowered in {
            "needs_manual_check",
            "manual_check",
            "missing",
            "unknown",
            "pending",
            "todo",
            "unverified",
        }:
            return True
        return True
    return bool(value)


def _facts_needs_manual_check(facts_pack: Optional[dict]) -> bool:
    if not facts_pack or facts_pack.get("_invalid_json"):
        return True
    relevant_keys = {"disclosure_status", "news_policy_context", "news", "policy"}
    has_relevant_signal = False
    needs_manual_check = facts_pack.get("needs_manual_check")
    if isinstance(needs_manual_check, bool):
        if needs_manual_check:
            return True
    elif isinstance(needs_manual_check, dict):
        for key, value in needs_manual_check.items():
            if key in relevant_keys:
                has_relevant_signal = True
                if _is_truthy_manual_check_value(value):
                    return True
    elif isinstance(needs_manual_check, list):
        for item in needs_manual_check:
            if not isinstance(item, str):
                continue
            lowered = item.lower()
            if any(token in lowered for token in ("disclosure", "news", "policy")):
                has_relevant_signal = True
                return True
    elif needs_manual_check is not None and _is_truthy_manual_check_value(needs_manual_check):
        return True

    missing = facts_pack.get("missing")
    if isinstance(missing, dict):
        for key in relevant_keys:
            if key not in missing:
                continue
            has_relevant_signal = True
            value = missing.get(key)
            if value is None:
                return True
            if _is_truthy_manual_check_value(value):
                return True
        return not has_relevant_signal
    if isinstance(missing, list):
        for item in missing:
            if not isinstance(item, str):
                continue
            lowered = item.lower()
            if any(token in lowered for token in ("disclosure", "news", "policy")):
                has_relevant_signal = True
                return True
        return not has_relevant_signal
    if missing is not None:
        return _is_truthy_manual_check_value(missing)
    return not has_relevant_signal


def _line_excerpt(line: str, limit: int = 160) -> str:
    text = line.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _is_negative_write_as_context(text: str) -> bool:
    return bool(
        re.search(
            r"(不|不能|不应|不把|不算|不是|并非).{0,120}写成",
            text,
        )
    )


def _date_tokens_in_text(text: str) -> List[str]:
    tokens: List[str] = []
    for token in re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", text):
        if token not in tokens:
            tokens.append(token)
    for token in re.findall(r"(?<!\d-)(?<!\d)(\d{2}-\d{2})(?=$|[^\d-])", text):
        if token not in tokens:
            tokens.append(token)
    return tokens


def _current_date_tokens(current_date: Optional[str]) -> List[str]:
    tokens = []
    if current_date:
        tokens.append(current_date)
    short = _short_date(current_date)
    if short:
        tokens.append(short)
    return tokens


def _is_comparison_reference_for_tokens(text: str, date_tokens: Sequence[str]) -> bool:
    if not date_tokens:
        return False
    if not any(token in text for token in date_tokens):
        return False
    for token in date_tokens:
        escaped = re.escape(token)
        scoped_patterns = [
            rf"(?:低于|高于|相比|较)\s*{escaped}(?:\s*的)?",
            rf"从\s*{escaped}\s*的.{{0,48}}升级为",
            rf"{escaped}.{{0,16}}(?:刷新|新低|新高)",
            rf"(?:刷新|新低|新高).{{0,16}}{escaped}",
        ]
        if not any(re.search(pattern, text) for pattern in scoped_patterns):
            return False
    return True


def _is_comparison_reference_line(text: str, previous_date: Optional[str], prev_short: Optional[str]) -> bool:
    return _is_comparison_reference_for_tokens(
        text,
        [token for token in (previous_date, prev_short) if token],
    )


def _is_stale_date_anchor_line(text: str, date_tokens: Sequence[str]) -> bool:
    if not date_tokens:
        return False
    stripped = text.strip()
    if stripped.startswith("#") and not any(marker in stripped for marker in ("截至", "沿用", "仍按", "维持")):
        return False
    for token in date_tokens:
        escaped = re.escape(token)
        stale_patterns = [
            rf"截至\s*{escaped}",
            rf"(?:仍按|仍沿用|沿用|按)\s*{escaped}",
            rf"{escaped}\s*[：:]\s*(?:当前|今日|本卡|口径|结论|观察)",
            rf"(?:当前|今日|本卡|口径|结论|观察).{{0,24}}(?:仍按|仍沿用|沿用|维持不变|维持).{{0,24}}{escaped}",
            rf"{escaped}.{{0,16}}(?:口径|结论).{{0,16}}(?:执行|维持|不变|沿用)",
        ]
        if any(re.search(pattern, text) for pattern in stale_patterns):
            return True
    return False


def _is_negative_support_context(text: str) -> bool:
    negative_patterns = [
        r"不是\s*硬底",
        r"不是\s*新硬底",
        r"不是\s*支撑位",
        r"不是\s*结构性支撑",
        r"不是\s*底部确认",
        r"不把.*当作硬底",
        r"不能把.*当作硬底",
        r"不能把.*当作支撑位",
        r"不因为.*就把它当作硬底",
        r"不因为.*就把它当作估值底",
        r"不因为.*就判断底部确认",
        r"不因为.*底部确认",
        r"不得视为支撑确认",
        r"不得视为新支撑",
        r"不是支撑确认",
        r"不等于支撑确认",
        r"不代表底部确认",
        r"不是底部确认",
        r"不等于底部确认",
        r"未构成底部确认",
        r"不能视为底部确认",
        r"不构成硬底",
        r"不构成支撑",
        r"不能视为硬底",
        r"不能视为支撑",
        r"不能视为新支撑",
        r"不能把.*当作新支撑",
        r"不能把.*当作支撑",
        r"不得把.*当作支撑",
        r"不能视为支撑确认",
        r"不视为支撑确认",
        r"不构成支撑确认",
    ]
    return any(re.search(pattern, text) for pattern in negative_patterns)


def _has_negative_support_intro(text: str) -> bool:
    intro_patterns = [
        r"^\s*\*{0,2}不是：?\*{0,2}\s*$",
        r"不能写成",
        r"不得写成",
        r"不应写成",
        r"禁止写成",
        r"不能理解为",
        r"不代表",
        r"不等于",
        r"不视为",
        r"不作为",
    ]
    for line in text.splitlines():
        if any(re.search(pattern, line) for pattern in intro_patterns):
            return True
    return False


def _is_negative_disclosure_instruction(text: str) -> bool:
    instruction_patterns = [
        r"不能把.*写成",
        r"不得把.*写成",
        r"不应把.*写成",
        r"不把.*写成",
        r"不把.*当作",
        r"不能写成",
        r"不得写成",
        r"不应写成",
        r"禁止写成",
        r"待核对状态.*不能写成",
        r"不因为.*就",
    ]
    return any(re.search(pattern, text) for pattern in instruction_patterns)


def _is_in_negative_disclosure_list(lines: Sequence[str], index: int) -> bool:
    line = lines[index].lstrip()
    if not re.match(r"^[-*]\s+", line):
        return False
    start = max(0, index - 3)
    intro = "\n".join(lines[start:index])
    intro_patterns = [
        r"不是：?\s*$",
        r"最值得观察的不是",
        r"当前最值得观察的不是",
    ]
    return any(re.search(pattern, intro) for pattern in intro_patterns)


def _match_announcement_assertion(text: str) -> Optional[str]:
    match = ANNOUNCEMENT_ASSERTION_RE.search(text)
    if not match:
        return None
    return match.group(0)


def _is_path_recap_line(text: str) -> bool:
    stripped = text.lstrip()
    return bool(
        re.match(
            r"^(?:[-*]\s*)?(?:20\d{2}-\d{2}-\d{2}|\d{2}-\d{2})[：:\s]",
            stripped,
        )
    )


def _path_recap_label(text: str) -> Optional[str]:
    stripped = text.lstrip()
    match = re.match(r"^(?:[-*]\s*)?(20\d{2}-\d{2}-\d{2}|\d{2}-\d{2})[：:\s]", stripped)
    if not match:
        return None
    return match.group(1)


def _path_label_has_immediate_current_anchor(text: str) -> bool:
    stripped = text.lstrip()
    match = re.match(r"^(?:[-*]\s*)?(?:20\d{2}-\d{2}-\d{2}|\d{2}-\d{2})[：:\s](.{0,24})", stripped)
    if not match:
        return False
    return _is_current_frame_line(match.group(1))


def _is_current_date_label(label: Optional[str], current_date: Optional[str]) -> bool:
    if not label or not current_date:
        return False
    return label == current_date or label == _short_date(current_date)


def _is_historical_index_row(line: str, current_date: Optional[str]) -> bool:
    if not current_date or not line.lstrip().startswith("|"):
        return False
    current_short = _short_date(current_date)
    full_dates = re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", line)
    short_dates = re.findall(r"(?<!\d-)(?<!\d)(\d{2}-\d{2})(?!-\d)", line)
    if current_date in full_dates or (current_short and current_short in short_dates):
        return False
    historical_file_signal = re.search(
        r"(?:sungrow_review|weekly_market_watch)_20\d{2}-\d{2}-\d{2}\.md",
        line,
    )
    historical_update_signal = re.search(r"(?<!\d-)(?<!\d)\d{2}-\d{2}\s*更新", line)
    historical_ledger_signal = any(token in line for token in ("历史链接", "历史归档", "已封箱", "归档"))
    return bool(historical_file_signal or historical_update_signal or historical_ledger_signal)


def _is_history_recap_context(section: str, nearby_context: str) -> bool:
    text = f"{section}\n{nearby_context}"
    recap_keywords = (
        "路径回顾",
        "历史回顾",
        "前期路径",
        "复盘路径",
        "走势回顾",
        "历史记录",
        "关键价位复盘",
        "上一交易周路径",
        "上一阶段路径",
    )
    return any(keyword in text for keyword in recap_keywords)


def _is_comparison_section_context(section: str) -> bool:
    comparison_keywords = ("关系", "对比", "相比", "比较")
    return any(keyword in section for keyword in comparison_keywords)


def _is_current_frame_line(text: str) -> bool:
    return any(token in text for token in CURRENT_FRAME_TOKENS)


def _is_safe_current_observation(text: str) -> bool:
    safe_patterns = [
        "不是支撑确认",
        "不是新支撑",
        "不是新硬底",
        "不是硬底",
        "不是估值底",
        "只是当日收盘价",
        "只是收盘价",
        "已重新收回的近端位",
        "重新收回的近端位",
        "只是被重新收回",
        "新低点，不是新硬底",
        "仍只是员工持股心理锚",
        "不是新支撑位",
        "不是结构性支撑位",
        "若后续继续跌破",
        "若继续跌破",
        "若重新收回",
        "若能重新收回",
    ]
    if any(pattern in text for pattern in safe_patterns):
        return True
    if "收盘" in text and "重新收回" in text:
        return True
    if "重新收回" in text and ("近端位" in text or "近端失守位" in text):
        return True
    if "能否重新收回" in text:
        return True
    return False


def _nearby_context_text(lines: List[str], index: int, window: int = 3) -> str:
    start = max(0, index - window)
    return "\n".join(lines[start:index + 1])


def _negative_support_window(lines: List[str], index: int, window: int = 3) -> str:
    start = max(0, index - window)
    return "\n".join(lines[start:index + 1])


def _is_in_negative_support_list(lines: List[str], index: int) -> bool:
    for cursor in range(index - 1, -1, -1):
        candidate = lines[cursor].strip()
        if not candidate:
            return False
        if _has_negative_support_intro(candidate):
            return True
        if candidate.startswith(("-", "*")):
            continue
        return False
    return False


def _section_for_line(line_no: int, sections: List[tuple[int, str, str]]) -> tuple[str, str]:
    current_heading = "root"
    current_kind = "current"
    for start_line, heading, kind in sections:
        if start_line <= line_no:
            current_heading = heading
            current_kind = kind
        else:
            break
    return current_heading, current_kind


def _build_section_map(lines: List[str], *, current_date: Optional[str] = None) -> List[tuple[int, str, str]]:
    sections: List[tuple[int, str, str]] = []
    seen_history = False
    current_heading = "root"
    current_kind = "current"
    active_dated_level: Optional[int] = None
    active_dated_kind: Optional[str] = None
    active_current_level: Optional[int] = None
    active_current_kind: Optional[str] = None
    active_history_level: Optional[int] = None
    active_history_kind: Optional[str] = None

    for idx, line in enumerate(lines, start=1):
        if _is_heading(line):
            heading_text = _strip_heading_markers(line)
            heading_date = _extract_date_heading(line)
            level = _heading_level(line) or 1
            if active_history_level is not None and level <= active_history_level:
                active_history_level = None
                active_history_kind = None
            if heading_date:
                if current_date and heading_date == current_date:
                    current_kind = "current"
                else:
                    seen_history = True
                    current_kind = "history"
                active_dated_level = level
                active_dated_kind = current_kind
                active_current_level = None
                active_current_kind = None
            elif _is_history_heading(heading_text):
                current_kind = "history"
                seen_history = True
                active_history_level = level
                active_history_kind = current_kind
                if active_dated_level is not None and level <= active_dated_level:
                    active_dated_level = None
                    active_dated_kind = None
                if active_current_level is not None and level <= active_current_level:
                    active_current_level = None
                    active_current_kind = None
            elif active_history_level is not None and level > active_history_level:
                current_kind = active_history_kind or "history"
            elif active_dated_level is not None and level > active_dated_level:
                current_kind = active_dated_kind or "history"
            elif active_current_level is not None and level > active_current_level:
                current_kind = active_current_kind or "current"
            elif _is_current_heading(heading_text) or _is_observation_heading(heading_text):
                current_kind = "current"
                if active_dated_level is not None and level <= active_dated_level:
                    active_dated_level = None
                    active_dated_kind = None
                if active_current_level is not None and level <= active_current_level:
                    active_current_level = None
                    active_current_kind = None
                active_current_level = level
                active_current_kind = current_kind
            elif not seen_history:
                current_kind = "current"
                if active_dated_level is not None and level <= active_dated_level:
                    active_dated_level = None
                    active_dated_kind = None
                if active_current_level is not None and level <= active_current_level:
                    active_current_level = None
                    active_current_kind = None
            else:
                current_kind = "history"
                if active_dated_level is not None and level <= active_dated_level:
                    active_dated_level = None
                    active_dated_kind = None
                if active_current_level is not None and level <= active_current_level:
                    active_current_level = None
                    active_current_kind = None
            current_heading = heading_text
            sections.append((idx, current_heading, current_kind))
    if not sections:
        sections.append((1, "root", "current"))
    return sections


def _contains_date_heading(text: str) -> bool:
    return any(_is_date_heading(line) for line in text.splitlines())


def _match_any(text: str, candidates: Iterable[str]) -> Optional[str]:
    for candidate in candidates:
        if candidate in text:
            return candidate
    return None


def _find_key_level_hits(text: str, key_levels: List[str]) -> List[str]:
    hits = []
    for key_level in key_levels:
        if key_level and re.search(rf"(?<![\d.]){re.escape(key_level)}(?![\d.])", text):
            hits.append(key_level)
    return hits


def _compose_matched_text(line: str, section_heading: str, heading_contributed: bool) -> str:
    excerpt = _line_excerpt(line)
    if heading_contributed and section_heading and section_heading != "root":
        return f"section heading: {section_heading} | line: {excerpt}"
    return excerpt


def _is_support_observation_question(text: str) -> bool:
    support_phrase = (
        "硬底",
        "新硬底",
        "估值底",
        "底部确认",
        "支撑确认",
        "支撑位",
        "修复支撑",
        "成为支撑",
        "形成支撑",
        "支撑成立",
        "结构性支撑",
        "估值支撑",
        "价格支撑",
        "关键支撑",
        "强支撑",
    )
    phrase_pattern = "|".join(re.escape(phrase) for phrase in support_phrase)
    return bool(
        re.search(rf"(?:能否|是否).{{0,12}}(?:{phrase_pattern})", text)
        or re.search(rf"(?:{phrase_pattern}).{{0,12}}(?:能否|是否).{{0,12}}(?:成立|确认|构成|形成)?", text)
    )


def _is_observation_only_support_question(text: str) -> bool:
    if _is_support_label_assertion(text):
        return False
    if _is_support_observation_question(text):
        return True
    observation_markers = (
        "是否",
        "能否",
        "观察",
        "再评估",
        "仍需观察",
        "后续确认",
        "需后续确认",
    )
    assertion_markers = (
        "已经",
        "已",
        "成为",
        "形成",
        "成立",
        "确认成立",
        "就是",
        "即是",
    )
    return any(marker in text for marker in observation_markers) and not any(
        marker in text for marker in assertion_markers
    )


def _is_hedged_support_observation(text: str) -> bool:
    if _is_support_label_assertion(text):
        return False
    hedge_markers = (
        "可能",
        "尝试",
        "有望",
        "尚需",
        "仍需",
        "需继续",
        "需要继续",
        "继续观察",
        "仍需继续观察",
        "需后续确认",
        "后续确认",
    )
    support_action_markers = (
        "形成支撑",
        "形成关键支撑",
        "形成修复支撑",
        "成为支撑",
        "成为支撑位",
        "构成支撑",
        "构成底部确认",
        "支撑成立",
        "底部确认成立",
    )
    return any(marker in text for marker in hedge_markers) and any(
        marker in text for marker in support_action_markers
    )


def _is_support_label_assertion(text: str) -> bool:
    label_phrase = (
        "支撑位",
        "新支撑",
        "关键支撑",
        "强支撑",
        "修复支撑",
        "结构性支撑",
        "估值支撑",
        "价格支撑",
    )
    phrase_pattern = "|".join(re.escape(phrase) for phrase in label_phrase)
    return bool(re.search(rf"(?:就是|即是|(?<![不只否])是(?!否)).{{0,6}}(?:{phrase_pattern})", text))


def _is_positive_support_claim(text: str) -> bool:
    if _is_hedged_support_observation(text):
        return False
    if _is_observation_only_support_question(text):
        return False
    if _match_any(text, SUPPORT_KEYWORDS):
        pass
    elif _match_any(text, BROAD_SUPPORT_KEYWORDS):
        has_assertion_marker = any(marker in text for marker in BROAD_SUPPORT_ASSERTION_MARKERS)
        has_label_assertion = _is_support_label_assertion(text)
        if has_assertion_marker or has_label_assertion:
            pass
        elif _is_support_observation_question(text):
            return False
        elif any(marker in text for marker in BROAD_SUPPORT_OBSERVATION_MARKERS):
            return False
    else:
        return False
    negative_support_pattern = re.compile(
        r"(不是|不能|不应|不把|不算|并非|未|无).{0,12}(硬底|新支撑|支撑位|修复支撑|成为支撑|形成支撑|支撑成立|结构性支撑|估值支撑|价格支撑|关键支撑|强支撑|支撑确认|估值底|底部确认|铁底|必守底|安全区)"
    )
    if negative_support_pattern.search(text):
        return False
    return True


def _segment_can_inherit_key_level(segment: str) -> bool:
    return bool(
        re.match(
            r"^(?:只是|仍是|仍然是|还是|可视为|可以视为|仍可视为|仍然可视为|已经|已|成为|形成|成立)",
            segment.strip(),
        )
    )


def _has_unnegated_positive_support_claim(text: str, key_levels: List[str]) -> bool:
    segments = re.split(r"(?:但是|不过|然而|同时|但|而|，|；|。|,|;|(?<!\d)\.(?!\d))", text)
    if len(segments) <= 1:
        return False
    line_hits = _find_key_level_hits(text, key_levels)
    if not line_hits:
        return False
    if not (_is_negative_support_context(text) or _is_negative_write_as_context(text)):
        return False
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        segment_hits = _find_key_level_hits(segment, key_levels)
        inherits_line_hit = bool(line_hits and _segment_can_inherit_key_level(segment))
        if not segment_hits and not inherits_line_hit:
            continue
        if "不因为" in text and segment.startswith("就"):
            continue
        if _is_negative_write_as_context(segment):
            continue
        if _is_negative_support_context(segment):
            continue
        if _is_positive_support_claim(segment):
            return True
    return False


def _is_positive_risk_relief_claim(text: str) -> bool:
    if not _match_any(text, RISK_RELIEF_KEYWORDS):
        return False
    if any(token in text for token in ("不是", "不能", "不应", "不把", "不算", "并非")):
        return False
    return True


def _detect_action_language(text: str) -> Optional[str]:
    return _match_any(text, ACTION_KEYWORDS)


def _find_findings_for_file(
    file_path: str,
    text: str,
    *,
    date: Optional[str],
    previous_date: Optional[str],
    key_levels: List[str],
    facts_pack: Optional[dict],
) -> List[Finding]:
    lines = text.splitlines()
    sections = _build_section_map(lines, current_date=date)
    findings: List[Finding] = []

    prev_short = _short_date(previous_date)

    def add_finding(
        line_no: int,
        section: str,
        rule_id: str,
        severity: Optional[str],
        disposition: str,
        matched_text: str,
        reason: str,
        suggested_fix: str,
    ) -> None:
        rule_config = RULE_REGISTRY.get(rule_id, {})
        if rule_config.get("enabled") is False:
            return
        resolved_severity = severity or rule_config.get("severity_default", "P3")
        findings.append(
            Finding(
                file=file_path,
                line=line_no,
                section=section,
                rule_id=rule_id,
                severity=resolved_severity,
                disposition=disposition,
                matched_text=matched_text,
                reason=reason,
                suggested_fix=suggested_fix,
            )
        )

    disclosure_needs_manual_check = _facts_needs_manual_check(facts_pack)

    for idx, line in enumerate(lines, start=1):
        section, section_kind = _section_for_line(idx, sections)
        stripped = line.strip()
        if not stripped:
            continue
        nearby_context = _nearby_context_text(lines, idx - 1, window=3)

        if section_kind == "history":
            continue
        if _is_historical_index_row(line, date):
            continue
        recap_label = _path_recap_label(line)
        skip_path_recap = bool(
            recap_label
            and (
                _is_history_recap_context(section, nearby_context)
                or "曾在" in line
                or (not _is_current_date_label(recap_label, date) and not _path_label_has_immediate_current_anchor(line))
            )
        )
        if skip_path_recap:
            continue

        # R004: stale current-zone date mentions
        if section_kind == "current" and date:
            stale_date_hit = None
            stale_date_tokens = [
                token
                for token in _date_tokens_in_text(line)
                if token not in set(_current_date_tokens(date))
            ]
            if (
                stale_date_tokens
                and not _is_comparison_reference_for_tokens(line, stale_date_tokens)
                and _is_stale_date_anchor_line(line, stale_date_tokens)
            ):
                stale_date_hit = stale_date_tokens[0]
            if stale_date_hit:
                add_finding(
                    idx,
                    section,
                    "R004_CURRENT_SECTION_STALE_DATE",
                    None,
                    "positive-assertion",
                    _line_excerpt(line),
                    f"current section still carries stale date anchor {stale_date_hit}",
                    "Advance the current section to the target trading date and move the old date into a history subsection or comparison-only note.",
                )

        # R005: stale level identity in current section
        if section_kind == "current" and key_levels:
            section_heading_hits = _find_key_level_hits(section, key_levels) if section and section != "root" else []
            line_hits = _find_key_level_hits(line, key_levels)
            hits = line_hits or section_heading_hits
            identity_stale_marker = any(keyword in line for keyword in ("继续跌破", "重新收回", "收盘跌破"))
            date_stale_marker = (
                any(date_token in line for date_token in ([previous_date] if previous_date else []) + ([prev_short] if prev_short else []))
                and _is_current_frame_line(line)
            )
            stale_markers = (
                identity_stale_marker
                or date_stale_marker
            )
            current_context_ok = section != "root" or _is_current_frame_line(line) or _is_current_frame_line(section)
            if stale_markers and current_context_ok and not _is_comparison_section_context(section) and not _is_safe_current_observation(line):
                if hits and not _is_negative_write_as_context(line):
                    add_finding(
                        idx,
                        section,
                        "R005_CURRENT_SECTION_STALE_LEVEL",
                        None,
                        "positive-assertion",
                        _compose_matched_text(line, section, bool(section_heading_hits and not line_hits)),
                        (
                            f"current section still frames prior key-level identity around {', '.join(hits)}"
                            + ("; key level inherited from section heading" if section_heading_hits and not line_hits else "")
                        ),
                        "Rewrite the current section so the old level is only history or comparison, and move the current judgment to the latest trading-day identity. If the key level comes from the section heading, consider moving the heading itself into the history/comparison block or restating the heading as observation-only.",
                    )

        # R003: hard-bottom / support overclaim in current section
        if section_kind == "current" and key_levels:
            section_heading_hits = _find_key_level_hits(section, key_levels) if section and section != "root" else []
            line_hits = _find_key_level_hits(line, key_levels)
            hits = line_hits or section_heading_hits
            has_segment_positive_claim = _has_unnegated_positive_support_claim(line, key_levels)
            if hits and (_is_positive_support_claim(line) or has_segment_positive_claim):
                negative_context = (
                    _is_negative_write_as_context(line)
                    or _is_negative_support_context(line)
                    or _has_negative_support_intro(line)
                    or (stripped.startswith(("-", "*")) and _is_in_negative_support_list(lines, idx - 1))
                    or skip_path_recap
                )
                if negative_context and not has_segment_positive_claim:
                    continue
                add_finding(
                    idx,
                    section,
                    "R003_SUPPORT_OR_BOTTOM_MISLABEL",
                    None,
                    "positive-assertion",
                    _compose_matched_text(line, section, bool(section_heading_hits and not line_hits)),
                    (
                        f"key level(s) {', '.join(hits)} are promoted to hard-bottom / support language in a current section"
                        + ("; key level inherited from section heading" if section_heading_hits and not line_hits else "")
                    ),
                    "Downgrade the wording to observation language such as 'near-term recovery level', 'comparison level', or 'historical anchor' unless a later section formally reclassifies it. If the key level comes from the section heading, consider moving the heading itself out of the current section or restating it as observation-only.",
                )

        # R008: workflow ledger / index status stale in current section
        if section_kind == "current":
            if "后续待同步" in line:
                add_finding(
                    idx,
                    section,
                    "R008_INDEX_OR_ASSOCIATED_FILES_STATUS",
                    None,
                    "positive-assertion",
                    _line_excerpt(line),
                    "current section still advertises pending downstream sync work",
                    "Update the ledger text to the closed state if the chain has been synchronized, or keep it explicitly pending if work remains.",
                )

        # R006: lightweight announcement-status safety gate
        if section_kind == "current":
            announcement_hit = _match_announcement_assertion(line)
            if (
                announcement_hit
                and disclosure_needs_manual_check
                and not _is_negative_disclosure_instruction(line)
                and not _is_in_negative_disclosure_list(lines, idx - 1)
            ):
                add_finding(
                    idx,
                    section,
                    "R006_DISCLOSURE_NEEDS_MANUAL_CHECK",
                    "P2",
                    "needs_human_review",
                    _line_excerpt(line),
                    "announcement-status assertion appears in a current section; facts pack not provided, incomplete, or marked needs_manual_check escalates disclosure assertions",
                    "If the facts pack is incomplete or marked needs_manual_check, keep the line as a review note and avoid presenting announcement-state conclusions as confirmed facts.",
                )

        # R001 / R002 remain placeholders; no hard blocking in v1.

    # R007: structural boundary summary if stale current-zone signals exist.
    current_stale = [
        f
        for f in findings
        if f.rule_id in {"R004_CURRENT_SECTION_STALE_DATE", "R005_CURRENT_SECTION_STALE_LEVEL"}
    ]
    if current_stale and not any(f.rule_id == "R007_CURRENT_SECTION_BOUNDARY" for f in findings):
        anchor = current_stale[0]
        add_finding(
            anchor.line,
            anchor.section,
            "R007_CURRENT_SECTION_BOUNDARY",
            None,
            "needs_human_review",
            anchor.matched_text,
            "current zone still contains stale date / key-level anchors after the latest trading-day update; review section synchronization holistically",
            "Synchronize all current sections together, not just the new date subsection, so the latest trading-day state is reflected consistently.",
        )

    return findings


def _group_findings(findings: List[Finding]) -> dict:
    grouped = {"P0": [], "P1": [], "P2": [], "P3": []}
    for finding in findings:
        grouped.setdefault(finding.severity, []).append(finding)
    return grouped


def _overall_status(findings: List[Finding]) -> str:
    for finding in findings:
        if finding.severity in {"P0", "P1", "P2"}:
            return "NEEDS_FIX"
    return "PASS"


def _render_markdown_report(
    *,
    args: argparse.Namespace,
    findings: List[Finding],
    files: List[str],
    facts_pack_path: Optional[str],
    key_levels: List[str],
) -> str:
    grouped = _group_findings(findings)
    lines: List[str] = []
    lines.append("# validate_review_chain.py report")
    lines.append("")
    lines.append(f"- Overall: `{_overall_status(findings)}`")
    lines.append(f"- Mode: `{'staged' if args.staged else 'files'}`")
    if args.date:
        lines.append(f"- Date: `{args.date}`")
    if args.previous_date:
        lines.append(f"- Previous date: `{args.previous_date}`")
    if key_levels:
        lines.append(f"- Key levels: `{', '.join(key_levels)}`")
    if facts_pack_path:
        lines.append(f"- Facts pack: `{facts_pack_path}`")
    lines.append(f"- Files: `{', '.join(files)}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- `P0`: {len(grouped['P0'])}")
    lines.append(f"- `P1`: {len(grouped['P1'])}")
    lines.append(f"- `P2`: {len(grouped['P2'])}")
    lines.append(f"- `P3`: {len(grouped['P3'])}")
    lines.append("")

    for severity in ("P0", "P1", "P2", "P3"):
        bucket = grouped[severity]
        lines.append(f"## {severity}")
        lines.append("")
        if not bucket:
            lines.append("- None")
            lines.append("")
            continue
        for finding in bucket:
            lines.append(f"- File: `{finding.file}`")
            lines.append(f"  - Line: `{finding.line}`")
            lines.append(f"  - Section: `{finding.section}`")
            lines.append(f"  - Rule: `{finding.rule_id}`")
            lines.append(f"  - Severity: `{finding.severity}`")
            lines.append(f"  - Disposition: `{finding.disposition}`")
            lines.append(f"  - Matched: `{finding.matched_text}`")
            lines.append(f"  - Reason: {finding.reason}")
            lines.append(f"  - Suggested fix: {finding.suggested_fix}")
            lines.append("")

    if any(f.rule_id in {"R001_ACTION_LANGUAGE", "R002_RISK_RELIEF_OVERCLAIM", "R006_DISCLOSURE_NEEDS_MANUAL_CHECK"} for f in findings):
        lines.append("## Placeholder coverage")
        lines.append("")
        lines.append("- R001 and R002 are reserved for a later pass.")
        lines.append("- R006 is present as a lightweight facts-pack safety gate.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Markdown validator for review-chain documents")
    parser.add_argument("--files", nargs="+", help="One or more Markdown files to lint")
    parser.add_argument("--staged", action="store_true", help="Lint staged files from git index")
    parser.add_argument("--date", help="Target trading day")
    parser.add_argument("--previous-date", dest="previous_date", help="Previous trading day")
    parser.add_argument(
        "--key-levels",
        help="Comma-separated key levels to lint, e.g. 126.00,126.10,126.16",
    )
    parser.add_argument("--facts-pack", dest="facts_pack", help="Optional local facts pack JSON")
    parser.add_argument("--report", help="Optional Markdown report output path")
    parser.add_argument("--verbose", action="store_true", help="Print the full markdown report to stdout")
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="Do not convert findings into a non-zero exit code; useful for manual review",
    )
    return parser


def _resolve_input_files(args: argparse.Namespace) -> tuple[List[str], dict[str, str]]:
    if args.staged and args.files:
        raise SystemExit("--files and --staged are mutually exclusive")
    if not args.staged and not args.files:
        raise SystemExit("Provide either --files or --staged")

    if args.staged:
        staged_files = [path for path in _get_staged_paths() if Path(path).suffix.lower() == ".md"]
        file_map: dict[str, str] = {}
        for staged_path in staged_files:
            staged_text = _load_staged_file(staged_path)
            if staged_text is not None:
                file_map[staged_path] = staged_text
        return [path for path in staged_files if path in file_map], file_map

    file_map = {}
    resolved_files = []
    for raw_path in args.files:
        path = Path(raw_path)
        resolved = _normalize_relative(str(path))
        if not path.exists():
            raise SystemExit(f"File not found: {raw_path}")
        resolved_files.append(resolved)
        file_map[resolved] = _read_text(path)
    return resolved_files, file_map


def _console_summary(findings: List[Finding], files: List[str], args: argparse.Namespace) -> str:
    grouped = _group_findings(findings)
    summary = [
        f"validate_review_chain: {_overall_status(findings)}",
        f"files={len(files)}",
        f"P0={len(grouped['P0'])}",
        f"P1={len(grouped['P1'])}",
        f"P2={len(grouped['P2'])}",
        f"P3={len(grouped['P3'])}",
    ]
    if args.report:
        summary.append(f"report={args.report}")
    return " | ".join(summary)


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    key_levels = [item.strip() for item in args.key_levels.split(",")] if args.key_levels else []
    facts_pack = _load_facts_pack(args.facts_pack)
    files, file_map = _resolve_input_files(args)
    if not args.date and any(_contains_date_heading(text) for text in file_map.values()):
        raise SystemExit("--date is required for dated markdown documents to avoid treating dated sections as history")

    all_findings: List[Finding] = []
    for file_path in files:
        text = file_map.get(file_path)
        if text is None:
            continue
        file_findings = _find_findings_for_file(
            file_path,
            text,
            date=args.date,
            previous_date=args.previous_date,
            key_levels=key_levels,
            facts_pack=facts_pack,
        )
        all_findings.extend(file_findings)

    print(_console_summary(all_findings, files, args))

    if getattr(args, "verbose", False):
        print(
            _render_markdown_report(
                args=args,
                findings=all_findings,
                files=files,
                facts_pack_path=args.facts_pack,
                key_levels=key_levels,
            ).rstrip()
        )

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_text = _render_markdown_report(
            args=args,
            findings=all_findings,
            files=files,
            facts_pack_path=args.facts_pack,
            key_levels=key_levels,
        )
        report_path.write_text(report_text, encoding="utf-8")

    if _overall_status(all_findings) == "PASS" or args.no_fail:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
