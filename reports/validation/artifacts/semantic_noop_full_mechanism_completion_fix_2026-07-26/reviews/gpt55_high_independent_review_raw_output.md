# semantic_noop full mechanism independent review raw output

metadata:
- model: gpt-5.5
- reasoning_effort: high
- session_id: 019f9576-c045-7d50-932a-efbc2667be11
- rollout_path: /Users/wongdaisy/.codex/sessions/2026/07/25/rollout-2026-07-25T02-50-15-019f9576-c045-7d50-932a-efbc2667be11.jsonl
- review_start_time: 2026-07-24T18:50:19.788Z / 2026-07-25T02:50:19.788+08:00
- review_end_time: 2026-07-24T18:53:56.755Z / 2026-07-25T02:53:56.755+08:00
- token_limit_touched: false
- base_head: 877e20aa8b1601ed92ed934f8bcd8300c5039845
- scoped_patch_sha256: 01cca38f18eeb3567e8c6ff5470c72985ad500ce38b204687be0ed5dffc925cf
- package_sha256_expected: 0980515c7450eb4fbb2b357e3894f38d911dbdc714571c4d5b030be4e8c557a4
- package_sha256_recorded: 0980515c7450eb4fbb2b357e3894f38d911dbdc714571c4d5b030be4e8c557a4
- package_sha_verification: PASS; bundle_package_sha256.txt records the expected package SHA
- manifest_file_sha_verification: PASS; all review_bundle_manifest.json listed files matched their declared SHA-256 values

scope:
- used only bundle files plus the current session JSONL for required identity verification
- did not read parent repository tree, git history, old GPT-5.5/Grok reviews, or other reports
- did not modify input files
- did not run git add, commit, or push
- did not run tests outside the bundle

result:
- P1 findings: none
- P2 findings: 1
- P3 findings: none
- SAME_BUNDLE_READY_FOR_DUAL_REVIEW: false

P2-1: Phase B previous-run idempotency can treat an invalid semantic_noop manifest as already completed

file:
- snapshots/tools/run_daily_facts_after_close.py

function:
- scan_previous_runs
- execute

evidence:
- scan_previous_runs marks a task completed when any matching manifest has write_official=true, dry_run=false, and write_action in {"created", "identical_noop", "semantic_noop"}.
- It does not validate schema_version, stage, outcome, reason_code, official_changed, before/after SHA consistency, candidate_path, comparison, or semantic_noop evidence.
- execute calls scan_previous_runs before runner_lock and before generating a new candidate. If previous_reason == "already_completed", it persists a skipped manifest and exits.
- The Phase B rule says only a legal official manifest counts as a formal completion record.
- The Phase C code has a much stricter Phase B semantic matrix and semantic_noop evidence validator, but that validation is not reused in Phase B scan_previous_runs.

invariant violated:
- Only a legal formal write_official manifest may suppress rerun as already_completed.
- semantic_noop completion must be tied to the exact action/outcome/reason combination, official_changed=false, stable before/after official SHA, raw candidate != official, committed candidate_path, and a valid comparison object.

trigger scenario:
1. In the same runtime/runs/<date>/... directory, a previous manifest exists with matching symbol, target_date, mode, run_id and a timestamp.
2. That manifest sets write_official=true, dry_run=false, write_action=semantic_noop.
3. The manifest is otherwise invalid or incomplete, for example outcome=failed, reason_code=forged_reason, official_changed=true, missing comparison, missing candidate_path, or mismatched SHAs.
4. A later Phase B --write-official run for the same symbol/date/mode starts.
5. scan_previous_runs returns already_completed before candidate generation and before transaction validation.

impact:
- A malformed, partial, or forged semantic_noop runner manifest can suppress a real official write attempt.
- The system can skip the only path that would regenerate candidate evidence and re-run the official transaction.
- This undermines fail-closed action/outcome/reason handling and runtime idempotency for the newly added semantic_noop path.
- Phase C may later reject that runner manifest, but Phase B has already been incorrectly prevented from producing a valid replacement run.

