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
work_status: completed
completed_scopes: [design, implementation, validation, closure]
design_status: frozen_design
implementation_status: implemented
validation_status: validated
closure_status: closed
closure_scope: implementation
relationship: follows_swp_design_closure
superseded_by: null
rule_paths: []
implementation_paths: [memory/README.md, memory/project_state.md, memory/phase_registry.md, memory/agent_benchmark.md, memory/decisions/ADR-0001.md, memory/decisions/ADR-0002.md, memory/decisions/ADR-0003.md, memory/decisions/ADR-0004.md, memory/decisions/ADR-0005.md, memory/decisions/ADR-0006.md, memory/decisions/ADR-0007.md, memory/decisions/ADR-0008.md, memory/decisions/ADR-0009.md]
test_paths: []
validation_paths: [reports/validation/project_memory_v0.1_implementation_candidate_2026-08-02.md, reports/validation/project_memory_v0.1_implementation_independent_review_2026-08-02.md, reports/validation/project_memory_v0.1_implementation_closure_delta_review_2026-08-02.md, reports/validation/project_memory_v0.1_implementation_final_closure_2026-08-02.md, reports/validation/artifacts/project_memory_v0.1_implementation_final_closure_2026-08-02/closure_manifest.json, reports/validation/project_memory_v0.1_provenance_revalidation_2026-08-02.md]
sealing_commit: 844d8b541d7fd3165ce9e9a1725f207e1764da51
dependencies: [SWP]
downstream_permissions: []
deferred_items: [production validator implementation]
next_allowed_action: evidence_refresh
evidence:
  - {path: memory/README.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: a69eb4de77084fc10d5f7a83d7f743fffc389105c28911bf5892c4f6ce3fb0e6, role: implementation}
  - {path: memory/project_state.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: c3c9ad62558d200971408d3583ab2700fc56c54d5058bb7ff8a2bd12501b252d, role: implementation}
  - {path: memory/phase_registry.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: 6ec5576800412e0a60214a4886e58b72e11dc7cd99384643f5dbc881b11dd982, role: implementation}
  - {path: memory/agent_benchmark.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: ce2bdb177f09c2400f917720b78f41c6afaac8bde1850d0d3e3f50622d3ba89e, role: implementation}
  - {path: memory/decisions/ADR-0001.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: bd4fd73d73f83d7bf8278cf8da1265f0362731c80c7e4217ae19a6e06681db0d, role: implementation}
  - {path: memory/decisions/ADR-0002.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: 7378cfe32f123f54f1fa5522033d4066b7838652fa80a6d91a610620d057127b, role: implementation}
  - {path: memory/decisions/ADR-0003.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: 7469535b7bf65a7a480993d42c8f5cbb06df3a8baef7fdb64e725fefda5d592f, role: implementation}
  - {path: memory/decisions/ADR-0004.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: 32604df46b90ba3b17a8847cf5d092ecf3701d8f1b6fb0e75a82fac4aaf39839, role: implementation}
  - {path: memory/decisions/ADR-0005.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: 12f18e732d36d16d0ca5acee275e8a665b848e5695fbb1ca73bb9fa3a83a34c7, role: implementation}
  - {path: memory/decisions/ADR-0006.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: de6128c0f92449e8a56e558f88d80c587fa4d9198b64636548d5cd5350b7b7c9, role: implementation}
  - {path: memory/decisions/ADR-0007.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: aeb0662668fe1a058d735df56674391669a3244ef7a9dee6ef32fb8f181e9d26, role: implementation}
  - {path: memory/decisions/ADR-0008.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: df681fda3fea3d368e7835db30a78964499a141df5882d1fab01ecb6f1a29154, role: implementation}
  - {path: memory/decisions/ADR-0009.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: 44b2313bd74e80f8c4b4041ce159e8290c96d582a6ae56eb851fa02650e2c97e, role: implementation}
  - {path: reports/validation/project_memory_v0.1_implementation_candidate_2026-08-02.md, snapshot_kind: commit, snapshot_commit: e1723c26efb76bee2aa2b879233a738f4e7e2323, raw_sha256: 27180b432c1201ba468d650a6f51f2e95cf7d4ee57d387cb3467f77a58b17c79, role: implementation_candidate_report}
  - {path: reports/validation/project_memory_v0.1_implementation_independent_review_2026-08-02.md, snapshot_kind: commit, snapshot_commit: 844d8b541d7fd3165ce9e9a1725f207e1764da51, raw_sha256: b892b0cd6f1d20a1ac9c0fff0a9940854d97fd602d1400e781b3875675c15419, role: historical_implementation_review_report_independence_superseded}
  - {path: reports/validation/project_memory_v0.1_implementation_closure_delta_review_2026-08-02.md, snapshot_kind: commit, snapshot_commit: 844d8b541d7fd3165ce9e9a1725f207e1764da51, raw_sha256: c54ce48770aca5c4383443212ee891f12df2b8ed912cde11f0fb4dd01566fb11, role: historical_closure_delta_review_report_independence_superseded}
  - {path: reports/validation/project_memory_v0.1_implementation_final_closure_2026-08-02.md, snapshot_kind: commit, snapshot_commit: 844d8b541d7fd3165ce9e9a1725f207e1764da51, raw_sha256: e525781b932aeede6296419883880b712c75beb47b9f6f8072aedcf2b7018e6a, role: implementation_final_closure_report}
  - {path: reports/validation/artifacts/project_memory_v0.1_implementation_final_closure_2026-08-02/closure_manifest.json, snapshot_kind: commit, snapshot_commit: 844d8b541d7fd3165ce9e9a1725f207e1764da51, raw_sha256: da4b0f023a18dd136f4f7d398f66294a90fac0b536c9e64c03f1c145d507fbd6, role: implementation_closure_manifest}
  - {path: reports/validation/project_memory_v0.1_provenance_revalidation_2026-08-02.md, snapshot_kind: commit, snapshot_commit: f38b563502fa7e098f8420062c5b71f9fb231fdf, raw_sha256: a188c02337204fb279fd2adaef5f5da35bcd231a8d7613b9fd6af7fba26f8895, role: provenance_revalidation_report}
  - {path: reports/validation/artifacts/project_memory_v0.1_provenance_revalidation_2026-08-02/gpt55_high_isolated_output.md, snapshot_kind: commit, snapshot_commit: f38b563502fa7e098f8420062c5b71f9fb231fdf, raw_sha256: 9df09a642651581db5647e048c082608c35ccae9eba30e995e558111d0d0b392, role: provenance_isolated_output}
  - {path: reports/validation/artifacts/project_memory_v0.1_provenance_revalidation_2026-08-02/review_meta.json, snapshot_kind: commit, snapshot_commit: f38b563502fa7e098f8420062c5b71f9fb231fdf, raw_sha256: 8a8ca17c8021d12ab4ba0d1e488259ec1725479f972f5f03ef3307c124de4510, role: provenance_review_metadata}
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

