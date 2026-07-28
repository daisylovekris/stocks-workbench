# Sunday Weekly Pipeline v0.1｜设计验证记录（2026-07-26）

## 结论

设计完成：SWP 被限定为“确定性输入核验 + 周观察候选”，机器最高仅到 `candidate_ready_for_human_review`。它不生成正式 weekly，不改 Phase C 权限，也不产出交易指令。

## 实际模型证据

- rollout：`/Users/wongdaisy/.codex/sessions/2026/07/26/rollout-2026-07-26T20-58-49-019f9e81-b942-7241-a802-22ee811fe8bc.jsonl`
- `turn_context`：line 8
- `payload.model`：`gpt-5.6-terra`
- `payload.effort`：`medium`；`payload.collaboration_mode.settings.reasoning_effort`：`medium`

## 黄金样本结论

2026-07-26 周观察以 07-20—07-24 五份 official facts 和五篇 Daily Review 为输入，复算周开盘 102.00、最高 120.45、最低 99.77、收盘 113.42、涨幅 +11.62287176459009939966538727%、成交额 401.21128040 亿、日均换手 4.608%、日均量比 1.076。四项背景仍是 TODO/null；周观察把仓位、成本、风险和补仓纪律明确标为 Lucien/用户判断。

07-19 样本确认既有人工流程的形态：周内事实链、观察价位和量价描述先由日资料汇总，风险/仓位/纪律随后由人工表达，且文件明确不是交易建议。07-26 validation 已对 facts SHA、数值、Daily Review、未来信息、五卡一致性与 P0—P3 进行了核验。

## 模块地图与复用决定

| 现有模块 | 可复用职责 | SWP 约束 |
|---|---|---|
| `config/a_share_trading_calendar_2026.json` / runner 日期逻辑 | 正式交易日集合与日期门 | 从 calendar 推导完整周；不硬编码五日 |
| `tools/validate_review_chain.py` | `assert_facts_pack_valid`、facts schema/数值核验 | 每份输入现场运行；generator 退出码不作为 Validator 证据 |
| `tools/official_facts_lock.py` | canonical pathname lock、锁内 hash/read | 多日期严格排序；最终复读 |
| `tools/safe_file_read.py` | no-follow、FD identity 安全读 | 同一思想覆盖 runtime 与审查输入 |
| `tools/phase_b_completion.py` | live completion 验证、semantic matrix | 复用其严格语义，不复制宽松“路径存在即完成”判断 |
| `tools/review_manifest.py` / Phase C rules | runtime artifact、atomic/index、权限常量 | SWP 不写 Phase C；仅校验其状态与全关闭权限 |
| `weekly/` 既有样本与 validation | 事实字段、人工边界、周观察文本格式 | 仅黄金样本，不作为机器写正式 weekly 的授权 |

## 设计核验

- 输入门：calendar、完整 facts、现场 Validator/identity/SHA、逐日 Daily Review、cutoff、Phase C 安全态、TODO/null 保留，均 fail-closed。
- 权限：candidate 只能允许人工审阅；weekly/current cards/repo index/Git/trading 永远 false。
- 恢复：完成检测现场复证；无效 manifest/index/证据漂移只记录诊断，不能吞掉新运行。
- 并发：先 weekly lock，后按 pathname 排序 facts locks；临时目录完成后才进行最终 SHA 复读、atomic rename 和 index 追加。
- 测试：16 个最小情形已写入规格和审查包；未运行任何未来实现测试，本轮为设计调查。

## P1 / P2 / P3

- P1：0（设计级调查未发现会突破机器/人工权限边界的既有约束）。
- P2：1（当前 Daily Review 是否均已机器可读地携带 facts SHA/引用身份，需实施时以明确 parser 契约核验；缺失时应 `blocked_missing_daily_review`，不得从正文猜测）。
- P3：1（交易日历仅为 2026 年文件；跨年运行必须显式提供/验证对应年度正式 calendar）。

## 范围与 Git

审查包身份已修正：`file_sha256_manifest.md` 的所有路径均为完整仓库相对路径；新增 `review_bundle_manifest.json`。审查包 package SHA 使用 UTF-8、`sort_keys=true`、固定 `separators=(',', ':')` 的 canonical JSON，`files` 按 path 升序，且不把 `package_sha256` 自身纳入哈希输入。新 package SHA：`23eefce624af7a6ace4dd890d676df86c1b02e6e02bd78c1737a8750822f03a0`。

独立从零复算：8 个 bundle 内容文件的 size/SHA 与 manifest 全部一致；重建 canonical JSON 后 package SHA 与 manifest 一致（PASS）。`file_sha256_manifest.md` 与 `review_bundle_manifest.json` 是身份元数据，不纳入 package SHA 输入，避免自指循环。

本轮仅修改审查包身份文件与本报告；没有修改设计规格、现有代码、facts、Daily Review、weekly、current 卡或 index。没有执行 `git add`、commit 或 push。工作区原有未提交变更保持未触及。
