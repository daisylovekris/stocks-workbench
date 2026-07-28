# Safe Phase C resolver design r7

1. Acquire request-key orchestration lock; safe-read `reviews/<date>/review_index.jsonl` with O_NOFOLLOW/fstat and derive bytes/SHA/JSON from that one FD result.
2. Apply bytes-based index-entry structural validation only; never call `inspect_index_entry` because it rereads disk.
3. For each candidate, canonical-path validate then safe-read manifest once; derive its bytes/SHA/JSON from the same FD result and compare index SHA.
4. Apply pure manifest validation to that parsed JSON; require facts_review, null incident reason, whitelist state, false downstream permissions and current official identity.
5. Require exactly one valid authority. Then safe-read the runner path named by it, compare SHA and run Phase B completion validation on that same parsed record/current official bytes.

Tests inject symlink, post-read replace, and hash/parse cross-source attempts; each must fail closed. No path-level check followed by separate read is permitted.
