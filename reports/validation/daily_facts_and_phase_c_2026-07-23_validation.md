# 2026-07-23 Daily Facts / Phase C 验证报告

## 结论

07-23 official facts 保持原字节与原 SHA `c5cf1efae2bcaacd586117ce413e3f374a54912fda5d0c81a5a5f90fad3eab27`。Phase B 已产生合法且持久的 `semantic_noop` 证据，Phase C 已产生 `facts_review`；其 `review_state=needs_manual_review`、无 incident、全部 downstream permissions 为 `false`。幂等复跑结果为 `review_already_exists`，P1=0、P2=0，已具备进入 Daily Review 人工审查流程的条件；这不代表已批准任何下游自动更新。

## 模型门

### 初始排障模型门

- 初始排障 rollout 日志：`model=gpt-5.6-terra`，`reasoning_effort=medium`。
- 此记录仅对应下述初始失败发现，不是 semantic_noop 实现的模型证据。

### semantic_noop 实现模型门

- semantic_noop 实现与恢复 rollout 日志：`model=gpt-5.6-sol`，`reasoning_effort=high`。

## 1. 初始运行与失败发现（Initial failed attempt / Pre-fix state）

- official：`data/daily/300274_2026-07-23_facts.json`；运行前后 raw SHA 均为 `c5cf1efae2bcaacd586117ce413e3f374a54912fda5d0c81a5a5f90fad3eab27`，未变化。
- 现场 `assert_facts_pack_valid(facts, facts_pack_path=...)`：PASS。`run.status=partial`；未决项仅为 `disclosure_status`、`market_indices`、`news_policy_context`、`sector_context`；`volume_ratio=false`，核心字段无 `needs_manual_check`。
- 临时 created manifest（历史保留）：`/private/tmp/stocks-facts-20260723-write-PH3y82/runs/2026-07-23/7d9d90f0-f411-43c0-a4eb-22cd4308ceda/manifest.json`，SHA `90129b2f12d925c32457ca0a6d6978f2ac95231808c984525cad61f1f2baf52a`，`created / partial / official_written_partial`。
- 初始持久重跑的 runner manifest（历史保留）：`/Users/wongdaisy/Library/Application Support/Mimo-Lab/stocks-runtime/runs/2026-07-23/ce07c22f-c698-44e6-b274-2578d4499c38/manifest.json`，SHA `a28d51901b1b63334fe2fac463c307fd376231a9832acde1ab6d1237ba6ebc38`。
- 该次命令为 `today_after_close`、`--write-official`、`symbol=300274`；结果为 `conflict_blocked / needs_manual_review / official_conflict`，candidate raw SHA `76d3fdb9b4618a0892939767f35f27a465ab2e7f64cbe16f0ef81b06c24cd971`，`official_changed=false`，无 postwrite incident。
- 当时未生成 Phase C manifest、summary 或 review index，也未创建 `incident_review`。这段结论只描述修复前状态，不代表当前最终状态。

## 2. P2 根因（Initial failed attempt / Pre-fix state）

- 既有 official 与初始 candidate 的业务事实一致；差异仅为 `generated_at`、`quote_verification.fetched_at`、`run.fetched_at`，以及三个 `volume_ratio` 时间戳。
- 修复前 Phase B 仅把 raw bytes 完全相等认定为 `identical_noop`；上述易变时间戳令 raw SHA 不同，因而安全地返回 `conflict_blocked / official_conflict`。
- 修复前 Phase C 语义矩阵接受预期的 `identical_noop` / `official_already_identical` / `partial`，不接受该次实际的 `conflict_blocked / official_conflict`，故不能产生所需的 `facts_review`。此为原 P2，现已关闭。

## 3. semantic_noop 设计与实现

