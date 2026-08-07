#!/usr/bin/env python3
"""同源密钥扫描器：pre-commit / pre-push / CI 共用同一套规则。

用法:
  secret_scan.py --staged
  secret_scan.py --commits <REVSET>
  secret_scan.py --files <path>...

`--commits` 扫描 REVSET 内每个 newly reachable blob，而不只比较首尾净 diff；
因此能够拦截“中间提交写入密钥、后续提交又删除”的历史泄露。

命中任一规则即退出码 1。诊断只输出路径/对象、规则 ID 与行号，不输出匹配值。
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

PATTERNS = [
    (
        "api_key_assignment",
        re.compile(
            r"\b[A-Z][A-Z0-9]*(?:_API_KEY|_AUTH_TOKEN|_TOKEN|_SECRET)"
            r"\s*=\s*(?P<value>"
            r'"[^"\r\n]*"|'
            r"'[^'\r\n]*'|"
            r"[^\s,]+)"
        ),
    ),
    ("openrouter_key", re.compile(r"sk-or-v1-[A-Za-z0-9_-]{10,}")),
    ("generic_sk_key", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("bearer_token", re.compile(r"Bearer[ \t]+(?P<value>[A-Za-z0-9._~+/=-]{20,})")),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{10,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("joyagent_key", re.compile(r"RsCenterCH-[A-Za-z0-9+/=]{10,}")),
]

PLACEHOLDER_WORDS = {
    "fake", "forged", "reason", "key", "secret", "test", "example",
    "dummy", "placeholder", "missing", "unset", "none", "value",
    "openai", "api", "token", "xxx", "na", "n/a", "action", "bearer",
    "authorization", "header", "redacted",
}


def normalize_value(value: str) -> str:
    value = value.strip()
    value = value.strip("\"'")
    if not value.startswith("$"):
        value = value.rstrip("}\"'")
    return value.strip()


def is_placeholder(value: str) -> bool:
    value = normalize_value(value)
    lowered = value.lower()
    uppered = value.upper()
    if not value:
        return True
    if uppered in {"REDACTED", "***REDACTED***", "<REDACTED>"}:
        return True
    if re.fullmatch(r"\$\{[A-Z_][A-Z0-9_]*\}", value):
        return True
    if re.fullmatch(r"\$[A-Z_][A-Z0-9_]*", value):
        return True
    if value.startswith("<") and value.endswith(">"):
        return True
    if lowered in {"missing", "unset", "not_set", "none", "empty", "true", "false", "n/a"}:
        return True
    parts = [part for part in re.split(r"[-_ ]", value) if part]
    return len(parts) >= 2 and all(part.lower() in PLACEHOLDER_WORDS for part in parts)


def run_git(*args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(["git", *args], capture_output=True, text=text, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(args)}")
    return result.stdout


def add_finding(findings: list[str], origin: str, rule_id: str, line_no: int) -> None:
    findings.append(f"{origin}:{line_no} [{rule_id}]")


def scan_text(text: str, origin: str, findings: list[str]) -> None:
    for line_no, line in enumerate(text.splitlines(), start=1):
        for rule_id, pattern in PATTERNS:
            for match in pattern.finditer(line):
                if rule_id in {"api_key_assignment", "bearer_token"}:
                    value = normalize_value(match.group("value"))
                    if len(value) < 12 or is_placeholder(value):
                        continue
                add_finding(findings, origin, rule_id, line_no)


def scan_blob(oid: str, path: str, findings: list[str]) -> None:
    data = run_git("cat-file", "blob", oid, text=False)
    assert isinstance(data, bytes)
    scan_text(data.decode("utf-8", errors="replace"), f"blob {oid} {path}".rstrip(), findings)


def scan_staged(findings: list[str]) -> None:
    raw = run_git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z", text=False)
    assert isinstance(raw, bytes)
    for item in raw.split(b"\0"):
        if not item:
            continue
        path = item.decode("utf-8", errors="surrogateescape")
        data = run_git("show", f":{path}", text=False)
        assert isinstance(data, bytes)
        scan_text(data.decode("utf-8", errors="replace"), f"staged {path}", findings)


def rev_list_objects(revset: str) -> list[tuple[str, str]]:
    output = run_git("rev-list", "--objects", revset)
    assert isinstance(output, str)
    objects: list[tuple[str, str]] = []
    for line in output.splitlines():
        oid, _, path = line.partition(" ")
        objects.append((oid, path))
    return objects


def object_types(oids: list[str]) -> dict[str, str]:
    if not oids:
        return {}
    result = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype)"],
        input="".join(f"{oid}\n" for oid in oids),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("git cat-file --batch-check failed")
    output: dict[str, str] = {}
    for line in result.stdout.splitlines():
        oid, _, object_type = line.partition(" ")
        output[oid] = object_type
    return output


def scan_commits(revset: str, findings: list[str]) -> None:
    objects = rev_list_objects(revset)
    types = object_types([oid for oid, _ in objects])
    seen_blobs: set[str] = set()
    for oid, path in objects:
        if types.get(oid) != "blob" or oid in seen_blobs:
            continue
        seen_blobs.add(oid)
        scan_blob(oid, path, findings)

    messages = run_git("log", "--format=%H%x00%B%x00", revset)
    assert isinstance(messages, str)
    parts = messages.split("\x00")
    for index in range(0, len(parts) - 1, 2):
        commit = parts[index].strip()
        message = parts[index + 1]
        if commit:
            scan_text(message, f"commit-message {commit}", findings)


def scan_files(paths: list[str], findings: list[str]) -> None:
    for path in paths:
        try:
            data = Path(path).read_bytes()
        except OSError:
            findings.append(f"{path}:0 [unreadable]")
            continue
        scan_text(data.decode("utf-8", errors="replace"), path, findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--staged", action="store_true", help="scan staged blobs")
    group.add_argument("--commits", metavar="REVSET", help="scan newly reachable blobs/messages in REVSET")
    group.add_argument("--files", nargs="+", metavar="PATH", help="scan files directly")
    args = parser.parse_args()

    findings: list[str] = []
    try:
        if args.staged:
            scan_staged(findings)
        elif args.commits:
            scan_commits(args.commits, findings)
        else:
            scan_files(args.files, findings)
    except RuntimeError as exc:
        print(f"SECRET_SCAN_ERROR: {exc}")
        return 2

    if findings:
        print("SECRET_SCAN_BLOCKED")
        for finding in findings[:50]:
            print("  " + finding)
        if len(findings) > 50:
            print(f"  ... total findings: {len(findings)}")
        return 1
    print("SECRET_SCAN_CLEAN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
