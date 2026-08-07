# Follow-up correction and closure check

Read-only architecture review. Do not modify files or print credential values.

Your prior focused verdict accepted the sealed-bytes-preserved contract and scanner hardening, with P2 items for enforcing operational old-identity zero and for negative allowlist tests.

One factual correction: current tracked history contains **10** immutable sealed/archive files with historical rewritten-identity text, not 9. Nine contain full old SHAs; one additional immutable Fable archive contains only an old 7+ character prefix. The explicit migration appendix is an 11th allowed historical-reference file. All 10 sealed/archive files are byte-preserved historical evidence; current operational/live records must contain zero old full or shortened identities.

The two P2 items are now implemented:

1. `tools/validate_history_sanitization.py` parses the exact 8-pair mapping from the migration appendix at the target revision, scans the target tree, and fails if any full old SHA or standalone 7–12 character old prefix appears outside the exact allowlist of 10 immutable archive paths plus the migration appendix. It does not hard-code old SHAs into operational source. The validator currently reports:
   - `HISTORY_SANITIZATION_POLICY_PASS`
   - `OPERATIONAL_OLD_IDENTITY_FILE_COUNT=0`
   - `ALLOWED_HISTORICAL_REFERENCE_FILE_COUNT=11`
   It is wired into pre-push and the deferred CI workflow.

2. Scanner allowlist hardening now has negative tests proving both of these remain blocked:
   - a real-looking synthetic secret appended to `***REDACTED***`;
   - a real-looking synthetic secret appended to an environment-variable reference.
   Exact redaction/env-reference placeholders alone remain allowed.

Additional verification after these changes:
- dedicated scanner + migration-contract tests: 12 passed;
- full repository tests: 642 passed + 28 subtests;
- full current-history scanner: `SECRET_SCAN_CLEAN`;
- `git diff --check`: pass;
- production reflogs purged and old secret-bearing object absent;
- local/remote sanitized branch still matched before the uncommitted hardening candidate.

CI workflow remains locally prepared and deferred because the current GitHub token lacks `workflow` scope. GitHub Push Protection remains active.

Questions:
1. Does the correction from 9 full-SHA archive files to 10 archive files total (9 full + 1 prefix-only) change the accepted sealed contract?
2. Are the prior P2 findings now closed?
3. May the small hardening commit include scanner, pre-commit/pre-push, migration validator, tests, and migration-report/Fable evidence updates while excluding `.github/workflows/secret-scan.yml` until token scope is upgraded?

End exactly:
SEALED_CONTRACT_VERDICT=<ACCEPT|ACCEPT_WITH_GATES|REJECT>
PREFIX_ONLY_ARCHIVE_EXCEPTION=<ACCEPT|REJECT>
OPERATIONAL_IDENTITY_GATE=<PASS|FAIL>
ALLOWLIST_NEGATIVE_TEST_GATE=<PASS|FAIL>
P1_COUNT=<integer>
P2_COUNT=<integer>
P3_COUNT=<integer>
READY_FOR_HARDENING_COMMIT=<YES|NO>
READY_FOR_PUSH_WITHOUT_WORKFLOW=<YES|NO>
