# 股票小工坊 v0.2 Phase B：受控正式 facts 落盘

## 边界

Phase B 只增加显式、受门禁保护的 official facts 写入模式；仍不创建或启用 launchd，不生成 review manifest，不修改 review、current 卡、index、weekly，也不处理 2026-07-15。

runner 默认不写正式文件。必须显式选择且只能选择一个模式：

```bash
python3 tools/run_daily_facts_after_close.py --dry-run ...
python3 tools/run_daily_facts_after_close.py --write-official ...
```

`--now` 只允许 `--dry-run`。`--write-official` 使用真实北京时间。

## 运行链

正式写入链路为：

时间与交易日门 → runner 单实例锁 → 锁内扫描并现场验证 previous-run completion → generator dry-run 候选 → marker 解析 → 候选身份门 → facts Validator → partial 写入策略 → official facts 排他锁 → 锁内重读 official → 创建或安全跳过 → 原子写入 → 写后 Validator/SHA → runtime bundle 最终提交。

runner 仍只以 `--dry-run --emit-runner-marker` 调用 generator 产出候选；runner 不让 generator 二次抓取。

generator 独立 CLI 只有显式提供 `--write-official` 时才允许调用 official transaction。该模式不接受自定义 `--output`，official 路径必须由 `symbol` 与 `date` 推导；未提供 `--write-official` 时，`--output` 只能作为候选或非 official 输出路径，不能写入规范 official facts。

## 正式路径

official facts 规范路径固定为：

```text
data/daily/<symbol>_<target_date>_facts.json
```

路径只能由 `symbol` 与 `target_date` 推导，用户不能任意指定。路径必须位于仓库内规范 `data/daily/`，禁止路径穿越，禁止 official 文件符号链接逃离规范目录。

runtime 与 candidate 仍写入仓库外 runtime run 目录。

## partial 白名单

允许写入的 partial 只限缺失项全部属于：

- `market_indices`
- `sector_context`
- `disclosure_status`
- `news_policy_context`

同时必须满足：quote 核心字段完整，行情日期不错位，换手率已确认，量比已确认或 `derived_confirmed`，无核心字段 `needs_manual_check`，facts Validator 无 P0/P1/P2。

合格 partial 写入后：

- `outcome=partial`
- `reason_code=official_written_partial`
- `needs_manual_review=true`

不得标记为 success。

若缺失 OHLC、昨收、涨跌幅、成交额，换手率未确认，量比仍为 `candidate/conflict/stale/unavailable`，`source_date` 错位，核心字段需要人工核验，Validator 失败，或缺失项超出白名单，则不得写 official：

- `outcome=needs_manual_review`
- `reason_code=partial_not_eligible_for_official`

## existing official 保守策略

- official 不存在：候选满足全部准入门后允许创建。
- official 已存在且字节相同：不重写，`write_action=identical_noop`，`reason_code=official_already_identical`。
- official 已存在且原始字节不同，但双方 facts Validator 均通过、身份字段一致、仅下列六个精确时间戳路径不同，删除这些路径后的确定性 JSON 完全相同：不重写，`write_action=semantic_noop`、`outcome=official_unchanged`、`reason_code=official_semantically_identical`、`official_changed=false`。
- official 已存在但内容不同：默认禁止覆盖，`write_action=conflict_blocked`，`reason_code=official_conflict`。
- sealed official：始终禁止自动覆盖，`write_action=sealed_blocked`，`reason_code=sealed_exists`。
- manual official：始终禁止自动覆盖，`write_action=manual_blocked`，`reason_code=manual_exists`。

`semantic_noop` 的排除白名单固定且不可递归扩张：

- `generated_at`
- `quote_verification.fetched_at`
- `run.fetched_at`
- `volume_ratio.five_day_volume_check.fetched_at`
- `volume_ratio.snapshot_ohlc_check.fetched_at`
- `volume_ratio.verification.fetched_at`

六个路径必须在双方均存在、值均为带时区的合法 ISO datetime 字符串。`symbol`、`trade_date`、`schema_version` 必须相同。删除六个路径后，结构和值必须完全相同；其他 `fetched_at`、未知字段、missing、needs_manual_check 或任何业务字段均不得忽略。任一条件不满足即 `conflict_blocked`。

Phase B 不实现自动择优覆盖、字段合并或旧产物迁移。

## manifest 与故障边界

Phase B manifest 记录：

- `write_official`
- `official_path`
- `official_exists_before`
- `official_sha256_before`
- `official_sha256_after`
- `candidate_sha256`
- `write_action`
- `partial_write_policy`
- `official_validator_before`
- `official_validator_after`
- `comparison`
- `manifest_bundle_failed`
- `manifest_bundle_reason_code`

`semantic_noop` 的 `comparison` 必须记录 raw SHA、semantic SHA、精确排除路径、双方排除值类型检查、ISO datetime 检查、`semantic_equal` 与 `official_changed=false`。semantic SHA 使用 UTF-8、`sort_keys=true`、固定 separators、无缩进换行的确定性 JSON 序列化；不得覆盖既有 raw SHA 字段。