- 保留 raw bytes 完全相等时的既有 `identical_noop`；新增严格 fail-closed 的 `semantic_noop`，只在 candidate 与 official 均通过 facts Validator、身份一致、白名单六路径均存在且均为带时区的合法 ISO datetime、删除后确定性 JSON 结构和值完全相同时成立。
- 精确白名单：`generated_at`、`quote_verification.fetched_at`、`run.fetched_at`、`volume_ratio.five_day_volume_check.fetched_at`、`volume_ratio.snapshot_ohlc_check.fetched_at`、`volume_ratio.verification.fetched_at`；不存在递归忽略任意 `fetched_at`。
- semantic SHA 使用 UTF-8、`sort_keys=true`、固定 separators、无缩进或换行的序列化；candidate 与 official semantic SHA 均为 `25c510c0b0cfba34f35f11e7c7a726f18ffbf70c66391dbc914ba65da440f8f7`。

## 4. 测试结果

- Phase C 定向测试：`python3 -m pytest -q tests/test_review_manifest.py`，`128 passed`。
- Phase B runner 定向测试：`132 passed`；official lock 测试：`6 passed`。
- generator / Validator 定向测试：`254 passed, 24 subtests passed`。
- 全量 pytest：`520 passed, 24 subtests passed`。

## 5. 07-23 真实恢复

- 持久 runtime 根：`/Users/wongdaisy/Library/Application Support/Mimo-Lab/stocks-runtime`。`resolve` 后位于仓库外，未发现指回仓库的 runtime symlink；`runs/`、`reviews/` 含同类日期目录体系。
- 新 runner manifest：`/Users/wongdaisy/Library/Application Support/Mimo-Lab/stocks-runtime/runs/2026-07-23/22972611-db15-4b55-8eb6-a2f390ce5f80/manifest.json`，SHA `adf11ffabbde4d5c6afd90e8e0d11ecc924f7dcc680aca8e9c8b32e3d707bf3d`。
- 新 candidate：`/Users/wongdaisy/Library/Application Support/Mimo-Lab/stocks-runtime/runs/2026-07-23/22972611-db15-4b55-8eb6-a2f390ce5f80/candidate.json`，raw SHA `ec0c7dcbd66b10739b9270b34e5eb32fad015e51f82017060443a284097abd8b`。
- 新 runner 的 `write_action / outcome / reason_code` 为 `semantic_noop / official_unchanged / official_semantically_identical`；official raw SHA 前后仍为 `c5cf1efae2bcaacd586117ce413e3f374a54912fda5d0c81a5a5f90fad3eab27`。
- Phase C manifest：`/Users/wongdaisy/Library/Application Support/Mimo-Lab/stocks-runtime/reviews/2026-07-23/rev_300274_2026-07-23_c5cf1efae2bcaacd/review_manifest.json`，SHA `d4717c4805acdd4915a6ed2dbcb43af861008f7faa5bf102ebf5c4b46a337677`。
- Phase C 结果：`artifact_type=facts_review`、`review_state=needs_manual_review`、`incident_reason_code=null`；`review`、`current_cards`、`index`、`weekly`、`trading`、`git` permissions 均为 `false`。
- review index 仅有一条该 review 的有效记录、无重复 review ID；幂等复跑为 `review_already_exists`。

## 6. 最终状态

| 项目 | 最终状态 |
|---|---|
| official SHA | `c5cf1efae2bcaacd586117ce413e3f374a54912fda5d0c81a5a5f90fad3eab27`，未变化 |
| Phase B action | `semantic_noop` |
| outcome | `official_unchanged` |
| reason_code | `official_semantically_identical` |
| runner manifest | `22972611-db15-4b55-8eb6-a2f390ce5f80/manifest.json` |
| Phase C type | `facts_review` |
| review state | `needs_manual_review` |
| incident | none |
| downstream permissions | all false |
| idempotency | `review_already_exists` |
| P1 | 0 |
| P2 | 0 |
| Daily Review | eligible under `needs_manual_review` |

未执行 `git add`、commit 或 push。本轮只更新本报告；其余既有工作区改动不在本报告的修改范围内。
