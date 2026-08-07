**1. Count correction (9 → 10):** No contract change. The 10th file (prefix-only Fable archive) is the same class of evidence — byte-preserved, immutable, historical. The sealed contract is defined by the property (byte-preserved historical evidence, zero old identities in operational records), not the file count. The validator's exact 10+1 allowlist encodes this correctly, and prefix detection (7–12 chars) covers the prefix-only case. Accepted.

**2. P2 closure:**
- P2-1 (operational zero enforcement): Closed. Validator parses the mapping from the appendix at the target revision (no hard-coded SHAs in operational source), scans full/prefix forms, exact-path allowlist, `OPERATIONAL_OLD_IDENTITY_FILE_COUNT=0`, wired to pre-push + deferred CI. That's the enforcement shape requested.
- P2-2 (negative allowlist tests): Closed. Both bypass shapes (secret appended to redaction placeholder; secret appended to env reference) proven blocked, exact placeholders still allowed. 12 dedicated tests + 642 full suite passing.

**3. Commit scope:** Yes. Scanner + hooks + validator + tests + evidence updates form one coherent hardening unit. Excluding `.github/workflows/secret-scan.yml` until the token gains `workflow` scope is correct — pushing it now would fail, and pre-push enforcement plus Push Protection cover the interim. P3: add the workflow file in a follow-up commit immediately after token scope upgrade, and confirm CI green on first run.

SEALED_CONTRACT_VERDICT=ACCEPT
PREFIX_ONLY_ARCHIVE_EXCEPTION=ACCEPT
OPERATIONAL_IDENTITY_GATE=PASS
ALLOWLIST_NEGATIVE_TEST_GATE=PASS
P1_COUNT=0
P2_COUNT=0
P3_COUNT=1
READY_FOR_HARDENING_COMMIT=YES
READY_FOR_PUSH_WITHOUT_WORKFLOW=YES
