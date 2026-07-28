# 完整状态矩阵 r2

| 状态 | outcome / reason_code | 权限 | 可重跑 | 完整证据 |
|---|---|---|---|---|
| `candidate_ready_for_human_review` | `candidate_created:all_gates_passed` | human_review=true；weekly/current/index/git/trading=false | 是 | all input SHA、validators、candidate/manifest/summary/validation、completion index |
| `blocked_missing_facts` | `blocked:facts_missing:<date>` | 全 false | 是 | calendar classifications、canonical paths、缺失清单、atomic diagnostic |
| `blocked_missing_daily_review` | `blocked:daily_review_missing:<date>` | 全 false | 是 | expected mapping、扫描结果、atomic diagnostic |
| `blocked_invalid_facts` | `blocked:calendar_window_invalid` / `as_of_date_invalid` / `facts_validator_failed` / `facts_sha_drift` / `metrics_field_missing_or_invalid` | 全 false | 是 | calendar raw SHA、coverage classification/冲突、validator/field diagnostic、复读结果 |
| `blocked_identity_conflict` | `blocked:identity_mismatch` / `legacy_review_sha_unverifiable` / `phase_c_state_invalid` / `phase_c_permission_invalid` / `forbidden_automatic_trading_field` | 全 false | 是 | expected/actual、review raw SHA、Phase C raw SHA、actual state、allowed enum、schema/permission finding |
| `blocked_future_data` | `blocked:future_input_detected` / `source_time_unverifiable` | 全 false | 是 | cutoff、source classification、source_time/raw ref 或不可验证理由 |
| `already_completed` | `no_op:valid_matching_completion` / `index_recovered` | 原 candidate，不升级；交易等 false | 是 | completion-grade live revalidation、current inputs、candidate SHA、index correlation |
| `failed` | `failed:runtime_io_error` / `lock_error` / `unexpected_exception` | 全 false | 是 | atomic diagnostic 或 lock-errors directory、logical_run_key、unique diagnostic_attempt_id、sanitized exception、commit boundary |

诊断和 lock-error evidence 永不作为 completion、no-op 或 `index_recovered` 输入。无效历史和 diagnostics 都不得 suppress 新 run。
