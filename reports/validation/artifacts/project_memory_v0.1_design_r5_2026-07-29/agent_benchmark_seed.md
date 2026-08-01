# agent_benchmark formal seed

The exact Agent set is `Luna`, `Terra`, `Sol`, `gpt-5.5 high`, `Pi Fable`, `Bare Fable`, `Kimi Code`, `GLM`, and `MiMo`. Routing-policy records are not benchmark runs. No observed run supports a general quality ranking, and every admitted observed run has commit-bound evidence.

```yaml
- record_type: routing_policy
  agent_or_model: Luna
  provider_backend: Codex
  task_class: facts_routing
  actual_model_evidence: routing_followup_commit_bound
  reasoning_effort: low
  observed_result: routing_only
  evidence_scope: policy
  sample_count: 0
  model_identity_confidence: medium
  cost: unknown
  cost_currency: unknown
  cost_scope: unknown
  latency: unknown
  limitations: no_bound_run
  adjudication_path: future_bound_review
  evidence_disposition: admitted
  benchmark_eligible: false
  adr_eligible: false
  strengths: routing_policy_only
  weaknesses: no_benchmark
  suitable_role: routing
  unsuitable_role: ranking
  confidence: medium
  last_verified_date: 2026-07-23
  evidence:
    - {path: reports/validation/codex_routing_followup_repair_2026-07-23.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: d3127bad40acd65c57aec8681bd520d144e748e9fae8331569c4d98c51a57a15, role: routing_followup}

- record_type: routing_policy
  agent_or_model: Terra
  provider_backend: Codex
  task_class: ordinary_development_routing
  actual_model_evidence: routing_followup_commit_bound
  reasoning_effort: medium
  observed_result: routing_only
  evidence_scope: policy
  sample_count: 0
  model_identity_confidence: medium
  cost: unknown
  cost_currency: unknown
  cost_scope: unknown
  latency: unknown
  limitations: no_bound_run
  adjudication_path: future_bound_review
  evidence_disposition: admitted
  benchmark_eligible: false
  adr_eligible: false
  strengths: routing_policy_only
  weaknesses: no_benchmark
  suitable_role: routing
  unsuitable_role: ranking
  confidence: medium
  last_verified_date: 2026-07-23
  evidence:
    - {path: reports/validation/codex_routing_followup_repair_2026-07-23.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: d3127bad40acd65c57aec8681bd520d144e748e9fae8331569c4d98c51a57a15, role: routing_followup}

- record_type: routing_policy
  agent_or_model: Sol
  provider_backend: Codex
  task_class: complex_implementation_routing
  actual_model_evidence: routing_followup_commit_bound
  reasoning_effort: high
  observed_result: routing_only
  evidence_scope: policy
  sample_count: 0
  model_identity_confidence: medium
  cost: unknown
  cost_currency: unknown
  cost_scope: unknown
  latency: unknown
  limitations: no_bound_run
  adjudication_path: future_bound_review
  evidence_disposition: admitted
  benchmark_eligible: false
  adr_eligible: false
  strengths: routing_policy_only
  weaknesses: no_benchmark
  suitable_role: routing
  unsuitable_role: ranking
  confidence: medium
  last_verified_date: 2026-07-23
  evidence:
    - {path: reports/validation/codex_routing_followup_repair_2026-07-23.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: d3127bad40acd65c57aec8681bd520d144e748e9fae8331569c4d98c51a57a15, role: routing_followup}

- record_type: observed_run
  agent_or_model: gpt-5.5 high
  provider_backend: Codex
  task_class: final_review
  actual_model_evidence: bound_raw
  reasoning_effort: high
  observed_result: recorded
  evidence_scope: one_run
  sample_count: 1
  model_identity_confidence: high
  cost: unknown
  cost_currency: unknown
  cost_scope: unknown
  latency: unknown
  limitations: no_general_ranking
  adjudication_path: recorded_review
  evidence_disposition: admitted
  benchmark_eligible: true
  adr_eligible: true
  strengths: scoped_review
  weaknesses: one_run
  suitable_role: final_review
  unsuitable_role: ranking
  confidence: high
  last_verified_date: 2026-07-26
  evidence:
    - {path: reports/validation/artifacts/semantic_noop_full_mechanism_completion_fix_2026-07-26/reviews/gpt55_high_independent_review_raw_output.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 4ad467c9b5e2acd118c67cc08f01f371eaaeaba30547965d0d9970c92d849701, role: raw}

- record_type: observed_run
  agent_or_model: Pi Fable
  provider_backend: Pi
  task_class: SWP_review
  actual_model_evidence: metadata_raw_and_comparison
  reasoning_effort: low
  observed_result: recorded
  evidence_scope: one_run
  sample_count: 1
  model_identity_confidence: high
  cost: 1.004
  cost_currency: USD
  cost_scope: run
  latency: 101_seconds
  limitations: SWP_only_no_ranking
  adjudication_path: ab_comparison
  evidence_disposition: admitted
  benchmark_eligible: true
  adr_eligible: true
  strengths: scoped_review
  weaknesses: one_run
  suitable_role: SWP_review
  unsuitable_role: ranking
  confidence: high
  last_verified_date: 2026-07-29
  evidence:
    - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_fable_final_review_2026-07-28/ab_runs/pi-20260729-011452-17167/run_meta.json, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 24d38f481098579b2ed01bb8d792b585392b807661003dfc83e82b15bc0b8fcd, role: run_meta}
    - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_fable_final_review_2026-07-28/ab_runs/pi-20260729-011452-17167/fable_raw.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 2b0c8bfa04416729ae1de892f0b1debe68aab4a741e40c631d8cf4b603cbd938, role: raw}
    - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_fable_final_review_2026-07-28/ab_comparison.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 174c3ad6af4e1579cc2de7bf5a2b84fa5613313d12ff8c024a160fa9d2287034, role: ab_comparison}

- record_type: observed_run
  agent_or_model: Bare Fable
  provider_backend: Bare
  task_class: SWP_comparator
  actual_model_evidence: recovered_metadata_raw_note_and_comparison
  reasoning_effort: unknown
  observed_result: recovered
  evidence_scope: one_run
  sample_count: 1
  model_identity_confidence: high
  cost: 1.581959
  cost_currency: USD
  cost_scope: run
  latency: unknown
  limitations: local_capture_failed
  adjudication_path: ab_comparison
  evidence_disposition: admitted
  benchmark_eligible: true
  adr_eligible: true
  strengths: scoped_comparator
  weaknesses: no_reliability_claim
  suitable_role: comparator
  unsuitable_role: ranking
  confidence: high
  last_verified_date: 2026-07-29
  evidence:
    - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_fable_final_review_2026-07-28/ab_runs/bare-recovered-20260729-0154/run_meta.json, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 61f5a8f4069e64943875b7e4ea9f2f02fe0ea8866fdf2460394d239a4bda1a2e, role: run_meta}
    - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_fable_final_review_2026-07-28/ab_runs/bare-recovered-20260729-0154/fable_raw.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 27edebeb3db5dd6aa1419fb3819aca49e29966152e4a673481215576713efc34, role: raw}
    - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_fable_final_review_2026-07-28/ab_runs/bare-recovered-20260729-0154/recovery_note.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 53e9be2c1b08957927a93d7e39a22f16caa82cd0432cbe1fafec4d7640023982, role: recovery_note}
    - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_fable_final_review_2026-07-28/ab_comparison.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 174c3ad6af4e1579cc2de7bf5a2b84fa5613313d12ff8c024a160fa9d2287034, role: ab_comparison}

- record_type: observed_run
  agent_or_model: Kimi Code
  provider_backend: Kimi
  task_class: narrow_review
  actual_model_evidence: provenance_and_raw
  reasoning_effort: high
  observed_result: recorded
  evidence_scope: one_run
  sample_count: 1
  model_identity_confidence: medium
  cost: unknown
  cost_currency: unknown
  cost_scope: unknown
  latency: unknown
  limitations: model_version_UNKNOWN_no_ranking
  adjudication_path: recorded_review
  evidence_disposition: admitted
  benchmark_eligible: true
  adr_eligible: true
  strengths: scoped_review
  weaknesses: one_run
  suitable_role: narrow_review
  unsuitable_role: ranking
  confidence: medium
  last_verified_date: 2026-07-26
  evidence:
    - {path: reports/validation/artifacts/semantic_noop_full_mechanism_completion_fix_2026-07-26/reviews/kimi_k3_semantic_noop_full_mechanism_review_raw.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: afee4601aa9f679acfae01fd5a835d837d8c05cefb7fae1f0fdbdfd7ffe3e79f, role: raw}
    - {path: reports/validation/artifacts/semantic_noop_full_mechanism_completion_fix_2026-07-26/reviews/kimi_k3_review_provenance.json, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: a3695acd474926516277cefc3077e7cbb784f8070e6a4654fcafed5e19b7a1cf, role: provenance}

- record_type: pending_observation
  agent_or_model: GLM
  provider_backend: unknown
  task_class: unknown
  actual_model_evidence: none
  reasoning_effort: unknown
  observed_result: unknown
  evidence_scope: none
  sample_count: 0
  model_identity_confidence: none
  cost: unknown
  cost_currency: unknown
  cost_scope: unknown
  latency: unknown
  limitations: no_evidence
  adjudication_path: future_bound_review
  evidence_disposition: pending
  benchmark_eligible: false
  adr_eligible: false
  strengths: unknown
  weaknesses: no_evidence
  suitable_role: none
  unsuitable_role: conclusion
  confidence: none
  last_verified_date: unknown
  evidence: []

- record_type: pending_observation
  agent_or_model: MiMo
  provider_backend: unknown
  task_class: unknown
  actual_model_evidence: none
  reasoning_effort: unknown
  observed_result: unknown
  evidence_scope: none
  sample_count: 0
  model_identity_confidence: none
  cost: unknown
  cost_currency: unknown
  cost_scope: unknown
  latency: unknown
  limitations: no_evidence
  adjudication_path: future_bound_review
  evidence_disposition: pending
  benchmark_eligible: false
  adr_eligible: false
  strengths: unknown
  weaknesses: no_evidence
  suitable_role: none
  unsuitable_role: conclusion
  confidence: none
  last_verified_date: unknown
  evidence: []
```
