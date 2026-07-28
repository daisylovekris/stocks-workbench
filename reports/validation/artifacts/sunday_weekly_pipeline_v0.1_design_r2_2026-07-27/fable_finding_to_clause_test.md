# Finding -> r2 条款 -> 测试映射

| Finding | r2 条款 | 状态/原因码 | 测试 |
|---|---|---|---|
| P2-1 legacy Review SHA | rules §2.1(3)、G5、§7 | `blocked_identity_conflict:legacy_review_sha_unverifiable` | R01 |
| P2-2 calendar 跨年 | rules §2.1(1)、G1、§4 | `blocked_invalid_facts:calendar_window_invalid` | C04-C05 |
| r2 calendar schema P2 | rules §2.1(1)、G1 | coverage membership；缺 coverage/重叠/日期/时区非法均 `calendar_window_invalid` | C01-C06 |
| P2-3 partial 集合 | rules §2.1(4)、G3 | `blocked_invalid_facts:metrics_field_missing_or_invalid` | R02-R04 |
| P2-4 index_recovered | rules §5 | 无效孤儿不 suppress；合法孤儿 `index_recovered` | R05-R06 |
| P3-1 semantic 外溢 | rules §4、§5 | SWP strict completion identity only | R07 |
| P3-2 时间契约 | rules §2.1(5)、G6 | `blocked_future_data:source_time_unverifiable` | R08-R10 |
| P3-3 as_of_date | rules §2.1(1)、G1 | `blocked_invalid_facts:as_of_date_invalid` | R11 |
| P3-4 diagnostics | rules §4、§7 | atomic diagnostics excluded from completion | C09-C11 |
| r2 Phase C enum P3 | rules G7、§7 | `blocked_identity_conflict:phase_c_state_invalid` | C07-C08 |
