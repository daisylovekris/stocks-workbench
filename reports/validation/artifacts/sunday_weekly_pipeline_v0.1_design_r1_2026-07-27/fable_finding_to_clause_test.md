# Fable finding -> 修订条款 -> 测试映射

| Fable finding | 修订条款 | 状态/原因码 | 测试 |
|---|---|---|---|
| P2-1 legacy review SHA | rules §2.1(3), G5, §7 | `blocked_identity_conflict:legacy_review_sha_unverifiable` | T03 |
| P2-2 跨年 calendar | rules §2.1(1), G1, §4 | `blocked_invalid_facts:calendar_window_invalid` | T04-T05 |
| P2-3 partial 集合 | rules §2.1(4), G3, §7 | `blocked_invalid_facts:metrics_field_missing_or_invalid` | T06-T08 |
| P2-4 index_recovered | rules §5, write path | invalid history does not suppress; valid=`index_recovered` | T09-T10 |
| P3-1 semantic 外溢 | rules §4, §5 | strict SWP no-op only | T11-T12 |
| P3-2 时间契约，Lucien 升 P2 | rules §2.1(5), G6, §7 | `blocked_future_data:source_time_unverifiable` | T13-T15 |
| P3-3 as_of_date | rules §2.1(1), G1, §7 | `blocked_invalid_facts:as_of_date_invalid` | T16 |
| P3-4 diagnostics | rules §4, §7; write path | diagnostics non-completion | T17-T18 |
