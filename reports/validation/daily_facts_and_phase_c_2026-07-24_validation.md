# 300274 2026-07-24 official facts 与 Phase C 验证

## 执行证据

- 模型：`gpt-5.6-luna`
- reasoning effort：`low`；真实 rollout session evidence：2026-07-26 当前 rollout 的 `turn_context`
- 分支：`workbench/mainline-2026-07`
- HEAD：`088a5e8849047e3ce6db3fe3b6a87b1e3542aebf`
- 已确认 completion 修复提交：`e2ccbaca4138bf0e9400baf80704864187b1dbcf`、`088a5e8849047e3ce6db3fe3b6a87b1e3542aebf`
- symbol/date/mode：`300274` / `2026-07-24` / `historical_backfill`
- runtime：`/Users/wongdaisy/Library/Application Support/Mimo-Lab/stocks-runtime`
- 数据来源：Tencent historical quote + Sohu five-day volume cross-check；交易日历包含 2026-07-24

## 核心行情

`open=116.13`，`high=120.45`，`low=113.13`，`close=113.42`，`previous_close=117.79`，`pct_change=-3.709992359283476%`，`amount=63.84702262`，`turnover_rate=3.47%`，`volume_ratio=0.74`。两份既有 dry-run candidate 的业务字段一致，仅批准时间戳不同；Validator 均 PASS。缺失字段仅为 `market_indices`、`sector_context`、`disclosure_status`、`news_policy_context`。

## Phase B

- run id：`43532eec-41b9-4c9a-8fc6-2dc763c19a84`
- action/outcome/reason：`created` / `partial` / `official_written_partial`
- candidate：`/Users/wongdaisy/Library/Application Support/Mimo-Lab/stocks-runtime/runs/2026-07-24/43532eec-41b9-4c9a-8fc6-2dc763c19a84/candidate.json`
- candidate SHA：`09b30acc84ae65715859101880ba9eb4ac1c5bf14afa27770323f0e806debff7`
- official：`data/daily/300274_2026-07-24_facts.json`
- official SHA：`09b30acc84ae65715859101880ba9eb4ac1c5bf14afa27770323f0e806debff7`
- candidate 与 official 原始字节一致；`official_changed=true`、`wrote_file=true`、`partial_eligible=true`
- runner manifest：`/Users/wongdaisy/Library/Application Support/Mimo-Lab/stocks-runtime/runs/2026-07-24/43532eec-41b9-4c9a-8fc6-2dc763c19a84/manifest.json`
- runner manifest SHA：`1892bfcb7fd989ef122a8e9f4aa24b706f4363886d9ba281c1f5ed340ae47b78`
- Validator：PASS；`missing`/`needs_manual_check` 为上述四个字段，`volume_ratio` 不缺失且无需人工检查

## Phase C

- manifest：`/Users/wongdaisy/Library/Application Support/Mimo-Lab/stocks-runtime/reviews/2026-07-24/rev_300274_2026-07-24_09b30acc84ae6571/review_manifest.json`
- manifest SHA：`ea869c02d083ddfa181d9334885ff44d09272298f0b43fb0fb25d0e0965ccaf3`
- review type：`facts_review`
- review state：`needs_manual_review`
- incident：`none`（`incident_reason_code=null`）
- downstream permissions：`current_cards=false, git=false, index=false, review=false, trading=false, weekly=false`
- summary：Phase C manifest 的 `evidence_summary`；review index：`/Users/wongdaisy/Library/Application Support/Mimo-Lab/stocks-runtime/reviews/2026-07-24/review_index.jsonl`
- review index SHA：`49dd452029be7917a6e02bb589ba86b5f92262560b500b9414299b2f686dfb4f`
- 幂等复跑：`review_already_exists`；未新增重复 index 项

## 保护与验证

- 07-23 official：`c5cf1efae2bcaacd586117ce413e3f374a54912fda5d0c81a5a5f90fad3eab27`
- 07-23 semantic_noop runner manifest：`adf11ffabbde4d5c6afd90e8e0d11ecc924f7dcc680aca8e9c8b32e3d707bf3d`
- 07-23 Phase C manifest：`d4717c4805acdd4915a6ed2dbcb43af861008f7faa5bf102ebf5c4b46a337677`
- 07-23 review index：`e2d498694cc14344a91f3157c489e0dfd595e47fc7f15030b6d1d7ef89c916b2`
- 07-23 review index 内容未改写；07-24 index 仅有一条 `300274/2026-07-24/facts_review` 记录
- P1：无；P2：无；P3：无
- 复验：facts Validator PASS；Phase B/Phase C 定向测试 `312 passed`；`py_compile` PASS；`git diff --check` PASS；`git diff --cached --check` PASS
- 未执行 `git add`、commit、push；未清理任何权威 runtime 产物

## 结论

达到 2026-07-24 Daily Review 准入条件的“facts 已正式写入、Phase C 已生成并需人工复核”门槛；由于四个字段缺失，状态保持 `needs_manual_review`，下游权限全部关闭。
