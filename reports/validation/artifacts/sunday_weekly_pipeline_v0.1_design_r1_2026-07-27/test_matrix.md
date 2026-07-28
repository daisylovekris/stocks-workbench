# 扩展测试矩阵 r1

| ID | 情形 | 核心断言 |
|---|---|---|
| T01 | 正常五交易日 | ready；SHA、Decimal metrics、五 reviews、仅 human_review=true |
| T02 | 节假日短周 | 2-4 个 calendar 交易日允许；不硬编码五日 |
| T03 | legacy Review 无 facts SHA | `blocked_identity_conflict:legacy_review_sha_unverifiable`；完整格式证据；无 candidate/index |
| T04 | 跨年周缺次年 calendar | `blocked_invalid_facts:calendar_window_invalid`；无聚合 |
| T05 | 跨年双 calendar 成功 | 合并窗口完整；两份 calendar raw SHA 均在 input_set |
| T06 | partial 仅四背景字段 | ready；四字段 TODO/null 原样在 unresolved_fields |
| T07 | partial 缺 close | `metrics_field_missing_or_invalid`；无 candidate；不聚合 |
| T08 | partial 成交字段非数值 | 同 T07；bool/NaN/Infinity 均拒绝 |
| T09 | 非法孤儿 manifest | 不得 index_recovered/补 index；新 run 不被 suppress |
| T10 | 合法孤儿 | completion-grade revalidation 后仅补 index；candidate bytes 零改动 |
| T11 | Phase B semantic-pass 但 SWP 输入变化 | 必须新 run，不得 SWP no-op |
| T12 | 同输入重跑 | canonical candidate bytes 与 SHA 完全一致；`already_completed` |
| T13 | provenance 时间晚于 cutoff | 合法；不视为市场事实 |
| T14 | 市场事件晚于 cutoff | `blocked_future_data:future_input_detected` |
| T15 | source_time_unverifiable | `blocked_future_data:source_time_unverifiable` fail-closed |
| T16 | Asia/Shanghai 周日边界 | 默认只接受上海周日；历史显式日期；非法=`as_of_date_invalid` |
| T17 | blocked 诊断原子写入 | 无半目录可见；仅 diagnostic directory + diagnostics record |
| T18 | diagnostics 记录不得压掉新 run | blocked/failed diagnostics 后同输入可生成新 candidate |
| T19 | facts SHA 最终漂移 | `facts_sha_drift`；不 rename candidate、不写 completion index |
| T20 | 双进程竞争 | 单一 completion marker；另一方 revalidate 后 no-op 或新 run |

每例还断言状态、reason_code、全 false/不升级权限、受控 runtime 路径、安全读、正式 `weekly/` 零写入。
