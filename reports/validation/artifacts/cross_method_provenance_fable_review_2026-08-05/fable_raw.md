# 2026-07-31 Cross-Method Provenance 架构裁决

## 一、证据基线

- official facts `data/daily/300274_2026-07-31_facts.json`（SHA `196d2b24…99cd` 与既定值一致），method 见 L171 `same_day_snapshot_plus_sohu_five_day_cross_check`，same-day 证据在 L97–164（`snapshot_ohlc_check`，archived_source `tencent_qt_direct_index_49` L104/L160）。
- conflict manifest（SHA `5fa5df4b…ebeb9`）：`/comparison/verification_method` = `historical_five_day_volume_cross_check`，`/comparison/semantic_equal` = false，`/write_action` = `conflict_blocked`，`/official_changed` = false，`/official_sha256_after` = official SHA，`/outcome` = `needs_manual_review`。v3 按预期 fail-closed 阻断，无矛盾。
- candidate（SHA `d94d0eb8…ac11a`）：`/volume_ratio/verification/method` = `historical_five_day_volume_cross_check`，timestamp path 集合含 `source_volume_checks.*.fetched_at`，与 profile v0.3 两个 method 的 required_paths（`rules/semantic_noop_timestamp_profiles_v0.3.json` L28–41 vs L50–62）互不相同——阻断依据正确。
- 两份回填报告只提供 locator 与 SHA claim（facts backfill L113、L116；review backfill L111–112），对应 raw bytes 未找到，无法复算。

范围前提与必读材料未发现矛盾。

## 二、三类判断分离

1. **official facts validity = 有效**：raw SHA 匹配，两次 Validator passed（manifest `/official_validator_before`、`/official_validator_after`）。
2. **historical provenance validity = 不可重建**：Tencent same-day snapshot 无法重取；原 candidate/runner/source bundle raw bytes 缺失；official L97–164 的 snapshot 证据由同一生成流程写入 official 自身，属于 official 自证——它证明"当时做过对照"这一 claim，但无 official 之外可独立复算的字节身份。
3. **automation authority validity = 缺失**：旧 Phase B runner manifest（`b6a27a19…`）仅剩 locator；SWP v0.1 明确拒绝无 runner 的 rebuilt Phase C（`rules/sunday_weekly_pipeline_v0.1.md` L24）。

## 三、十四问简答

1. **不存在**可证明的 cross-method equivalence。等价证明需两侧 source raw bytes 与独立身份；一侧（same-day snapshot）原始字节已灭失，只剩 official 内嵌摘要。
2. **不能**作为独立证据。`snapshot_ohlc_check`（L97–164）与 `cross_check`（L63–70）的字节由生成 official 的同一次 run 写入 official 本身，验证 official 时引用它们即自证循环；独立性要求证据字节存在于 official 之外且可独立哈希复算。
3. 回填报告**只能作 locator / historical claim**（facts backfill L113–116）。不能形成 authority：缺 Phase B manifest raw bytes、Phase C review_manifest raw bytes（claimed SHA `3ecfd1c4…`，review backfill L112）、原 candidate、Tencent source bundle，任一缺失即无法复算链条。
4. 数值相同 + 双 PASS **不足**：它只证明业务投影相等，不证明证据来源独立、采集时点合法、方法契约满足。相同数值可由复制 official 数值伪造。不可替代证据：两侧 source raw SHA、evidence path contract、采集时点约束、policy version/SHA 绑定、独立第三源复算。
5. **不存在**普适机器可判的偏序。"same-day + cross-check ⊃ historical double-source"仅是名称语义直觉；两个 method 的证据 path 集合本就不同（profiles v0.3 L28–41 vs L50–62），candidate 的 tolerance 0.01 vs official 的 0.05（candidate `/volume_ratio/cross_check/tolerance` vs official L68），说明 policy 参数也不同构。若未来要建偏序，必须给出提示词第七题所列全套契约（method schema、source identity、evidence path contract、source raw SHA、projection rules、tolerances、policy version/SHA、非对称声明、未知 pair fail-closed），这在当前样本上因 raw bytes 灭失不可能满足。
6. 未来若建，选 **`provenance_migration_v1`**（作为独立 authority type），不建 `cross_method_profile_v1`（自动跨 method 等价的攻击面大于单样本价值），且不改 v3 语义。
7. Machine authority 最小字段集：`authority_schema_version`、`authority_type`、`source_method`、`target_method`、`method_pair_id`、`official_raw_sha256`、`candidate_raw_sha256`、`source_evidence_paths`、`source_evidence_sha256`、`migration_policy_version`、`migration_policy_sha256`、`profile_registry_sha256`、`generated_at`、`signer_type`、`downstream_permissions`（全 false）。`shared_business_projection_sha256` 保留（防投影漂移）。`human_authorization`、`supersedes_authority_sha256` 归 human-only audit record；human record 缺 `source_evidence_sha256` 时永不升级为 machine authority。
8. 独立第三方源只能重证 OHLC/volume 数值，不能重证"same-day snapshot 曾存在"。当前样本：无法重取 → 处置只能 KEEP_DEFERRED。
9. 人工 attestation **允许，仅限 human-only audit record**。可确认：曾目视执行过回填、报告 locator 真实性。不得确认：灭失字节的哈希等价、机器等价。signer identity 与签署原文需绑定被签内容的 SHA 与 policy version/SHA。不形成 machine authority，不修改 official，不进入 Validator 判定路径——自由文本永不成为机器证据，生成器不得自签。
10. 未来 authority 进入管线：新增 Phase B `write_action=provenance_migration_authority_created`、新 manifest schema（独立 raw bytes + SHA）、Phase C `artifact_type` 新增迁移类型、`review_state=needs_manual_review` 起步、SWP 复证 authority raw SHA + policy SHA + 双侧 evidence SHA、downstream/Git/交易权限全 false。
11. rebuild-from-official 的 SWP 阻断**必须保持**（SWP L24 `blocked_identity_conflict:phase_b_evidence_missing`）。不存在安全的 runner-less authority：无人能凭独立证据签发，任何构造都是 Phase B 绕过。
12. 继续 blocked 的记录方式：项目记忆写"facts valid / original provenance unavailable / Phase B authority missing / automated weekly inclusion denied"；周观察人工引用 official 数值并注明 authority 缺失；审计报告将两份回填报告标注 locator-only；SWP 自动候选排除 07-31。
13. **是**。第十三题最小方案最安全最经济，与本裁决一致。
14. 理论价值 MEDIUM（provenance 灭失会再发生）；当前样本恢复价值 NONE（证据不可恢复，机制建成也救不了它）；实施成本高于单样本收益 → 现在不施工，留 DESIGN_ONLY。

