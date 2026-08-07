# 历史脱敏迁移记录（2026-08-07）

## 一、背景

GitHub Push Protection 在推送 `workbench/mainline-2026-07` 时拦截：历史中存在 OpenRouter API Key。核验后发现实际是 pi 审查器把整个 `PI_*` 环境变量块写进了事件日志，共 4 把凭据（环境变量名）：

- `OPENROUTER_API_KEY`
- `CUN_API_KEY`
- `JOYAGENT_API_KEY`
- `SENSENOVA_API_KEY`

值均为平台颁发格式（OpenRouter / CUN / JoyAgent / Sensenova），已全部脱敏，本文件不保留任何前缀字面量。

均位于同一文件：
`reports/validation/artifacts/sunday_weekly_pipeline_v0.1_fable_final_review_2026-07-28/ab_runs/pi-20260728-230214-12038/pi_events.jsonl`，
由 `bcda233a`（07-29）引入，重写前仍存在于 HEAD。

`origin/main` 从未包含该文件（远程零泄露）。

## 二、重写

在隔离克隆中执行 range 限定重写（`bcda233a^..HEAD`），仅脱敏上述 4 把凭据：

- 重写提交数：**8**（`bcda233a` + 7 个后代）
- 保留旧 SHA 的祖先：**87**
- 全历史与 HEAD 凭据残留：**0**
- 新旧 HEAD 树差异：仅 `pi_events.jsonl` 一个文件（6 行）

## 三、旧→新提交 SHA 映射

| 旧 | 新 |
|---|---|
| 32426e2afde730c2313d7c0ec5dd150c67ed3877 | 57f1976ba2f09bf3a9ec7c22abdb1c6425cdac6f |
| 6d0d2251810b9d04d78386f7bc6271e5233e9611 | 6f7d4795aabc955481b9db79483ec617138f2316 |
| 6432855b001dee50332ecd402affa8421c3cab81 | 1ecfb2fd932230ac86bd890797c15fa7fa37b431 |
| f38b563502fa7e098f8420062c5b71f9fb231fdf | b4af83aa18ffa2520630d484aa5a26e9590a2876 |
| 844d8b541d7fd3165ce9e9a1725f207e1764da51 | 5909dd40976ad81f479c8e73b783829a503c83e8 |
| e1723c26efb76bee2aa2b879233a738f4e7e2323 | d5d971d4e45dc0104f949edf08357703afdcbc6a |
| d33a7cfd39a8608524096021ae581a6825bc5cc4 | 5e8c1a39dcc81697e3d46ff244162d64290e2b11 |
| bcda233a3c06a1f875a01843d2b3f5a4cec2c1ca | 5651b07b40bfb5c52bbccffbc031fbe712cffe4c |

## 四、重绑与保留边界

**已重绑（迁移提交 5b3a27c）**：32 个文件中的结构化 git 绑定——12 个活文档
（`memory/*`）、14 个验证报告（`reports/validation/*.md`）、6 个包外清单
（`design_manifest.json`、`closure_manifest.json`、`review_meta.json` 的
`base_head` / `reviewed_head` / `implementation_commit` 等字段）；另在
`project_state.md` / `phase_registry.md` 中按迁移提交重算受影响文件的
`raw_sha256` 与 `snapshot_commit`。

**保持字节不变（sealed 成员与审查档案）**：r5 密封成员、cross_method 审查档案
（fable_raw/formal_prompt/pi_events/run_meta）等密封证据原样保留，包身份
（如 r5 `design_package_sha256=64dfa32a…`）不受影响；其中记录旧 SHA 的引用
为历史事实，按本附录映射解析。

## 五、验证

- 全历史 4 把凭据残留 0；HEAD 残留 0。
- 重写 8 枚 / 保留 87 枚。
- 除 `pi_events.jsonl` 外无任何文件内容变化（树级 diff 确认）。
- r5 等密封包身份复算不变。

## 六、未做事项

- 未放行（GitHub 侧未点 allow）。
- 切换前生产仓库 HEAD/refs/未跟踪文件保持原样。
- push 在切换并验证后执行。
