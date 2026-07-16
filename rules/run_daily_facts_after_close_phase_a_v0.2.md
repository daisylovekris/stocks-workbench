# 收盘后 facts runner｜v0.2 Phase A 运行说明

## 定位

Phase A 只实现只读 dry-run runner：

- 无 launchd；
- 不写正式 `data/daily/` facts；
- 不生成正式 review；
- 不修改 current 卡、index 或 weekly；
- 不联网更新交易日历。

## 入口

```bash
python3 tools/run_daily_facts_after_close.py \
  --dry-run \
  --symbol 300274 \
  --now 2026-07-16T15:25:00+08:00 \
  --runtime-dir /private/tmp/stocks-runner-phase-a
```

历史补跑 dry-run：

```bash
python3 tools/run_daily_facts_after_close.py \
  --dry-run \
  --mode historical_backfill \
  --date 2026-07-14 \
  --reason "manual Phase A replay" \
  --runtime-dir /private/tmp/stocks-runner-phase-a
```

## 业务时间

- 固定业务时区：`Asia/Shanghai`。
- 默认收盘门：`15:20`。
- `today_after_close` 在收盘门前返回 `skipped / before_close`。
- `historical_backfill` 必须显式提供 `--date` 和非空 `--reason`，不受当日收盘门限制。
- `--now` 仅供 dry-run / 测试注入，必须是带显式 `+08:00` offset 的 ISO datetime；无时区、`Z`、`+00:00` 或其他 offset 均拒绝。

## 交易日历

默认日历：

- `config/a_share_trading_calendar_2026.json`

Phase A 日历是本地只读 seed，不联网更新。当前覆盖范围为 `2026-07-01` 到 `2026-07-31`，用于 runner 骨架和 07-13 / 07-14 / 07-16 一带回放；超出覆盖范围返回 `calendar_uncovered`。

## runtime 目录

默认：

```text
~/Library/Application Support/Mimo-Lab/stocks-runtime
```

可通过环境变量覆盖：

```bash
STOCKS_RUNTIME_DIR=/private/tmp/stocks-runner-phase-a
```

无论使用默认值、`--runtime-dir` 还是 `STOCKS_RUNTIME_DIR`，runtime 经过 `expanduser()` 和 `resolve(strict=False)` 后都必须位于仓库外。仓库根目录、`data/daily/`、`logs/`、任意仓库子目录，以及最终指向仓库的符号链接都会以 `runtime_inside_repository` 失败，且不会创建目标目录。

结构：

```text
runs/YYYY-MM-DD/<run_id>/
  manifest.json
  summary.md
  generator_stdout.txt
  generator_stderr.txt
  candidate.json  # 仅有候选时
alerts/YYYY-MM-DD/
  <run_id>.json
```

运行产物不写入仓库 `logs/`。

`manifest.json` 是一个 run bundle 的最终提交标记。写入顺序固定为 stdout、stderr、candidate（若存在）、summary、alert（若需要），最后才写 manifest；前置产物失败时不得留下成功 manifest。alert 继续集中保存在 `alerts/YYYY-MM-DD/`，其路径记录在 manifest 的 `alerts` 字段。

## stdout 候选协议

runner 调用生成器时附加内部 `--emit-runner-marker`，生成器在保留原有人工可读 dry-run JSON 的同时，额外输出恰好一行：

```text
STOCKS_FACTS_CANDIDATE_JSON=<单行 JSON 对象>
```

runner 只解析该 marker；普通日志、警告、空行或其他 JSON 日志不参与候选提取，stderr 永不作为候选。marker 缺失、重复或 JSON 损坏分别记录 `stdout_candidate_missing`、`stdout_candidate_ambiguous`、`stdout_parse_failed`。

## outcome 语义

- `success`：dry-run candidate 与 Validator 均通过；Phase A 不代表正式 facts 已写入。
- `partial` 不会映射为 `success`；生成器 partial 会记录为 `needs_manual_review / generator_partial`。
- `failed`：生成器失败、Validator 失败、日历损坏、manifest 写入失败等。
- `skipped`：非交易日、收盘前、覆盖范围外、已有正式成功记录、sealed facts、runner 已活跃等。

所有已经结束的运行统一记录 `stage=finished`；`last_stage` 表示最后完成或发生异常/人工复核的位置，例如生成器 partial 为 `last_stage=fetch`。不能用 `last_stage=fetch` 推断进程仍在运行。

Phase A manifest 使用以下指纹语义：

- `candidate_sha256`：实际写入 `candidate.json` 的规范化 JSON 字节哈希；没有候选时为 `null`；
- `official_sha256_before`：Phase A 当前不读取正式 facts 指纹，保持 `null`；
- `official_sha256_after`：Phase A 永远为 `null`，明确表示未更新正式 facts。

dry-run `success` 只表示候选与 Validator 通过，不构成正式 completed；只有完全匹配 `target_date + symbol + mode` 且 `dry_run=false / outcome=success` 的历史记录才可触发 `already_completed`。

## 已知能力缺口

- 尚未创建或启用 launchd；
- 尚未实现正式 facts 写入；
- 尚未实现 missed-run catch-up；
- 尚未实现通知推送；
- 尚未生成正式 review 草稿；
- cards / index / weekly 继续人工确认。
