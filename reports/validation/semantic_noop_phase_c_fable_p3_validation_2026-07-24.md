# semantic_noop Phase C：Fable P3 核验与终审准备

## 结论

本轮严格以 Fable 实际收到的 worktree diff 为审查对象，没有扩展为整个 semantic_noop 机制审查。Fable 明确给出 `GREEN_LIGHT_PHASE_C=YES`、P1=0、P2=0、P3=5；回包因 `stop_reason=max_tokens` 截断，正文真实终止于 `DIFF_CONTEXT_LIMITATIONS` 开头的 `DI`，因此不得把截断后的栏目或内容归于 Fable。

项目在完整仓库中逐项核验后，确认 P3-1、P3-2、P3-3 存在对象身份窗口并完成 fd 级加固；P3-5 原本已通过 review manifest 中的 runner SHA 间接 fail-closed，本轮补成解析前显式 SHA 锚定与稳定诊断；P3-4 的中断状态可识别、复跑可确定恢复且不会污染 index，本轮只补故障注入测试，分流为 `deferred_hardening`。当前 P1=0、P2=0，项目判断 `READY_FOR_PHASE_C_GPT_5_5_HIGH=YES`；由于 Fable 输入只包含 `tools/review_manifest.py` 的 diff，`READY_FOR_FULL_MECHANISM_REVIEW=NO`。

## 输入证据归档

1. Fable 实际输入 diff：`reports/validation/artifacts/semantic_noop_phase_c_2026-07-24/review_manifest_phase_c_worktree.diff`
   - SHA-256：`93b2efed271187a5b9053eaebe2f627c306dac02b7784f5867991896dde8ea20`
   - 范围：`tools/review_manifest.py`
   - request 中 `REVIEW_ARTIFACT_BEGIN/END` 之间的字节内容与该 diff 完全一致。
2. Fable 最终提示词：
   - 实际发送值位于 `reports/validation/artifacts/semantic_noop_phase_c_2026-07-24/request-worktree-review-low.json` 的 `.system`。
   - `.system` UTF-8 SHA-256：`fa191616bb2abe07bd51c1998e8a6c2a7ae14990421835eef9cf67cc92b34fa0`。
   - `fable_phase_c_worktree_prompt.txt` 是其基础提示词，实际 `.system` 还追加了“最终输出硬约束”；不得把基础文件单独当作最终发送值。
   - 完整 request JSON SHA-256：`b0cb6674fe02a45f419b4d1f324a01a16af6e81834748309ad9ff66c6d2c6a5f`。
3. 原始 JSON 回包：`reports/validation/artifacts/semantic_noop_phase_c_2026-07-24/response-worktree-review-low.json`
   - SHA-256：`a56080ec8e40cd884a21eabe4d255fd306f7c241678af998d00e581db6c06440`
   - response id：`32eb8bc352ba4fd183ee9eeae31b8295`
   - model：`anthropic/claude-fable-5`
   - `stop_reason=max_tokens`
   - output tokens：2600，其中 thinking tokens：1542。
4. 提取后的正文：`reports/validation/artifacts/semantic_noop_phase_c_2026-07-24/fable_phase_c_worktree_review_low_zh.md`
   - SHA-256：`7613ebcdf73b0d13ce2d22a8208a0b354aa6e069e9ce1915e43e997169cec6ff`
   - 与 response 的 text block 内容一致，仅归档文件末尾多一个 LF。
   - 原始 text block 的真实结尾为 `candidate.json。\n\nDI`；没有可恢复或可推断的截断后正文。

## 结论归属

### Fable 明确结论

- `GREEN_LIGHT_PHASE_C=YES`
- P1=0
- P2=0
- P3=5
- Fable 认为没有安全阻塞项，五项均为 P3 健壮性问题。

### 输出截断状态

- `stop_reason=max_tokens`
- `DIFF_CONTEXT_LIMITATIONS` 仅输出开头的 `DI`。
- `FINAL_REVIEW_READINESS` 未出现在真实回包正文中。
- 不得声称 Fable 明确输出了任何截断后的 limitation、readiness 或最终事项。

### 项目流程判断

- `READY_FOR_PHASE_C_GPT_5_5_HIGH=YES`
- `READY_FOR_FULL_MECHANISM_REVIEW=NO`
- 前者依据本轮完整仓库核验、窄范围加固与测试结果，不是 Fable 截断回包中的明确结论。
- 后者保持为 NO，因为 Fable 实际输入只含 `tools/review_manifest.py`，未覆盖 Phase B 写入端、Validator、共享锁实现和完整测试 diff。

## P3 分流矩阵

