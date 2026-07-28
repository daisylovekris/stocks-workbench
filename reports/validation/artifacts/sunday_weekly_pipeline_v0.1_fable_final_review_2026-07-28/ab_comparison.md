# Fable Shell A/B Comparison — Pi Guarded vs Claude Code Bare

## 1. Experiment objective

本实验比较同一 r14 密封母包、同一 Fable 模型、同一低思考档、同一 6144 最大输出上限下，两种宿主壳层的费用、质量、权限面与落盘可靠性。

- **A 组**：Pi guarded tools
- **B 组**：Claude Code bare

该实验比较的是"宿主壳层 + 工具面"的整体效果，不是模型能力差异。

## 2. Controlled conditions

| 条件 | 值 |
| --- | --- |
| package | `reports/validation/artifacts/sunday_weekly_pipeline_v0.1_design_r14_2026-07-27/` |
| expected package SHA-256 | `e2301e00fb97a1b1383ba13ec1400693c265984370eb6c74ae0c0eccc6522f6d` |
| model | `anthropic/claude-fable-5` |
| provider | ZenMux |
| thinking / effort | low |
| maximum output tokens | 6144 |
| 审查提示 | 同一 |
| 身份基准 | 同一 |
| 判决规则 | 同一 |
| 运行环境 | 隔离 worktree |

## 3. Run inventory

| 项目 | A: Pi guarded | B: Claude Code Bare |
| --- | --- | --- |
| run id | `pi-20260729-011452-17167` | `bare-recovered-20260729-0154` |
| backend | anthropic-messages via Pi guarded tools | Claude Code bare via ZenMux |
| duration | 101 seconds | — |
| engine_exit_code | 0 | — |
| engine_error | null | — |
| git_status_unchanged | true | — |
| local report landing | 成功 | 失败（从 ZenMux web logs 手工恢复） |
| final decision | `GREEN_LIGHT` | `GREEN_LIGHT` |
| reported counts | P1=0, P2=0, P3=1 | P1=0, P2=0, P3=1 |
| tool surface | review_list, review_read, review_search, review_file_sha256, review_json_identity, review_package_identity | Read, Glob, Grep, Bash |

## 4. Cost comparison

### 4.1 正式运行费用

| 项目 | A: Pi guarded | B: Claude Code Bare |
| --- | --- | --- |
| formal-run cost | `$1.004` | `$1.581959` |
| cost derivation | — | `$1.600254 - $0.018295` |
| smoke-test cost | `$0.00155`（不计入） | `$0.018295`（不计入） |

### 4.2 Token usage（A 组）

| 类别 | 数量 |
| --- | --- |
| input | 18 |
| output | 4,995 |
| cacheRead | 186,039 |
| cacheWrite | 45,440 |
| totalTokens | 236,492 |
| reasoning | 485 |

### 4.3 计算公式

- **Pi savings vs Bare** = `1 - 1.004 / 1.581959 ≈ 36.5%`
- **Bare premium vs Pi** = `1.581959 / 1.004 - 1 ≈ 57.6%`
- **正式 A/B 总费用** = `$1.004 + $1.581959 ≈ $2.585959`

## 5. Quality comparison

| 维度 | A: Pi guarded | B: Claude Code Bare |
| --- | --- | --- |
| 最终判决 | `GREEN_LIGHT`（正确） | `GREEN_LIGHT`（正确） |
| 正文长度 | 紧凑 | 更长 |
| 事实滑移 | 更少 | 更多 |
| 逐项核验 | 较简 | 更细 |
| `.DS_Store` 判断 | 证据描述有误（false-positive） | 判断更准确 |

### 5.1 两组报告中的误差分类

| 组别 | 类型 | 项目 | 说明 |
| --- | --- | --- | --- |
| A: Pi guarded | 证据描述错误 | `.DS_Store` 被声称纳入密封清单并影响 package SHA | `.DS_Store` 实际存在（6148 bytes），但未列入 82 个受封文件，也未参与 package SHA |
| B: Claude Code Bare | 计数误差 | "manifest 33 项" | 实际 sealed file count 为 82；33 很可能来自状态四元组数量 |
| B: Claude Code Bare | 计数误差 | "finding mapping 72 行" | 实际数据行数量为 71 |
| B: Claude Code Bare | 范围误差 | test ID 范围 `T01–T50` | 实际最高为 `T49` |
| B: Claude Code Bare | 身份描述误差 | runtime identity 把 provider 写为 Anthropic | 在独立审查格式下应写 UNKNOWN；实际调用路径为 ZenMux |

