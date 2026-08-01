# project_state formal seed

```yaml
schema_version: project_memory_v0.1
as_of_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca
as_of_date: 2026-07-29
current_branch: workbench/mainline-2026-07
current_milestone: Project Memory v0.1 r5 mechanically sealed and ready for focused review
work_status: in_progress
completed_scopes: []
completed_closures:
  - Phase A
  - Phase B
  - Phase C
  - semantic_noop mechanism
  - SWP design
active_work:
  - Fable focused review
queued_work:
  - design closure commit after review
  - memory implementation
  - implementation validation
deferred_work:
  - Phase D archaeology
  - production validator implementation
blockers: []
known_dirty_exclusions:
  - tests/test_codex_auto_routing.sh
  - tools/codex-auto.sh
  - repo_harness_readonly_research_notes.md
  - reports/validation/artifacts/project_memory_v0.1_design_2026-07-29/
  - reports/validation/artifacts/project_memory_v0.1_design_r1_2026-07-29/
  - reports/validation/artifacts/project_memory_v0.1_design_r2_2026-07-29/
  - reports/validation/artifacts/project_memory_v0.1_design_r3_2026-07-29/
  - reports/validation/artifacts/project_memory_v0.1_design_r4_2026-07-29/
  - reports/validation/artifacts/semantic_noop_full_mechanism_2026-07-25/
  - reports/validation/artifacts/semantic_noop_phase_c_2026-07-24/
  - reports/validation/daily_review_2026-07-23_2026-07-24_validation.md
  - reports/validation/project_memory_v0.1_design_2026-07-29.md
  - reports/validation/project_memory_v0.1_design_r1_2026-07-29.md
  - reports/validation/project_memory_v0.1_design_r2_2026-07-29.md
  - reports/validation/project_memory_v0.1_design_r3_2026-07-29.md
  - reports/validation/project_memory_v0.1_design_r4_2026-07-29.md
  - reports/warp_windows_BCD_review_2026-07-25.md
  - rules/fable_phase_c_external_review_v0.1.md
source_references:
  - {path: reports/validation/run_daily_facts_after_close_phase_a_final_2026-07-16.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 3396fc8aab922919901c2b61c110ed0debf430f87d2eac4592197d1815735427, role: Phase_A_closure}
  - {path: reports/validation/run_daily_facts_after_close_phase_b_final_2026-07-16.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 42be442b6a0d326c0d9c0f280f2de7e10e2f2afacba339e6f2286dfaadab25ba, role: Phase_B_closure}
  - {path: reports/validation/review_manifest_phase_c_final_matrix_review_2026-07-20.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 5c7d1d590c0529b70289f659b3f9ba6b510f73b1116f577f2b3f4890d8b0ee9c, role: Phase_C_closure}
  - {path: reports/validation/semantic_noop_completion_fix_final_review_2026-07-26.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 354c4bc6bdcc6670d77bd18cc7ddb161971340e892f1977c1ce2418ebb95b9bc, role: semantic_noop_closure}
  - {path: reports/validation/sunday_weekly_pipeline_v0.1_final_closure_2026-07-29.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 2cb4c6e9969901d2525560ce90b8a6ec26cfbc782ff8ad20e110a438bab59243, role: SWP_design_closure_report}
  - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_final_closure_2026-07-29/closure_manifest.json, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 467e8620ec0fd1815bca2de376bf4c365b3845ff0ed2f345afd15eb765523aae, role: SWP_design_closure_manifest}
  - {path: stock_workbench_index.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 2753045592485753f68df039e760ed0d5be8965075ffa6ce88cece92bab535db, role: current_business_navigation_index}
```

The r5 report and r5 artifact directory are the active content-closure scope, not dirty exclusions. All listed exclusions pre-existed or belong to other design/review lines and remain untouched.
