# 股票小工坊 v0.2 Phase C：确定性 Review Manifest

## 1. 定位与边界

Phase C 是 official facts 的确定性只读审查层，不是事实链的新事实来源，也不是人工批准层。正式链路固定为：

```text
official facts / Phase B runner manifest
→ official bytes、runner manifest、现场 Validator 三方核验
→ deterministic review_manifest.json
→ deterministic review_summary.md
→ review_index.jsonl 最终提交标记
```

Phase C 不调用 LLM，不创建 `decisions.jsonl`，不安装或创建 launchd，不发送通知，不修改正式 review、current 卡、仓库 index、weekly、official facts 或 Git，也不生成交易判断。

Phase C 只处理经明确授权的目标交易日，且目标日期必须存在于正式交易日历。每次生成还必须同时满足以下输入门：

1. canonical official facts 已存在；
2. 对该 canonical official facts 的现场 facts Validator 通过；
3. 存在与当前 official SHA 匹配、合法的 Phase B runner manifest；
4. runner manifest 的 `write_action`、`outcome` 与 `reason_code` 通过 Phase B 语义矩阵；
5. official SHA 在最终提交的锁内复核仍一致。

Phase C 接受的 semantic no-op 组合仅为：

```text
write_action=semantic_noop
outcome=official_unchanged
reason_code=official_semantically_identical
official_changed=false
```

处理该组合时，Phase C 必须从 runner manifest 同目录读取 committed `candidate.json`，核验 candidate raw SHA 与当前 official raw SHA，现场对双方运行 facts Validator，并使用 Phase B 同一精确白名单与确定性序列化重新计算完整 comparison。candidate 缺失、symlink、SHA 不符、comparison 被篡改、白名单不一致、semantic SHA 不同或出现额外业务差异时，一律按非法 runner evidence fail-closed，不得生成正常 `facts_review`。

不得凭任意日期、旧 runner manifest 或归档报告生成 review。`2026-07-15` 在交易日历修复后，如同样满足上述授权与全部输入门，即为合法输入。

人工决定留给 Phase D。Phase C 的代码和 schema 均不存在 `human_decision`、`human_notes`、`approved` 或 `rejected` 写入入口。

## 2. 仓库外 runtime 硬门

所有运行产物只允许位于仓库外：

```text
<runtime>/reviews/<trade_date>/<review_id>/
  review_manifest.json
  review_summary.md

<runtime>/reviews/<trade_date>/review_index.jsonl
<runtime>/locks/review_<sha256(symbol_trade_date)>.lock
```

runtime 在创建前后均执行 `expanduser + resolve`，拒绝仓库本身或仓库内路径；任何既有 symlink 解析回仓库时拒绝。失败时不得回落到仓库内写入。official 路径只可由 `symbol + trade_date` 推导为：

```text
data/daily/<symbol>_<trade_date>_facts.json
```

official 文件或其规范父目录为 symlink 时失败关闭。

Phase B runner manifest 必须位于同一受控 runtime 根内；manifest 本身、从 runtime 根到 manifest 的任一父目录及其同目录 committed `candidate.json` 均不得为 symlink，也不得解析越出 runtime 根。Phase C 对 runner manifest、candidate 与锁内 official 的读取必须逐级使用 `O_NOFOLLOW` 打开目录/文件、以 `fstat` 确认为常规文件，并只从同一文件描述符读取字节；不得以 `is_symlink → resolve → read_bytes` 的路径级检查代替对象身份保护。

## 3. 权威输入与禁止来源

只认以下三类输入：

1. 在 Phase B 共享 official lock 内读取的原始 official bytes 与现场自算 SHA-256；
2. schema、身份、模式、official 路径与 SHA 字段校验通过的 `runner_manifest_v0.2_phase_b`；`semantic_noop` 还必须带可现场复算的 committed candidate 与 comparison；
3. 对当前 official bytes 现场调用 `validate_review_chain.assert_facts_pack_valid` 的结果。

禁止从 stdout、stderr、summary、alert、LLM 文本、环境变量、命令行事实参数或与当前 official SHA 不一致的 runner manifest 提取事实。命令行只提供 `symbol`、`trade_date`、runtime 和输入文件位置，不提供 quote、missing 或 confirmed 字段。

runner manifest 的 bytes 另算 `runner_manifest_sha256`。当前 official 自算 SHA 必须与 runner 的 `official_sha256_after` 三方交叉核验；不一致时生成 `incident_review`，不得提升状态。

## 4. Review 类型

### 4.1 `facts_review`

