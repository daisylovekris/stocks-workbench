# 状态矩阵 r3

| 状态 | outcome / reason | 权限 | 关键证据 |
|---|---|---|---|
| `candidate_ready_for_human_review` | `candidate_created:all_gates_passed` | human_review=true；其余含 trading=false | input set、semantic key、attempt id、candidate/manifest/summary/validation、index exact fields |
| `blocked_missing_facts` | `blocked:facts_missing:<date>` | 全 false | request_key、available/missing inputs、raw SHA、atomic diagnostic |
| `blocked_missing_daily_review` | `blocked:daily_review_missing:<date>` | 全 false | request_key、expected identity、available/missing inputs、atomic diagnostic |
| `blocked_invalid_facts` | `blocked:calendar_window_invalid` / `as_of_date_invalid` / metrics/facts reasons | 全 false | request_key、calendar classifications、raw SHA、validator diagnostic |
| `blocked_future_data` | `blocked:future_input_detected` / `source_time_unverifiable` | 全 false | source_kind、structured time/trade_date or exact failure、Shanghai cutoff |
| `blocked_identity_conflict` | `blocked:phase_c_state_invalid` / `ambiguous_orphan_completion` / other identity reasons | 全 false | request key, actual/expected, orphan inventory or enum evidence |
| `already_completed` | `no_op:valid_matching_completion` / `index_recovered` | existing candidate only; trading=false | exact index row + completion-grade revalidation |
| `failed` | `failed:lock_error` / runtime reasons | 全 false | request_key、unique diagnostic_attempt_id、lock-error or diagnostic path、available/missing inputs |

Diagnostics and lock-error evidence never participate in completion, no-op, or index recovery.
