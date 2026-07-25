SEMANTIC_NOOP FULL MECHANISM — 第三方独立盲审（Kimi Code 会话）

============================================================
MODEL_RECORD
============================================================
- model: Kimi Code CLI agent（具体模型版本 UNKNOWN；输出文件名中的 "k3" 为用户命名，本会话无法自行证明）
- provider/display name: UNKNOWN（只能自证当前为 Kimi Code CLI 会话；provider 字符串无法自证）
- thinking_effort: high（会话启动系统通知所示）
- session_id: UNKNOWN（会话未向审查者暴露可证明的 session id）
- 开始时间: 2026-07-25T17:14:06Z（会话环境时间戳）
- bundle package SHA 核验结果: PASS
  - package_sha256 = 0980515c7450eb4fbb2b357e3894f38d911dbdc714571c4d5b030be4e8c557a4，与 bundle_package_sha256.txt 及任务声明一致
  - base_head = 877e20aa8b1601ed92ed934f8bcd8300c5039845，与 review_bundle_manifest.json 一致
  - scoped_patch_sha256 = 01cca38f18eeb3567e8c6ff5470c72985ad500ce38b204687be0ed5dffc925cf，full_mechanism.patch 与 phase_b_scoped.patch 复算一致且两文件逐字节相同（diff -q 通过）
  - manifest 所列 18 个文件全部在场，逐个复算 SHA-256 全部匹配，无缺失、无不符
  → 未触发 INPUT_INTEGRITY_FAILURE

============================================================
审查范围与方法
============================================================
仅使用 bundle 内材料：full_mechanism.patch（= phase_b_scoped.patch）、snapshots/{rules,tools,tests}、scope_notes.md、test_baseline.txt、test_execution_result.txt、protected_fingerprints.json、credential_scan.txt。未读取父目录、主仓库工作树、Git 历史、外部网络或任何其他 reviewer 结果。未修改 bundle 内任何文件。

逐字执行的审查提示词（common_review_prompt.txt）要求覆盖：Phase B/Phase C 调用链闭合、semantic_noop 与 identical_noop 互斥、candidate 与 official 双方校验、规范化语义比较、raw/semantic SHA 规则、no-follow 身份保护、锁/TOCTOU 行为、runtime index 幂等、fail-closed 的 action/outcome/reason 组合，并报告 P1/P2/P3、scope limitations、test gaps 与 SAME_BUNDLE_READY_FOR_DUAL_REVIEW 结论。

逐文件完整阅读：official_facts_transaction.py（693 行）、run_daily_facts_after_close.py（1251 行）、review_manifest.py（1667 行）、generate_daily_facts.py 写入事务/CLI/run/marker 全链路及 build_facts_pack 等辅助函数、两份规则文件、patch 全部 781 行；三个测试文件按入口映射覆盖并抽查关键用例。

