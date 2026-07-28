# Sunday Weekly Pipeline v0.1

## 1. 定位、范围与硬边界

Sunday Weekly Pipeline（以下简称 SWP）是在每个周日为一个 `symbol` 生成**待人工审阅的周观察候选**的只读输入验证与候选装配流程。它不生成正式 `weekly/weekly_market_watch_YYYY-MM-DD.md`，不写 facts、Daily Review、current 卡、仓库 index，也不执行 Git 操作。

机器输出的最高状态是 `candidate_ready_for_human_review`。它绝不等于批准、交易建议、趋势确认或可执行的买卖信号；Phase C 的 `weekly=false`、`trading=false` 权限常量不得被改变。

本设计只定义未来实现的运行时产物和候选格式，不授权实施代码或对现有文件的迁移。

## 2. 两层模型

### 2.1 确定性层（机器可写）

输入仅为正式交易日历、该周 canonical official facts、逐日 Daily Review、合法 Phase B/Phase C 现场证据与静态配置。机器必须：

1. `as_of_date` 一律按 `Asia/Shanghai` 的 civil date 解释。默认模式只接受周日；历史模式必须显式提供 `as_of_date`，二者均须映射到唯一、紧邻其前的周一至周五窗口。非法模式、非法日期或默认模式非周日一律为 `blocked_invalid_facts:as_of_date_invalid`。窗口涉及的**全部** calendar 年度文件均须存在、通过 schema 校验；不得只按 `as_of_date` 年份加载。真实 calendar schema 仅为 `coverage_start`、`coverage_end`、`trading_days`：每个 coverage 表示闭区间，`trading_days` 中的 date 为 trading，coverage 内但不在 `trading_days` 的 date 为 non-trading；不要求或推断逐日状态行。窗口的每个自然日必须落入恰好一份合法 coverage。缺 coverage、coverage 重叠、同一 date 重复出现、日期非法、`coverage_start > coverage_end`、`trading_days` 不在 coverage 内、或 date/timezone 不符合 `Asia/Shanghai` civil-date 契约，均为 `blocked_invalid_facts:calendar_window_invalid`。任何日期不得因缺 coverage 被静默视作 non-trading。所有参与分类的 calendar raw SHA（按 year/path 升序）必须进入 `input_set_sha256`。不得假设总是五天。
2. 对每一交易日由 `symbol + trade_date` 推导 canonical facts 路径；安全读取 bytes、计算 SHA-256、校验 JSON 身份并现场运行 `assert_facts_pack_valid`。
3. 精确一对一定位该日 Daily Review；确认其日期、symbol、引用的 facts 日期/SHA。旧格式或缺 facts SHA 一律为 `blocked_identity_conflict:legacy_review_sha_unverifiable`，全权限 false，可重跑；证据必须含 review canonical path、raw SHA、格式指纹、期待 facts identity/SHA 与缺失字段，绝不从正文猜测。
4. `partial` 只允许 `market_indices`、`sector_context`、`disclosure_status`、`news_policy_context` 四项背景字段为 TODO/null，并必须原样进入 `unresolved_fields`。周统计必需的 OHLC、涨跌幅所需字段、成交额、换手率、量比及其数值类型任一缺失、null、bool、NaN、Infinity 或非法时，一律为 `blocked_invalid_facts:metrics_field_missing_or_invalid`；不得跳过该日继续聚合。用 facts 原始结构以 Decimal 或等价精确十进制规则复算，不从 Markdown 抄数。
5. 时间证据仅按 `rules/sunday_weekly_pipeline_semantic_config_v0.1.json` 的精确 registry 与 grammar 标准化；不得在本规则另列 `**`、`.*` 或宽松映射。未登记路径、未知 schema、路径冲突、naive/date-only/free-text 仍为 `blocked_future_data:source_time_unverifiable`。cutoff 固定为 `Asia/Shanghai` 最后交易日 `15:00:00`，比较固定为 `source_time <= cutoff`；provenance 不参加 cutoff。
6. 原样保留 `missing`、`needs_manual_check`、TODO/null 背景缺口；不补齐、不将缺口解释为利多/利空。
7. Phase C authority 只能由 `<runtime>/reviews/<trade_date>/review_index.jsonl` 解析，不得根据 symbol hash 猜 manifest 路径。index 与每份 manifest 都必须通过 `safe_file_read` 读取；每份文件的 bytes、SHA-256、JSON 解析均来自同一 FD 读取结果。禁止调用 `inspect_index_entry` 当前自带的磁盘读取路径；未来实现只能复用其纯校验规则，或先抽出接受 `{bytes, sha, parsed_json}` 的 bytes-based validator。仅保留 review_id、canonical manifest path/SHA、symbol、trade_date、current official SHA 一致的 entry，且候选必须为 `artifact_type=facts_review`、`incident_reason_code=null`、accepted review_state、所有 downstream permissions false；`incident_review` 或任一不符为 `blocked_identity_conflict:phase_c_evidence_invalid`。恰好一项 authoritative valid entry 才可继续；零项合法 entry 为 `phase_c_evidence_missing`，存在非法候选但无合法 entry 为 `phase_c_evidence_invalid`，两个或更多相互冲突合法 authority 为 `ambiguous_phase_c_authority`。Phase C raw SHA 是该唯一 manifest 的同 FD bytes SHA。
8. Phase B authority 只能从已验证的 Phase C manifest 读取 `runner_manifest_path` 与 `runner_manifest_sha256`；安全读取该 path、核对 raw SHA 后，以 `phase_b_completion.validate_completion_manifest` 对 current symbol、trade_date、canonical official path、official bytes、official SHA 与 runner mode 做全量现场复证。Phase B manifest schema 必须为 `runner_manifest_v0.2_phase_b`，其物理 path 必须满足现行 validator 的真实 `<runtime>/runs/<trade_date>/<run_id>/manifest.json` 约束；禁止自行扫描并任意选择某个 Phase B run。Phase B raw SHA 是该 runner manifest 的安全读取 bytes SHA。若已验证 Phase C manifest 的 `provenance.rebuilt_from_official=true` 且 runner path 或 SHA 为空，必须为 `blocked_identity_conflict:phase_b_evidence_missing`，全权限 false、可重跑；SWP v0.1 不接受缺少 Phase B runner 的 rebuilt Phase C。
9. 生成 immutable candidate、manifest、summary 和验证证据，全部在仓库外受控 runtime；正式 weekly 必须由人工另行写入。
10. candidate schema canonical path 为 `rules/sunday_weekly_candidate_v0.1.schema.json`，candidate semantics canonical path 为 `rules/sunday_weekly_candidate_semantics_v0.1.md`，input-set schema canonical path 为 `rules/sunday_weekly_input_set_v0.1.schema.json`。初始快照和最终提交均须安全同 FD 读取三者，并从各自同一 bytes 取得 SHA/JSON 或 contract parse；分别与 semantic config 的 `candidate_schema_raw_sha256`、`candidate_semantics_raw_sha256`、`input_set_schema_raw_sha256` 比较。schema 漂移为 `blocked_identity_conflict:candidate_schema_identity_invalid`，semantics 漂移为 `blocked_identity_conflict:candidate_semantics_identity_invalid`，input-set schema 漂移为 `blocked_identity_conflict:input_set_schema_identity_invalid`；均全 false、可重跑。completion/no-op/index recovery 必须从当前现场输入按 candidate semantics 重新生成 canonical candidate UTF-8 bytes（`sort_keys=true`、`separators=(',', ':')`）并与原 bytes 严格相等。review locks 只能由 `review_manifest.review_lock_path(runtime_dir, symbol, trade_date)` 取得，禁止复制 hash 算法；所有返回路径排序后统一获取。SWP-owned runtime dynamic tokens 仅可使用固定字面量和 `[0-9a-f]` SHA/attempt token；外部 Phase B/C 路径仍按各自 canonical contract 校验。