## 四、Findings

NONE。

（说明：official 内嵌 snapshot 证据的自证性质不是缺陷——v3 已正确拒绝将其用于跨 method 等价，manifest `/comparison/semantic_equal=false`、`/write_action=conflict_blocked` 证明防线生效。）

## 五、固定输出

```text
ACTUAL_MODEL = UNKNOWN
BACKEND = UNKNOWN
PROVIDER = UNKNOWN
IDENTITY_CONFIDENCE = LOW

HEAD_EXPECTED = 6432855b001dee50332ecd402affa8421c3cab81
HEAD_ACTUAL = 6432855b001dee50332ecd402affa8421c3cab81
HEAD_MATCH = YES
SOURCE_STATUS_SHA_BEFORE = 2fb23efa607a1b937d6a44aa8156b61d03e04b53ac7b5beb2268492999654b5e
SOURCE_STATUS_SHA_AFTER = 2fb23efa607a1b937d6a44aa8156b61d03e04b53ac7b5beb2268492999654b5e
SOURCE_WORKTREE_UNCHANGED = YES
REVIEW_SCOPE_RESPECTED = YES
FILES_MODIFIED = NO

OFFICIAL_FACTS_VALID = YES
OFFICIAL_SELF_ATTESTATION_SAFE = NO
CROSS_METHOD_EQUIVALENCE_PROVABLE = NO
ORIGINAL_PROVENANCE_RECONSTRUCTION_POSSIBLE = NO
AUTOMATED_AUTHORITY_RECOVERY_POSSIBLE = NO
HUMAN_AUDIT_USE_ALLOWED = YES

CURRENT_0731_DISPOSITION = KEEP_DEFERRED
FUTURE_GENERAL_ARCHITECTURE = DESIGN_PROVENANCE_MIGRATION
FUTURE_MECHANISM_APPLICABLE_TO_CURRENT_0731 = NO

MINIMAL_SAFE_DESIGN = 保留07-31 official；回填报告标注locator-only/provenance unavailable；记录Phase B authority missing；自动SWP排除该日；人工周说明可引用facts；不新增write_action、Phase C artifact或runner-less authority
NEW_COMPARISON_MODE_REQUIRED = NO
NEW_MANIFEST_SCHEMA_REQUIRED = NO
HUMAN_ATTESTATION_ALLOWED = YES
HUMAN_ATTESTATION_MACHINE_AUTHORITY = NO
PHASE_B_AUTHORITY_MODEL = 仅合法runner manifest raw bytes可构成authority；rebuilt/runner-less一律无authority
PHASE_C_MODEL = 不为07-31生成绕过Phase B的Phase C；rebuild-from-official产物维持SWP阻断
SWP_POLICY = blocked_identity_conflict:phase_b_evidence_missing；07-31不入自动周候选；downstream权限全false
REJECTED_ROUTES = B(cross-method自动等价：原始字节灭失无法证明)；C用于当前样本(无official之外独立证据，禁止借设计恢复authority)；runner-less authority；method名称语义偏序
FAIL_CLOSED_CONDITIONS = 未知method pair；任一侧source raw SHA缺失；evidence path contract不满足；policy/version/SHA不绑定；identity漂移；human-only record被引用为machine证据；rebuilt_from_official且runner path/SHA为空

THEORETICAL_ARCHITECTURE_VALUE = MEDIUM
CURRENT_SAMPLE_RECOVERY_VALUE = NONE
IMPLEMENTATION_VALUE = NOT_WORTH_BUILDING

P1_COUNT = 0
P2_COUNT = 0
P3_COUNT = 0

VERDICT = KEEP_DEFERRED

READY_FOR_RULE_DESIGN = YES
READY_FOR_CODE_IMPLEMENTATION = NO
READY_FOR_RUNTIME_ACTION = NO
READY_FOR_COMMIT = NO

STAGED = NO
COMMITTED = NO
PUSHED = NO
```

说明：`READY_FOR_RULE_DESIGN = YES` 仅指未来方向已唯一（provenance migration 型 authority，人工签署限 audit record），且明确该设计不适用于当前 07-31；鉴于 `IMPLEMENTATION_VALUE = NOT_WORTH_BUILDING`，建议规则设计仅在下一次真实 provenance 灭失事件出现时启动。