============================================================
机制核验结论（主链与旁链逐项）
============================================================
[PASS] Phase B 调用链闭合：runner 门（时间/日历/cutoff）→ 锁内 official 快照（run_daily_facts_after_close.py:936）→ runner 单实例锁 → generator 仅以 `--dry-run --emit-runner-marker` 调用（:446-461）→ marker 单例解析 + 敏感键拒绝（:508-543）→ 候选身份门（:550-581）→ facts Validator → partial 白名单 → promote_candidate_to_official（锁内重读 + expected_sha256 TOCTOU 复核）→ runtime bundle 按 stdout→stderr→candidate→summary→alert→manifest 顺序落盘（:783-802），manifest 为最终提交标记。
[PASS] semantic_noop / identical_noop 互斥：字节相等先判 identical_noop（official_facts_transaction.py:512）；字节不同才进入语义比较（:528）。Phase C 侧 semantic_noop 强制 official_bytes_equal_candidate 必须为 False（review_manifest.py:651），identical_noop 强制 after_sha == candidate_sha256（:632），同一 manifest 不可能同时满足两套。
[PASS] 双方 Validator：candidate validator_before 必须先通过（official_facts_transaction.py:464-483），official validator 通过且 semantic_equal 才允许 semantic_noop（:543-563）；official 未过 Validator 一律 conflict_blocked 并保留诊断。
[PASS] 规范化语义比较：白名单固定六路径（:42-49），不可递归扩张；身份门要求 symbol/trade_date 与参数一致且 schema_version 为 str 且双方相同（:134-142）；六路径双方均存在、均为 str、均通过 vre.parse_timezone_datetime（:149-176）；semantic_json_bytes 使用 UTF-8 + sort_keys + 固定 separators + allow_nan=False（:80-89）；semantic_equal 要求 dict 相等且 semantic SHA 相等（:185-188）。int/float/bool 类型差异（Python dict 相等但 JSON 字节不同）由 SHA 复核兜底，NaN/Inf 由 allow_nan=False 兜为 conflict，均 fail-closed。
[PASS] raw/semantic SHA 规则：raw SHA 取自 committed 字节，semantic SHA 取自删路径后的确定性序列化，二者分列，不覆盖既有 official_sha256_* 字段；runner manifest 新增 comparison 字段（run_daily_facts_after_close.py:692, 1083, 1112），summary 仅追加 comparison_mode 展示行（:762）。
[PASS] no-follow 身份保护：Phase C 对 runner manifest、committed candidate、锁内 official 均走 _read_regular_file_beneath 的 O_NOFOLLOW fd 链 + fstat 常规文件确认 + 同 fd 读字节（review_manifest.py:378-460）；official 路径/父目录 symlink 前置拒绝（:1471-1472）；Phase B 侧 canonical 路径推导、符号链接拒绝与仓库逃逸拒绝（official_facts_transaction.py:192-219）。
[PASS] 锁/TOCTOU：Phase B 先快照 expected_sha256，事务锁内 read_locked_official 复核，变化即 conflict_blocked/official_conflict（official_facts_transaction.py:413-434）；Phase C 锁顺序 review lock → official lock（初读）→ 无锁构建 → official lock（最终复核+提交+index 追加）（review_manifest.py:1474-1664），SHA 变化即 official_changed_during_generation 取消提交并清理临时目录。ofl 模块本体不在 bundle，见 SCOPE_LIMITATIONS。
[PASS] runtime index 幂等：尾部半行/空行/非法 JSON/未知 schema 全 fail-closed；重复同内容行去重、冲突行拒绝；review_already_exists / review_index_recovered（重推导全等校验 verify_uncommitted_manifest）/ summary 孤儿恢复 / invalid 唯一后缀记录 / supersedes 派生，均有对应实现与测试。
[PASS] fail-closed 矩阵：PHASE_B_WRITE_SEMANTICS（review_manifest.py:189-227）覆盖 patch 可产生的全部 (write_action, reason_code) 组合——除发现 P2-1 所述的一个组合缺口；outcome、official_changed、after/before/candidate SHA 交叉校验齐备（:590-636）。
[PASS] Phase B→C 真实集成：semantic_noop runner manifest 被 Phase C 以真实 Validator 接受（测试 test_phase_b_semantic_noop_manifest_is_accepted_by_phase_c_with_real_validator），且双方共用同一 oft.build_semantic_comparison（测试断言模块级 identity）。
[PASS] 幂等重跑主链：semantic_noop 完成后同任务重跑 → already_completed、generator 不再调用、official 字节不变（测试 test_write_official_only_approved_timestamps_differ_is_semantic_noop 的 rerun 段）。
[PASS] wrote_file 语义修正：generate_daily_facts.py:1861 改为 result.official_changed，identical_noop/semantic_noop 均为 wrote_file=false，created_postcheck_failed 为 true，与规则 v0.2 L102 一致，并有子测试覆盖四种组合。

============================================================
FINDINGS
============================================================

------------------------------------------------------------
P2-1 semantic_noop 完成记录 × manifest bundle 失败 → 同任务重跑死锁，且产物组合落在 Phase C 矩阵之外
------------------------------------------------------------
- severity: P2
- 文件/位置:
  - snapshots/tools/run_daily_facts_after_close.py — persist_terminal_bundle() L826-836（official_was_written 判定集合不含 "semantic_noop"）
  - snapshots/tools/run_daily_facts_after_close.py — scan_previous_runs() L399-404（completed 只看 write_action ∈ {created, identical_noop, semantic_noop}，不看 outcome/manifest_bundle_failed）
  - snapshots/tools/review_manifest.py — PHASE_B_WRITE_SEMANTICS L189-227（无 ("semantic_noop", "official_written_manifest_failed") 组合；"manifest_write_failed" 不在 allowed_reasons）