### 2.2 人工判断层（机器只建槽位）

candidate 必须带 `human_judgment`，其每个字段均为 `{ "owner": "Lucien_or_user", "status": "unfilled", "value": null }`：

- `risk_level`
- `position_and_cost`
- `add_position_discipline`
- `observation_price_levels`
- `volume_price_structure_description`
- `next_week_observation_framework`

machine schema 禁止 `buy`、`sell`、`trade_instruction`、`action_signal`、`stop_loss`、`take_profit`、`auto_execute`、`approved`、`rejected`。任何这些字段、非 null 的机器填充人工槽位，或将 Phase C downstream permission 改为 true，均为 `blocked_identity_conflict` / `forbidden_automatic_trading_field`，不得产出 candidate。

## 3. 准入门（全部必过）

| 门 | 现场验证 | 失败状态 |
|---|---|---|
| G1 calendar | 涉及的全部年度 calendar 均存在、真实 schema 合法；窗口每个自然日落入恰好一份 coverage，并仅由 coverage + `trading_days` 分类；周区间由合并 calendar 推导；至少一个交易日；所有参与 raw SHA 入 input set | `blocked_invalid_facts`（`calendar_window_invalid` / `as_of_date_invalid`） |
| G2 completeness | 每个 calendar 交易日恰有一份 canonical facts；无额外替代日 | `blocked_missing_facts` |
| G3 facts validity | 安全读取、path/symbol/trade_date 一致、现场 facts Validator PASS；`partial` 仅四项背景白名单，所有 metrics 字段完整且为有限数值 | `blocked_invalid_facts` / `blocked_identity_conflict` |
| G4 integrity | Phase C index 唯一 resolver 与 Phase C→Phase B authority chain 合法；两阶段 raw SHA、semantic config raw SHA 与本次 manifest/input set 一致；最终复读未漂移 | `blocked_identity_conflict` |
| G5 daily review | 每日一份，日期/symbol/facts identity/SHA 一一对应；legacy 无 SHA 格式 fail-closed | `blocked_missing_daily_review` / `blocked_identity_conflict` |
| G6 cutoff | source_kind 由已登记字段路径内部标准化；未知 schema/未登记字段/路径冲突 fail-closed；daily_bar 仅登记 `YYYY-MM-DD`，外部市场事实仅显式映射的 offset/Z RFC3339；自由文本非证据；provenance 分离 | `blocked_future_data` |
| G7 Phase C | 每日 Phase C evidence 合法且 `review_state` **精确属于** `needs_manual_review`、`ready_for_human_review`；未知、空值和其他值一律拒绝；所有既有 downstream permissions 仍关闭 | `blocked_identity_conflict:phase_c_state_invalid` / `blocked_identity_conflict:phase_c_permission_invalid` |
| G8 safety | manifest/candidate/runtime 输入路径在 runtime 根内、无 symlink、schema 允许 | `failed` |

