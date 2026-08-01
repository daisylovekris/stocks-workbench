# Phase Registry

The exact phase set is `A`, `B`, `C`, `semantic_noop`, `SWP`, `project_memory`, and `D`. Every path in a path array has matching commit-bound evidence. Memory records status and navigation only; `downstream_permissions` does not grant authority beyond the cited source.

## A

```yaml
phase_id: A
name: after-close facts
scope: Phase A
work_status: completed
completed_scopes: [implementation, validation, closure]
design_status: frozen_design
implementation_status: implemented
validation_status: validated
closure_status: closed
closure_scope: implementation
relationship: extended_by_phase_b
superseded_by: null
rule_paths: [rules/run_daily_facts_after_close_phase_a_v0.2.md]
implementation_paths: [tools/generate_daily_facts.py]
test_paths: [tests/test_generate_daily_facts.py]
validation_paths: [reports/validation/run_daily_facts_after_close_phase_a_final_2026-07-16.md]
sealing_commit: 90d32c34ee1e05b2d9a0994f3a653692109d30ea
dependencies: []
downstream_permissions: []
deferred_items: []
next_allowed_action: evidence_refresh
evidence:
  - {path: rules/run_daily_facts_after_close_phase_a_v0.2.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 9fde2adcd204a63b2df93a4efcdaca99e95073d7bd7fb4545117b5a2c4bd92c4, role: rule}
  - {path: tools/generate_daily_facts.py, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: f9ca3b3131c66a0da7e2cffddf46addd8f90ac7855a333e1e4686441a8afe936, role: implementation}
  - {path: tests/test_generate_daily_facts.py, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: bf459bc78fd8e384d47e87cbb0897d84d331bd253ad4c8a0f3ff17a699206eb0, role: test}
  - {path: reports/validation/run_daily_facts_after_close_phase_a_final_2026-07-16.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 3396fc8aab922919901c2b61c110ed0debf430f87d2eac4592197d1815735427, role: final_validation}
```

## B

```yaml
phase_id: B
name: controlled facts writes
scope: Phase B
work_status: completed
completed_scopes: [implementation, validation, closure]
design_status: frozen_design
implementation_status: implemented
validation_status: validated
closure_status: closed
closure_scope: implementation
relationship: extends_phase_a
superseded_by: null
rule_paths: [rules/run_daily_facts_after_close_phase_b_v0.2.md]
implementation_paths: [tools/run_daily_facts_after_close.py, tools/official_facts_transaction.py, tools/phase_b_completion.py]
test_paths: [tests/test_run_daily_facts_after_close.py]
validation_paths: [reports/validation/run_daily_facts_after_close_phase_b_final_2026-07-16.md]
sealing_commit: 034673f5457f1f52b64e19f249e70086ffbb529b
dependencies: [A]
downstream_permissions: []
deferred_items: []
next_allowed_action: evidence_refresh
evidence:
  - {path: rules/run_daily_facts_after_close_phase_b_v0.2.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 65ae9a711fb6e3785c9e58deb7d1eaa46908be0e64808425843c1110369c1813, role: rule}
  - {path: tools/run_daily_facts_after_close.py, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: ea383fd67eb0e05235fb1ec0592e09dd7540642bbdccd59ba06094892cb6bfbe, role: implementation}
  - {path: tools/official_facts_transaction.py, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: ccf89703590f48916c4630f098ed610997cbe43f1e02daa8cbe61ea80f8b8397, role: implementation}
  - {path: tools/phase_b_completion.py, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 6628f70ce7cef35eaf8b7884c6fba8c1f2b769ee5e133195973f67dafca4f292, role: implementation}
  - {path: tests/test_run_daily_facts_after_close.py, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 06a66bbd90776ad437fa94ea75f205ec110e8c84a70ffa4e1e62c488b4c9019b, role: test}
  - {path: reports/validation/run_daily_facts_after_close_phase_b_final_2026-07-16.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 42be442b6a0d326c0d9c0f280f2de7e10e2f2afacba339e6f2286dfaadab25ba, role: final_validation}
```

## C