仅用于 official JSON 可解析、`symbol/trade_date` 与 canonical 路径身份一致、现场 Validator 已执行且不存在事故条件的记录。`missing` 与 `needs_manual_check` 直接复制 official 对应 JSON 值；`confirmed_fields` 仅从已验证 official facts 的结构化字段确定性派生。

### 4.2 `incident_review`

以下任一条件生成事故记录：

- official JSON 损坏、截断或身份不一致；
- 现场 Validator 失败；
- runner SHA 与当前 official SHA 不一致；
- Phase B 记录 official conflict、post-write failure 或 bytes mismatch；
- 事务证据表明写后 Validator/读取失败。

事故记录保留当前原始 SHA、runner SHA、candidate SHA、before/after SHA、write action/reason、写后错误与 Validator 诊断。它不得猜测 `missing`、quote 或 `confirmed_fields`；这些字段为空，`review_state` 固定为 `needs_manual_review`。

## 5. Review Manifest Schema

schema 为 `review_manifest_v0.2_phase_c`，最小字段如下：

- `schema_version`
- `artifact_type`
- `review_id`
- `run_id`
- `symbol`
- `trade_date`
- `mode`
- `official_path`
- `official_sha256`
- `candidate_sha256`
- `runner_manifest_path`
- `runner_manifest_sha256`
- `official_sha256_before`
- `official_changed`
- `official_sha_match`
- `write_action`
- `write_reason_code`
- `postcheck_status`
- `incident_reason_code`
- `facts_status`
- `validator_result`
- `missing`
- `needs_manual_check`
- `confirmed_fields`
- `unresolved_fields`
- `partial_write_policy`
- `evidence_summary`
- `source_refs`
- `generated_at`
- `generator_version`
- `review_state`
- `downstream_permissions`
- `provenance`

`downstream_permissions` 是代码常量，永久为：

```json
{
  "review": false,
  "current_cards": false,
  "index": false,
  "weekly": false,
  "git": false,
  "trading": false
}
```

schema validator 递归拒绝 `human_decision`、`human_notes`、`approved`、`rejected` 字段，并拒绝值为 `approved` 或 `rejected` 的机器状态。错误和来源引用输出前执行敏感信息过滤。

## 6. 状态与人工边界

状态派生固定为：

- `facts_status=success`、现场 Validator PASS、runner SHA 与 official SHA 一致、无未决项、无事务事故：`ready_for_human_review`；
- `partial` 或存在有效 `missing/needs_manual_check`：`needs_manual_review`；
- `--rebuild-from-official`：`needs_manual_review`；
- official conflict、postcheck failure、bytes mismatch、Validator failure 或任何 incident：`needs_manual_review`。

机器最高只能到 `ready_for_human_review`，不能生成批准或拒绝。`missing` 与 `needs_manual_check` 原样保存在各自字段；其中有效未决项按原值组成结构化 `unresolved_fields`，不转写成弱化散文。

## 7. Summary 固定模板

`review_summary.md` 只展示：artifact type、review state、official SHA、runner SHA 核验、Validator 结果、`missing`、`needs_manual_check`、`unresolved_fields`、write action/reason、人工待核清单和下游权限全关闭声明。

顶部固定警示只能二选一：

```text
⚠️ 固定警示：本记录存在未决事项或事务异常，必须人工逐项核验；禁止弱化、推断或启用任何下游权限。
```

```text
⚠️ 固定警示：本记录仅已具备人工审查条件，尚未批准；全部下游权限保持关闭。
```

summary 不得生成交易判断、趋势观点或可直接写入正式复盘的自由结论。

## 8. Review ID、幂等与取代

基础 ID 固定为：

```text
rev_<symbol>_<trade_date>_<official_sha256 前 16 位>
```

完整 SHA 保存在 manifest 与 index。`today_after_close` 与 `historical_backfill` 不参与 ID，因此同一 symbol、trade_date 与 SHA 不会产生两份活动记录。

- 合法 manifest + 合法匹配 index：返回 `review_already_exists`，不改目录和 index；
- 合法 manifest、index 缺失：在锁内复核 SHA 后补写 index，返回 `review_index_recovered`；
- 只有 summary 的孤儿目录：允许用固定模板原子覆盖 summary，并写入 manifest 与 index；
- manifest 损坏：旧文件不修改，生成 `_invalid_<unique>` 后缀的新记录，`provenance.invalid_prior_manifest` 保存脱敏诊断；
- index 指向缺失或损坏 manifest：保留旧行，生成带唯一后缀的新记录和 invalid 诊断；
- official SHA 变化：产生新的基础 review ID，旧目录永不改写，新的 index 行通过 `supersedes_review_id` 指向最近的合法旧 SHA 记录；`superseded` 只由 index 派生，不写回旧 manifest。