`partial` facts 不是自动失败：仅当 facts Validator 通过且未决项原样保留时，才可进入候选。任一门失败写出诊断证据，但**不**写正式 weekly。

## 4. 运行身份、产物与顺序

始终先构造 request identity：`{symbol, canonical_as_of_date, mode, candidate_schema_version}` 的 UTF-8 canonical JSON（`sort_keys=true`、`separators=(',', ':')`）SHA-256 为 `request_key`。四个字段统一使用安全 envelope：有效值为 `{status:"valid",value:<normalized value>}`；无效值为 `{status:"invalid",field:<field name>,raw_type:<JSON type>,raw_length:<UTF-8 canonical raw byte length>,raw_sha256:<SHA-256>}`。`canonical_as_of_date` 的有效 normalized value 是 `Asia/Shanghai` `YYYY-MM-DD` civil date；其余有效值必须各自通过 schema normalization。任何原始 field value 都不得进入路径、日志或 diagnostic 正文；diagnostic 只可写 envelope、request_key 与受控状态码。calendar/facts/review/Phase C 缺失等 input-set 前失败仅依赖 `request_key`。每份 diagnostic evidence 必须列出 `available_inputs`、`missing_inputs`、已取得 raw SHA 与可选 `observed_input_digest`；后者只对已观测输入 canonical 化，绝不伪称完整 input set。

