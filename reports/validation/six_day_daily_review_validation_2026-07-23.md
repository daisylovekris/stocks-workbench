# 六篇阳光电源 Daily Review 正式核验与入库报告｜2026-07-23

## 范围与模型门

- 当前 rollout：`/Users/wongdaisy/.codex/sessions/2026/07/23/rollout-2026-07-23T02-32-46-019f8b1a-0790-7ba2-89e9-7e7d99a13a12.jsonl`。
- 实际 `turn_context`：`model=gpt-5.6-terra`，`effort=medium`；本轮执行模型门通过（Terra/medium）。
- 输入修订稿：`/private/tmp/sungrow-longcat-daily-review-from-original-20260723/`；该目录与 LongCat 原稿目录均未修改。
- final candidate：`/private/tmp/sungrow-daily-review-final-candidate-20260723/`。
- 只新增六篇正式 review 和本报告；未修改 facts、Phase C runtime、五张 current 卡、总索引或 weekly；未执行 `git add`、commit 或 push。

## 规则门结论

- `rules/review_manifest_phase_c_v0.2.md` 规定：`partial` 或存在有效 `missing` / `needs_manual_check` 时，`review_state=needs_manual_review`；缺失项必须原样保留。
- `rules/review_chain_update_rules_v0.1.md` 禁止将观察条件写成即时仓位动作。
- `tools/validate_review_chain.py --help` 显示 `--files` 支持任意 Markdown 文件路径，因此 candidate 在仓库外逐篇通过 Validator 后才被复制到正式路径。
- 结论：六份 `facts_review` 均可保持 `run.status=partial`、`review_state=needs_manual_review` 和四项公开上下文 TODO/null；没有将状态提升为 `approved`、`complete` 或 `ready_for_human_review`。

## Candidate、正式写入与 SHA

| trade_date | candidate | 正式路径 | 写入 | facts SHA-256 | review manifest SHA-256 | review_state |
|---|---|---|---|---|---|---|
| 2026-07-15 | `sungrow_review_2026-07-15.md` | `sungrow/reviews/sungrow_review_2026-07-15.md` | `created`，与 candidate 字节一致 | `0ae94a7d612d2f7c5a35a5f06b5f7e44a4ced95c7f55b89fa049339b5b57c00f` | `cadd191d33f50f75a98942e398c9332eac89e096948d9851049fac6fa0f52e3a` | `needs_manual_review` |
| 2026-07-16 | `sungrow_review_2026-07-16.md` | `sungrow/reviews/sungrow_review_2026-07-16.md` | `created`，与 candidate 字节一致 | `430c05a685712a22ed362a34b7fdaad0bbd843529663b39bc89db741b0ac0984` | `f7a0087c4a0c777885966f1dda80da68a672981ec31614cbf20e35d289ae9121` | `needs_manual_review` |
| 2026-07-17 | `sungrow_review_2026-07-17.md` | `sungrow/reviews/sungrow_review_2026-07-17.md` | `created`，与 candidate 字节一致 | `74731d190a1946df1b79f580c498d2a57b4a191c8d3f8415d8fe9b953e2ab1bd` | `e81d230e75b4ebc7f1d91722d2acf61ae0c885448d955cdfbfa27eb13f07955b` | `needs_manual_review` |
| 2026-07-20 | `sungrow_review_2026-07-20.md` | `sungrow/reviews/sungrow_review_2026-07-20.md` | `created`，与 candidate 字节一致 | `4ef128d6314383f40263b6cba137ae10a9e7fc5d3353ef109db666e6978b1460` | `cd7a603504be41cee7df1670fed65a09f7fc2b16507cac19f1a0912314790122` | `needs_manual_review` |
| 2026-07-21 | `sungrow_review_2026-07-21.md` | `sungrow/reviews/sungrow_review_2026-07-21.md` | `created`，与 candidate 字节一致 | `d5049f43f612744558c5e572938e49c60650657991c339627cade2979b3fc071` | `85d0ffe38d2e3e0f56837476ce1e005b2f8677350b9bf234b9146e147b35c671` | `needs_manual_review` |
| 2026-07-22 | `sungrow_review_2026-07-22.md` | `sungrow/reviews/sungrow_review_2026-07-22.md` | `created`，与 candidate 字节一致 | `795a4e77a84fcdebfd5f2f52b088728d86c20833c0d33318c3687298e30ab30a` | `fce2bcaf88759ef5fc2d00bb793c9fdb401889c6f6e77263a94fcb244c6cf008` | `needs_manual_review` |

每份 manifest 均为 `symbol=300274`、对应 `trade_date` 的 `facts_review`，且 `downstream_permissions` 全部为 `false`。六篇正文的 facts / manifest SHA 与真实 runtime manifest 一致；OHLC、昨收链、涨跌幅、成交额、换手率和量比均按 canonical facts 核对。

## 缺失字段与关联文件状态

- 每篇都保留并扫描到两处：`market_indices`、`sector_context`、`disclosure_status`、`news_policy_context`；均为待补证，不作为行情结论。
- 每篇均保留“仓位与行动判断留待人工复核，本篇仅记录已确认事实与价格结构。”；行动化措辞扫描无命中。
- 07-15 继续关联已封箱的 07-14 正式 review。
- 07-16 至 07-22 的 candidate 在六篇均存在后，将前一日关联从“拟生成文件，待本批草稿核验完成后入库”转换为“前一交易日日复盘，用于对照本日的状态链变化。”关联 review 仅用于状态链说明，不作为行情事实来源。

## Validator 结果

| 范围 | 结果 |
|---|---|
| 六篇 candidate，逐篇 `validate_review_chain.py --files` | 全部 PASS；每篇 P0/P1/P2/P3 = 0 |
| 六篇正式 review，逐篇 Validator | 全部 PASS；每篇 P0/P1/P2/P3 = 0 |
| 2026-07-13、2026-07-14 facts Validator | PASS |
| 六份目标 facts Validator | PASS |
| 2026-07-13、2026-07-14 review Validator | PASS，P0/P1/P2/P3 = 0 |
| 两篇旧 review + 六篇新 review 联合 Validator | PASS，`files=8`，P0/P1/P2/P3 = 0 |

## 受保护材料指纹

- 07-13 review：`9dd9f7403bd97e29997beccbd4e541a134281e2acae2d9ee38b23f9f1a57662f`，写前后一致。
- 07-14 review：`0941e43cdf4be34f8d7bb71d0fa4a0f9e1bb69d3b2f48e19f80fe07869f87392`，写前后一致。
- 五张 current 卡、`stock_workbench_index.md` 与 `weekly/*.md` 的写前后 SHA-256 均一致；总索引 SHA 为 `d85c3e5cdd9feeb5796b34e38fbc8a7b18994d22164af37eada16622491c90f6`。

## Git 与终审建议

- `git diff --check`：PASS。
- `git diff --cached --check`：PASS。
- 未暂存的既有用户状态仍包括 `tools/codex-auto.sh`、`tests/test_codex_auto_routing.sh` 和两份既有未跟踪文件；本轮新增六篇正式 review 与本报告，未进行 Git 写操作。
- P1：无。
- P2：无。
- 终审建议：六篇正式 review 已满足送入独立 `gpt-5.5/high` 最终窄审的输入条件；该审查应只审六篇 review、本报告与既有受保护文件未变性，不应改写 facts、runtime、current 卡、总索引或 weekly。
