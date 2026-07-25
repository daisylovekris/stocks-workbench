# Previous findings regression evidence

## GPT-5.5/high P2 and K3 P2-1

`scan_previous_runs()` no longer treats an action name as sufficient completion evidence. It safely reads each matching manifest, invokes the Phase B completion validator, records a stable `scan_diagnostics` reason for every invalid prior, and permits generator plus official transaction rerun. The authoritative scan is called only after the same-task runner lock is acquired.

The mutation matrix covers failed outcome, bundle failure, `manifest_write_failed`, forged reason, missing comparison/candidate path, deleted/tampered/symlinked candidate, official_changed mismatch, SHA mismatches, raw SHA equality, semantic SHA mismatch, all four six-path whitelist corruptions, unfinished stage, wrong run mode, and symbol/date/mode/run-id mismatch.

## K3 P3-1

semantic_noop completion requires the committed run `candidate.json` at its exact identity path. The validator re-reads it with the shared no-follow fd helper, derives raw SHA and JSON from the same bytes, runs the facts Validator, and recomputes `build_semantic_comparison()` against the current official bytes read under the official lock. Deleted, tampered, escaped, or symlinked candidates do not count completed and the next run reconverges.

## Failure-bundle boundary

`outcome=failed`, `manifest_bundle_failed=true`, and `manifest_write_failed` never qualify for completion. The injected semantic_noop summary collision produces an `incident_review`, then the same task reruns and converges to a legal semantic_noop record. No failed-bundle action/reason pair was added to normal Phase C facts-review semantics.

## Positive compatibility

Legal created, identical_noop, and semantic_noop records still return `already_completed`; their generator call count remains one and protected official bytes remain unchanged.