`swp_semantic_config_sha256` 是唯一权威文件 `rules/sunday_weekly_pipeline_semantic_config_v0.1.json` 的 raw canonical bytes SHA-256；不得从规则文字或运行参数重新拼装。该文件必须完整覆盖 schema_version、candidate schema version、顺序固定的 partial whitelist、顺序固定的 accepted Phase C state whitelist、time evidence path registry、JSON path/wildcard matcher syntax、timezone、market cutoff、provenance policy、rebuild_from_official policy。仅在全部 input 完整后生成 `input_set_sha256`：它是所有参与分类 calendar（按 year/path 升序）的 raw SHA、按交易日排序的 facts raw SHA、Daily Review raw SHA、每日由 authority resolver 得到的 Phase B raw SHA、每日 authoritative Phase C raw SHA、`swp_semantic_config_sha256` 的 canonical JSON 哈希。`logical_run_key=sha256(canonical JSON {request_key,input_set_sha256})`；候选生成后 `semantic_completion_key=sha256(canonical JSON {logical_run_key,input_set_sha256,candidate_sha256})`。manifest 必须写入 semantic config path/raw SHA 及逐日 Phase C index path/entry、Phase C manifest path/schema/raw SHA、Phase B manifest path/schema/raw SHA；completion 现场复验必须安全重读、重新 resolve 并比较它们。任何 Phase B evidence 或 semantic config raw bytes 变化都必须产生新的 input set。每次 completion 分配随机 128-bit 或等价不可预测、非输入导出的 `completion_attempt_id`；每次 blocked/failed 分配同性质且独立的 `diagnostic_attempt_id`。物理 completion identity 为 `{semantic_completion_key, completion_attempt_id}`，而不是固定目录名。SWP no-op 只承认有 index 精确关联且全量现场复验通过的相同 `semantic_completion_key`。candidate canonical digest 只含 schema 固定字段、输入身份、确定性 metrics、unresolved fields、固定人工槽位；不得含生成时间、run/attempt id、主机、pid、路径、锁等待或 diagnostics 等易变 metadata。候选 SHA 为该 canonical candidate JSON 的 SHA-256。所有 runtime 路径 token 只能使用固定字面量和 `[0-9a-f]` SHA/attempt token；解析出的 symbol、日期或原始参数不得写入路径。

R12 input-set 修订（取代上段对 input-set 成员的概括）：semantic config 必须覆盖 input_set_schema_raw_sha256。input set 只按 rules/sunday_weekly_input_set_v0.1.schema.json 的 canonical UTF-8 JSON 构造：calendar identity、semantic config SHA，以及按 trade_date 升序的 facts SHA、真正 sungrow/reviews/sungrow_review_YYYY-MM-DD.md SHA、Phase B manifest SHA、authoritative Phase C manifest SHA。bundle-relative evidence/snapshot path、Phase C index bytes、diagnostics、candidate bytes、validator output 一律禁止进入；Phase C index path/entry 仅写运行 manifest 并在最终锁内重解。schema 初始/最终均 same-FD 检查；漂移为 blocked_identity_conflict:input_set_schema_identity_invalid。Phase B semantic_noop 只可作为其 manifest 的输入证据，绝不是 SWP completion reason；SWP no-op 唯一 reason 是 valid_matching_completion。本节所有路径 token 表述均为 SWP-owned runtime dynamic tokens。

运行时目录（必须在仓库外）为：

```text
<runtime>/sunday-weekly/requests/<request_key>/diagnostics/diagnostic_<diagnostic_attempt_id>/
<runtime>/sunday-weekly/requests/<request_key>/lock-errors/diagnostic_<diagnostic_attempt_id>/
<runtime>/sunday-weekly/runs/<logical_run_key>/completions/completion_<semantic_completion_key>_<completion_attempt_id>/
  candidate.json
  candidate_summary.md
  manifest.json
  validation.json
<runtime>/sunday-weekly/runs/<logical_run_key>/index.jsonl
<runtime>/sunday-weekly/requests/<request_key>/diagnostics.jsonl
<runtime>/locks/sunday_weekly_request_<request_key>.lock
```

成功写入顺序：request lock 内输入快照 → 无锁校验/复算/临时目录写入并 fsync → request lock 内最终安全复读与 SHA 比较 → 原子 rename `tmp` 为带 unique completion attempt suffix 的 completion 目录 → fsync 父目录 → 追加一行 index（最终 completion 标记）→ fsync index 与父目录。candidate、manifest、summary、validation 缺一不可；index 不得先于完整目录出现。每行 index 必须精确记录 `semantic_completion_key`、`input_set_sha256`、`candidate_sha256`、`completion_attempt_id`、相对 completion directory 与 manifest SHA-256。blocked/failed 使用仅含 `request_key` + `diagnostic_attempt_id` 的独立诊断临时目录，写入最小 `diagnostic.json` 与 `validation.json` 并 fsync 后原子 rename 到准确 diagnostic 路径，再 append+fsync 独立 `diagnostics.jsonl`；同一 request 的连续失败也绝不覆盖或目录冲突。`diagnostics.jsonl` 的 append 必须在同一 request lock 内执行，采用单次 `O_APPEND` 记录写入、fsync 文件和父目录。若锁尚未取得，或诊断 append/fsync 失败，结果为 `failed:lock_error`；以 request_key 分配的 lock-error evidence 同样 tmp→rename+fsync，且不得写 completion index。diagnostics、lock-error evidence 永不参与 completion/no-op/index_recovered 判定。

