# 阳光电源 current 卡与索引更新验证｜2026-07-24

## 范围与人工授权

- 状态截止：2026-07-24 收盘；未使用 2026-07-25 及以后数据。
- 本次是 Lucien/用户显式授权的人工更新。Phase C 下游权限仍全为 `false`；未将人工判断改写为机器批准，未生成自动交易指令。
- 仅修改五张 current 卡、`stock_workbench_index.md` 与本报告；未修改其他股票条目、weekly、official facts、runtime、Daily Review、routing 或长期排除文件。

## 准确路径与修改摘要

| 项目 | 路径 | 本次摘要 |
|---|---|---|
| 持仓主卡 v0.1.1 | `sungrow_test/sungrow_position_card_v0.1.1.md` | 状态日、收盘、仓位/成本、连续行情、行动纪律、facts/review 链与 SHA |
| 低位区域观察卡 | `sungrow_test/sungrow_low_zone_observation_v0.1.md` | 近端与更低历史观察分离；明确无补仓授权 |
| 风险与跟踪卡 | `sungrow_test/sungrow_risk_and_tracking_v0.1.md` | 高风险、118—120 抛压、近端上下方观察与背景缺口 |
| 补仓分析卡 | `sungrow_test/sungrow_add_position_analysis_v0.1.md` | 当前不补仓；任一价位均非自动触发 |
| 估值卡 | `sungrow_test/sungrow_valuation_v0.1.md` | 最新价格/日期、相对成本位置与背景资料不完整 |
| 总索引 | `stock_workbench_index.md` | 07-24 状态、两篇 Daily Review、五张 current 卡与人工/权限边界 |

## facts / review 链

| 日期 | facts 路径与 SHA | Daily Review |
|---|---|---|
| 2026-07-23 | `data/daily/300274_2026-07-23_facts.json` / `c5cf1efae2bcaacd586117ce413e3f374a54912fda5d0c81a5a5f90fad3eab27` | `sungrow/reviews/sungrow_review_2026-07-23.md` |
| 2026-07-24 | `data/daily/300274_2026-07-24_facts.json` / `09b30acc84ae65715859101880ba9eb4ac1c5bf14afa27770323f0e806debff7` | `sungrow/reviews/sungrow_review_2026-07-24.md` |

两日 facts 均为 `partial`，Daily Review 均为 `needs_manual_review`。四项背景缺口均继续为 TODO/null：`market_indices`、`sector_context`、`disclosure_status`、`news_policy_context`。

## 五卡交叉一致性与索引引用

- 状态截止均为 2026-07-24 收盘；持仓主卡、估值卡和索引记录最新收盘 113.42，其余卡按各自职责维持同一状态口径。
- 行情链：07-23 为放量强反弹、高位收盘；07-24 为上探 120.45 后缩量回撤，收盘靠近日低 113.13。
- 仓位与行动：3 手、成本 181 元、当前无补仓计划、不追涨杀跌；不由机器生成买卖指令。
- 风险：高风险；07-23 单日强反弹未确认完整趋势反转，118—120 抛压继续观察。
- 观察层级：下方 113.13 / 109.95 / 108.50，上方 114.05 / 117.79 / 118.27 / 120.45；均非硬底、有效支撑、突破确认或自动触发器。
- 索引已引用两篇新增 Daily Review、07-24 facts 与五张 current 卡；未将 07-19 weekly 冒充 07-24 周度结论。

## 校验结果

- 07-23 Daily Review + 对应 facts：`validate_review_chain.py` PASS，`P0=0 / P1=0 / P2=0 / P3=0`。
- 07-24 Daily Review + 对应 facts：`validate_review_chain.py` PASS，`P0=0 / P1=0 / P2=0 / P3=0`。
- 字段交叉检查（按各卡职责）：五张卡与索引均标注 2026-07-24；持仓主卡、估值卡和索引记录最新价 113.42；持仓主卡与补仓分析卡记录 3 手、181 元和不补仓；风险卡记录高风险；低位、风险、补仓卡与索引使用同一观察层级；`partial` / `needs_manual_review` 与下游权限关闭声明一致。补仓分析卡按职责不重复最新收盘数值。
- 事实 SHA 与 review 引用：07-23、07-24 SHA 均已在持仓主卡、低位观察卡和本报告中逐项匹配；索引已引用两篇 Daily Review 与两份 facts。
- 未来数据泄漏：目标 diff 中无 2026-07-25 及以后日期命中。
- 其他股票零改动：本次目标 diff 未包含其他股票文件；工作区原有的 `tools/codex-auto.sh` 与 `tests/test_codex_auto_routing.sh` 改动未触碰。
- `git diff --check`：通过；`git diff --cached --check`：通过，且暂存区为空。

### Raw generic-validator findings

通用 `validate_review_chain.py --no-fail` 的原始汇总为 `P0=0 / P1=0 / P2=2 / P3=2`。仓库未提供五张 current 卡与索引的专用 Validator；下列为本次通用 Validator 的两类启发式命中，不删除其原始结果。

1. `sungrow_test/sungrow_position_card_v0.1.1.md:2189`：`R005_CURRENT_SECTION_STALE_LEVEL`（P2）及 `R007_CURRENT_SECTION_BOUNDARY`（P3）。命中 07-23 带日期的历史对比锚点（117.79 / 118.27），该对比用于说明 07-24 的连续状态。
2. `stock_workbench_index.md:165`：`R004_CURRENT_SECTION_STALE_DATE`（P2）及 `R007_CURRENT_SECTION_BOUNDARY`（P3）。命中 `weekly_market_watch_2026-07-12.md` 的带日期 weekly 历史入口。

### Project adjudication

- 两类命中均有明确日期或历史身份，未被用作 2026-07-24 当前状态或周度结论。
- 保留历史：不删除 07-23 对比，也不删除 07-12 weekly 历史入口。
- 本轮发现并关闭索引 Markdown 表格连续性问题：原引用块位于阳光电源首行与“阳光电源 短线规则”行之间；现已移至“## 当前样板卡”标题之后、表头之前，表格从表头至最后一行连续。
- unresolved P1=0。
- unresolved P2=0。
- unresolved P3=0。
