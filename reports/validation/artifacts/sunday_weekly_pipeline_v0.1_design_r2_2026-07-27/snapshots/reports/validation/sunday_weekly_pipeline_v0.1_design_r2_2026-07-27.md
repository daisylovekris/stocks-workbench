# Sunday Weekly Pipeline v0.1｜设计冻结前验证记录 r2（2026-07-27）

## 结论

r1 包保持原样。本轮只修订设计规则并生成独立 r2 闭包包；没有实现代码、暂存、提交或 push。r2 将 Fable 原始 4 个 P2、4 个 P3 的闭合继续保留，并关闭 r1 后复核识别的 calendar schema P2 与三项 P3（Phase C 精确枚举、诊断身份/路径、诊断写锁）。

`P1=0`、`P2=0`、`P3=0`、`FOCUSED_CLOSURE_READY=YES`。该结论是本包的设计自检与可执行验收矩阵结论；focused closure prompt 已封存，供后续外部 focused review 仅审 r2 使用，不表示本轮调用了 Fable 或执行了实现测试。

## 开工核验与边界

- 运行证据：`/Users/wongdaisy/.codex/sessions/2026/07/27/rollout-2026-07-27T04-09-30-019fa00c-06e9-7f53-ba2f-3dbb8a751392.jsonl` 的唯一 `turn_context`：`model=gpt-5.6-terra`、`effort=medium`。
- r1 原包：`reports/validation/artifacts/sunday_weekly_pipeline_v0.1_design_r1_2026-07-27/`；未修改。
- Fable raw 采用原路径内容的逐字快照；其 SHA-256 为 `4cafde436432a20e843c0e39b981beda938a956341c40e17a9eb9743d684fd79`。
- 本轮只更新 `rules/sunday_weekly_pipeline_v0.1.md` 与本报告/r2 包；未读取或改写 r1 外部材料来作为 r2 closure 证据。

## r2 修订条款

| 类别 | 根因 | r2 闭合条款 | 验收 |
|---|---|---|---|
| calendar P2 | r1 假定逐日显式状态，真实 schema 是 coverage + `trading_days` | G1/§2.1(1) 要求每个窗口自然日恰落一份合法 coverage；coverage 内由 membership 推导 trading/non-trading；全部参与 calendar SHA 入 input_set；缺 coverage、重叠、重复/非法日期或 timezone 不符 fail-closed | C01-C06 |
| Phase C P3 | “至少为”不是可机判的有限枚举 | G7 仅接受 `needs_manual_review`、`ready_for_human_review`；未知、null、空和其他状态均为 `blocked_identity_conflict:phase_c_state_invalid`，权限全 false | C07-C08 |
| diagnostics P3 | 逻辑运行身份与失败尝试身份混用，且 JSONL 锁语义不足 | §4 区分 logical_run_key、completion identity、随机 unique diagnostic_attempt_id；规定 completion/diagnostic/lock-error 精确路径、atomic write、weekly lock 下 append+fsync | C09-C11 |

## 原 Fable finding 保留映射

| 原 finding | r2 状态 | 说明 |
|---|---|---|
| P2-1 legacy Review SHA | closed | 保留 `legacy_review_sha_unverifiable` 的唯一状态、证据与测试。 |
| P2-2 跨年 calendar | superseded and closed | 改由真实 coverage schema 的 C04-C05 精确覆盖。 |
| P2-3 partial 白名单 | closed | 四背景白名单与 metrics fail-closed 保留。 |
| P2-4 index_recovered | closed | 仍要求 completion-grade live revalidation。 |
| P3-1 Phase B semantic 外溢 | closed | SWP completion identity 独立且严格。 |
| P3-2 时间可判定性 | closed | 上海时间、市场事实分类、不可验证 fail-closed 保留。 |
| P3-3 as_of_date | closed | 上海 civil date 与默认周日/历史显式日期保留。 |
| P3-4 diagnostics 原子性 | superseded and closed | 扩展为身份、路径、并发 append 和 lock_error 证据的 C09-C11。 |

## 未决项与成本

未决设计 finding：`P1=0`、`P2=0`、`P3=0`。实现风险仍限于未来实现是否忠实遵守本规格；本轮未实施或运行未来测试。预期运行成本仍为低：每周每 symbol 一次本地文件、哈希、验证与有限锁重试；无 LLM/网络。主要成本是完整 facts validator 和安全复读，均为强制安全成本。
