* 审查对象：Phase B 受控正式 facts 落盘
* 审查日期：2026-07-16
* 审查性质：首次只读终审
* 结论：暂缓封箱
* 阻断项：P1×2、P2×1

结论

* 暂缓封箱

我独立复跑了关键测试，不引用报告数字：

* 窄范围四个测试文件：`250 passed, 22 subtests passed`
* 全量测试：`356 passed, 22 subtests passed`
* 07-13 facts/review Validator：`PASS | P0=0 | P1=0 | P2=0 | P3=0`
* 07-14 facts/review Validator：`PASS | P0=0 | P1=0 | P2=0 | P3=0`
* `git diff --check`：通过
* 07-13/07-14 facts SHA 复查未变：
  * `888cdaaa...` `data/daily/300274_2026-07-13_facts.json`
  * `63d13699...` `data/daily/300274_2026-07-14_facts.json`
* 本轮没有执行 `git add/commit/push`，没有修改文件。

P1/P2

P1-1：`generate_daily_facts.py` 仍暴露未受 `--write-official` 控制的写入面。

* 文件/位置：
  * [tools/generate_daily_facts.py](/Users/wongdaisy/Mimo-Lab/stocks/tools/generate_daily_facts.py:238)
  * [tools/generate_daily_facts.py](/Users/wongdaisy/Mimo-Lab/stocks/tools/generate_daily_facts.py:1814)
  * [tools/generate_daily_facts.py](/Users/wongdaisy/Mimo-Lab/stocks/tools/generate_daily_facts.py:1831)
* 真实触发路径：独立调用 generator CLI 时，`--output` 由用户任意提供；只要未传 `--dry-run` / `--no-write`，且候选满足写入条件，就会进入 `promote_candidate_to_official(...)`。该调用还设置了 `enforce_canonical_path=False`。
* 影响：Phase B 要求“正式 facts 落盘必须显式 `--write-official`、official 路径只能由 symbol/date 推导、用户不能提供任意 official 输出路径”。当前 generator 仍可能作为旁路写入实现存在；如果用户把 `--output` 指向真实 `data/daily/<symbol>_<date>_facts.json`，就不是 runner 的显式 `--write-official` 路径。
* 最小修补方向：generator 独立 CLI 默认只允许 `--dry-run` / `--no-write` / 候选输出；正式 official 写入只保留 runner `--write-official`。如果必须保留 generator 写入能力，也应要求显式写入旗标，并强制 canonical path enforcement，且不得接受任意 `--output` 作为 official 目标。

P1-2：写后 Validator 失败或写后 bytes 不一致时，official 已改变但 manifest 没有记录真实写入事实。

* 文件/位置：
  * [tools/official_facts_transaction.py](/Users/wongdaisy/Mimo-Lab/stocks/tools/official_facts_transaction.py:397)
  * [tools/official_facts_transaction.py](/Users/wongdaisy/Mimo-Lab/stocks/tools/official_facts_transaction.py:406)
  * [tools/run_daily_facts_after_close.py](/Users/wongdaisy/Mimo-Lab/stocks/tools/run_daily_facts_after_close.py:1085)
* 真实触发路径：我用临时 repo 构造了两个场景：
  * 写后 Validator 第二次失败：official 已创建，CLI code=1，但 manifest 为 `reason_code=runner_unexpected_error`，`write_action=null`，`official_sha256_after=null`。
  * 写后 bytes 被篡改导致不一致：official 已变成 tampered bytes，CLI code=1，但 manifest 同样为 `runner_unexpected_error`，`write_action=null`，`official_sha256_after=null`。
* 影响：这违反“若实现无法安全回滚，应明确报告 official 已改变但写后验证失败，不得伪装成未写入”。后续人工处理缺少 official path、after SHA、write_action、before/after 状态证据。
* 最小修补方向：transaction 在 `_write_bytes_locked` 之后、post-write Validator 之前应形成“已改变 official”的结构化结果；post-write failure 不应直接裸抛给 runner generic exception。runner 应输出专用 `reason_code`，保留 `official_path`、`official_sha256_before`、`official_sha256_after`、`candidate_sha256`、`write_action=created_postcheck_failed` 或等价状态、`official_validator_after` 错误。

P2-1：partial 量比状态白名单与 Phase B 文档/本轮要求不一致。

* 文件/位置：
  * [tools/official_facts_transaction.py](/Users/wongdaisy/Mimo-Lab/stocks/tools/official_facts_transaction.py:37)
  * [rules/run_daily_facts_after_close_phase_b_v0.2.md](/Users/wongdaisy/Mimo-Lab/stocks/rules/run_daily_facts_after_close_phase_b_v0.2.md:45)
  * [tests/test_run_daily_facts_after_close.py](/Users/wongdaisy/Mimo-Lab/stocks/tests/test_run_daily_facts_after_close.py:81)
