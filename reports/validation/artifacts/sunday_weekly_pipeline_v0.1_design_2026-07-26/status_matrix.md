# 状态矩阵

| 状态 | outcome | reason_code 示例 | downstream permissions | 重跑 | 最小证据 |
|---|---|---|---|---|---|
| candidate_ready_for_human_review | candidate_created | all_gates_passed | human_review=true；其余全 false | 是 | 完整输入 SHA、validators、candidate、manifest、summary、index |
| blocked_missing_facts | blocked | facts_missing:date | 全 false | 是 | calendar + expected paths |
| blocked_invalid_facts | blocked | facts_validator_failed / facts_sha_drift | 全 false | 是 | raw bytes SHA + diagnostic |
| blocked_missing_daily_review | blocked | daily_review_missing:date | 全 false | 是 | expected one-to-one mapping |
| blocked_future_data | blocked | future_input_detected | 全 false | 是 | cutoff + offending ref |
| blocked_identity_conflict | blocked | identity_mismatch / forbidden_automatic_trading_field | 全 false | 是 | expected/actual identity or schema finding |
| already_completed | no_op | valid_matching_completion / index_recovered | 原 candidate 权限，不升级 | 是 | live revalidation + index correlation |
| failed | failed | runtime_io_error / lock_error | 全 false | 是 | sanitized failure record |

任何 blocked/failed/invalid historical run 都不是 completion，不能阻止后续正常重跑。

