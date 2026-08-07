#!/usr/bin/env python3
"""Enforce the post-migration old-identity contract for the stocks repository.

Operational/current records must not contain any rewritten pre-migration commit identity.
Only enumerated immutable sealed archives and the migration mapping appendix may retain
those identities as historical testimony.
"""

from __future__ import annotations

import argparse
import re
import subprocess


MIGRATION_APPENDIX = "reports/validation/history_sanitization_2026-08-07.md"
EXPECTED_MAPPING_COUNT = 8

ALLOWED_HISTORICAL_PATHS = {
    MIGRATION_APPENDIX,
    "reports/validation/artifacts/cross_method_provenance_fable_review_2026-08-05/fable_raw.md",
    "reports/validation/artifacts/cross_method_provenance_fable_review_2026-08-05/formal_prompt.md",
    "reports/validation/artifacts/cross_method_provenance_fable_review_2026-08-05/pi_events.jsonl",
    "reports/validation/artifacts/cross_method_provenance_fable_review_2026-08-05/run_meta.json",
    "reports/validation/artifacts/project_memory_v0.1_design_r5_2026-07-29/adr_seed_inventory.md",
    "reports/validation/artifacts/project_memory_v0.1_design_r5_2026-07-29/agent_benchmark_seed.md",
    "reports/validation/artifacts/project_memory_v0.1_design_r5_2026-07-29/phase_registry_seed.md",
    "reports/validation/artifacts/project_memory_v0.1_design_r5_2026-07-29/project_state_seed.md",
    "reports/validation/artifacts/project_memory_v0.1_design_r5_2026-07-29/source_inventory.json",
    "reports/validation/artifacts/project_memory_v0.1_fable_final_review_2026-08-02/formal_runs/pi-project-memory-r5-20260802-012956/fable_raw.md",
}

MAPPING_ROW = re.compile(
    rb"^\|\s*([0-9a-f]{40})\s*\|\s*([0-9a-f]{40})\s*\|\s*$",
    re.MULTILINE,
)


def git(repo: str, *args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True,
        text=text,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(args)}")
    return result.stdout


def revision_file(repo: str, rev: str, path: str) -> bytes:
    data = git(repo, "show", f"{rev}:{path}", text=False)
    assert isinstance(data, bytes)
    return data


def load_old_identities(repo: str, rev: str) -> tuple[str, ...]:
    appendix = revision_file(repo, rev, MIGRATION_APPENDIX)
    rows = MAPPING_ROW.findall(appendix)
    if len(rows) != EXPECTED_MAPPING_COUNT:
        raise RuntimeError(
            f"migration mapping count mismatch: expected {EXPECTED_MAPPING_COUNT}, got {len(rows)}"
        )
    old = tuple(row[0].decode("ascii") for row in rows)
    if len(set(old)) != EXPECTED_MAPPING_COUNT:
        raise RuntimeError("migration mapping old identities are not unique")
    return old


def identity_hits(data: bytes, old_identities: tuple[str, ...]) -> list[int]:
    hits: list[int] = []
    lowered = data.lower()
    for index, identity in enumerate(old_identities, start=1):
        prefix7 = identity[:7].encode("ascii")
        if prefix7 not in lowered:
            continue
        full = identity.encode("ascii")
        if full in lowered:
            hits.append(index)
            continue
        for length in range(7, 13):
            prefix = identity[:length].encode("ascii")
            pattern = rb"(?<![0-9a-f])" + re.escape(prefix) + rb"(?![0-9a-f])"
            if re.search(pattern, lowered):
                hits.append(index)
                break
    return hits


def revision_blob_paths(repo: str, rev: str) -> dict[str, list[str]]:
    raw = git(repo, "ls-tree", "-r", "-z", rev, text=False)
    assert isinstance(raw, bytes)
    output: dict[str, list[str]] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, path_raw = record.split(b"\t", 1)
        _mode, object_type, oid_raw = meta.split()
        if object_type != b"blob":
            continue
        oid = oid_raw.decode("ascii")
        path = path_raw.decode("utf-8", errors="surrogateescape")
        output.setdefault(oid, []).append(path)
    return output


def batch_blob_contents(repo: str, oids: list[str]):
    if not oids:
        return
    process = subprocess.Popen(
        ["git", "-C", repo, "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    for oid in oids:
        process.stdin.write((oid + "\n").encode("ascii"))
    process.stdin.close()

    for expected_oid in oids:
        header = process.stdout.readline().rstrip(b"\n")
        parts = header.split()
        if len(parts) != 3 or parts[0].decode("ascii") != expected_oid or parts[1] != b"blob":
            process.kill()
            raise RuntimeError("git cat-file --batch returned an unexpected object")
        size = int(parts[2])
        data = process.stdout.read(size)
        if process.stdout.read(1) != b"\n":
            process.kill()
            raise RuntimeError("git cat-file --batch framing error")
        yield expected_oid, data

    if process.wait() != 0:
        raise RuntimeError("git cat-file --batch failed")


def validate(repo: str, rev: str) -> tuple[list[tuple[str, list[int]]], int]:
    probe = subprocess.run(
        ["git", "-C", repo, "cat-file", "-e", f"{rev}:{MIGRATION_APPENDIX}"],
        capture_output=True,
        check=False,
    )
    if probe.returncode != 0:
        return [], -1

    old_identities = load_old_identities(repo, rev)
    violations: list[tuple[str, list[int]]] = []
    allowed_reference_files = 0
    blob_paths = revision_blob_paths(repo, rev)
    for oid, data in batch_blob_contents(repo, list(blob_paths)):
        hits = identity_hits(data, old_identities)
        if not hits:
            continue
        for path in blob_paths[oid]:
            if path in ALLOWED_HISTORICAL_PATHS:
                allowed_reference_files += 1
                continue
            violations.append((path, hits))
    return violations, allowed_reference_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--rev", default="HEAD")
    args = parser.parse_args()

    try:
        violations, allowed_count = validate(args.repo, args.rev)
    except RuntimeError as exc:
        print(f"HISTORY_SANITIZATION_POLICY_ERROR: {exc}")
        return 2

    if allowed_count == -1:
        print("HISTORY_SANITIZATION_POLICY_NOT_APPLICABLE")
        return 0

    if violations:
        print("HISTORY_SANITIZATION_POLICY_BLOCKED")
        for path, identities in violations:
            labels = ",".join(f"old_identity_{index}" for index in identities)
            print(f"  {path} [{labels}]")
        print(f"OPERATIONAL_OLD_IDENTITY_FILE_COUNT={len(violations)}")
        return 1

    print("HISTORY_SANITIZATION_POLICY_PASS")
    print("OPERATIONAL_OLD_IDENTITY_FILE_COUNT=0")
    print(f"ALLOWED_HISTORICAL_REFERENCE_FILE_COUNT={allowed_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