- 被破坏的安全不变量: 失败与重跑语义——"损坏/失败的 manifest 不阻断安全重跑；同一任务的最新合法正式记录才参与幂等"（规则 v0.2 L116）；所有可产出的 completed-class (write_action, reason_code) 组合必须在 Phase C 语义矩阵内有定义，保证 B→C 交接闭合。
- 最小触发场景:
  1. `--write-official`（historical_backfill + 过去日期 + reason），official 已存在且仅六个白名单时间戳不同 → 事务返回 semantic_noop / official_unchanged / official_semantically_identical；
  2. persist_terminal_bundle 写 bundle 中途失败（如 summary 写冲突，与测试 install_context_collision(monkeypatch, "summary") 同类注入），但异常路径的 atomic_write_json(ctx.manifest_path) 成功；
  3. 落盘 manifest 为：write_action="semantic_noop"、outcome="failed"、reason_code="manifest_write_failed"、manifest_bundle_failed=true、stage="finished"；
  4. 同 (symbol, target_date, mode) 重跑：scan_previous_runs 命中该 manifest（write_official=true、dry_run=false、write_action="semantic_noop"）→ completed=true → outcome=skipped / already_completed，exit 0，generator 不再执行；
  5. Phase C 读该 manifest：reason_code "manifest_write_failed" 不在矩阵 allowed_reasons → runner_manifest_reason_code_invalid → 只能生成 incident_review（runner_manifest_invalid）。
- 实际影响: 同一任务被一条"写动作算完成、终态却是 failed"的记录永久阻断：Phase B 不再重跑，Phase C 不可能产出正常 facts_review。对历史日期，today_after_close 以当天为目标，无法用作替代 mode，实际无自动收敛路径，需人工删除失败 run 目录。全程 fail-closed（无误写、无误批），但恢复语义断裂，且 incident 原因 runner_manifest_invalid 对"manifest 本身 schema 合法"的情形具有误导性。对照组：created 与 identical_noop 的 bundle 失败分别产生 official_written_manifest_failed，均在矩阵内（review_manifest.py:192-200）；唯独 semantic_noop 因 persist_terminal_bundle 的 official_was_written 集合不含它而落到矩阵外——这是本 patch 在 scan_previous_runs 完成集合中加入 semantic_noop 时未同步处理的组合。
- 最小修正方案（二选一，建议 a）:
  a. persist_terminal_bundle 的 official_was_written 集合加入 "semantic_noop"（official 存在且字节未变，与 identical_noop 同构），使失败记录产
     生 reason_code=official_written_manifest_failed；同时在 PHASE_B_WRITE_SEMANTICS 增加 ("semantic_noop", "official_written_manifest_failed") → outcomes={official_unchanged}、official_changed=False、after_sha_required=True；
  b. scan_previous_runs 的 completed 判定附加 `manifest.get("manifest_bundle_failed") is not True`（至少对 semantic_noop 记录），让失败记录不计完成、重跑可收敛。
- 应新增/强化的测试:
  - runner：semantic_noop + summary 冲突注入，断言首轮 reason_code/exit，重跑不被 already_completed 阻断（或断言补偿组合被 Phase C 接受）；
  - Phase C：("semantic_noop","official_written_manifest_failed") 组合的矩阵接受/拒绝测试（按所选修正）。

------------------------------------------------------------
P3-1 scan_previous_runs 判定 semantic_noop 完成时不核验 committed candidate.json；其事后丢失造成第二类同任务死锁
------------------------------------------------------------
- severity: P3
- 文件/位置:
  - snapshots/tools/run_daily_facts_after_close.py — scan_previous_runs() L399-404
  - snapshots/tools/review_manifest.py — validate_semantic_noop_evidence() L707-712（candidate 缺失即 runner_manifest_semantic_candidate_missing）