* 真实触发路径：代码允许 `manual_confirmed` 进入 partial official 准入；文档和本轮要求写的是“量比已确认或 `derived_confirmed`”，即 `confirmed` / `derived_confirmed`。
* 影响：策略边界不清。当前测试还把 `manual_confirmed` 作为 eligible partial 的正例，容易把“量比人工确认”扩展成 Phase B partial official 自动准入。
* 最小修补方向：要么把代码收窄到 `confirmed` / `derived_confirmed`，并调整测试；要么明确更新 Phase B 文档和准入说明，把 `manual_confirmed` 作为允许状态并要求完整 `manual_verification`。

十一项核对

1. 权限边界：runner 本身满足二选一：`--dry-run` / `--write-official`，`--now` 仅 dry-run，正式模式使用真实北京时间；未见 launchd 创建、review/current/index/weekly 写入。但 generator 独立 CLI 仍是 P1 写入旁路。

2. 候选准入：runner 链路为 generator dry-run → marker → candidate bytes → 身份门 → Validator → official transaction；marker 恰好一条、symbol/date/source_date、有限数、exit/status mismatch、未知状态、NaN/Inf/bool/date mismatch 均有门禁/测试覆盖。未发现第二次远程抓取。

3. partial 策略：白名单字段集中在 `market_indices / sector_context / disclosure_status / news_policy_context`；核心 quote、换手率、量比、Validator 门禁存在。但 `manual_confirmed` 是否可准入与要求不一致，列 P2。

4. existing official：created / identical_noop / conflict_blocked / sealed_blocked / manual_blocked / invalid JSON / symbol/date mismatch / symlink 均有实现或测试支撑；不做覆盖、合并、择优、历史迁移。sealed/manual 代码支持 top-level 与 run 形态，但测试主要覆盖 top-level，作为 P3 观察。

5. 共享事务：核心锁内顺序基本成立：锁内重读 existing、expected SHA、Validator、absent/identical/conflict、同目录临时写、fsync、replace、目录 fsync、写后读取和 Validator。generator 已调用共享 transaction，但仍保留独立写入入口，见 P1-1。

6. 写后验证失败：不合格。official 已改变时 manifest 没有记录 write_action/after SHA，列 P1-2。

7. manifest 故障边界：runtime bundle/manifest 失败时不回滚 official，且已有测试覆盖 `official_written_manifest_failed`、official path/after SHA、不残留 `.tmp`。这一项通过。

8. 正式幂等：dry-run success 不算正式完成；`write_official=true` 且 `write_action=created/identical_noop` 才算完成；损坏 manifest 会跳过并记录 diagnostic；previous_run_id 不串 symbol/date/mode。通过。

9. 并发：共享 official lock 覆盖两个 writer 序列化、后者重读、stale SHA stop、异常后后续写入可继续。runner 单实例锁存在。未发现锁反转；但 generator 旁路仍会参与写入面，见 P1-1。

10. 测试与演练：正式写入测试使用临时 repo/runtime；我未在真实仓库运行 `--write-official`。全量 `356 passed, 22 subtests passed`；07-13/07-14 SHA 未变；受保护 review/current/index/weekly 没有 diff；无 `.tmp` 残留。

11. Git 边界：本轮 diff 中目标相关文件包括 runner、generator、official transaction、测试、Phase B doc。`tools/codex-auto.sh` 和 `repo_harness_readonly_research_notes.md` 确实存在于工作树状态中，但已按要求排除出本轮判断。未暂存。

P3

* [tools/run_daily_facts_after_close.py](/Users/wongdaisy/Mimo-Lab/stocks/tools/run_daily_facts_after_close.py:2) 模块 docstring 仍写“Phase A read-only”，与 Phase B official 写入模式不一致，非阻断但建议同步。
* sealed/manual official 的实现支持多种形态，但测试只覆盖 top-level flag；建议补 run-level sealed/manual 格式回归。
* `official_facts_transaction.py` 是未跟踪文件；提交前需要确认加入本轮提交范围，否则 runner import 会依赖未入库文件。

最终判定

Phase B 目前不具备归档和提交条件；至少需要先封闭 generator 非 `--write-official` 写入旁路，并修正写后复核失败的 manifest 证据语义。

<oai-mem-citation>
<citation_entries>
MEMORY.md:2-35|note=[prior Phase A runner marker and runtime boundary context]
</citation_entries>
<rollout_ids>
</rollout_ids>
</oai-mem-citation>