## 5. 幂等、恢复与伪造防御

扫描既有完成记录必须复用 `phase_b_completion.validate_completion_manifest` 的 fail-closed 原则：解析、身份、受控路径、schema、现场 SHA、现场 Validator、action/outcome/reason 语义及 committed evidence 必须逐项重验；绝不以文件存在、旧 summary 或 index 单行作为完成。

- 合法相同 `semantic_completion_key` 的 index 记录与物理目录：在 `validate_completion_manifest` 级别全量现场重验后 `already_completed`，不重写。
- 合法 candidate 孤儿目录而 index 缺失：仅可在最终锁内执行与正常 completion 完全相同的全量现场重验（manifest schema、candidate bytes/SHA、四文件齐备、semantic key、attempt identity、当前 input SHA、Validator、语义、受控路径和最终复读）后补 index，`already_completed`（`index_recovered`），且不得改动 candidate bytes。恰有一个合法同 semantic key 孤儿才可恢复；两个或更多合法同 semantic key 孤儿为 `blocked_identity_conflict:ambiguous_orphan_completion`，全 false、不得任意选择。任一失败均为无效历史：不得补 index、不得阻止新 run。
- input set 改变：新 logical/semantic identity；旧成功记录保留，并在新 manifest 以 `supersedes_semantic_completion_key` 引用。
- 缺 manifest、损坏、SHA 漂移、schema 非法、伪造完成或证据不一致：诊断为无效历史，绝不 suppress 新 run；不得删除、覆盖或复用旧孤儿路径，新 run 必须分配新的 physical completion attempt directory。
- 中途失败的 tmp 目录不是 completion；下次可清理本进程可证明拥有的陈旧 tmp，或保留作诊断后重新运行。
- `failed` 与所有 `blocked_*` 历史均不阻止新运行；只有可现场复证的成功记录才可 no-op。

## 6. 锁与安全读取

锁顺序只能为：

```text
sunday_weekly_request_<request_key>.lock
  → 按 canonical pathname 升序获取 Phase C review locks（初始 authority 快照）
  → 按 canonical pathname 升序获取 official facts locks（初始快照）
  → 释放外部 locks，做本地验证和临时写入
  → 同一顺序重新获取 Phase C review locks，再获取 official facts locks（最终复读）
  → 最终锁内重新解析 Phase C authority，恰好一项才提交 index
  → 释放 facts locks、review locks，再释放 request-key orchestration lock
```

唯一 SWP orchestration lock 是 `<runtime>/locks/sunday_weekly_request_<request_key>.lock`；不得存在第二种 SWP orchestration lock。不得先取 official facts lock 再取 request-key orchestration lock，也不得在不同顺序取得多个 facts lock。official facts locks 保留且必须按 canonical pathname 升序。使用 `safe_file_read` 的逐级 `O_NOFOLLOW`、目录/文件 `fstat` 和同一 FD 读 bytes 思路；facts lock 使用既有 `official_facts_lock`。manifest、candidate、Daily Review 和 calendar 也须拒绝 symlink/逃逸路径。锁只能协调遵守该合约的 writer；最终复读仍是必须门。

## 7. 状态矩阵

