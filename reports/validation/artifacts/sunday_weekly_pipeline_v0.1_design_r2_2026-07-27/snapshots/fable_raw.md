GREEN_LIGHT_DESIGN=YES
P1_COUNT=0
P2_COUNT=4
P3_COUNT=4
DESIGN_FREEZE_READY=NO
SOL_HIGH_IMPLEMENTATION_READY=NO
INPUT_INTEGRITY=PASS

身份核验记录：HEAD=b409f40ab2f4334e2f1205acb56b5a1628d38e9d（匹配）；review_bundle_manifest.json SHA=3434…98a2c（匹配）；file_sha256_manifest.md SHA=fa12…21cbf（匹配）；8 个 payload SHA 与 size_bytes 逐项匹配；canonical package SHA 重建=23eefce6…f03a0（匹配）；35 个输入文件 SHA 全部匹配。

---

## 1. BLOCKING_SUMMARY

无 P1。核心安全不变量（candidate ≠ weekly、交易权限永久 false、fail-closed completion、锁顺序单向、最终 SHA 复读）在设计层闭合且相互加固，未发现可让机器越权写正式 weekly 或产生交易信号的路径。存在 4 个 P2：均为契约闭合缺口（reason_code 未收录、跨年 calendar 未定义、allowed-partial 集合未枚举、index_recovered 重验强度不足），需在设计冻结前修补，但不推翻架构。

## 2. P1

无。

## 3. P2

**P2-1｜`legacy_review_sha_unverifiable` 未纳入状态矩阵闭合**
- 位置：`rules/sunday_weekly_pipeline_v0.1.md` §2.1 第 3 条 vs §7 状态矩阵、`status_matrix.md` G5 行。
- 被破坏不变量：每个 blocked 结果必须映射到状态矩阵中唯一 (状态, reason_code, 权限, 证据) 元组。
- 最小触发：某日 Daily Review 为旧格式、无 facts SHA 字段；§2.1(3) 要求记录 `legacy_review_sha_unverifiable` 并 blocked，但 §7 中 G5 只允许 `daily_review_missing:<date>` / `future_input_detected`，该 code 无归属状态、无证据要求、无 downstream permissions 行。
- 实际影响：实现者被迫自行发明映射；不同实现可能落入 `failed`（丢失可重跑语义清晰度）或错误复用 `daily_review_missing`（诊断失真），测试矩阵也无法断言。
- 最小修正：在 §7 增加一行（建议 `blocked_invalid_facts` 或新增 `blocked_legacy_review`，reason_code=`legacy_review_sha_unverifiable`，全 false，可重跑，证据=review 路径+格式指纹），并同步 `status_matrix.md`。
- 所需测试：legacy 格式 Daily Review → 断言该状态/reason_code/证据/无 candidate/无 index/后续重跑不被 suppress。

**P2-2｜跨年交易周的 calendar 契约缺失**
- 位置：`rules` §2.1 第 1 条、G1；`module_map.md` 仅引用 `config/a_share_trading_calendar_2026.json`。
- 被破坏不变量：G2 completeness 的"每个 calendar 交易日恰有一份 facts"要求 calendar 对整个候选周区间完整可信；周区间跨年（如 2026-12-28—2027-01-01）时单年度文件无法覆盖。
- 最小触发：2027-01-03（周日）运行，上一完整周含 2026 与 2027 日期，2027 calendar 文件不存在或未定义合并规则。
- 实际影响：未定义行为——实现可能把缺失年份日期当"非交易日"静默跳过（漏交易日、G2 失效，产生基于不完整周的 candidate），或崩溃为 `failed`。前者是数据正确性风险。
- 最小修正：在 G1 定义：周区间涉及的每个日历年必须存在通过 schema 校验的 calendar 文件且窗口内每一天有显式交易日/非交易日标记；任一年缺失 → `blocked_invalid_facts:calendar_window_invalid`（fail-closed），并将各 calendar bytes SHA 全部纳入 `input_set_sha256`。
- 所需测试：跨年周 + 次年 calendar 缺失 → blocked；双 calendar 齐备 → 正确合并窗口且两份 calendar SHA 均入 input set。