- 被破坏的安全不变量: 幂等完成记录应与该记录后续被 Phase C 使用所需的证据整体性一致；否则"完成"记录实际不可用。
- 最小触发场景: semantic_noop 正常完成（manifest 合法）；随后 runtime run 目录内 candidate.json 被删除或损坏（runtime 清理、手工整理、备份还原缺文件）；同任务重跑 → already_completed；Phase C → 非法 runner evidence → incident_review。
- 实际影响: 与 P2-1 同类的收敛死锁，但触发需要 bundle 外的文件丢失事件；保持 fail-closed。对 created/identical_noop 无此耦合（Phase C 不需要 committed candidate）。
- 最小修正方案: scan_previous_runs 对 write_action="semantic_noop" 的候选完成记录附加同目录 candidate.json 的存在性与 candidate_sha256 校验，不符则不计完成（安全重跑）；或在运行手册明确该情形的人工恢复步骤。
- 应新增/强化的测试: 删除/篡改 candidate.json 后重跑的行为断言（不计完成并安全重跑，或明确断言阻断并记录人工步骤）。

------------------------------------------------------------
P3-2 generator 独立 CLI --write-official 丢弃事务的 write_action/outcome/reason_code，冲突/封锁时仍输出 facts 层 "success"
------------------------------------------------------------
- severity: P3（pre-existing：补丁前 `should_write = result.write_action in {"created","identical_noop"}` 同样丢弃；本 patch 未改变该旁链）
- 文件/位置: snapshots/tools/generate_daily_facts.py — write_generated_facts_transaction() L1850-1865（只取 result.official_changed 与 official_sha256_after）与 run() L2129-2142（exit_code/status 仅由 facts 的 run_status 派生）
- 被破坏的安全不变量: 规则 v0.2 L102——完成/冲突语义以 write_action、outcome、reason_code 为准；独立 CLI 是规则允许的三条入口之一（L24），却不承载这三个字段。
- 最小触发场景: 直接 `python3 tools/generate_daily_facts.py --write-official --symbol ... --date ...`，official 已存在且业务字段不同 → 事务 conflict_blocked（未写任何字节）→ CLI 输出 {"status":"success","exit_code":0,"wrote_file":false,"output":null,"output_sha256":<existing sha>}。sealed_blocked/manual_blocked/not_eligible 同理。
- 实际影响: 无写入安全风险（事务已阻断，fail-closed）；但独立 CLI 的脚本化调用方看到 exit 0 + success，冲突信号完全丢失。runner 主链不受影响（runner 只用 --dry-run marker）。
- 最小修正方案: RunOutcome 增加 write_action/reason_code（或 transaction_result）字段，--write-official 分支在 CLI JSON 中输出；conflict/blocked 类结果给非 0 exit。
- 应新增/强化的测试: 独立 CLI --write-official 对冲突 official 的端到端测试，断言 exit code 与输出包含事务语义字段。

------------------------------------------------------------
P3-3 partial 候选命中 semantic_noop 时 runner 层 needs_manual_review=false，与相同 facts 内容命中 identical_noop 时不一致（规则认可的语义，记录为一致性观察）
------------------------------------------------------------
- severity: P3
- 文件/位置:
  - snapshots/tools/official_facts_transaction.py — promote_candidate_to_official() semantic_noop 分支 L547-563（outcome 固定 "official_unchanged"）vs identical_noop 分支 L513-527（outcome 随 candidate_status 为 "partial"）
  - snapshots/tools/run_daily_facts_after_close.py — finish_manifest() L718（needs_manual_review 由 outcome 派生）
- 被破坏的安全不变量: 无强不变量被破坏——规则 v0.2 L66 固定 semantic_noop 的 outcome=official_unchanged，L114 明确 official_unchanged 不代表批准且仍按 facts 未决项进入审查，Phase C 从 facts 独立重推 needs_manual_review（review_manifest.py:927-943）。属于规则认可语义下的一致性缺口。
- 最小触发场景: partial 候选（缺失项均在白名单）+ official 仅六时间戳不同 → semantic_noop → runner manifest outcome=official_unchanged、needs_manual_review=false、exit 0；同一 facts 内容若字节相同则 identical_noop → outcome=partial、needs_manual_review=true、exit 2。
- 实际影响: runner 层人工复核/告警信号对同一 facts 内容不一致；Phase C 兜底正确，不会升级为 ready_for_human_review。
- 最小修正方案: 保持 outcome=official_unchanged 不变，runner 在 semantic_noop 且 candidate_status="partial" 时按 partial_write_policy.needs_manual_review 置位 manifest 的 needs_manual_review（Phase C 矩阵无需变动）。
- 应新增/强化的测试: partial 候选 + semantic_noop 的 runner 层 outcome/needs_manual_review 断言，以及对应 Phase C review_state 断言。

