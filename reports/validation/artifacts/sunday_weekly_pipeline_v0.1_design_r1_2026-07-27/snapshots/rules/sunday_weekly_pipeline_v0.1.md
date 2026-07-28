# Sunday Weekly Pipeline v0.1

## 1. 定位、范围与硬边界

Sunday Weekly Pipeline（以下简称 SWP）是在每个周日为一个 `symbol` 生成**待人工审阅的周观察候选**的只读输入验证与候选装配流程。它不生成正式 `weekly/weekly_market_watch_YYYY-MM-DD.md`，不写 facts、Daily Review、current 卡、仓库 index，也不执行 Git 操作。

机器输出的最高状态是 `candidate_ready_for_human_review`。它绝不等于批准、交易建议、趋势确认或可执行的买卖信号；Phase C 的 `weekly=false`、`trading=false` 权限常量不得被改变。

本设计只定义未来实现的运行时产物和候选格式，不授权实施代码或对现有文件的迁移。

## 2. 两层模型

### 2.1 确定性层（机器可写）

输入仅为正式交易日历、该周 canonical official facts、逐日 Daily Review、合法 Phase B/Phase C 现场证据与静态配置。机器必须：

1. `as_of_date` 一律按 `Asia/Shanghai` 的 civil date 解释。默认模式只接受周日；历史模式必须显式提供 `as_of_date`，二者均须映射到唯一、紧邻其前的周一至周五窗口。非法模式、非法日期或默认模式非周日一律为 `blocked_invalid_facts:as_of_date_invalid`。窗口涉及的每个 calendar 年度文件均须存在、通过 schema 校验，并为窗口内每一个自然日提供显式 trading/non-trading 标记；缺任何年度、日期或标记一律为 `blocked_invalid_facts:calendar_window_invalid`。不得假设总是五天。
2. 对每一交易日由 `symbol + trade_date` 推导 canonical facts 路径；安全读取 bytes、计算 SHA-256、校验 JSON 身份并现场运行 `assert_facts_pack_valid`。
3. 精确一对一定位该日 Daily Review；确认其日期、symbol、引用的 facts 日期/SHA。旧格式或缺 facts SHA 一律为 `blocked_identity_conflict:legacy_review_sha_unverifiable`，全权限 false，可重跑；证据必须含 review canonical path、raw SHA、格式指纹、期待 facts identity/SHA 与缺失字段，绝不从正文猜测。
4. `partial` 只允许 `market_indices`、`sector_context`、`disclosure_status`、`news_policy_context` 四项背景字段为 TODO/null，并必须原样进入 `unresolved_fields`。周统计必需的 OHLC、涨跌幅所需字段、成交额、换手率、量比及其数值类型任一缺失、null、bool、NaN、Infinity 或非法时，一律为 `blocked_invalid_facts:metrics_field_missing_or_invalid`；不得跳过该日继续聚合。用 facts 原始结构以 Decimal 或等价精确十进制规则复算，不从 Markdown 抄数。
5. 固定市场事实判断截止为最后一个交易日 `Asia/Shanghai` 收盘。市场事件、公告、新闻、政策及其可验证 source_time 晚于 cutoff 均为 `blocked_future_data:future_input_detected`。采集、生成、hash、runtime 写入等 provenance metadata 不属于市场事实，可晚于 cutoff。任何必须判定为市场事实的 `source_time` 不可验证、缺失、格式/时区不可解析或来源类型无法确认，均为 `blocked_future_data:source_time_unverifiable`（fail-closed）；不得以 `needs_manual_check` 放行。可解析时间统一转换为 Asia/Shanghai 再比较。
6. 原样保留 `missing`、`needs_manual_check`、TODO/null 背景缺口；不补齐、不将缺口解释为利多/利空。
7. 生成 immutable candidate、manifest、summary 和验证证据，全部在仓库外受控 runtime；正式 weekly 必须由人工另行写入。

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
| G1 calendar | 涉及的全部年度 calendar 均存在、schema 合法；窗口每个自然日有显式标记；周区间由合并 calendar 推导；至少一个交易日 | `blocked_invalid_facts`（`calendar_window_invalid` / `as_of_date_invalid`） |
| G2 completeness | 每个 calendar 交易日恰有一份 canonical facts；无额外替代日 | `blocked_missing_facts` |
| G3 facts validity | 安全读取、path/symbol/trade_date 一致、现场 facts Validator PASS；`partial` 仅四项背景白名单，所有 metrics 字段完整且为有限数值 | `blocked_invalid_facts` / `blocked_identity_conflict` |
| G4 integrity | 读取 bytes 后的 SHA 与本次 manifest、Phase B/Phase C 可验证证据一致；最终复读未漂移 | `blocked_invalid_facts` |
| G5 daily review | 每日一份，日期/symbol/facts identity/SHA 一一对应；legacy 无 SHA 格式 fail-closed | `blocked_missing_daily_review` / `blocked_identity_conflict` |
| G6 cutoff | 所有市场事实 source_time 可验证且 `<= last_trade_date close`；provenance metadata 分离；背景缺口保留 | `blocked_future_data` |
| G7 Phase C | 每日 Phase C evidence 合法且 `review_state` 至少为 `needs_manual_review` 或 `ready_for_human_review`；权限仍关闭 | `blocked_identity_conflict` |
| G8 safety | manifest/candidate/runtime 输入路径在 runtime 根内、无 symlink、schema 允许 | `failed` |

