# Codex Routing Follow-up Repair Validation - 2026-07-23

## Scope

- Target files:
  - `tools/codex-auto.sh`
  - `tests/test_codex_auto_routing.sh`
- Archive file:
  - `reports/validation/codex_routing_followup_repair_2026-07-23.md`
- Excluded from this batch:
  - facts, reviews, current cards, `stock_workbench_index.md`, weekly files
  - Phase A/B/C implementation code outside `tools/codex-auto.sh`
  - `repo_harness_readonly_research_notes.md`
  - `rules/fable_phase_c_external_review_v0.1.md`
- Push: not performed.

## Newly Observed Failures

During the six Daily Review workflow, multi-line workflow prompts containing words such as `review`, `P1/P2`, and `gpt-5.5/high` in the body could be misclassified as final review instead of ordinary Terra/medium workflow work. The affected class was a primary workflow task whose first line asked to review, revise, seal, or archive work, while later lines merely described review evidence or final-check requirements.

Independent follow-up review also exposed two related routing edges while hardening the fix:

- An over-broad first-line workflow rule could have swallowed explicit final code-review prompts such as `审查并完成最终代码审查`.
- Phase C P1/P2 repair prompts such as `审查并修复 Phase C P1/P2 review manifest 缺陷` and `review and repair Phase C P1/P2 review manifest fix` were not consistently routed to heavy.

## Current Diff

`tools/codex-auto.sh`:

- Added `is_primary_workflow_general_prompt`.
- The rule only inspects the first non-empty prompt line through `prompt_title`.
- It routes primary workflow prompts such as `审查并封存...`, `复核并归档...`, and `核验并修订...` to `general`.
- It refuses explicit final-review wording, including `代码审查`, `最终审查`, `终审`, `审查当前改动`, and English `final code review` / `review current changes`.
- Phase C P1/P2 repair detection now runs before the workflow-general rule.
- Phase C P1/P2 repair detection now returns heavy whenever the first line contains Phase C, P1/P2, and repair semantics, except explicit after-repair verification handoff.
- The final-review log gate, session segmentation, and fail-closed status codes were not loosened.

`tests/test_codex_auto_routing.sh`:

- Added fixtures for workflow prompts that should route to Terra/general.
- Added negative fixtures proving explicit final code review still routes to review.
- Added Phase C P1/P2 repair fixtures proving repair goes heavy.
- Added after-repair verification fixtures proving review handoff remains review.
- Added missing `session_meta`, missing `turn_context`, missing model, and missing effort fixtures.

## Root Cause

The earlier route classifier gave body-level review markers too much influence for workflow prompts. In multi-line operational prompts, later sections often contain review evidence, P1/P2 status, or model-gate language without making the whole task a final code review.

The repair therefore needed to prioritize the first-line task intent, while preserving stricter exceptions for final review and Phase C P1/P2 repair.

## Repair Behavior

The final route contract is:

- facts pack -> `gpt-5.6-luna` / `low`
- ordinary development and verification -> `gpt-5.6-terra` / `medium`
- complex workflow implementation and Phase C P1/P2 repair -> `gpt-5.6-sol` / `high`
- final code review -> `gpt-5.5` / `high`

Final review remains fail-closed when any of the following are missing or mismatched:

- rollout file
- target session id
- `session_meta`
- `turn_context`
- target-session segmentation
- `model=gpt-5.5`
- `reasoning_effort=high`

After-repair verification prompts that explicitly say `修复后` / `after repair` plus review or verification terms remain review handoff, preserving the final-review route.

## Test Matrix

Passed:

- `bash -n tools/codex-auto.sh`
- `bash -n tests/test_codex_auto_routing.sh`
- `bash tests/test_codex_auto_routing.sh`
- `tools/codex-auto.sh --verify-mapping`
- Luna / Terra / Sol / review route fixtures
- final `gpt-5.5/high` fixture
- multi-line body containing `review`, `P1/P2`, and `gpt-5.5/high`
- current-session valid log fixture
- historical-session and cross-session mismatch fixtures
- missing log, missing `session_meta`, missing `turn_context`, missing model, missing effort
- model mismatch and effort mismatch
- path containing spaces for review log verification
- `git diff --check`
- `git diff --cached --check`

Route matrix observed from `--verify-mapping`:

```text
route=mini    model=gpt-5.6-luna   reasoning_effort=low
route=general model=gpt-5.6-terra  reasoning_effort=medium
route=heavy   model=gpt-5.6-sol    reasoning_effort=high
route=review  model=gpt-5.5        reasoning_effort=high
```

## 5.5/high Final Review

Final successful review:

- model: `gpt-5.5`
- reasoning_effort: `high`
- session id: `019f8b71-8038-7b00-bef3-1dc506f739b5`
- rollout: `/Users/wongdaisy/.codex/sessions/2026/07/23/rollout-2026-07-23T04-08-19-019f8b71-8038-7b00-bef3-1dc506f739b5.jsonl`
- machine check: `tools/codex-auto.sh --review --verify-review-log ... --session-id ...`
- machine check output:

```text
actual_review_model=gpt-5.5
actual_review_reasoning_effort=high
```

Final 5.5/high verdict:

- GREEN_LIGHT: YES
- P1: 0
- P2: 0

Earlier review attempts are retained as audit context:

- A direct `codex exec --profile stocks-review` attempt was intercepted by the router and ran as Luna/low; it was rejected as final-review evidence.
- A later valid 5.5/high pass found that the first workflow-general rule could swallow explicit final code-review prompts; fixed by excluding final-review terms and adding tests.
- Another valid 5.5/high pass found that Phase C P1/P2 repair could be swallowed by general; fixed by running heavy repair detection before workflow-general detection.
- Another valid 5.5/high pass found Phase C P1/P2 repair phrases such as `审查并修复...` could still fall to mini/general; fixed by tightening the Phase C P1/P2 repair detector and adding tests.

## P1 / P2

- P1: 0
- P2: 0

## Git Boundary

Intended Commit 1 scope:

- `tools/codex-auto.sh`
- `tests/test_codex_auto_routing.sh`

Actual Commit 1:

- `763b5a4 fix: harden codex routing after workflow recovery`

Intended Commit 2 scope:

- `reports/validation/codex_routing_followup_repair_2026-07-23.md`

Excluded files remain outside this batch:

- `repo_harness_readonly_research_notes.md`
- `rules/fable_phase_c_external_review_v0.1.md`

No facts, reviews, current cards, index, weekly files, or Phase A/B/C code outside `tools/codex-auto.sh` are part of this repair.

## Final Judgment

GREEN_LIGHT: YES

The routing repair and validation report are ready for exact Git sealing, with no P1/P2 remaining and no push to be performed.
