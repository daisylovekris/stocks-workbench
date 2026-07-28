# 测试矩阵 r3

| ID | 情形 | 必须断言 |
|---|---|---|
| E01 | 非法 as_of_date | safe raw canonical representation -> request_key；原始值不进入路径。 |
| E02 | calendar 缺失 | 无 input_set 仍以 request_key 原子写 diagnostic。 |
| E03 | facts 缺失 | 无 input_set 仍写 diagnostic，列出 missing facts。 |
| E04 | Review 缺失 | 无 input_set 仍写 diagnostic，列出 missing review。 |
| E05 | lock 获取失败 | 无 input_set 保存 request-key lock-error evidence。 |
| E06 | 同 request 两次失败 | diagnostic_attempt_id 与物理路径均唯一。 |
| R01 | 2026 schema 正常周/周末 | coverage+trading_days 成功；coverage 内周末为 non-trading。 |
| R02 | coverage 外/跨年缺 coverage | `calendar_window_invalid`；不静默 non-trading。 |
| R03 | overlap classification 不同 | 阻断。 |
| R04 | overlap classification 相同 | 仍阻断；每窗口日期恰一 coverage。 |
| R05 | partial 背景字段/缺 close | 前者 ready，后者 metrics fail-closed。 |
| R06 | Phase C enum | 仅两种白名单可过；unknown/null/other 全 false。 |
| R07 | 固定位置损坏孤儿后新 run | 新 completion attempt 成功，旧孤儿 bytes 不变。 |
| R08 | candidate SHA 与 manifest 不符孤儿 | 不占位、不补 index、不 suppress。 |
| R09 | 合法单孤儿 | 全量复验后唯一 index recovery。 |
| R10 | 双合法同 semantic identity 孤儿 | `ambiguous_orphan_completion` fail-closed，绝不任择。 |
| R11 | 合法相同 semantic identity | no-op，index 精确含 six identity fields。 |
| T01 | `+08:00` RFC3339 | 转上海时间并比较 cutoff。 |
| T02 | `Z` RFC3339 | 转上海时间并比较 cutoff。 |
| T03 | naive datetime | `source_time_unverifiable`。 |
| T04 | date-only news | `source_time_unverifiable`。 |
| T05 | daily_bar trade_date | `YYYY-MM-DD` 可作为日线时间证据。 |
| T06 | provenance 晚于 cutoff | 合法且不参加 cutoff。 |
| T07 | 自由文本日期无结构化时间 | `source_time_unverifiable`。 |

每例还断言状态、reason、全 false 或不升级权限、安全路径 token、原子性、无正式 weekly 写入。