**P2-3｜"允许的 partial" 集合与复算字段缺失的失败映射未定义**
- 位置：`rules` G3（"`success` 或允许的 `partial`"）、§3 末段、§2.1 第 4 条。
- 被破坏不变量：确定性层的准入判断必须机器可判定；"允许的 partial"未枚举即不可判定。
- 最小触发：facts Validator 返回 `partial`，但未决项恰好包含复算必需的价格/成交字段（而非黄金样本中的四个背景 TODO 字段）；G3 按宽松解释放行，§2.1(4) 复算随即因字段缺失失败，失败落点（`failed`? `blocked_invalid_facts`?）无定义。
- 实际影响：不同实现对同一输入给出不同 outcome；宽松实现可能用 null 参与聚合或跳过该日，产生数值错误的 candidate（人工层依赖这些"机器确定性事实"）。
- 最小修正：G3 显式枚举 partial 白名单（如仅 `market_indices`、`sector_context`、`disclosure_status`、`news_policy_context` 四背景字段可 TODO/null）；复算必需字段任一缺失/非数值 → `blocked_invalid_facts:facts_validator_failed`（或新 code `metrics_field_missing`），禁止跳日聚合。
- 所需测试：partial 含背景 TODO → ready 且 unresolved 原样保留；partial 缺 close 价 → blocked、无 candidate、聚合未执行。

**P2-4｜`index_recovered` 路径的重验强度低于主 no-op 路径**
- 位置：`rules` §5 第二个 bullet vs 第一个 bullet 及 §5 首段。
- 被破坏不变量：§5 首段"绝不以文件存在……作为完成"——一切 no-op 判定须逐项 fail-closed 重验（解析、身份、schema、现场 SHA、Validator、语义）。
- 最小触发：runtime 中出现一个目录结构完整但 manifest 被篡改/candidate SHA 与 manifest 不符的"孤儿" run 目录（无 index 行）；恢复路径仅"复核输入 SHA"即补写 index 并报 `already_completed`。
- 实际影响：一个从未通过完整重验的目录被升格为正式 completion 标记，此后主路径（第一 bullet）依 index+目录一致而持续 no-op——伪造/损坏产物被永久固化，且合法重跑被错误 suppress（正是 prompt 关注的 forged-completion 与 suppress 组合）。
- 最小修正：§5 明确 `index_recovered` 前置条件 = 与第一 bullet 完全相同的 `validate_completion_manifest` 级全量现场重验（manifest schema、candidate SHA、四文件齐备、证据语义）+ 输入 SHA 复核；任何一项不符 → 该目录降级为无效历史，新 run id 重跑。
- 所需测试：孤儿目录 manifest 内 candidate SHA 被改 1 字节 → 不补 index、不 no-op、新 run 正常产出；合法孤儿目录 → 仅补 index，bytes 零改动。

## 4. P3

**P3-1｜SWP 层 "semantic no-op" 借用 Phase B 语义，自身定义未落地**——`test_matrix.md` #12 断言"合法 Phase B semantic evidence 可通过"，但 `rules` §5 对 SWP 自身 no-op 采用严格 byte/SHA 等价（这是好的），二者关系未写明：Phase B semantic evidence 只作为 G4/G7 输入证据，还是可参与 SWP no-op 判定？最小修正：在 §5 加一句"SWP 层 no-op 仅接受 input_set_sha256 + candidate SHA 严格相等；Phase B semantic 判定不外溢到 SWP completion"。测试：Phase B semantic-pass 但 SWP 输入变更 → 必须新 run。

**P3-2｜G6 未来信息扫描的可判定契约缺失**——"扫描日期、时间戳、链接标签"未定义可识别的日期格式集合、时区基准与不可解析引用的处置（fail-open 还是 fail-closed）。最小修正：定义识别格式白名单 + "不可解析日期引用记 `needs_manual_check` 且不阻断，可解析且晚于 cutoff 才 `blocked_future_data`"或更严格策略，二选一并写死。测试：含模糊日期字符串的 review → 行为确定。

**P3-3｜`as_of_date` 时区与"周日"判定未定义**——周日午夜边界或非本地时区运行可能推导出不同的"上一完整周"。最小修正：固定 Asia/Shanghai、`as_of_date` 取运行时刻当地日期，且仅当为周日（或显式传参）才运行。测试：边界时刻推导断言。