## 9. 并发、锁顺序与最终一致性

统一锁顺序不可反转：

```text
review(symbol, trade_date) lock
  → official facts lock（第一次短快照）
  → 无 official lock 的 schema/Validator/临时产物阶段
  → official facts lock（最终复核、目录提交、index 追加）
```

任何路径均不得在持有 official lock 时再申请 review lock。按 symbol + trade_date 的 review flock 使用非阻塞排他锁；并发进程只有持锁者可以提交。

提交顺序固定为：

1. 获取 review lock；
2. 在 official lock 内读取 bytes 与 SHA；
3. 校验 runner manifest；
4. 对当前 official bytes 现场运行 Validator；
5. 在同一 trade-date 父目录的临时目录生成 summary 与 manifest，并 `fsync`；
6. 再次获取 official lock；
7. 重读 SHA；变化则删除本次临时产物并取消提交；
8. 保持 official lock，原子 rename 临时目录为最终 review 目录；
9. 在 review lock 内向 index 追加完整单行；
10. `fsync` index 与父目录；
11. 释放 official lock，再释放 review lock。

共享锁只能约束遵守 Phase B lock contract 的 official writer；绕过共享锁的外部写入不在保证范围内。

## 10. Index 最终提交语义

`review_index.jsonl` 是唯一最终提交标记。每行 schema 为 `review_index_v0.2_phase_c`，至少包含：

- `review_id`
- `symbol`
- `trade_date`
- `official_sha256`
- `manifest_path`
- `manifest_sha256`
- `review_state`
- `created_at`
- `supersedes_review_id`

追加必须在 review lock 内，以 `O_APPEND` 打开，循环直到完整单行写完，然后 `fsync` 文件与父目录。读取时：尾部没有换行视为半行并 fail-closed；任意中间空行、非法 JSON、未知 schema 或字段错误均 fail-closed。合法 index 行与 manifest 的路径、bytes SHA、review ID、身份、official SHA 与状态必须互相核验。

目录完整但 index 追加失败时，该目录是未提交孤儿。重跑验证 manifest、当前 official SHA 与 index 后，只补写 index，不重写 manifest。index 已有但 manifest 缺失或损坏时，旧行不删除，重跑创建带唯一后缀和 invalid 诊断的新记录。

## 11. Rebuild 模式

```bash
python3 tools/generate_review_manifest.py \
  --symbol 300274 \
  --date YYYY-MM-DD \
  --runtime-dir '<runtime>' \
  --rebuild-from-official
```

重建模式固定：

- `run_id=null`；
- `mode=rebuild_from_official`；
- `provenance.rebuilt_from_official=true`；
- `review_state=needs_manual_review`；
- 没有可核验 runner manifest 时 `write_action`、reason 与事务 SHA 均为 `null`，不得伪造；
- 显式提供且可核验的 runner manifest 只作为辅助事务证据；
- official 无法解析时生成 `incident_review`，只保留原始 SHA 与错误。

## 12. 故障处理

- official 在生成期间变化：取消本次提交，不写最终目录或 index；
- index 半行或中间损坏：fail-closed，不追加；
- index write/fsync 失败：保留未提交目录，由重跑补 index；
- 原子目录提交失败：无 index，临时目录清理；
- review manifest 损坏：不覆盖旧文件，生成唯一后缀记录；
- runtime 不可写或解析回仓库：非零退出，禁止回落；
- 任何诊断均脱敏，不从错误自由文本提取事实。

Phase C 不回滚、不修改 Phase B official facts。

## 13. 验证与封箱门

Phase C 终审至少运行：

- 新增 Python 文件 `py_compile`；
- Phase C 定向测试与并发、故障注入测试；
- Phase A/B runner、official transaction、Generator + Validator 回归；
- 全量 pytest；
- `2026-07-13`、`2026-07-14` facts/review Validator；
- 两篇 review + 五张 current 卡 Validator；
- 正式 review、五张 current 卡、仓库 index 与 weekly 的运行前后 SHA-256；
- `git diff --check`、新增未跟踪文件 whitespace check 与 `git status --short`。

任一 P1/P2、测试失败、受保护文件漂移、runtime 工件进入仓库或 Git 路径集合变化时不得封箱。

## 14. Phase D 预留

Phase D 可另行设计人工决定记录和受控归档，但不得通过改写 Phase C manifest 实现。Phase C 不创建 `decisions.jsonl`，不提供人工决定写入函数，也不预先赋予任何下游权限。
