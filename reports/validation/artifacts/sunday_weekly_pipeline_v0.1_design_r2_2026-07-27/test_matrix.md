# 测试矩阵 r2

| ID | 情形 | 核心断言 |
|---|---|---|
| C01 | 2026 `trading_days` 正常周 | coverage 内工作日 membership 分类成功、ready、calendar SHA 入 input_set。 |
| C02 | coverage 内周末 | 不在 `trading_days` 的周六/日推导为 non-trading，非逐日状态缺失。 |
| C03 | 日期在 coverage 外 | `blocked_invalid_facts:calendar_window_invalid`；不把它静默视为 non-trading。 |
| C04 | 跨年双 calendar | 2026/2027 coverage 合并成功；两份 raw SHA 均入 input_set。 |
| C05 | 跨年缺任一 coverage | `calendar_window_invalid`；无聚合、无 candidate。 |
| C06 | overlap conflict | 两个 coverage 对同 date 给出不同 trading 分类时 `calendar_window_invalid`；全 false。 |
| C07 | Phase C 精确白名单 | 两个允许 state 分别可过 G7，全部 downstream permissions 仍 false。 |
| C08 | Phase C 非法 state | unknown、null、空、其他 state 均 `blocked_identity_conflict:phase_c_state_invalid`；全 false。 |
| C09 | 同输入连续两次失败 | logical_run_key 相同但两个 unique attempt_id/diagnostic paths；不覆盖且不 suppress。 |
| C10 | 并发 diagnostic | 同 weekly lock 下 `diagnostics.jsonl` 每条完整、无交织、均 fsync；无 completion index。 |
| C11 | lock_error | 保存至规定 `lock-errors/diagnostic_<logical_run_key>_<attempt_id>/`；`failed:lock_error`、全 false。 |
| R01 | legacy Review 无 facts SHA | 唯一 fail-closed state、格式证据、无 candidate/index。 |
| R02 | partial 仅四背景字段 | ready；TODO/null 原样进入 unresolved_fields。 |
| R03 | partial 缺 close | `metrics_field_missing_or_invalid`；无 candidate、不聚合。 |
| R04 | partial 成交字段非法 | bool/NaN/Infinity 全拒绝。 |
| R05 | 非法孤儿 manifest | 不补 index、不 no-op、新 run 不被 suppress。 |
| R06 | 合法孤儿 | completion-grade revalidation 后只补 index，candidate bytes 零改动。 |
| R07 | Phase B semantic-pass 但 SWP 输入变化 | 必须新 completion identity。 |
| R08 | provenance 晚于 cutoff | 合法，不视为市场事实。 |
| R09 | 市场事件晚于 cutoff | `blocked_future_data:future_input_detected`。 |
| R10 | source_time 不可验证 | `blocked_future_data:source_time_unverifiable`。 |
| R11 | Shanghai 周日边界 | 默认仅上海周日；历史须显式日期；非法为 `as_of_date_invalid`。 |

每例还断言状态、reason_code、全 false 或不升级权限、受控 runtime 路径、安全读、正式 `weekly/` 零写入。