`partial` facts 不是自动失败：仅当 facts Validator 通过且未决项原样保留时，才可进入候选。任一门失败写出诊断证据，但**不**写正式 weekly。

## 4. 运行身份、产物与顺序

运行身份固定为 `swp_<symbol>_<week_end>_<input_set_sha16>`，其中 `input_set_sha256` 是所有涉及 calendar 年度（按 year/path 升序）的 raw SHA、按交易日排序的 facts raw SHA、Daily Review raw SHA、Phase C manifest SHA 与候选 schema version 的 canonical JSON 哈希。SWP no-op 只承认自身 `input_set_sha256` 与 deterministic candidate bytes SHA 严格相等；Phase B semantic evidence 仅是 G4/G7 输入证据，绝不外溢为 SWP completion。candidate canonical digest 只含 schema 固定字段、输入身份、确定性 metrics、unresolved fields、固定人工槽位；不得含生成时间、run id、主机、pid、路径、锁等待、诊断或其他易变 runtime metadata。候选 SHA 为该 canonical candidate JSON 的 SHA-256。

运行时目录（必须在仓库外）为：

```text
<runtime>/sunday-weekly/<symbol>/<week_end>/<run_id>/
  candidate.json
  candidate_summary.md
  manifest.json
  validation.json
<runtime>/sunday-weekly/<symbol>/<week_end>/index.jsonl
<runtime>/sunday-weekly/<symbol>/<week_end>/diagnostics.jsonl
<runtime>/locks/sunday_weekly_<sha256(symbol_week_end)>.lock
```

成功写入顺序：锁内输入快照 → 无锁校验/复算/临时目录写入并 fsync → 锁内最终安全复读与 SHA 比较 → 原子 rename `tmp` 为 run 目录 → fsync 父目录 → 追加一行 index（最终 completion 标记）→ fsync index 与父目录。candidate、manifest、summary、validation 缺一不可；index 不得先于完整目录出现。blocked/failed 使用独立诊断临时目录，写入最小 `diagnostic.json` 与 `validation.json` 并 fsync 后原子 rename 到不可作 completion 的 diagnostic run 目录，再 append+fsync 独立 `diagnostics.jsonl`；diagnostics 永不参与 completion/no-op/index_recovered 判定。

## 5. 幂等、恢复与伪造防御

扫描既有完成记录必须复用 `phase_b_completion.validate_completion_manifest` 的 fail-closed 原则：解析、身份、受控路径、schema、现场 SHA、现场 Validator、action/outcome/reason 语义及 committed evidence 必须逐项重验；绝不以文件存在、旧 summary 或 index 单行作为完成。

- 合法相同 `input_set_sha256` 且 candidate SHA 一致、完整目录和 index 一致：在 `validate_completion_manifest` 级别全量现场重验后 `already_completed`，不重写。
- 合法 candidate 孤儿目录而 index 缺失：仅可在最终锁内执行与正常 completion 完全相同的全量现场重验（manifest schema、candidate bytes/SHA、四文件齐备、身份、当前 input SHA、Validator、语义、受控路径和最终复读）后补 index，`already_completed`（`index_recovered`），且不得改动 candidate bytes。任一失败均为无效历史：不得补 index、不得阻止新 run。
- input set 改变：新 run；旧成功记录保留，并在新 manifest 以 `supersedes_run_id` 引用。
- 缺 manifest、损坏、SHA 漂移、schema 非法、伪造完成或证据不一致：诊断为无效历史，绝不 suppress 新 run；使用新唯一 run id，不覆盖旧证据。
- 中途失败的 tmp 目录不是 completion；下次可清理本进程可证明拥有的陈旧 tmp，或保留作诊断后重新运行。
- `failed` 与所有 `blocked_*` 历史均不阻止新运行；只有可现场复证的成功记录才可 no-op。

