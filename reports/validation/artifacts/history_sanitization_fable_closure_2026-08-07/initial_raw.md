## Review

### 1. Sealed evidence contract

Accept. This is the correct design — arguably better than the original "rebind + repack" proposal. Rewriting sealed member bytes to update SHA text would destroy the package identity (`design_package_sha256`) and convert immutable evidence into edited evidence, which is worse for fail-closed semantics than stale-but-mapped identifiers. The key invariants are all verified:

- Package identity independently recomputed and matches the declared value.
- All 17 member hash declarations validate from bytes (no grandfathering — contract point 4 holds).
- Zero unmapped old identities in operational/live records.
- The mapping is a single explicit, tracked appendix — one authority, not scattered annotations.

The contract cleanly separates "historical testimony" (sealed bytes) from "current Git authority" (rewritten branch + migrated operational records). Point 3's hard-failure rule for unmapped old identities outside the sealed set is exactly right, but it should be *enforced by a check*, not just asserted — see P2 below.

### 2. Should the nine sealed files be repacked?

No. Repacking would:
- invalidate the verified package identity, breaking the strongest integrity claim you have;
- destroy the provenance chain (bytes would no longer match what was originally sealed/reviewed);
- gain nothing, since the old commit objects no longer exist in production `.git` and the SHAs are inert text interpretable only through the mapping.

Old SHA strings in sealed archives are not secrets and not live references. Leave them.

### 3. Scanner architecture

Accept. Scanning every newly-reachable blob from `rev-list --objects` is the canonical fix for the add-then-delete evasion — it inspects history content, not net diff. Commit-message scanning, staged-blob pre-commit scanning, correct new-branch tip handling, and value-free diagnostics are all right. The red-team test directly exercises the closed gap. Gap: closed.

### 4. CI deferral

Acceptable. Local hooks (pre-commit + pre-push blob-level) plus GitHub Push Protection give two independent layers. CI is a third layer, not the primary control. Deferring until a `workflow`-scoped token exists is fine, provided it's tracked (see P3).

### 5. Remaining issues

**P1: none.** Nothing blocks a small scanner hardening commit and push.

**P2 (2):**
1. **Contract point 3 is a policy, not a gate.** Add an automated check (in the scanner or a sibling validator) that fails if any tracked file outside the enumerated sealed/archive set + migration appendix contains one of the 8 old SHAs. Without enforcement, drift can silently reintroduce unmapped old identities. Doesn't block the scanner commit, but should land soon.
2. **Allowlist mechanisms (redaction markers, env-var refs, synthetic placeholders) need a negative test** proving a real-looking secret adjacent to an allowlist marker still triggers. If such a test exists among the 6, this drops to P3; if not, add it before broadening allowlist patterns.

**P3 (2):**
1. Track the deferred `secret-scan.yml` push as an explicit open item with an owner/date so it doesn't silently rot.
2. Quarantined contaminated backups: record the deletion date and verify restrictive permissions in the sanitization report so closure is auditable.

None of the above blocks committing/pushing the hardened scanner (hooks + tests) without the workflow file.

SEALED_CONTRACT_VERDICT=ACCEPT
SEALED_BYTES_PRESERVE=YES
SEALED_REPACK_REQUIRED=NO
MIGRATION_MAPPING_AUTHORITY=ACCEPT
OPERATIONAL_OLD_SHA_ZERO_REQUIRED=YES
SCANNER_ARCHITECTURE_VERDICT=ACCEPT
ADD_THEN_DELETE_GAP_CLOSED=YES
CI_WORKFLOW_CAN_BE_DEFERRED=YES
P1_COUNT=0
P2_COUNT=2
P3_COUNT=2
READY_FOR_SMALL_SCANNER_COMMIT=YES
READY_FOR_SCANNER_PUSH_WITHOUT_WORKFLOW=YES
