# Phase A 只读收盘 runner 最终只读核验归档

- 审查对象：Phase A 只读收盘 runner
- 审查日期：2026-07-16
- 审查性质：最终只读核验
- 最终结论：可封箱
- P1 / P2：未发现

## 终审原文

已完成 v0.2 Phase A，只实现只读 dry-run runner 骨架；未写正式 facts，未创建/启用 launchd，未修改 review/current/index/weekly，未执行 git add/commit/push。

1. runner 路径和入口命令

新增：

- `tools/run_daily_facts_after_close.py`

入口示例：

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
  --reason phase-a-readonly-example \
  --runtime-dir /private/tmp/stocks-runner-phase-a \
  --now 2026-07-16T15:25:00+08:00
```

2. runtime 目录设计

默认：

```text
~/Library/Application Support/Mimo-Lab/stocks-runtime
```

支持：

- `STOCKS_RUNTIME_DIR`
- `--runtime-dir /private/tmp/...`

结构：

```text
runs/YYYY-MM-DD/<run_id>/
  manifest.json
  summary.md
  generator_stdout.txt
  generator_stderr.txt
  candidate.json
alerts/YYYY-MM-DD/
  <run_id>.json
review_manifests/
locks/
```

所有运行产物默认在仓库外；测试和示例均写入 `/private/tmp`。

3. 日历 schema 与覆盖范围

新增：

- `config/a_share_trading_calendar_2026.json`

当前为 Phase A 本地 seed：

- `timezone`: `Asia/Shanghai`
- `coverage_start`: `2026-07-01`
- `coverage_end`: `2026-07-31`
- `source`: `manual_phase_a_seed_no_network_update`

按本轮限制，未联网更新日历，也未处理 2026-07-15；默认 seed 覆盖 07-13、07-14、07-16 等 Phase A 回放日期。

4. 时间门和两种运行模式

- 固定业务时区：`Asia/Shanghai`
- 默认收盘门：`15:20`

模式：

- `today_after_close`
  - 默认模式
  - 目标日期为北京时间当天
  - 收盘门前返回 `skipped / before_close`
- `historical_backfill`
  - 必须显式 `--date YYYY-MM-DD`
  - 必须显式 `--reason <非空文本>`
  - 不受当日收盘门限制
  - 仍要求目标日属于交易日历

5. 状态模型

manifest 使用独立字段：

- `stage`: `gate | fetch | validate | manifest | finished`
- `outcome`: `success | partial | failed | skipped | needs_manual_review`
- `reason_code`: 已覆盖
  - `non_trading_day`
  - `before_close`
  - `calendar_uncovered`
  - `calendar_invalid`
  - `runner_already_active`
  - `generator_failed`
  - `generator_partial`
  - `source_date_mismatch`
  - `validator_failed`
  - `already_completed`
  - `sealed_exists`
  - `manifest_write_failed`

生成器 partial 不会记为 success，会映射为：

```text
needs_manual_review / generator_partial
```

6. manifest schema

manifest 至少记录：

- `schema_version`
- `run_id`
- `pid`
- `mode`
- `reason`
- `symbol`
- `target_date`
- `timezone`
- `calendar`
- `scheduled_cutoff`
- `now`
- `started_at`
- `finished_at`
- `duration_ms`
- `stage`
- `outcome`
- `reason_code`
- `dry_run`
- `generator.command`
- `generator.exit_code`
- `generator.result_status`
- `candidate_path`
- `official_path`
- `old_sha256`
- `new_sha256`
- `validator`
- `retry_count`
- `alerts`
- `exception`
- `previous_run_id`

不保存完整环境变量；stdout/stderr 经过基础敏感信息过滤。

7. runner 锁

实现 runner 专用单实例锁：

- 锁键：`symbol + target_date + mode`
- 锁文件位置：runtime `locks/`
- dry-run 也加锁
- 与 official facts lock 分离
- 同一标的、同一日期、同一模式第二实例返回：
  - `skipped / runner_already_active`

8. 生成器 dry-run 调用方式

runner 使用 subprocess 调用现有生成器：

```text
python -B tools/generate_daily_facts.py
  --symbol 300274
  --date YYYY-MM-DD
  --output <run_dir>/candidate.json
  --dry-run