## 6. 锁与安全读取

锁顺序只能为：

```text
sunday-weekly(symbol, week_end) lock
  → 按 canonical pathname 升序获取每个 official facts lock（快照）
  → 释放 facts locks，做本地验证和临时写入
  → 同一升序重新获取 facts locks（最终复读、提交）
  → 提交 index，释放 facts locks，再释放 weekly lock
```

不得先取 official lock 再取 weekly lock，也不得在不同顺序取得多个 facts lock。使用 `safe_file_read` 的逐级 `O_NOFOLLOW`、目录/文件 `fstat` 和同一 FD 读 bytes 思路；facts lock 使用既有 `official_facts_lock`。manifest、candidate、Daily Review 和 calendar 也须拒绝 symlink/逃逸路径。锁只能协调遵守该合约的 writer；最终复读仍是必须门。

## 7. 状态矩阵

| 状态 | outcome / reason_code | 下游权限 | 可重跑 | 必需证据 |
|---|---|---|---|---|
| `candidate_ready_for_human_review` | `candidate_created` / `all_gates_passed` | human review=true；weekly/current/index/git/trading=false | 是，合法同输入为 no-op | input SHA set、五类校验、candidate/manifest/summary/validation、index |
| `blocked_missing_facts` | `blocked` / `facts_missing:<date>` | 全 false | 是 | calendar dates、canonical paths、缺失清单 |
| `blocked_invalid_facts` | `blocked` / `facts_validator_failed`、`facts_sha_drift`、`calendar_window_invalid`、`as_of_date_invalid` 或 `metrics_field_missing_or_invalid` | 全 false | 是 | raw SHA、validator diagnostic、calendar window 或 metrics-field diagnostic、复读结果 |
| `blocked_missing_daily_review` | `blocked` / `daily_review_missing:<date>` | 全 false | 是 | expected review path/identity 与扫描结果 |
| `blocked_future_data` | `blocked` / `future_input_detected` 或 `source_time_unverifiable` | 全 false | 是 | cutoff、source classification、违规 source/ref/time 或不可验证原因 |
| `blocked_identity_conflict` | `blocked` / `identity_mismatch`、`legacy_review_sha_unverifiable`、`phase_c_permission_invalid` 或 `forbidden_automatic_trading_field` | 全 false | 是 | expected/actual identity、review raw SHA/格式指纹/缺失 SHA、权限或 schema finding |
| `already_completed` | `no_op` / `valid_matching_completion` 或 `index_recovered` | 同原 candidate；交易等仍 false | 是 | 现场重验的完整 prior manifest、current input set SHA、index correlation |
| `failed` | `failed` / `runtime_io_error`、`lock_error`、`unexpected_exception` | 全 false | 是 | 原子 diagnostic directory、脱敏异常、run identity、已提交边界；不得假称完成 |

## 8. 测试矩阵与验收

实现前至少增加测试：正常五日、节假日短周、legacy Review 无 facts SHA、跨年缺 calendar、跨年双 calendar、partial 四背景白名单、partial 缺 close、partial 成交字段非数值、缺 facts、facts SHA 漂移、Daily Review 缺失、Review 引用未来市场事实、provenance 晚于 cutoff、source_time_unverifiable、Asia/Shanghai 周日边界、TODO/null 原样保留、全部数值精确复算、人工字段为空、非法自动交易字段、同输入 bytes 一致重跑、Phase B semantic-pass 但 SWP 输入变化、非法孤儿不补 index、合法孤儿仅补 index、blocked 原子诊断、diagnostics 不压掉新 run、双进程竞争、其他 symbol/业务文件零改动。每项须断言状态、reason、权限、证据目录和无正式 weekly 写入。

## 9. 成本与调度

预期为低成本：每周每 symbol 一次、本地 calendar/JSON/Markdown/哈希与 validator；不调用 LLM、网络或外部行情。先扫描合法 completion 再读取全量输入；命中时只做必要现场复证。失败最多一次有限重试（仅锁竞争/瞬态 I/O），其余失败等待人工修复；不做轮询。完整 facts Validator 是强制成本，不能为节省额度跳过。