以上误差属于报告撰写与证据描述层面的问题，不推翻模型最终 `GREEN_LIGHT` 判决。

## 6. Reliability and security comparison

| 维度 | A: Pi guarded | B: Claude Code Bare |
| --- | --- | --- |
| 本地 JSONL 落盘 | 成功 | 失败 |
| 本地报告落盘 | 成功 | 失败（依赖手工恢复） |
| 元数据落盘 | 成功 | — |
| Git 状态校验 | 成功 | — |
| 权限面 | 六件 guarded tools，无自由 Bash、写文件、Git、包外路径与环境变量读取 | Write/Edit/NotebookEdit/WebFetch/WebSearch 被禁用，但自由 Bash 仍使权限面大于 Pi guarded |
| Key 管理 | macOS Keychain | macOS Keychain（通过 `apiKeyHelper` 取用） |
| 工程可靠性 | 更高 | 更低 |

### 6.1 B 组运行链问题

ZenMux 日志保留完整最终回答，但 Claude Code 未将正文序列化到本地 `bare_result.json`，runner 又在收尾阶段失败并清理临时目录。该问题属于宿主与归档链，不属于模型审查失败。

## 7. Findings audit

### 7.1 权威包事实

| 项目 | 值 |
| --- | --- |
| sealed file count | 82 |
| package identity result | declared 82 / actual 82 / missing=[] / extra=[] / mismatches=[] |
| `.DS_Store` | 存在，6148 bytes，未列入 manifest，未参与 package SHA |
| cumulative finding mapping | 71 data rows |
| exact test ID range | `T01–T49` |

### 7.2 两组共同结论

- 五枚身份匹配
- A–I PASS
- P1=0, P2=0
- `GREEN_LIGHT`

### 7.3 问题分类总结

- **真实问题**：包目录存在 `.DS_Store`，且 `canonical_package_algorithm.md` 未显式排除 OS 元数据文件，形成轻微的归档卫生与复算措辞摩擦；该问题仅为 P3，不影响 82 个受封文件及 package SHA。
- **证据描述错误**：A 组把 `.DS_Store` 错写为已纳入密封清单并影响 package SHA。
- **报告撰写误差**：B 组存在 sealed file count、finding mapping 行数、test ID 范围与 runtime identity 描述误差。
- **运行链问题**：B 组本地归档失败，最终报告依赖 ZenMux 日志手工恢复。

## 8. Decision

- **默认方案**：Pi guarded
- **适用任务**：密封包外审、只读核验、身份复算、证据审计、结构化报告
- **Bare 保留用途**：需要 Claude Code 交互体验、复杂临时排查、Pi 专用工具尚未覆盖的任务
- **不再把 Bare 作为常规 Fable 二审入口**

## 9. Operating policy

1. 默认命令走已封装 runner，禁止随手裸开 Pi。
2. 保留 `thinking low`、6144 输出上限、无 session、无 context files、无 skills、无主题、无无关扩展。
3. 六件 guarded tools 为默认工具面；新增工具需单独审查。
4. 专用 ZenMux Key 保持 `$4` Credit Limit、RPM 10、TPM 300000、仅限 Fable。
5. Key 只放 macOS Keychain，不放普通环境变量。
6. 每轮必须记录 run id、开始/结束时间、费用、token、Git 状态、最终判决、报告 SHA。
7. 若本地正文为空但 ZenMux 日志存在最终回答，标记 `local_capture_failed`，从日志恢复，禁止立刻重跑全量任务。
8. 发现 P3 或其他 finding 后，必须核对原始文件与 manifest，避免把证据描述错误当成真实缺陷。

## Appendix A. Excluded diagnostic costs

以下费用记录但排除于正式 A/B 比较：

| 项目 | 费用 |
| --- | --- |
| CUN failed diagnostic 1 | `$0.677628` |
| CUN failed diagnostic 2 | `$0.106040` |
| CUN diagnostic subtotal | `$0.783668` |
| Pi smoke test | `$0.00155` |
| Bare smoke test | `$0.018295` |

未知或未单独量出的护栏烟雾费用不得猜测。

---

`FINAL_SELECTION = PI_GUARDED`