```yaml
phase_id: C
name: review manifest
scope: Phase C
work_status: completed
completed_scopes: [implementation, validation, closure]
design_status: frozen_design
implementation_status: implemented
validation_status: validated
closure_status: closed
closure_scope: implementation
relationship: reserves_phase_d_without_implementation
superseded_by: null
rule_paths: [rules/review_manifest_phase_c_v0.2.md]
implementation_paths: [tools/review_manifest.py, tools/generate_review_manifest.py]
test_paths: [tests/test_review_manifest.py]
validation_paths: [reports/validation/review_manifest_phase_c_final_matrix_review_2026-07-20.md]
sealing_commit: 0e45c6611c55d5f1dd11f4bd1e8156a3295299f5
dependencies: [B]
downstream_permissions: []
deferred_items: [Phase D archaeology]
next_allowed_action: evidence_refresh
evidence:
  - {path: rules/review_manifest_phase_c_v0.2.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 1d9ed3101594b12cea127f459b6e195d94098912fa6308508be74d1f441b0cc8, role: rule}
  - {path: tools/review_manifest.py, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: fa7b6fb47588a9df2561fd6967d5a16db24f6c72e76b40c00cfd9f700ebcd8b7, role: implementation}
  - {path: tools/generate_review_manifest.py, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 9388f88ec7252d09b4a082617c4ec0dae9922600a05d0661c25daa17e859504a, role: implementation}
  - {path: tests/test_review_manifest.py, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: a6e66162b7c26462c98ff9e4a53c64e4efb3c59872ec473e8af30160a777c943, role: test}
  - {path: reports/validation/review_manifest_phase_c_final_matrix_review_2026-07-20.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 5c7d1d590c0529b70289f659b3f9ba6b510f73b1116f577f2b3f4890d8b0ee9c, role: final_validation}
```

## semantic_noop

```yaml
phase_id: semantic_noop
name: semantic_noop mechanism
scope: mechanism
work_status: completed
completed_scopes: [mechanism, validation, closure]
design_status: not_applicable
implementation_status: implemented
validation_status: validated
closure_status: closed
closure_scope: mechanism
relationship: completion_mechanism_within_phase_b
superseded_by: null
rule_paths: [rules/run_daily_facts_after_close_phase_b_v0.2.md]
implementation_paths: [tools/phase_b_completion.py]
test_paths: [tests/test_run_daily_facts_after_close.py]
validation_paths: [reports/validation/semantic_noop_completion_fix_final_review_2026-07-26.md]
sealing_commit: 088a5e8849047e3ce6db3fe3b6a87b1e3542aebf
dependencies: [B, C]
downstream_permissions: []
deferred_items: []
next_allowed_action: evidence_refresh
evidence:
  - {path: rules/run_daily_facts_after_close_phase_b_v0.2.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 65ae9a711fb6e3785c9e58deb7d1eaa46908be0e64808425843c1110369c1813, role: rule}
  - {path: tools/phase_b_completion.py, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 6628f70ce7cef35eaf8b7884c6fba8c1f2b769ee5e133195973f67dafca4f292, role: implementation}
  - {path: tests/test_run_daily_facts_after_close.py, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 06a66bbd90776ad437fa94ea75f205ec110e8c84a70ffa4e1e62c488b4c9019b, role: test}
  - {path: reports/validation/semantic_noop_completion_fix_final_review_2026-07-26.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 354c4bc6bdcc6670d77bd18cc7ddb161971340e892f1977c1ce2418ebb95b9bc, role: final_validation}
```

## SWP

```yaml
phase_id: SWP
name: Sunday Weekly Pipeline v0.1
scope: design
work_status: completed
completed_scopes: [design, validation, closure]
design_status: frozen_design
implementation_status: not_started
validation_status: validated
closure_status: closed
closure_scope: design
relationship: candidate_only_human_review_boundary
superseded_by: null
rule_paths: [rules/sunday_weekly_pipeline_v0.1.md]
implementation_paths: []
test_paths: []
validation_paths: [reports/validation/sunday_weekly_pipeline_v0.1_final_closure_2026-07-29.md, reports/validation/artifacts/sunday_weekly_pipeline_v0.1_final_closure_2026-07-29/closure_manifest.json]
sealing_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca
dependencies: [B, C]
downstream_permissions: [candidate_only]
deferred_items: [production implementation]
next_allowed_action: human_review
evidence:
  - {path: rules/sunday_weekly_pipeline_v0.1.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 733da074ff9e3d6b85fc2da1da70d95d3a9e201b6968555a248a2a5a1506db33, role: frozen_design_rule}
  - {path: reports/validation/sunday_weekly_pipeline_v0.1_final_closure_2026-07-29.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 2cb4c6e9969901d2525560ce90b8a6ec26cfbc782ff8ad20e110a438bab59243, role: closure_report}
  - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_final_closure_2026-07-29/closure_manifest.json, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 467e8620ec0fd1815bca2de376bf4c365b3845ff0ed2f345afd15eb765523aae, role: closure_manifest}
```

