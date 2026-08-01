# ADR formal seeds

ADR status is restricted to `proposed | accepted | superseded | rejected`; `decision_basis` is restricted to `owner_decision | documents_existing_authority | pending_owner_decision`. Every evidence entry is a complete commit-bound object.

```yaml
- ID: ADR-0001
  title: Memory navigation only
  status: proposed
  decision_basis: pending_owner_decision
  scope: project
  date: 2026-07-29
  decision: Project Memory is a navigation layer over repository evidence and is not an authority source.
  context: Rules, facts, reviews, cards, weekly observations, indexes, and closures already retain their own authority classes.
  alternatives: Treat Memory as authoritative; duplicate source content into Memory; retain navigation-only references.
  consequences: Memory stays small and auditable, while every material claim must retain an exact source identity.
  authority_boundaries: Grants no permission, fact, business-state, trading, Git, or review authority.
  evidence:
    - {path: rules/review_manifest_phase_c_v0.2.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 1d9ed3101594b12cea127f459b6e195d94098912fa6308508be74d1f441b0cc8, role: authority_boundary}
  supersedes: null
  superseded_by: null

- ID: ADR-0002
  title: Repository and runtime separation
  status: proposed
  decision_basis: pending_owner_decision
  scope: project
  date: 2026-07-29
  decision: Portable repository Memory may describe runtime identities but does not copy or depend on external runtime state.
  context: Local sessions, caches, credentials, and runtime manifests are machine-specific and may contain sensitive or non-portable state.
  alternatives: Merge runtime state into the repository; link absolute runtime paths; retain a repository/runtime boundary.
  consequences: Repository artifacts remain portable; missing runtime evidence fails closed instead of being inferred.
  authority_boundaries: Runtime state cannot replace repository evidence and absolute local paths are forbidden in formal seeds.
  evidence:
    - {path: rules/review_manifest_phase_c_v0.2.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 1d9ed3101594b12cea127f459b6e195d94098912fa6308508be74d1f441b0cc8, role: repository_boundary}
  supersedes: null
  superseded_by: null

- ID: ADR-0003
  title: Fail-closed source identity
  status: proposed
  decision_basis: pending_owner_decision
  scope: project
  date: 2026-07-29
  decision: Every formal evidence claim binds repository-relative path, commit snapshot, raw SHA-256, and role.
  context: Path-only or summary-only evidence can silently drift and cannot establish the bytes reviewed.
  alternatives: Trust current worktree paths; trust summaries; require commit-bound identity.
  consequences: Missing, malformed, or mismatched identity blocks the claim and requires adjudication or evidence refresh.
  authority_boundaries: Identity proves bytes at a snapshot only; it does not infer model identity, correctness, permission, or current business truth.
  evidence:
    - {path: rules/review_manifest_phase_c_v0.2.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 1d9ed3101594b12cea127f459b6e195d94098912fa6308508be74d1f441b0cc8, role: fail_closed_identity_boundary}
    - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_final_closure_2026-07-29/closure_manifest.json, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 467e8620ec0fd1815bca2de376bf4c365b3845ff0ed2f345afd15eb765523aae, role: commit_bound_closure_identity}
  supersedes: null
  superseded_by: null

- ID: ADR-0004
  title: Machine and human permission split
  status: proposed
  decision_basis: pending_owner_decision
  scope: project
  date: 2026-07-29
  decision: Machines may prepare bounded candidates; final review, business judgment, and downstream authorization remain human decisions.
  context: Deterministic automation can assemble evidence but cannot safely create trading or Git authority from navigation metadata.
  alternatives: Permit autonomous downstream action; disable automation; preserve a candidate-only boundary.
  consequences: Automation remains useful while every consequential transition requires explicit authority outside Memory.
  authority_boundaries: No autonomous trading, staging, commit, push, review verdict, or business-state decision.
  evidence:
    - {path: rules/sunday_weekly_pipeline_v0.1.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 733da074ff9e3d6b85fc2da1da70d95d3a9e201b6968555a248a2a5a1506db33, role: candidate_only_rule}
    - {path: reports/validation/sunday_weekly_pipeline_v0.1_final_closure_2026-07-29.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 2cb4c6e9969901d2525560ce90b8a6ec26cfbc782ff8ad20e110a438bab59243, role: candidate_only_closure}
  supersedes: null
  superseded_by: null

- ID: ADR-0005
  title: No future-data leakage
  status: proposed
  decision_basis: pending_owner_decision
  scope: project
  date: 2026-07-29
  decision: Dated analyses and validations must be bound to their stated cutoff and may not import later observations.
  context: Later data can make a historical result appear stronger and silently change the meaning of a dated artifact.
  alternatives: Use latest data for every refresh; omit cutoffs; retain explicit time-bounded evidence.
  consequences: Historical statements remain reproducible and later evidence is recorded separately.
  authority_boundaries: Time-bounded evidence does not itself create a trading conclusion or action trigger.
  evidence:
    - {path: rules/sunday_weekly_pipeline_v0.1.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 733da074ff9e3d6b85fc2da1da70d95d3a9e201b6968555a248a2a5a1506db33, role: cutoff_rule}
  supersedes: null
  superseded_by: null

- ID: ADR-0006
  title: Precise staging and no-push default
  status: accepted
  decision_basis: owner_decision
  scope: project
  date: 2026-07-29
  decision: Future Memory closure stages exact intended paths and defaults to no push.
  context: The worktree may contain unrelated or untracked evidence, so broad staging would erase the audit boundary.
  alternatives: Broad staging; automatic push; exact-path staging with separately authorized push.
  consequences: Closure remains reviewable and unrelated dirt stays excluded; additional explicit authority is required for push.
  authority_boundaries: This ADR documents workflow policy but does not authorize staging, commit, or push in any particular run.
  evidence:
    - {path: reports/validation/sunday_weekly_pipeline_v0.1_final_closure_2026-07-29.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 2cb4c6e9969901d2525560ce90b8a6ec26cfbc782ff8ad20e110a438bab59243, role: closure_workflow_evidence}
    - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_final_closure_2026-07-29/closure_manifest.json, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 467e8620ec0fd1815bca2de376bf4c365b3845ff0ed2f345afd15eb765523aae, role: closure_scope_evidence}
  supersedes: null
  superseded_by: null

- ID: ADR-0007
  title: Routing and independent review separation
  status: proposed
  decision_basis: pending_owner_decision
  scope: project
  date: 2026-07-29
  decision: Routing policy records and observed independent-review runs remain different record types.
  context: A routing label states intended task allocation, while a benchmark claim requires a bound observed run.
  alternatives: Rank models from routing labels; merge routing and review records; retain typed separation.
  consequences: Luna, Terra, and Sol stay routing-only until bound runs exist, and one run never becomes a general ranking.
  authority_boundaries: Routing evidence cannot prove quality, cost, latency, or review outcome.
  evidence:
    - {path: reports/validation/codex_routing_repair_final_2026-07-22.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 50db7b8d1fca607975b3f9b46035768c58f7e56b9f9162c0f40cca02e528b933, role: routing_early}
    - {path: reports/validation/codex_routing_followup_repair_2026-07-23.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: d3127bad40acd65c57aec8681bd520d144e748e9fae8331569c4d98c51a57a15, role: routing_followup}
  supersedes: null
  superseded_by: null

- ID: ADR-0008
  title: Pi Fable entry
  status: accepted
  decision_basis: documents_existing_authority
  scope: SWP only
  date: 2026-07-29
  decision: Record the admitted Pi Fable run as SWP-scoped evidence alongside its raw output and A/B comparison.
  context: The run has bound metadata, raw output, measured cost and latency, and an adjudication comparison.
  alternatives: Exclude the run; make Pi a general default; admit it only for the observed SWP scope.
  consequences: The observation is reproducible but remains a one-run, task-specific entry.
  authority_boundaries: No general model ranking, default-provider change, or reliability guarantee follows.
  evidence:
    - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_fable_final_review_2026-07-28/ab_runs/pi-20260729-011452-17167/run_meta.json, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 24d38f481098579b2ed01bb8d792b585392b807661003dfc83e82b15bc0b8fcd, role: run_meta}
    - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_fable_final_review_2026-07-28/ab_runs/pi-20260729-011452-17167/fable_raw.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 2b0c8bfa04416729ae1de892f0b1debe68aab4a741e40c631d8cf4b603cbd938, role: raw}
    - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_fable_final_review_2026-07-28/ab_comparison.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 174c3ad6af4e1579cc2de7bf5a2b84fa5613313d12ff8c024a160fa9d2287034, role: ab_comparison}
  supersedes: null
  superseded_by: null

- ID: ADR-0009
  title: SWP candidate-only output
  status: accepted
  decision_basis: documents_existing_authority
  scope: SWP v0.1
  date: 2026-07-29
  decision: SWP v0.1 machine authority ends at a candidate ready for human review.
  context: The frozen design and closure explicitly separate candidate preparation from approval and downstream action.
  alternatives: Permit autonomous final output; stop at diagnostics; preserve candidate-only completion.
  consequences: A successful run can establish candidate readiness but cannot establish approval or execution authority.
  authority_boundaries: No trading action, Git action, final review verdict, or automatic trigger is authorized.
  evidence:
    - {path: rules/sunday_weekly_pipeline_v0.1.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 733da074ff9e3d6b85fc2da1da70d95d3a9e201b6968555a248a2a5a1506db33, role: candidate_only_rule}
    - {path: reports/validation/sunday_weekly_pipeline_v0.1_final_closure_2026-07-29.md, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 2cb4c6e9969901d2525560ce90b8a6ec26cfbc782ff8ad20e110a438bab59243, role: candidate_only_closure_report}
    - {path: reports/validation/artifacts/sunday_weekly_pipeline_v0.1_final_closure_2026-07-29/closure_manifest.json, snapshot_kind: commit, snapshot_commit: bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca, raw_sha256: 467e8620ec0fd1815bca2de376bf4c365b3845ff0ed2f345afd15eb765523aae, role: candidate_only_closure_manifest}
  supersedes: null
  superseded_by: null
```