| P3 | 代码核验 | 是否属实 | 现有保护 | 本轮处理 | 测试 | 后续事项 |
|---|---|---|---|---|---|---|
| P3-1 candidate TOCTOU | 原实现为 `is_symlink → resolve → is_file → read_bytes`，路径检查与读取不是同一对象 | 是 | candidate raw SHA、Validator、现场 semantic comparison 会 fail-closed，但不能证明读取对象就是检查对象 | 新增受控根目录 fd 链读取：`os.open + O_NOFOLLOW + fstat`，只从同一常规文件 fd 读取 | 合法 semantic_noop；在 candidate 最终 fd open 前替换为 symlink，稳定拒绝 | 无 |
| P3-2 runner manifest symlink 链 | 原 `load_runner_evidence` 直接 `resolve → read_bytes`，未拒绝 manifest/父目录 symlink，也未约束到 Phase C runtime 根 | 是 | manifest 内路径自证与 candidate 目录约束只能绑定解析结果，不能阻止跟随 symlink | runner manifest 必须位于受控 runtime 根；从根到文件逐级 `O_NOFOLLOW`，拒绝 manifest symlink、父目录 symlink和 runtime 越界 | manifest symlink、父目录 symlink、root escape 三种专项用例 | 无 |
| P3-3 official path 锁边界 | 共享锁、锁前 symlink 检查和锁内最终 SHA 已存在，但 `read_current_official` 仍以 pathname 读取，不覆盖不遵守共享锁的检查后 symlink 替换 | 是，范围限于不协作替换者 | canonical official path、共享 writer lock、初始/最终 SHA 复核均存在 | Phase C 在锁内改用 repo 根下逐级 no-follow fd 读取；`fstat` 后从同一 fd 取字节及 SHA | 锁内 official 最终 open 前替换为 symlink时拒绝；普通 official SHA 变化仍取消提交 | 共享锁只承诺协作 writer；不扩大为全系统强制锁 |
| P3-4 summary orphan | 两次 `os.replace` 之间异常可留下“新 summary、无 manifest” | 是 | manifest 完成前不 append index；下次运行将该目录识别为 summary orphan 并覆写恢复 | 不改提交结构；新增第一次 replace 后异常的故障注入与确定性复跑测试，分流为 `deferred_hardening` | 异常后仅 summary 存在、manifest/index 不存在；复跑为 `review_summary_orphan_recovered`，index 仅一条 facts_review | 若未来需要目录级原子事务，再单独设计，不阻断本次终审 |
| P3-5 runner manifest 二次读取 SHA | 原流程二次读取后通过重建 manifest 与既有 `runner_manifest_sha256` 间接绑定，替换会 fail-closed，但诊断统一为 authority mismatch | 部分属实：安全绑定已有，诊断不精确 | review manifest 已保存原 runner SHA，重建全等会阻止绕过 | `verify_uncommitted_manifest` 将原 SHA 传入读取层；先核对 raw SHA，再解析和重算，变化稳定报 `runner_manifest_changed`；未改 schema | unindexed manifest 创建后替换 runner raw bytes，生成稳定 invalid-prior 诊断且 index 不重复 | 无 schema 扩张；不阻断终审 |

## 实际修改

- `tools/review_manifest.py`
  - 新增受控根目录下逐级 no-follow 的常规文件 fd 读取。
  - candidate、runner manifest、锁内 official 统一使用同一 fd 读取字节。
  - production 默认将 runner manifest 限制在 Phase C runtime 根；测试可显式注入独立 runner runtime 根。
  - uncommitted manifest 恢复时先核对既有 `runner_manifest_sha256`，区分 `runner_manifest_changed`。
- `tests/test_review_manifest.py`
  - 新增 candidate symlink 竞态、runner manifest/父目录 symlink、runtime 越界、official 锁内 symlink 替换、summary orphan 中断恢复和 runner SHA 二次读取诊断测试。
- `rules/review_manifest_phase_c_v0.2.md`
  - 补充 runtime 边界、父目录链、`O_NOFOLLOW`、`fstat` 与同 fd 读取要求。

未修改 Phase B official 写入语义、official facts、daily review、current 卡、总索引、weekly 或 07-23 runtime 产物。

## 测试结果

- Fable P3 定向组合：`25 passed, 110 deselected`
  - 覆盖合法 semantic_noop、candidate symlink 替换、runner manifest symlink 链与越界、official 路径替换、summary orphan、runner manifest 篡改、semantic SHA 篡改、candidate 缺失、action/outcome/reason 错配、幂等与 index 去重。
- Phase C 全部测试：`135 passed`
- 全量 pytest：`527 passed, 24 subtests passed`
- `python3 -m py_compile tools/review_manifest.py`：PASS
- `git diff --check`：PASS

## official / runtime 指纹

以下指纹在本轮修改与测试前后完全一致：

| 产物 | SHA-256 |
|---|---|
| `data/daily/300274_2026-07-23_facts.json` | `c5cf1efae2bcaacd586117ce413e3f374a54912fda5d0c81a5a5f90fad3eab27` |
| 07-23 semantic_noop runner manifest | `adf11ffabbde4d5c6afd90e8e0d11ecc924f7dcc680aca8e9c8b32e3d707bf3d` |
| 07-23 Phase C review manifest | `d4717c4805acdd4915a6ed2dbcb43af861008f7faa5bf102ebf5c4b46a337677` |
| 07-23 Phase C review index | `e2d498694cc14344a91f3157c489e0dfd595e47fc7f15030b6d1d7ef89c916b2` |

## 最终门

- P1：0
- P2：0
- deferred_hardening：P3-4 目录级整体原子化；现有 fail-closed 与确定性恢复已经专项验证。
- Phase C gpt-5.5/high 最终审查：具备送审条件，但最终审查本身仍须由实际 session JSONL 证明 `model=gpt-5.5`、`reasoning_effort=high`。
- Git：本轮不执行 commit 或 push。
