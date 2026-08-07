# Focused external review — sealed evidence migration contract + secret-scanner hardening

You are a read-only external architecture reviewer. Do not modify files, run Git writes, push, or print credential values.

Repository state after the 2026-08-07 history sanitization:

- branch: `workbench/mainline-2026-07`
- local HEAD = remote HEAD = `da0dd8f35ebba500a7b1107e58f9677287892f95`
- the original secret-bearing range was rewritten as exactly 8 commits; 87 earlier ancestors retained identical commit IDs.
- comparing pre-rewrite HEAD to the rewritten equivalent HEAD, the tree differs in exactly one tracked path: the affected `pi_events.jsonl`.
- current reachable refs contain none of the four historical credential values.
- production reflogs were expired and `git gc --prune=now` was run after verified local contaminated backups existed; old secret-bearing commit object is now absent from production `.git`.
- no refs/original, replace refs, notes, tags, or stash refs retain the old range.
- contaminated rollback backups remain local with restrictive permissions and are scheduled for deletion after the agreed quarantine period.

## Sealed-evidence route actually taken

The original design proposal said “rebind + repack” for sealed packages. The implementation instead preserved sealed member bytes and package identities, while rebinding operational/live records and adding an explicit migration mapping appendix.

Verified facts:

- migration commit `5b3a27c` changed 32 tracked files:
  - 12 `memory/*` files;
  - 13 `reports/validation/*.md` live validation reports;
  - 7 artifact metadata files such as `design_manifest.json`, `closure_manifest.json`, and `review_meta.json` where structured Git identity fields were load-bearing.
- follow-up `a8c479c` recomputed affected `project_state.md` / `phase_registry.md` snapshot raw hashes and records the 8-pair old→new mapping in `reports/validation/history_sanitization_2026-08-07.md`.
- nine historical sealed/archive files still contain old commit SHA text as historical evidence; one additional tracked file is the migration appendix itself containing the explicit 8-pair mapping.
- no operational/live binding outside that historical sealed/archive set points to an unmapped old identity.
- the r5 sealed package has 17 declared sealed members; all 17 byte size/SHA declarations independently match current bytes.
- independently recomputed r5 package identity exactly equals the declared `design_package_sha256=64dfa32ad9573bfdea074b7731c2dace324b693bc8e47dcbfe4dc8d37a3f9bfd`.
- therefore the historical sealed package is byte-for-byte the same package it originally claimed to be; old SHA references inside it are historical statements interpreted through the explicit migration appendix, not current operational Git authority.

Proposed contract:

1. Sealed historical packages remain immutable byte evidence and retain their original package identity.
2. Old commit identities inside sealed historical evidence are interpreted only through the single explicit 8-pair migration mapping.
3. Current operational/live evidence must use mapped identities; an unmapped old identity outside sealed historical evidence + migration appendix is a hard failure.
4. A sealed package must still validate its own declared member hashes/package identity from bytes; no stale member SHA is grandfathered.
5. Current repository authority is the rewritten branch plus current operational records; sealed archives preserve historical testimony, not current Git authority.

## Secret scanner hardening candidate

The already-pushed scanner had one design defect: `--commits BASE..TIP` scanned only the net `git diff`, so an intermediate commit that added a secret and a later commit that deleted it could evade the pre-push scan.

The uncommitted hardening candidate now:

- obtains `git rev-list --objects REVSET`;
- identifies every blob object newly reachable in the revision set;
- scans each unique blob, so add-then-delete history is inspected;
- scans commit messages too;
- pre-commit scans the staged blob contents for ACMR paths rather than deleted text;
- new-branch pre-push uses the tip revision rather than an empty-tree diff;
- existing-branch pre-push uses `remote_sha..local_sha`;
- diagnostics report only object/path, rule ID, and line number, never value fragments;
- allows explicit redaction markers, environment-variable references, and documented synthetic placeholders;
- the same implementation is wired for CI.

Verification:

- 6 dedicated scanner tests pass, including a synthetic add-secret / commit / delete-secret / commit red-team case.
- full repository tests: 636 passed + 28 subtests.
- `python3 tools/secret_scan.py --commits HEAD` returns `SECRET_SCAN_CLEAN` on the current sanitized history.
- `git diff --check` passes for scanner/hooks/tests/workflow candidate.
- GitHub Push Protection remains the server-side backstop.
- `.github/workflows/secret-scan.yml` is locally prepared but cannot yet be pushed because the current GitHub token lacks `workflow` scope.

## Questions

1. Is the “sealed bytes preserved + explicit migration mapping” contract acceptable for fail-closed evidence semantics, given the verified package identity remains unchanged and all operational bindings are migrated?
2. Must those nine sealed historical files be rewritten/repacked anyway, or would doing so unnecessarily destroy provenance/package identity?
3. Is the hardened scanner architecture sufficient to close the add-then-delete gap?
4. Is postponing the CI workflow until a token with `workflow` scope is available acceptable while local hooks + GitHub Push Protection remain active?
5. Identify any P1/P2/P3 issue still blocking a small scanner hardening commit and push (excluding the workflow file).

End with exactly:

SEALED_CONTRACT_VERDICT=<ACCEPT|ACCEPT_WITH_GATES|REJECT>
SEALED_BYTES_PRESERVE=<YES|NO>
SEALED_REPACK_REQUIRED=<YES|NO>
MIGRATION_MAPPING_AUTHORITY=<ACCEPT|REJECT>
OPERATIONAL_OLD_SHA_ZERO_REQUIRED=<YES|NO>
SCANNER_ARCHITECTURE_VERDICT=<ACCEPT|ACCEPT_WITH_GATES|REJECT>
ADD_THEN_DELETE_GAP_CLOSED=<YES|NO>
CI_WORKFLOW_CAN_BE_DEFERRED=<YES|NO>
P1_COUNT=<integer>
P2_COUNT=<integer>
P3_COUNT=<integer>
READY_FOR_SMALL_SCANNER_COMMIT=<YES|NO>
READY_FOR_SCANNER_PUSH_WITHOUT_WORKFLOW=<YES|NO>
