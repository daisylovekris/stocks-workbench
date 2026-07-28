# r11 fully expanded cumulative finding mapping

Every historical finding has one row; evidence is sealed in this bundle.

| Finding ID | Severity | Final clause | State/reason | Permissions | Evidence | Exact test ID |
|---|---|---|---|---|---|---|
| Fable-P2-1 | P2 | §2.1.3 review identity | legacy_review_sha_unverifiable | false | review bytes | T01 |
| Fable-P2-2 | P2 | §2.1 calendar coverage | calendar_window_invalid | false | calendar snapshot | T02 |
| Fable-P2-3 | P2 | §2.1.4 partial facts | metrics_field_missing_or_invalid | false | facts snapshot | T07 |
| Fable-P2-4 | P2 | §6 recovery | index_recovered | false | completion evidence | T24 |
| Fable-P3-1 | P3 | §6 matching completion | valid_matching_completion | inherited candidate; trading false | input identity | T20 |
| Fable-P3-2 | P3 | §2.1.5 time registry | source_time_unverifiable | false | config snapshot | T27 |
| Fable-P3-3 | P3 | §3 request envelope | invalid request diagnostic | false | envelope | T11 |
| Fable-P3-4 | P3 | §6 diagnostics | lock_error | false | atomic evidence | T12 |
| Lucien-r2-calendar | P2 | §2.1 coverage contract | calendar_window_invalid | false | calendar raw SHA | T03 |
| Lucien-r2-phase-c | P2 | §2.1 Phase C enum | phase_c_state_invalid | false | review manifest | T09 |
| Lucien-r2-diagnostic | P2 | §6 diagnostics | lock_error | false | unique attempt ID | T12 |
| Lucien-r3-request | P2 | §3 request_key | invalid request diagnostic | false | envelope | T11 |
| Lucien-r3-completion | P2 | §6 physical completion | ambiguous_orphan_completion | false | completion index | T25 |
| Lucien-r3-time | P2 | §2.1.5 cutoff | source_time_unverifiable | false | time fields | T26 |
| Lucien-r4-sealing | P2 | package algorithm | package identity | n/a | manifests | T36 |
| Lucien-r4-mapping | P2 | closure matrices | matrix integrity | n/a | local matrices | T36 |
| Lucien-r4-time | P2 | config registry | source_time_unverifiable | false | config bytes | T27 |
| Lucien-r4-envelope | P2 | §3 safe envelope | invalid request diagnostic | false | redacted envelope | T11 |
| Lucien-r4-lock | P2 | §6 lock contract | lock_error | false | lock path | T29 |
| Lucien-r5-input-set | P2 | §3 input set | input identity changed | false | raw SHA ledger | T20 |
| Lucien-r5-phase-evidence | P2 | §2.1 authority | phase_b_evidence_missing | false | expected/actual paths | T13 |
| Lucien-r5-golden | P2 | candidate semantics | all_gates_passed | human review only | golden inputs | T35 |
| Lucien-r5-lock-order | P2 | §6 lock order | lock_error | false | order evidence | T29 |
| Lucien-r6-resolver | P2 | §2.1 Phase C resolver | phase_c_evidence_invalid | false | index/manifest chain | T17 |
| Lucien-r6-phase-b | P2 | §2.1 Phase B resolver | phase_b_evidence_invalid | false | runner manifest | T14 |
| Lucien-r6-rebuild | P2 | §2.1 rebuild policy | phase_b_evidence_missing | false | provenance | T19 |
| Lucien-r6-config | P2 | semantic config | input identity changed | false | raw config SHA | T21 |
| Lucien-r7-safe-read | P2 | §2.1 same-FD read | phase_c_evidence_invalid | false | safe-read snapshot | T18 |
| Lucien-r7-time-grammar | P2 | config grammar | source_time_unverifiable | false | registry | T27 |
| Lucien-r7-candidate-gate | P2 | §2.1 Phase C gate | phase_c_evidence_invalid | false | candidate metadata | T17 |
| Lucien-r7-path-boundary | P2 | §3 runtime token boundary | invalid path | false | rule snapshot | T29 |
| Lucien-r8-package | P2 | package algorithm | package identity | n/a | manifests | T36 |
| Lucien-r8-schema | P2 | candidate schema | candidate_schema_identity_invalid | false | schema SHA | T22 |
| Lucien-r8-concurrency | P2 | §6 final lock window | ambiguous_phase_c_authority | false | locked resolver | T29 |
| Lucien-r9-decimal | P2 | candidate schema decimals | schema validation | false | AJV output | T30 |
| Lucien-r9-schema-binding | P2 | §2.1 schema identity | candidate_schema_identity_invalid | false | same-FD SHA | T22 |
| Lucien-r9-review-lock | P2 | §6 review lock source | lock_error | false | module map | T29 |
| Lucien-r9-matrix | P2 | closure matrices | matrix integrity | n/a | local matrices | T36 |
| Lucien-r10-decimal | P2 | schema decimal families | schema validation | false | AJV output | T30 |
| Lucien-r10-safe-value | P2 | candidate schema safe_value | schema validation | false | schema snapshot | T32 |
| Lucien-r10-semantics | P2 | candidate semantics | candidate_semantics_identity_invalid | false | semantics SHA | T23 |
| Lucien-r10-golden | P2 | golden derivation | all_gates_passed | human review only | golden candidate | T34 |
| R11-decimal-regex | P2 | schema `$defs` | schema validation | false | AJV draft-2020 record | T30 |
| R11-unresolved-source | P2 | candidate semantics | all_gates_passed | human review only | five Phase C manifests | T33 |
| R11-semantics-identity | P2 | §2.1.10 | candidate_semantics_identity_invalid | false | same-FD SHA | T23 |
| R11-input-set | P2 | §3 input-set algorithm | all_gates_passed | human review only | input-set ledger | T35 |
| R12-candidate-bytes | P2 | candidate canonical bytes | valid_matching_completion | inherited candidate; trading false | raw bytes/manifest | T37 |
| R12-true-daily-review | P2 | input-set contract | all_gates_passed | human review only | five review SHA values | T39 |
| R12-input-schema | P2 | §2.1.10/§4 | input_set_schema_identity_invalid | all false | same-FD schema evidence | T38 |
| R12-live-evidence | P2 | Phase B/C audit evidence | phase_c_evidence_invalid | all false | validation snapshots | T40 |
| R12-matrix-sync | P2 | §7 | valid_matching_completion | inherited candidate; trading false | static audit | T41 |
| R12-ajv-record | P3 | candidate schema | candidate_schema_identity_invalid | all false | fixtures/execution log | T42 |
