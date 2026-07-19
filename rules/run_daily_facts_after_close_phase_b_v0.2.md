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

时间与交易日门 → runner 单实例锁 → generator dry-run 候选 → marker 解析 → 候选身份门 → facts Validator → partial 写入策略 → official facts 排他锁 → 锁内重读 official → 创建或安全跳过 → 原子写入 → 写后 Validator/SHA → runtime bundle 最终提交。

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
- official 已存在但内容不同：默认禁止覆盖，`write_action=conflict_blocked`，`reason_code=official_conflict`。
- sealed official：始终禁止自动覆盖，`write_action=sealed_blocked`，`reason_code=sealed_exists`。
- manual official：始终禁止自动覆盖，`write_action=manual_blocked`，`reason_code=manual_exists`。

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

runtime bundle 仍按 Phase A 顺序写入：

stdout → stderr → candidate → summary → alert → manifest。

manifest 是最终提交标记。若 official 已成功写入但最终 runtime bundle/manifest 写入失败，official 不回滚；CLI 必须报告 `official_written_manifest_failed`，并在结构化 stderr 中带 official path 与写后 SHA，后续补偿任务可用 official SHA 重建运行记录。

## 幂等

dry-run success 永远不算正式完成。

只有 `write_official=true` 且 `write_action=created/identical_noop` 的合法正式 manifest 才算正式完成记录。partial official 记录为已落盘，但仍需要人工补全。

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