```

说明：

- `--output` 只指向 run 目录；
- 生成器自身 dry-run 不写 output；
- runner 解析 stdout 后，把候选 JSON 写入 run 目录内 `candidate.json`；
- 不允许写入 `data/daily/`。

9. 幂等骨架

已实现 Phase A 只读判断：

- 已存在正式成功记录且 `dry_run=false` → `already_completed`
- 旧记录 failed / partial / needs_manual_review → 允许新 run，并记录 `previous_run_id`
- sealed facts 存在 → `sealed_exists`
- manifest 损坏不会当成已完成
- dry-run success 不计作正式完成

正式写入幂等留到 Phase B。

10. 测试矩阵与结果

新增：

- `tests/test_run_daily_facts_after_close.py`

覆盖 25 项：

- 正常交易日收盘后
- 收盘前
- 周末
- 日历内休市日
- 覆盖范围外
- 日历缺失
- 日历 JSON 损坏
- 日期重复/乱序
- 时区错误
- historical_backfill 缺 reason
- historical_backfill 非交易日
- 生成器 dry-run 正常
- 生成器 partial
- 生成器非零退出
- 来源日期错位
- Validator 失败
- 同一日期 runner 锁
- 已存在正式成功记录
- 旧 partial 后重跑
- sealed facts
- runtime 不可写
- manifest 写入失败
- stdout/stderr 敏感文本过滤
- dry-run 不写 data/daily
- manifest 不进仓库 logs

验证结果：

```text
python3 -m py_compile tools/run_daily_facts_after_close.py tools/generate_daily_facts.py tools/validate_review_chain.py tests/test_run_daily_facts_after_close.py
通过
```

```text
/private/tmp/stocks-gdf-venv/bin/python3 -B -m pytest -q -p no:cacheprovider tests/test_run_daily_facts_after_close.py
25 passed
```

```text
/private/tmp/stocks-gdf-venv/bin/python3 -B -m pytest -q -p no:cacheprovider tests/test_generate_daily_facts.py tests/test_validate.py
155 passed, 22 subtests passed
```

```text
/private/tmp/stocks-gdf-venv/bin/python3 -B -m pytest -q -p no:cacheprovider
277 passed, 22 subtests passed
```

```text
python3 -B tools/validate_review_chain.py --files sungrow/reviews/sungrow_review_2026-07-13.md --date 2026-07-13 --facts-pack data/daily/300274_2026-07-13_facts.json --no-fail
PASS | P0=0 | P1=0 | P2=0 | P3=0
```

```text
python3 -B tools/validate_review_chain.py --files sungrow/reviews/sungrow_review_2026-07-14.md --date 2026-07-14 --facts-pack data/daily/300274_2026-07-14_facts.json --no-fail
PASS | P0=0 | P1=0 | P2=0 | P3=0
```

```text
两篇 review + 五张 current 卡 Validator
PASS | files=7 | P0=0 | P1=0 | P2=0 | P3=0
```

```text
git diff --check
通过
```

11. dry-run 示例结果

命令：

```bash
python3 -B tools/run_daily_facts_after_close.py \
  --dry-run \
  --mode historical_backfill \
  --date 2026-07-14 \
  --reason phase-a-readonly-example \
  --runtime-dir /private/tmp/stocks-runner-phase-a-example-2 \
  --now 2026-07-16T15:25:00+08:00
```

结果：

```text
exit_code=2
outcome=needs_manual_review
reason_code=generator_partial
stage=fetch
generator_exit_code=2
generator_result_status=partial
validator_status=passed
candidate_exists=True
alerts_count=1
```

这是预期行为：07-14 facts dry-run 仍为 partial，runner 没有把 partial 误记为 success。

12. Git 状态

`git diff --stat` 为空，因为本轮新增文件尚未暂存。

`git status --short --untracked-files=all`：

```text
?? config/a_share_trading_calendar_2026.json
?? repo_harness_readonly_research_notes.md
?? rules/run_daily_facts_after_close_phase_a_v0.2.md
?? tests/test_run_daily_facts_after_close.py
?? tools/run_daily_facts_after_close.py
```

其中 `repo_harness_readonly_research_notes.md` 是既有范围外未跟踪文件，未处理。

13. 是否存在 P1/P2

本轮 Phase A 范围内未发现剩余 P1/P2。

明确边界：

- 还不能启用自动触发；
- 还没有 launchd；
- 还不会正式写 facts；
- 还不会生成正式 review；
- 还不会改 cards/index/weekly。

14. Phase B 前仍需解决的事项

Phase B 前至少还要补：

- 完整权威 A 股交易日历来源与年度覆盖；
- launchd 配置，但先 disabled/人工 load；
- missed-run / 休眠后补跑策略；
- 正式 facts 写入模式；
- 正式写入前后 SHA 与 rollback 说明；
- partial 告警策略；
- review manifest schema 正式化；
- 通知渠道或本地告警收敛；
- runner 与 official facts lock 的端到端正式写入测试；
- 不把 dry-run success 当正式 completed 的升级规则。

15. 供只读终审的精简摘要

本轮新增只读 Phase A runner：`tools/run_daily_facts_after_close.py`。它固定 Asia/Shanghai、15:20 收盘门，支持 `today_after_close` 与带 reason 的 `historical_backfill`，读取本地交易日历 seed，使用 runtime 目录写 manifest/summary/stdout/stderr/candidate/alert，使用 runner 单实例锁，subprocess 调用 `generate_daily_facts.py --dry-run`，解析结果并运行 facts Validator。partial 被标记为 `needs_manual_review / generator_partial`，不会写入 `data/daily/`。新增 25 项 runner 测试，全量 `277 passed, 22 subtests passed`；07-13、07-14 facts/review 与两篇 review+五张 current 卡 Validator 均 PASS。未创建 launchd，未改 review/current/index/weekly，未执行 git add/commit/push。

## 非阻断事项（P3 留档）

- runner 测试已覆盖 NaN 与 bool。
- Infinity / -Infinity 已经只读探针验证为正确拒绝。
- 后续可将三类非有限数整理为参数化测试。
- 本项不阻断 Phase A 封箱。

## 封箱执行补充（非终审原文）

本次 Git 封箱前最终验证基线为：

- runner 测试：`92 passed`
- 生成器与 Validator 定向测试：`155 passed, 22 subtests passed`
- 全量 pytest：`344 passed, 22 subtests passed`
- 07-13 facts/review Validator：`PASS | P0=0 | P1=0 | P2=0 | P3=0`
- 07-14 facts/review Validator：`PASS | P0=0 | P1=0 | P2=0 | P3=0`
- 两篇 review + 五张 current 卡 Validator：`PASS | files=7 | P0=0 | P1=0 | P2=0 | P3=0`
