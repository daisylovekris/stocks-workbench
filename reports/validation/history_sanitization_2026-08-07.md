# 历史脱敏迁移记录（2026-08-07）

## 一、背景

GitHub Push Protection 在推送 `workbench/mainline-2026-07` 时拦截历史凭据。核验后确认同一份 Pi 审查事件日志写入了 4 个凭据环境变量值：

- `OPENROUTER_API_KEY`
- `CUN_API_KEY`
- `JOYAGENT_API_KEY`
- `SENSENOVA_API_KEY`

4 个历史凭据均已失效；2026-08-07 由用户逐一确认。本报告不保留凭据值或值前缀。

污染文件：
`reports/validation/artifacts/sunday_weekly_pipeline_v0.1_fable_final_review_2026-07-28/ab_runs/pi-20260728-230214-12038/pi_events.jsonl`

由 `bcda233a`（07-29）引入。首次失败 push 前远端分支不存在，`origin/main` 从未包含污染对象。

## 二、限定范围重写

在隔离克隆中重写 `bcda233a^..HEAD`，仅修改污染事件日志内的 4 个历史凭据值：

- 重写提交数：**8**
- 保持原 SHA 的边界前祖先：**87**
- 重写前后等价 HEAD 的树差异路径：**1**
- 唯一差异路径：上述 `pi_events.jsonl`
- 当前正式 refs 中 4 个历史凭据精确值残留：**0**

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

该表是旧身份解释的单一迁移映射权威。

## 四、重绑与 sealed 边界

迁移提交 `5b3a27c` 修改 32 个结构化 Git 绑定文件：

- `memory/*`：12
- `reports/validation/*.md` 活跃验证报告：13
- artifact 元数据文件：7

随后 `a8c479c` 重算 `memory/project_state.md` 与 `memory/phase_registry.md` 中受影响的 `raw_sha256` / `snapshot_commit`，并落盘本迁移映射。

历史 sealed/archive 采用**字节保留**契约：

- 10 个 immutable sealed/archive 文件保留历史旧身份文本；其中 9 个含完整旧 SHA，1 个只含旧 SHA 短前缀。
- 本迁移映射报告是第 11 个允许出现旧身份文本的文件。
- 所有 current operational/live 记录必须使用迁移后身份；allowlist 外任何完整旧 SHA 或独立 7–12 位旧前缀均为硬失败。
- `tools/validate_history_sanitization.py` 从本报告现场解析 8 对映射，不在工具源码内硬编码旧 SHA，并执行上述硬门。

r5 sealed 包独立复算：

- sealed members：17
- member size/SHA mismatch：0
- declared package SHA：`64dfa32ad9573bfdea074b7731c2dace324b693bc8e47dcbfe4dc8d37a3f9bfd`
- recomputed package SHA：同上

因此 sealed bytes 保持原始历史证据身份，不做 repack。

Fable 外审最终裁决：

- `SEALED_CONTRACT_VERDICT=ACCEPT`
- `PREFIX_ONLY_ARCHIVE_EXCEPTION=ACCEPT`
- `OPERATIONAL_IDENTITY_GATE=PASS`
- `P1_COUNT=0`
- `P2_COUNT=0`
- `P3_COUNT=1`（仅 CI workflow 延后）

审查归档：
`reports/validation/artifacts/history_sanitization_fable_closure_2026-08-07/`

## 五、本机旧对象清理

远端 SHA 已与本地 sanitized branch 对齐且两份受限权限污染备份存在后，生产仓执行：

- `git reflog expire --expire=now --expire-unreachable=now --all`
- `git gc --prune=now`

结果：

- reflog 旧身份命中：16 → 0
- 原污染提交对象：present → absent
- HEAD 未变化
- 远端 sanitized branch 未变化
- index 保持为空

污染备份继续本地隔离：

- `/tmp/stocks-backup.4TJk7J`（0700）
- `/Users/wongdaisy/Mimo-Lab/_quarantine/stocks-contaminated-20260807-0730`（0700）

生命周期：远端验证完成后保留 7 天隔离期，**2026-08-14** 复核后删除；禁止上传云盘或远端仓库。

## 六、防复发硬化

已推送的首版扫描器存在一处历史扫描缺口：仅比较 `BASE..TIP` 首尾净 diff，会漏掉“中间提交写入、后续提交删除”的内容。

本轮 hardening 修正为：

- `--commits` 使用 `git rev-list --objects REVSET`，扫描 revision set 内 newly reachable blobs；
- add-then-delete 中间 blob 仍会被扫描；
- commit message 同时扫描；
- pre-commit 扫描 staged ACMR blobs，不因删除旧内容产生误报；
- pre-push：新远端 ref 扫 tip 历史，已有 ref 扫 `remote_sha..local_sha`；
- pre-push 同时执行 history-sanitization identity validator；
- 诊断仅输出路径/对象、rule ID、行号，不输出值片段；
- 仅精确 redaction marker、精确环境变量引用与明确 synthetic placeholder 可豁免；
- 已增加负向测试，证明 redaction/env-reference 后拼真实形态 synthetic secret 仍会被拦截。

验证：

- scanner + history-sanitization contract dedicated tests：**12 passed**
- full tests：**642 passed + 28 subtests**
- current sanitized history：`SECRET_SCAN_CLEAN`
- history identity validator：`OPERATIONAL_OLD_IDENTITY_FILE_COUNT=0`
- allowed historical reference files：11
- `git diff --check`：PASS

## 七、CI 延后项

`.github/workflows/secret-scan.yml` 已在本地准备，复用同一 scanner + history identity validator。

当前 GitHub token 缺少 `workflow` scope，因此本轮 hardening push 明确排除该文件。期间保护层：

1. pre-commit
2. pre-push
3. GitHub Push Protection

Fable 认可该临时安排：`READY_FOR_PUSH_WITHOUT_WORKFLOW=YES`。

open item：

- owner：Lucien + 用户
- 复核日期：2026-08-14
- 条件：GitHub token 获得 `workflow` scope 后单独提交并推送 `.github/workflows/secret-scan.yml`，首次 CI 必须 green。

## 八、AgentDock 停摆任务

原无人值守任务 `tsk_a165c12c35eff141` 的 worker 在 preflight 后停摆，但任务卡长期保持 `active`。迁移随后经用户授权由 Codex 完成。

该 AgentDock 任务现已置为 `blocked`，原因固定为：worker stalled、工作已由独立路径完成、任务永久 superseded，禁止恢复以避免重复执行。

监控事故与通用修复记录保存在本地 `AgentDock/PITFALLS.md`。

## 九、最终状态

- 历史重写：PASS
- 8-commit boundary：PASS
- 87 ancestors preserved：PASS
- remote sanitized branch：PASS
- current refs secret residue：0
- production reflog/object purge：PASS
- operational old identity gate：PASS
- sealed package identity：PASS
- Fable sealed-contract review：ACCEPT
- scanner add-then-delete gap：CLOSED
- P1：0
- P2：0
- P3：1（CI workflow deferred）
