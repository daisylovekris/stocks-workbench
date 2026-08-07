#!/usr/bin/env python3
"""同源密钥扫描器：pre-commit / pre-push / CI 共用同一套模式。

用法:
  secret_scan.py --staged                 扫暂存区内容（pre-commit）
  secret_scan.py --commits <base>..<tip>  扫提交范围内容（pre-push / CI）
  secret_scan.py --files <path>...        直接扫文件

命中任一模式即退出码 1（fail closed）。只报告模式类别与位置，不打印完整值。
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

PATTERNS = [
    (
        "api_key_assignment",
        re.compile(r"[A-Z][A-Z0-9]*(?:_API_KEY|_AUTH_TOKEN|_TOKEN|_SECRET)=[^\s\"\\,}]+"),
    ),
    ("openrouter_key", re.compile(r"sk-or-v1-[A-Za-z0-9_-]{10,}")),
    ("generic_sk_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("bearer_token", re.compile(r"Bearer[ \t]+[A-Za-z0-9._~+/=-]{20,}")),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{10,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("joyagent_key", re.compile(r"RsCenterCH-[A-Za-z0-9+/=]{10,}")),
]

PLACEHOLDER_WORDS = {
    "fake", "forged", "reason", "key", "secret", "test", "example",
    "dummy", "placeholder", "missing", "unset", "none", "value",
    "openai", "api", "token", "xxx", "na", "n/a", "action", "bearer",
    "authorization", "header",
}


def is_placeholder(value: str) -> bool:
    """占位/脱敏值不视为真实凭据：脱敏标记或全由占位词构成的值。"""
    if value.startswith("***"):
        return True
    lowered = value.lower()
    if lowered in {"missing", "unset", "not_set", "none", "empty", "true", "false", "n/a"}:
        return True
    parts = [p for p in re.split(r"[-_ ]", value) if p]
    return len(parts) >= 2 and all(p.lower() in PLACEHOLDER_WORDS for p in parts)


def mask(value: str) -> str:
    if len(value) <= 8:
        return "***REDACTED***"
    return value[:8] + "***REDACTED***"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=False,
    ).stdout


def scan_text(text: str, origin: str, findings: list) -> None:
    for name, pattern in PATTERNS:
        for match in pattern.finditer(text):
            if name in ("api_key_assignment", "bearer_token"):
                value = match.group(0).split("=", 1)[1] if name == "api_key_assignment" else match.group(0).split(None, 1)[1]
                if len(value) < 12 or is_placeholder(value):
                    continue
            findings.append(f"{origin}  [{name}] {mask(match.group(0))}")


def scan_commits(rev_range: str, findings: list) -> None:
    patch = git("diff", "--no-color", rev_range)
    scan_text(patch, f"commits {rev_range}", findings)
    messages = git("log", "--no-color", "--format=%B", rev_range)
    scan_text(messages, f"commit messages {rev_range}", findings)


def scan_files(paths: list, findings: list) -> None:
    for path in paths:
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(f"{path}  [unreadable] {exc}")
            continue
        scan_text(text, path, findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--staged", action="store_true", help="scan staged content")
    group.add_argument("--commits", metavar="BASE..TIP", help="scan commit range content")
    group.add_argument("--files", nargs="+", metavar="PATH", help="scan files directly")
    args = parser.parse_args()

    findings = []
    if args.staged:
        scan_text(git("diff", "--cached", "--no-color"), "staged", findings)
    elif args.commits:
        scan_commits(args.commits, findings)
    else:
        scan_files(args.files, findings)

    if findings:
        print("SECRET_SCAN_BLOCKED")
        for finding in findings[:50]:
            print("  " + finding)
        if len(findings) > 50:
            print(f"  ... 共 {len(findings)} 处命中")
        return 1
    print("SECRET_SCAN_CLEAN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