minimum fix:
- Replace the write_action-only completion predicate in scan_previous_runs with a local validator for completion manifests.
- Required checks at minimum:
  - schema_version == runner_manifest_v0.2_phase_b
  - stage == finished and finished_at is a valid timestamp
  - write_official is true and dry_run is false
  - action/outcome/reason are a legal Phase B combination
  - created and identical_noop require official_sha256_after == candidate_sha256
  - no-change transactions require official_sha256_before == official_sha256_after
  - semantic_noop specifically requires outcome=official_unchanged, reason_code=official_semantically_identical, official_changed=false, official_bytes_equal_candidate=false, valid candidate_path, and a structurally valid comparison
- Prefer sharing the same Phase B semantic matrix shape used by snapshots/tools/review_manifest.py, or moving the matrix to a common module.
- Invalid matching manifests should be recorded in scan_diagnostics and must not produce already_completed.

minimum tests:
- Add a test that writes a matching previous manifest with write_official=true, dry_run=false, write_action=semantic_noop, but outcome=failed or reason_code=forged_reason; assert scan_previous_runs returns reason=None and execute runs the generator.
- Add a test for semantic_noop missing comparison/candidate_path; assert it does not skip.
- Add a positive test for a fully legal semantic_noop previous manifest; assert it still skips already_completed.
- Add regression tests that created/identical_noop completion still works only for legal action/outcome/reason/SHA combinations.

non-findings / checked items:
- semantic_noop and identical_noop mutual exclusion is implemented in the transaction order: byte-identical official returns identical_noop before semantic comparison; semantic_noop requires raw byte difference through the conflict branch and records official_bytes_equal_candidate=false.
- The six-path whitelist is fixed in SEMANTIC_NOOP_EXCLUDED_JSON_PATHS and the code pops exact paths only.
- The semantic comparison requires symbol, trade_date, and schema_version equality before path exclusion.
- Missing approved paths, non-string timestamp values, invalid timezone datetimes, unknown fields, non-whitelisted fetched_at, missing fields, needs_manual_check, and business-field changes are covered by tests as conflicts.
- candidate and official validators are both required for semantic_noop in the transaction path.
- raw SHA fields and semantic SHA fields are both recorded and not collapsed into one value.
- Phase C re-reads committed candidate.json, checks raw SHA, validates candidate and official, recomputes comparison using the shared implementation, and rejects tampering as runner_manifest_invalid.
- Phase C fail-closed action/reason/outcome matrix includes semantic_noop and rejects mismatches.
- generate_daily_facts wrote_file now tracks official_changed, so semantic_noop and identical_noop report wrote_file=false.

scope limitations:
- The bundle does not include source snapshots for tools/official_facts_lock.py, tools/validate_review_chain.py, or tools/volume_ratio_evidence.py.
- Therefore full source-level verification of official lock implementation, all no-follow behavior in Phase B dependencies, the facts Validator, and the ISO timezone parser is not possible from this bundle alone.
- The included Phase C code has its own O_NOFOLLOW fd-chain reader and tests for candidate/official symlink replacement, but Phase B's dependency-level lock/read implementation cannot be independently audited from the provided files.
- The bundle contains recorded test results, but the complete synthetic candidate tree path points outside the bundle and was not read under the requested boundary.

test evidence in bundle:
- test_execution_result.txt reports targeted tests: 364 passed, 28 subtests passed.
- test_execution_result.txt reports full pytest: 545 passed, 28 subtests passed.
- test_execution_result.txt reports py_compile: PASS.
- test_execution_result.txt reports git diff --check: PASS.
- test_baseline.txt reports expected full pytest: 545 passed, 28 subtests passed.

final verdict:
- Not ready for SAME_BUNDLE_READY_FOR_DUAL_REVIEW until P2-1 is fixed or explicitly accepted as out of scope.