| 状态 | outcome / reason_code | 下游权限 | 可重跑 | 必需证据 |
|---|---|---|---|---|
| `candidate_ready_for_human_review` | `candidate_created` / `all_gates_passed` | human review=true；weekly/current/index/git/trading=false | 是，合法同输入为 no-op | input SHA set、五类校验、candidate/manifest/summary/validation、index |
| `blocked_missing_facts` | `blocked` / `facts_missing:<date>` | 全 false | 是 | calendar dates、canonical paths、缺失清单 |
| `blocked_invalid_facts` | `blocked` / `facts_validator_failed`、`facts_sha_drift`、`calendar_window_invalid`、`as_of_date_invalid` 或 `metrics_field_missing_or_invalid` | 全 false | 是 | raw SHA、validator diagnostic、calendar window 或 metrics-field diagnostic、复读结果 |
| `blocked_missing_daily_review` | `blocked` / `daily_review_missing:<date>` | 全 false | 是 | expected review path/identity 与扫描结果 |
| `blocked_future_data` | `blocked` / `future_input_detected` 或 `source_time_unverifiable` | 全 false | 是 | cutoff、source classification、违规 source/ref/time 或不可验证原因 |
| `blocked_identity_conflict` | `blocked` / `identity_mismatch`、`legacy_review_sha_unverifiable`、`phase_b_evidence_missing`、`phase_b_evidence_invalid`、`phase_c_evidence_missing`、`phase_c_evidence_invalid`、`ambiguous_phase_c_authority`、`phase_c_state_invalid`、`phase_c_permission_invalid`、`ambiguous_orphan_completion` 或 `forbidden_automatic_trading_field` | 全 false | 是 | Phase C index path/entry inspection、expected/actual manifest path、raw SHA、schema/identity finding、available_inputs/missing_inputs、request key、Phase B/Phase C resolver evidence 或 orphan inventory |
| `already_completed` | `no_op` / `valid_matching_completion` 或 `index_recovered` | 同原 candidate；交易等仍 false | 是 | 现场重验的完整 prior manifest、current input set SHA、index correlation |
| `failed` | `failed` / `runtime_io_error`、`lock_error`、`unexpected_exception` | 全 false | 是 | 原子 diagnostic 或 lock-errors directory、request_key、available/missing inputs、raw SHA、optional observed input digest、脱敏异常、unique diagnostic_attempt_id、已提交边界；不得假称完成 |

## 8. 测试矩阵与验收

实现前至少增加测试：2026 `trading_days` 正常周、coverage 内周末推导 non-trading、coverage 外日期阻断、跨年缺任一 coverage、跨年双 calendar、overlap classification 不同阻断、overlap classification 相同仍阻断、每窗口日期恰一 coverage、calendar/facts/Review 缺失均可仅凭 request_key 原子诊断、无需 input set 的 lock-error evidence、同一 request 双失败 attempt 唯一、非法 symbol/mode/candidate_schema_version/多字段非法仍在 input set 前诊断且原始值不泄漏、legacy Review 无 facts SHA、Phase B evidence missing/invalid、Phase C evidence missing/invalid、Phase B evidence SHA 变化新 input set、semantic config 变化新 input set 并在 manifest/revalidation 比较、Phase C `needs_manual_review` 成功、Phase C `ready_for_human_review` 成功、Phase C unknown/null/empty/other 阻断、partial 四背景白名单、partial 缺 close、partial 成交字段非数值、缺 facts、facts SHA 漂移、Daily Review 缺失、`+08:00` RFC3339、`Z` 转上海时间、naive datetime 拒绝、date-only news 拒绝、daily_bar trade_date、07-24 generated_at/fetched_at=07-25 provenance 合法、07-24 source_date/trade_date daily_bar、未登记时间字段 fail-closed、source_kind 不要求 JSON 字面存在、provenance 晚于 cutoff、自由文本日期无结构化证据、Asia/Shanghai 周日边界、TODO/null 原样保留、全部数值精确复算、人工字段为空、非法自动交易字段、同输入 bytes 一致重跑、Phase B semantic-pass 但 SWP 输入变化、固定位置损坏孤儿后新 attempt 成功、candidate SHA/manifest 不符孤儿不占位、合法孤儿补 index、双合法同 semantic identity 孤儿确定 fail-closed、新 run 不改旧孤儿 bytes、L01 单一 request lock+official facts lock 升序且不可反转、并发 diagnostic 的 JSONL 锁语义、diagnostics 不压掉新 run、双进程竞争、其他 symbol/业务文件零改动。每项须断言状态、reason、权限、证据目录和无正式 weekly 写入。

## 9. 成本与调度

预期为低成本：每周每 symbol 一次、本地 calendar/JSON/Markdown/哈希与 validator；不调用 LLM、网络或外部行情。先扫描合法 completion 再读取全量输入；命中时只做必要现场复证。失败最多一次有限重试（仅锁竞争/瞬态 I/O），其余失败等待人工修复；不做轮询。完整 facts Validator 是强制成本，不能为节省额度跳过。