**P3-4｜blocked/failed 诊断证据的写入次序未纳入写序图**——`write_lock_sequence.md` 只覆盖成功路径；blocked 证据写在何处、是否也走 tmp+rename、是否写 index 行（§7 暗示 blocked 有证据但 index 语义是"最终提交标记"）未定义。半完成的 blocked 证据虽不 suppress 重跑（§5 已保证），但取证一致性受损。最小修正：blocked/failed 证据同样 tmp→rename，且明确 blocked 记录是否/如何进 index（建议独立 `diagnostics.jsonl`，与 completion index 分离）。测试：#3/#4 追加断言证据目录原子性。

## 5. VERIFIED_INVARIANTS

- 权限隔离：`human_judgment` 六槽位 owner/status/value 契约 + 禁用字段黑名单 + `blocked_identity_conflict` fail-closed，机器无任何路径写非 null 人工值或升级 Phase C 权限（§2.2、G7、状态矩阵全行 trading=false）。
- candidate 永不等于 weekly：runtime 强制仓库外、G8 路径约束、测试 #16 与"每例断言正式 `weekly/` 零写入"三重闭合。
- 锁次序单向（weekly → facts 升序 → 释放 → 同序重取），无锁反转/死锁窗口；释放-重取间的 TOCTOU 由最终 SHA 复读关死（§6 + write_lock_sequence）。
- index 作为最终提交标记严格后置于原子 rename + fsync；双进程由 weekly 锁串行化（测试 #15）。
- blocked/failed 历史不 suppress 重跑（§5、状态矩阵尾注），合法重跑不被失败记录阻断。
- forged completion：主路径复用 `phase_b_completion` fail-closed 原则并要求现场 SHA/Validator 重验（P2-4 修复后该不变量在恢复路径也闭合）。
- 黄金样本交叉核对：07-26 weekly 的 OHLC/涨幅/成交额与 golden_sample_summary 一致；07-20—07-24 五份 facts 与五篇 review 均在 35 文件清单内且 SHA 匹配，样本依据成立。

## 6. CROSS_PHASE_DEPENDENCIES

- G4/G7 依赖 Phase B/Phase C 证据 schema 稳定；Phase C `review_state` 枚举若扩展，G7 的"至少为"偏序需同步（与 P3-1 相关）。
- `input_set_sha256` 含 Phase C manifest SHA：Phase C 重跑会改变 SWP input set，触发合法新 run 并 `supersedes_run_id` 链接——该语义正确但实现需保留旧证据。
- `official_facts_lock`、`safe_file_read`、`validate_review_chain` 被作为契约依赖复用；其接口变更即 SWP 安全前提变更。

## 7. SCOPE_LIMITATIONS

仅审查规格与 8 payload；35 文件仅用于 SHA 核验与有限交叉检查。未审计 5 个 tools/*.py 的实现正确性（如 `official_facts_lock` 的锁语义、`safe_file_read` 的 O_NOFOLLOW 完备性）——设计正确性以其宣称行为为前提。未读取任何历史 reviewer 结论、response JSON 或 debug 产物。未执行任何代码或测试。

## 8. FALSE_NEGATIVE_RISK

- 工具实现层缺陷（锁非排他、symlink 检查遗漏）会在设计正确的前提下击穿 G8/G4，本轮不可见。
- runtime 根目录本身的权限/所有权模型未在规格中定义，恶意本地 writer 不受锁合约约束（规格已承认"锁只协调遵守合约的 writer"，最终 SHA 复读部分缓解，但 index.jsonl 被外部篡改的检测契约较薄）。
- calendar 文件本身被污染（标错交易日）时 G1 schema 校验无法发现，属数据信任根问题。

## 9. FINAL_RATIONALE

架构的两层模型、fail-closed 状态机、锁次序与最终复读设计在安全语义上成立，无越权写 weekly 或交易信号的可达路径，故 GREEN_LIGHT_DESIGN=YES。但 4 个 P2 均是"契约未闭合"型缺口——其中 P2-4（恢复路径重验降级）直接触及 forged-completion/suppress 核心不变量，P2-2/P2-3 会导致确定性层在真实边界输入下行为分歧。这些必须在冻结前以文字修订 + 对应测试补入，故 DESIGN_FREEZE_READY=NO、SOL_HIGH_IMPLEMENTATION_READY=NO。修订量小（均为条款级补丁），不需要架构重做。
