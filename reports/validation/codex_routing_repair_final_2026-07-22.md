# Codex Routing Repair Final Validation (2026-07-22)

## Scope and conclusion

Only `tools/codex-auto.sh` and `tests/test_codex_auto_routing.sh` were changed.
This repair is GREEN for the requested routing and final-review identity gate.
No facts, Phase C rules, daily review, current card, index, or weekly file was
changed. The two pre-existing untracked out-of-scope files remain excluded.

## Fault symptom and root cause

Long, multi-line sealing prompts could be sent to the wrong route when their
body mentioned `/review`, `P1/P2`, or a final review example. The previous
heuristics did not consistently give the first-line/main task intent priority.

The initial review-log gate also compared the CLI rollout/session ID to
`turn_context.payload.turn_id`. Real Codex JSONL uses the rollout ID in
`session_meta.payload.session_id` / `id`, while `turn_id` is a separate value.
That made a real current rollout fail closed even when its model and effort
were correct. The first independent review additionally found that taking the
global final `turn_context` could cross a later session boundary.

## Script diff summary

- Adds narrow first-line and body classifiers so facts packs select Luna/low,
  ordinary development and sealing select Terra/medium, complex implementation
  selects Sol/high, and explicit final code review selects gpt-5.5/high.
- Preserves first-line general intent when the body merely quotes `/review` or
  reports final-review evidence; ordinary tasks do not enter the review gate.
- Splits JSONL into `session_meta`-anchored segments. The review gate requires
  exactly one matching session ID and uses only the last `turn_context` in that
  segment. Missing or ambiguous session metadata/context exits 30, wrong model
  exits 31, and wrong effort exits 32. An attempted review without the gate
  exits 33.
- Keeps arguments in arrays, quotes all path/session arguments, and uses
  `printf %q` only for dry-run rendering. No credentials or full session logs
  are emitted or written to the repository.

## Current model routing table

| Task | Route | Model | reasoning_effort |
| --- | --- | --- | --- |
| facts pack | mini | gpt-5.6-luna | low |
| ordinary development/debugging | general | gpt-5.6-terra | medium |
| complex implementation | heavy | gpt-5.6-sol | high |
| final code review | review | gpt-5.5 | high |

## Test matrix and results

| Check | Result |
| --- | --- |
| `bash -n tools/codex-auto.sh` | PASS |
| `bash -n tests/test_codex_auto_routing.sh` | PASS |
| `tests/test_codex_auto_routing.sh` | PASS |
| Luna/Terra/Sol model fixtures | PASS: each rejected with exit 31 |
| missing log, session mismatch, ambiguous/missing current record | PASS: exit 30 |
| gpt-5.5 with low effort | PASS: exit 32 |
| historical gpt-5.5 and cross-session context | PASS: cannot authorize current rollout |
| valid current gpt-5.5/high log, including a path with spaces | PASS |
| normal Luna/Terra/Sol routing and review routing | PASS |
| `git diff --check` and `git diff --cached --check` | PASS |

## Fail-closed evidence

The test harness asserts exact exit statuses for missing log, wrong session,
Luna, Terra, Sol, low effort, historical gpt-5.5, and a cross-session gpt-5.5
record. It separately proves a valid gpt-5.5/high current segment succeeds.
The launcher accepts no UI label or requested flag as proof; it reads only the
target rollout JSONL's session metadata and its bound turn context.

## Real gpt-5.5/high final review

- model: `gpt-5.5`
- reasoning_effort: `high`
- session / rollout: `019f8ad8-cb8e-7cb3-a9b5-459e7cc7041d` /
  `rollout-2026-07-23T01-21-31-019f8ad8-cb8e-7cb3-a9b5-459e7cc7041d.jsonl`
- current-rollout verification: `actual_review_model=gpt-5.5` and
  `actual_review_reasoning_effort=high`

Original final-review text:

> GREEN_LIGHT: YES; P1: <none>; P2: <none>; summary: session_meta segmentation
> is fail-closed and uses only turn_context entries in the matched segment
> before the next session_meta; route precedence and tests match intended
> behavior.

## P1/P2 and Git boundary

P1: none. P2: none.

No user session file was modified. No Phase A/B/C data flow was changed. The
launcher performs no Git write operation and no push was performed. Staging is
limited to the two source/test files for commit 1 and this report for commit 2.
The following remain excluded and untracked:

- `repo_harness_readonly_research_notes.md`
- `rules/fable_phase_c_external_review_v0.1.md`

## Sealing recommendation

Approve the two scoped commits. Do not push as part of this repair.