`candidate_only` is a restriction to human-reviewable candidate output, not a trading, Git, business-state, or review-verdict grant.

## project_memory

```yaml
phase_id: project_memory
name: Project Memory v0.1
scope: implementation
work_status: in_progress
completed_scopes: [design, validation, closure]
design_status: frozen_design
implementation_status: in_progress
validation_status: not_started
closure_status: closed
closure_scope: design
relationship: follows_swp_design_closure
superseded_by: null
rule_paths: []
implementation_paths: []
test_paths: []
validation_paths: [reports/validation/project_memory_v0.1_design_final_closure_2026-08-02.md, reports/validation/artifacts/project_memory_v0.1_design_final_closure_2026-08-02/closure_manifest.json]
sealing_commit: d33a7cfd39a8608524096021ae581a6825bc5cc4
dependencies: [SWP]
downstream_permissions: []
deferred_items: [production validator implementation]
next_allowed_action: implementation_validation
evidence:
  - {path: reports/validation/project_memory_v0.1_design_final_closure_2026-08-02.md, snapshot_kind: commit, snapshot_commit: d33a7cfd39a8608524096021ae581a6825bc5cc4, raw_sha256: c891f6c56d65d0dfd6fb4acfe377f48d408674e5830c244829128cb7b72faf7d, role: final_design_closure_report}
  - {path: reports/validation/artifacts/project_memory_v0.1_design_final_closure_2026-08-02/closure_manifest.json, snapshot_kind: commit, snapshot_commit: d33a7cfd39a8608524096021ae581a6825bc5cc4, raw_sha256: f9d5812da342c088d3b60f4e8f2236357cb3557237f6d3f07c70dbf2b63bd2bd, role: final_design_closure_manifest}
  - {path: reports/validation/artifacts/project_memory_v0.1_design_r5_2026-07-29/design_manifest.json, snapshot_kind: commit, snapshot_commit: d33a7cfd39a8608524096021ae581a6825bc5cc4, raw_sha256: 92131e36802c9e0359c4c1933a3650f1a1bca5f809788fe9b41adca7e4538d8d, role: r5_design_manifest}
  - {path: reports/validation/artifacts/project_memory_v0.1_fable_final_review_2026-08-02/formal_runs/pi-project-memory-r5-20260802-012956/fable_raw.md, snapshot_kind: commit, snapshot_commit: d33a7cfd39a8608524096021ae581a6825bc5cc4, raw_sha256: bfa6076db3fa39da1bfe266a3cdd9dddbd259f7355905c1e092f71b1532bb55f, role: final_independent_review_raw}
  - {path: reports/validation/artifacts/project_memory_v0.1_fable_final_review_2026-08-02/formal_runs/pi-project-memory-r5-20260802-012956/run_meta.json, snapshot_kind: commit, snapshot_commit: d33a7cfd39a8608524096021ae581a6825bc5cc4, raw_sha256: 3a615d6bfa84d9ca0df5bd10c8175d344a4ffd20e2be9b2f7673ae50b3478f26, role: final_independent_review_run_metadata}
```

## D

```yaml
phase_id: D
name: Phase D reservation
scope: reservation
work_status: deferred
completed_scopes: []
design_status: not_started
implementation_status: not_started
validation_status: not_started
closure_status: not_applicable
closure_scope: not_applicable
relationship: reserved_by_phase_c_rule
superseded_by: null
rule_paths: [rules/review_manifest_phase_c_v0.2.md]
implementation_paths: []
test_paths: []
validation_paths: []
sealing_commit: null
dependencies: [C]
downstream_permissions: []
deferred_items: [archaeology]
next_allowed_action: separate_design
evidence:
  - {path: rules/review_manifest_phase_c_v0.2.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 1d9ed3101594b12cea127f459b6e195d94098912fa6308508be74d1f441b0cc8, role: reservation_rule}
```