无 P1 发现。

============================================================
SCOPE_LIMITATIONS / DIFF_CONTEXT_LIMITATIONS / UNPROVEN
============================================================
- SCOPE_LIMITATION: tools/official_facts_lock.py 不在 bundle。锁获取/释放、stale lock、read_locked_official 的 expected_sha256 语义（如 expected=None 时 official 存在的行为）、跨平台 flock 行为无法验证；相关锁/TOCTOU 结论基于调用点契约与测试声明。
- SCOPE_LIMITATION: tools/validate_review_chain.py 不在 bundle。facts Validator 对 NaN/未知字段/schema_version 的具体判定无法独立验证。
- SCOPE_LIMITATION: tools/volume_ratio_evidence.py 不在 bundle。parse_timezone_datetime 的接受域（naive、date-only、异常 offset、 fractional seconds 等）无法独立验证；runner 参数化测试声明 naive 被拒绝（all_valid_iso_datetime=False），只能作为声明证据采信。
- DIFF_CONTEXT_LIMITATION: base HEAD 877e20aa 的完整树不可见，只有快照；已抽查快照与 patch 的 '+' 行一致（comparison、scan 集合、wrote_file 等），未逐行重放整个 patch。
- UNPROVEN: test_baseline.txt / test_execution_result.txt（targeted 364 passed、full 545 passed、py_compile PASS、git diff PASS）为文本声明。bundle 缺少 ofl/vrc/vre 三个依赖模块，快照测试在本审查环境无法 import 运行，未复现。
- SCOPE_LIMITATION: protected_fingerprints.json 中的 official_facts_sha256、2026_07_23 runner manifest SHA、Phase C review manifest SHA、review index SHA 指向 bundle 外对象，无法核验其真实性；本审查未依赖其数值成立任何结论。
- SCOPE_LIMITATION: credential_scan.txt 为声明性证据；已抽查测试文件中的敏感样式仅为显式 fake/secret 占位符，与声明一致。

============================================================
TEST_GAPS
============================================================
1. semantic_noop + manifest bundle 失败（P2-1）：现有 bundle 失败测试只覆盖 created 与 created_postcheck_failed（test_run_daily_facts_after_close.py:1537, 1756）。
2. semantic_noop 完成后 candidate.json 丢失/篡改的重跑行为（P3-1）。
3. generator 独立 CLI --write-official 的 conflict/sealed/manual_blocked 端到端语义（P3-2）；现有新增测试只到 mock 级 wrote_file 映射。
4. partial 候选 + semantic_noop 的 runner 层 outcome/flag 组合（P3-3）。
5. semantic_noop 冲突分支（comparison 非 None 的 conflict_blocked）在 Phase C 侧 incident 证据链（official_validator_after、comparison 保留）的显式断言未见；Phase B 侧已有充分 conflict 参数化覆盖，此条为强化项。

============================================================
SAME_BUNDLE_READY_FOR_DUAL_REVIEW 结论
============================================================
- 作为双盲审输入包: YES。18 文件 SHA 全部核验通过，双 patch 逐字节相同，scope/基线/指纹/凭据扫描齐备，两份独立审查可在同一冻结输入上进行。
- 作为机制放行结论: 不给 GREEN_LIGHT。机制主链、互斥、no-follow、锁复核、index 幂等与 Phase B→C 集成均验证通过且无 P1；但存在 1 个 P2（P2-1：semantic_noop × bundle 失败的重跑死锁 + 矩阵组合缺口），需在封箱前修复或经明确的书面风险接受；另有 3 个 P3。因此 SAME_BUNDLE_READY_FOR_DUAL_REVIEW 的"可供双审"层面成立，"机制可放行"层面不成立。

============================================================
REVIEW_RUNTIME
============================================================
- model: Kimi Code CLI agent（具体版本 UNKNOWN）
- thinking_effort: high
- session_id: UNKNOWN
- elapsed_time: 约 21 分钟（2026-07-25T17:14:06Z → 2026-07-25T17:35:34Z）
- output_truncated: NO
- bundle_sha_verified: YES