`generate_daily_facts.py` 的 `RunOutcome.wrote_file` 与 CLI 同名字段只表示本轮是否真实创建或替换 official bytes，必须与 transaction 的 `official_changed` 一致。`identical_noop` 与 `semantic_noop` 均为 `wrote_file=false`；完成/冲突语义不得借该布尔值表达，仍以 `write_action`、`outcome` 与 `reason_code` 为准。

runtime bundle 仍按 Phase A 顺序写入：

stdout → stderr → candidate → summary → alert → manifest。

manifest 是最终提交标记。若 official 已成功写入但最终 runtime bundle/manifest 写入失败，official 不回滚；CLI 必须报告 `official_written_manifest_failed`，并在结构化 stderr 中带 official path 与写后 SHA，后续补偿任务可用 official SHA 重建运行记录。

## 幂等

dry-run success 永远不算正式完成。

只有成功、完整且现场证据仍成立的 `created`、`identical_noop` 或 `semantic_noop` 正式 manifest 才算完成记录。completion validator 属于 Phase B，并与 Phase C 共用 Phase B action/outcome/reason 矩阵；Phase B 不依赖 `tools/review_manifest.py`。

通用完成门要求：`schema_version=runner_manifest_v0.2_phase_b`、`stage=finished`、带时区 `finished_at`、`outcome!=failed`、`manifest_bundle_failed` 未置真、`write_official=true`、`dry_run=false`，且 symbol、target_date、mode、run_id、manifest/candidate/official 规范路径身份一致。candidate 与当前 official 必须通过安全 no-follow fd 读取；字节、SHA 与 JSON 解析来自同一读取对象；双方必须现场通过 facts Validator；当前 official 在共享 official lock 内读取。

分动作完成门：

- `created`：仅接受 `official_written/success` 或 `official_written_partial/partial`，`official_changed=true`，before SHA 为空，after SHA 等于 candidate SHA，当前 official SHA 等于 after SHA，candidate 与 official 原始字节相同。
- `identical_noop`：仅接受 `official_already_identical` 与候选 facts 状态一致的 outcome，`official_changed=false`、`official_bytes_equal_candidate=true`，before SHA、after SHA、candidate SHA 与当前 official SHA 全部相等。
- `semantic_noop`：仅接受 `official_unchanged/official_semantically_identical`，`official_changed=false`、`official_bytes_equal_candidate=false`，before SHA 等于 after SHA 且不同于 candidate raw SHA；committed `candidate.json` 必须仍存在并匹配 candidate SHA；`comparison` 字段全集、六条排除路径及顺序必须精确一致，raw/semantic SHA 关系合法，`semantic_equal=true`；最后用共享 `build_semantic_comparison()` 对现场 candidate/official 字节重算并与 manifest 逐字段相等。

previous-run scan 必须在 runner lock 内执行。非法或失效的 matching manifest 不计完成，按路径与稳定 reason code 写入 `scan_diagnostics`，然后允许 generator 与 official transaction 重新运行。candidate 丢失、符号链接替换、路径逃逸、内容篡改或 current official 漂移均按此处理。

任何 `outcome=failed`、`manifest_bundle_failed=true` 或 `manifest_write_failed` 记录只保留为运行审计及 Phase C incident evidence，不扩展为正常 `facts_review`，也不得阻断安全重跑。partial official 或 `official_unchanged` 记录不代表人工批准，仍按 facts 未决项进入审查。

official 文件存在但 manifest 缺失时，不猜测完成状态；下一次正式运行必须读取并验证 official 后输出创建、相同 no-op 或冲突诊断。损坏 manifest 不阻断安全重跑；同一任务的最新合法正式记录才参与幂等。

## 手动命令

今日收盘后候选 dry-run：

```bash
python3 tools/run_daily_facts_after_close.py \
  --dry-run \
  --symbol 300274
```

今日收盘后正式写入：

```bash
python3 tools/run_daily_facts_after_close.py \
  --write-official \
  --symbol 300274
```

历史补跑正式写入必须带日期与非空原因：

```bash
python3 tools/run_daily_facts_after_close.py \
  --write-official \
  --mode historical_backfill \
  --date YYYY-MM-DD \
  --reason "受控历史补跑原因"
```

## 回滚与冲突处理

Phase B 不自动回滚已写入的 official。若写入后 manifest 失败，使用结构化 stderr 中的 `official_path` 与 `official_sha256_after` 进行补偿记录。

遇到 `official_conflict`、`sealed_exists`、`manual_exists` 或 `partial_not_eligible_for_official`，停止自动写入，进入独立人工核验或受控迁移工具流程。

## Phase C 前遗留事项

- launchd 调度仍未启用。
- 公告、新闻、政策、指数板块上下文仍未自动核验。
- existing official 自动择优覆盖、字段合并、旧产物迁移仍未实现。
- 通知推送未实现。
