# 测试矩阵 r4

| ID | 情形 | 断言 |
|---|---|---|
| C01 | 跨年双 calendar | 相关年度 coverage 合并成功，全部 raw SHA 入 input_set。 |
| C02 | overlap 同分类 | 仍 `calendar_window_invalid`；每窗口日不得有两份 coverage。 |
| C03 | overlap 不同分类 | `calendar_window_invalid`。 |
| I01 | 非法 as_of_date | safe envelope -> request_key；原值不进路径/日志/诊断正文。 |
| I02 | calendar 缺失 | input_set 前仅凭 request_key 原子诊断。 |
| I03 | facts/Review 缺失 | 各自 input_set 前原子诊断且记录 available/missing inputs。 |
| I04 | lock 获取失败 | input_set 前保存 request-key lock-error evidence。 |
| I05 | 同 request 两次失败 | attempt_id 和物理目录唯一。 |
| I06 | 非法 symbol | safe envelope/request_key/原子诊断；原始值不泄漏。 |
| I07 | 非法 mode | 同 I06。 |
| I08 | 非法 candidate_schema_version | 同 I06。 |
| I09 | 多字段同时非法 | 每字段 envelope 均在 request identity 内，仍可诊断。 |
| K01 | 损坏固定孤儿后新 run | 新 attempt 可成功；旧孤儿 bytes 不变。 |
| K02 | candidate SHA/manifest 不符孤儿 | 不占位、不补 index、不 suppress。 |
| K03 | 合法单孤儿 | full revalidation 后唯一 index recovery。 |
| K04 | 双合法同 semantic identity 孤儿 | `ambiguous_orphan_completion` fail-closed。 |
| K05 | Phase B semantic-pass 但 SWP 输入变 | 新 semantic completion，不 no-op。 |
| L01 | 锁契约静态扫描 | rules、身份图、写锁路径、状态/测试矩阵均仅使用 `sunday_weekly_request_<request_key>.lock`。 |
| M01 | legacy Daily Review 无 facts SHA | `legacy_review_sha_unverifiable`，全 false，无 candidate/index。 |
| M02 | partial 复算字段缺失 | `metrics_field_missing_or_invalid`，不聚合。 |
| P01 | Phase C `needs_manual_review` | G7 成功，所有既有 downstream permissions 仍 false。 |
| P02 | Phase C `ready_for_human_review` | G7 成功，所有既有 downstream permissions 仍 false。 |
| P03 | Phase C unknown/null/empty/other | `phase_c_state_invalid`，全 false。 |
| S01 | 密封完整性 | 每个审查材料（含 identity-free body）都在 manifest.files 与 package input。 |
| S02 | mapping 静态交叉核验 | 无悬空 ID；Fable P2/P3、r2/r3 新 finding 各至少一个真实测试。 |
| T01 | `+08:00` / `Z` RFC3339 | 转 Asia/Shanghai 后比较 cutoff。 |
| T02 | naive datetime/date-only news | `source_time_unverifiable`。 |
| T03 | daily_bar trade_date | 登记 `YYYY-MM-DD` 可用。 |
| T04 | provenance 晚于 cutoff | 合法，不参与 cutoff。 |
| T05 | 07-24 generated_at/fetched_at=07-25 | 归一为 provenance，合法。 |
| T06 | 07-24 source_date/trade_date=07-24 | 归一为 daily_bar。 |
| T07 | 未登记时间字段 | `source_time_unverifiable` fail-closed。 |
| T08 | source_kind 非原 JSON 字面 | 仅凭登记路径完成标准化。 |

每例还断言受控路径 token、状态/reason、权限不升级、原子性和正式 `weekly/` 零写入。
