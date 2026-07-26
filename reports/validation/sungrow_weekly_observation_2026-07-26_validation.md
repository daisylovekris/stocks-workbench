# 阳光电源 300274｜2026-07-26 周日观察验证

## 实际模型证据

- session id：`019f9b70-bde9-7432-b5b9-4a3d8e2c9c79`
- rollout：`/Users/wongdaisy/.codex/sessions/2026/07/26/rollout-2026-07-26T06-41-25-019f9b70-bde9-7432-b5b9-4a3d8e2c9c79.jsonl`
- 结构化日志：line 432，`payload.model='gpt-5.6-luna'`，`payload.collaboration_mode.settings.reasoning_effort='low'`。
- model：`gpt-5.6-luna`
- reasoning_effort：`low`

## 周观察与时间边界

- 周观察：`weekly/weekly_market_watch_2026-07-26.md`
- 统计区间：2026-07-20 至 2026-07-24；五个交易日。
- 判断截止：2026-07-24 收盘。
- 文件日期为 2026-07-26；市场判断仅引用统计区间内的 official facts 与对应 Daily Review，未引用后续行情、周末新闻、公告或政策。

## facts 输入与 SHA-256

| 日期 | facts 路径 | SHA-256 |
|------|------------|---------|
| 2026-07-20 | `data/daily/300274_2026-07-20_facts.json` | `4ef128d6314383f40263b6cba137ae10a9e7fc5d3353ef109db666e6978b1460` |
| 2026-07-21 | `data/daily/300274_2026-07-21_facts.json` | `d5049f43f612744558c5e572938e49c60650657991c339627cade2979b3fc071` |
| 2026-07-22 | `data/daily/300274_2026-07-22_facts.json` | `795a4e77a84fcdebfd5f2f52b088728d86c20833c0d33318c3687298e30ab30a` |
| 2026-07-23 | `data/daily/300274_2026-07-23_facts.json` | `c5cf1efae2bcaacd586117ce413e3f374a54912fda5d0c81a5a5f90fad3eab27` |
| 2026-07-24 | `data/daily/300274_2026-07-24_facts.json` | `09b30acc84ae65715859101880ba9eb4ac1c5bf14afa27770323f0e806debff7` |

五份 facts 均现场通过 facts Validator，均为 `partial`；缺失项保持 `market_indices`、`sector_context`、`disclosure_status`、`news_policy_context` 的 TODO/null，未作为确认性背景使用。

## 五日统计复算

- 周开盘：`102.00`，来源 07-20 `quote.open`。
- 周最高：`120.45`，来源 07-24 `quote.high`，为五日 high 的最大值。
- 周最低：`99.77`，来源 07-20 `quote.low`，为五日 low 的最小值。
- 周收盘：`113.42`，来源 07-24 `quote.close`。
- 周涨跌幅：`+11.62287176459009939966538727%`，公式 `(113.42 - 101.61) / 101.61 × 100%`，其中 101.61 为 07-20 `quote.prev_close`。
- 五日成交额：`401.21128040` 亿，`67.732162 + 69.121156 + 93.31922099 + 107.19171879 + 63.84702262`。
- 日均成交额：`80.24225608` 亿，`401.21128040 / 5`。
- 日均换手率：`4.608%`，`(4.15 + 4.22 + 5.34 + 5.86 + 3.47) / 5`。
- 日均量比：`1.076`，`(0.94 + 0.98 + 1.36 + 1.36 + 0.74) / 5`。

## Daily Review 与 current 卡核验

- 已引用：`sungrow/reviews/sungrow_review_2026-07-20.md` 至 `sungrow/reviews/sungrow_review_2026-07-24.md`。
- current 卡与周观察一致：3 手、181 元成本、高风险、无补仓计划、不追涨杀跌、控制回撤优先；118—120 区域压力仍待观察。
- 下方 113.13 / 109.95 / 108.50 与上方 114.05 / 117.79 / 118.27 / 120.45 均保留为观察层级，不写成硬支撑、确认突破、止损线、买点或自动交易触发器。
- 人工判断与机器边界明确：上述仓位、风险和纪律来自 Lucien/用户人工判断；facts 为 `partial`、Phase C 为 `needs_manual_review`、下游权限未被改写为机器授权。

## 验证结果

- 五份 facts Validator：PASS。
- 周观察 Validator：PASS，`P0=0 / P1=0 / P2=0 / P3=0`。
- 数值逐字段复算：PASS；周内最高日期为 07-24，最低日期为 07-20。
- 时间边界与未来信息扫描：PASS；统计和市场判断仅使用 07-20 至 07-24 输入，未发现统计区间之后的市场事实进入历史判断。
- facts SHA 引用：PASS；五份 SHA 均列于本报告并与现场复算一致。
- Daily Review 引用：PASS；周观察列出 07-20 至 07-24 五篇 Daily Review。
- 五卡一致性：PASS；仓位、成本、风险、纪律与观察层级一致。
- 其他股票零改动：PASS；本轮新增文件仅在 `weekly/` 与 `reports/validation/` 下。
- tracked worktree diff check：PASS。
- 两份新 Markdown 独立 whitespace scan：PASS；覆盖行尾空格、Tab 尾随、文件末尾换行与 Markdown 表格结构。
- cached diff check：暂存区为空，精确暂存后再次执行。

## P1 / P2 / P3

- P1：0。
- P2：0。
- P3：0。

本报告不执行 `git add`、commit 或 push。
