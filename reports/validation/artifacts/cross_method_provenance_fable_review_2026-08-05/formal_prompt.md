# Fable Architecture Review — 2026-07-31 Cross-Method Provenance

你是股票小工坊 2026-07-31 cross-method provenance 架构外审员。

本轮严格只读，仅做架构裁决。禁止修改代码、设计日期特例、生成 runtime、暂存、commit、push。

仓库：

`/Users/wongdaisy/Mimo-Lab/stocks`

分支：

`workbench/mainline-2026-07`

预期 HEAD：

`6432855b001dee50332ecd402affa8421c3cab81`

---

## 0. 运行身份与仓库边界

审查开始时读取一次：

- 当前 HEAD
- `git status --porcelain=v1 --untracked-files=all` 原始字节 SHA-256

输出前再次读取同样两项。

只有两次 HEAD 都等于预期 HEAD，才允许：

`HEAD_MATCH = YES`

只有两次 status 原始字节 SHA-256 完全相同，才允许：

`SOURCE_WORKTREE_UNCHANGED = YES`

仓库当前存在既有脏项，因此不得用“工作区为空”作为判断标准。

运行模型、provider、backend 无法从运行事件或受信元数据观测时填写 `UNKNOWN`，不得从提示词、文件名或用户描述推断。

---

## 一、任务背景

阳光电源 2026-07-31 已存在 canonical official facts：

`data/daily/300274_2026-07-31_facts.json`

official SHA-256：

`196d2b24fcd4d600db0c7b55d367c229cf9132526576ad0970ab163d4a9a99cd`

official 中：

`volume_ratio.verification.method = same_day_snapshot_plus_sohu_five_day_cross_check`

其内嵌证据包括：

- Tencent archived same-day snapshot
- Sohu historical OHLC 对照
- Sohu five-day volume calculation
- `snapshot_ohlc_check`
- `verification.status=confirmed`

当前重新运行历史生成器时，Tencent same-day snapshot 已无法重新取得，生成器降级输出：

`historical_five_day_volume_cross_check`

当前 replay 与 official 的行情业务值一致，但 method、timestamp path 集合与 provenance 身份不同。

v3 method-profile 机制据此阻断 `semantic_noop`：

- candidate method 与 official method 不同
- 不允许跨 method 自动等价
- official 字节保持不变
- Phase C 未生成
- 2026-07-31 状态为 DEFERRED

当前 conflict run：

`/Users/wongdaisy/Library/Application Support/Mimo-Lab/stocks-runtime/runs/2026-07-31/54681ca9-3c8b-46a2-8fdb-1ef487d71b9d/manifest.json`

若该 manifest 的 `candidate_path` 指向同一 run 目录中的常规文件，允许只读该精确 candidate；若不存在，记录为 absent。禁止遍历整个 runtime。

原始 07-31 candidate、旧 Phase B runner、旧 Phase C manifest、Tencent source bundle 的原始字节目前均未找到。

但两份历史回填报告仍保留 locator：

- 旧 Phase B runner：
  `<runtime>/runs/2026-07-31/b6a27a19-cc1c-4c2e-b600-aca7b575c864/manifest.json`
- 旧 Phase C：
  `<runtime>/reviews/2026-07-31/rev_300274_2026-07-31_196d2b24fcd4d600/review_manifest.json`

这些历史报告仅属于 locator / historical claim，不得替代缺失的 raw manifest、candidate、source bundle 或独立 provenance authority。

---

## 二、已成立的范围前提

以下结论无需重跑此前全量审查与测试矩阵：

1. method-profile v3 生产实现已通过既有 Fable、K3 与测试矩阵。
2. v3 默认按 method 精确授权 timestamp paths。
3. 未知 method、跨 method、额外 timestamp path、列表路径均 fail-closed。
4. 07-27～07-30 四日 runtime 权威链已由 K3 真实字节终审通过。
5. 07-31 official facts 当前 Validator PASS。
6. 07-31 official 不允许被当前 historical candidate 覆盖。
7. rebuild-from-official 会生成无 Phase B runner 的 Phase C。
8. Sunday Weekly Pipeline v0.1 要求：
   - Phase C manifest 指向合法 Phase B runner
   - `rebuilt_from_official=true` 且 runner path/SHA 为空时阻断
9. 本轮不得为 2026-07-31 写日期特例。

这些属于审查范围前提，不代表忽略文件矛盾。若必读材料与任一前提冲突，必须报告精确矛盾，不得静默采用前提。

---

## 三、必读材料

### Canonical 与规则

- `data/daily/300274_2026-07-31_facts.json`
- `rules/run_daily_facts_after_close_phase_b_v0.3.md`
- `rules/review_manifest_phase_c_v0.3.md`
- `rules/semantic_noop_timestamp_profiles_v0.3.json`
- `rules/semantic_noop_timestamp_profile_registry_v0.1.json`
- `rules/sunday_weekly_pipeline_v0.1.md`

### 生产实现

- `tools/official_facts_transaction.py`
- `tools/phase_b_completion.py`
- `tools/review_manifest.py`

### v3 验证

- `reports/validation/semantic_noop_method_profile_v3_candidate_2026-08-04.md`
- `reports/validation/semantic_noop_profile_identity_durability_2026-08-04.md`

### 07-31 历史 locator

- `reports/validation/sungrow_daily_facts_backfill_2026-07-27_2026-07-31_validation.md`
- `reports/validation/sungrow_daily_review_backfill_2026-07-27_2026-07-31_validation.md`

### 当前 conflict evidence

- 当前 conflict manifest 的精确绝对路径
- 仅当 manifest 指向同一 run 目录内现存 candidate 时，读取该精确 candidate

无需阅读整个仓库，无需运行全量测试。若需结构推演，仅使用只读检索或内存推演，不写临时文件。

---

## 四、先分离三种判断对象

不得混淆以下三类结论：

1. **official facts validity**
   - official bytes 是否 canonical
   - 当前 Validator 是否通过
   - 行情业务字段是否有效

2. **historical provenance validity**
   - 原 same-day Tencent snapshot 与 source bundle 是否仍有独立、可复算身份
   - 当前 replay 是否能证明与原 provenance 同源

3. **automation authority validity**
   - 当前是否存在合法 Phase B runner
   - Phase C 与 SWP 是否有权把该日纳入自动链

official facts 有效，不自动推出 historical provenance 完整；historical provenance 不完整，也不自动否定 official 中的行情数值；两者均不自动形成 Phase B authority。

---

## 五、候选路线

### A. 当前样本永久保持 blocked / DEFERRED

含义：

- official bytes 保留
- 不生成替代 Phase B authority
- 不生成绕过 Phase B 的 Phase C
- 07-31 从自动 SWP candidate 中阻断或排除
- 项目记忆、周观察、审计报告明确记录：
  - facts valid
  - original provenance unavailable
  - Phase B authority missing
  - automated weekly inclusion denied
- 人工叙述可引用 official facts，但不得伪称自动 authority 已闭环

### B. 新增受控 cross-method equivalence

可能形式：

- 独立 comparison mode
- 独立 method-pair registry
- method-pair authorization
- 共同业务字段 projection
- 两侧 source identity 与证据完整度要求
- official bytes 永不变化

只有当机器能依靠 official 之外的独立证据证明两种 method 在该 policy 下等价，才允许选择 B。

method 名称、相同 OHLC、相同 volume_ratio、双方 Validator PASS 均不得单独构成充分证据。

### C. 新增 provenance migration / attestation

特征：

- 不把两种 method 宣告为普通 `semantic_noop`
- 生成独立、可审计的迁移或替代证明
- 可能形成一种新的 authority type
- Phase B、Phase C、SWP 均明确识别该 authority type
- 保留旧 official method，不重写历史事实
- 不降低 v3 普通 `semantic_noop` 门槛

若当前 07-31 已无 official 之外的独立证据，C 可能只适合作为未来设计，不得借设计概念恢复当前样本 authority。

---

## 六、双层裁决

三条路线并非天然互斥于两个时间层。必须分别回答：

### 当前 07-31 处置

只能选一项：

- `KEEP_DEFERRED`
- `CURRENT_AUTHORITY_RECOVERABLE`

### 未来通用架构

只能选一项：

- `NO_NEW_MECHANISM`
- `DESIGN_CROSS_METHOD_EQUIVALENCE`
- `DESIGN_PROVENANCE_MIGRATION`

允许出现：

- 当前 07-31 = `KEEP_DEFERRED`
- 未来通用架构 = `DESIGN_PROVENANCE_MIGRATION`

但必须明确该未来设计是否能作用于当前 07-31。不得用未来设计的理论安全性冒充当前样本已有证据。

---

## 七、必须回答的问题

1. 原始 candidate、runner 与 source bundle 原始字节已丢失时，当前 07-31 是否仍存在可证明的 cross-method equivalence？

2. official 内嵌 archived Tencent snapshot 与 Sohu 对照字段，能否作为独立 provenance evidence？
   - 若能，说明独立性来源。
   - 若不能，说明为何属于 official 自证循环。

3. 两份历史回填报告中的旧 path、状态与 SHA claim：
   - 能否仅作为 locator / historical claim？
   - 能否形成 authority？
   - 缺少哪些 raw bytes 后无法复算？

4. 数值字段完全相同、双方 Validator PASS，为何足够或不足以支撑跨 method 等价？
   列出不可替代证据。

5. same-day method 与 historical method 是否存在普适、机器可判的严格偏序或强弱关系？

   例如：

   `same-day snapshot + historical cross-check`

   是否能视为：

   `historical double-source cross-check`

   的证据超集？

   若能，必须给出：
   - method schema
   - source identity
   - evidence path contract
   - source raw SHA
   - projection rules
   - tolerances
   - policy version/SHA
   - 对称与非对称条件
   - 未知 pair 的 fail-closed 规则

   若不能，说明根因。不得仅凭 method 名称语义作答。

6. 是否应新增：
   - `cross_method_profile_v1`
   - `provenance_migration_v1`
   - 或两者皆不新增

   禁止修改现有 v3 语义来容纳跨 method。

7. 新机制若存在，authority identity 至少应包含哪些字段？

   候选：

   - `authority_schema_version`
   - `authority_type`
   - `source_method`
   - `target_method`
   - `method_pair_id`
   - `official_raw_sha256`
   - `candidate_raw_sha256`
   - `shared_business_projection_sha256`
   - `source_evidence_paths`
   - `source_evidence_sha256`
   - `migration_policy_version`
   - `migration_policy_sha256`
   - `profile_registry_sha256`
   - `generated_at`
   - `signer_type`
   - `human_authorization`
   - `supersedes_authority_sha256`
   - `downstream_permissions`

   请删减、补充，并区分 machine authority 与 human-only audit record。

8. 是否必须由独立第三方源重新验证 official 中的 archived snapshot？
   当前时间已过且 same-day snapshot 无法重取时，当前样本应如何处置？

9. 是否允许人工签署 provenance attestation？

   若允许，必须说明：

   - 人工实际确认的对象
   - 人工不得确认的对象
   - signer identity 与签署原文如何绑定
   - policy/version/SHA 如何绑定
   - 人工签署是否仅形成 human-only audit record
   - 能否形成 machine authority
   - 是否仍禁止修改 official
   - 如何防止人工签署演化成 validator 绕过

   自由文本不得成为机器证据。生成器不得自行签署 provenance。

10. 新 authority 若成立，如何进入 Phase B / Phase C / SWP？

    明确：

    - 是否新增 Phase B `write_action`
    - 是否新增 manifest schema
    - authority 是否必须拥有独立 raw bytes 与 SHA
    - Phase C `artifact_type` 是否变化
    - `review_state` 应为何值
    - SWP 验证哪些 identity 与 raw SHA
    - downstream permissions 是否仍全 false
    - Git 与交易权限是否仍全 false

11. rebuild-from-official 是否继续保持 SWP 阻断？
    是否存在安全的 runner-less authority？
    若主张存在，必须说明谁签发、凭何独立证据、如何复算、为何不构成 Phase B 绕过。

12. 若当前 07-31 继续 blocked：
    - 项目记忆如何记录
    - 周观察如何引用
    - 审计报告如何表达
    - 自动周候选如何阻断
    - 人工周说明如何保留事实而不冒充 authority

13. 以下最小方案是否最安全、最经济：

    - 保留 07-31 official
    - 将旧回填报告标记为 provenance unavailable / locator-only
    - 记录 Phase B authority missing
    - 周观察允许人工引用 facts，但自动 SWP 不纳入该日
    - 保留人工说明
    - 不新增 Phase B write_action
    - 不新增 Phase C artifact
    - 不构造 runner-less authority

14. 是否值得为单个遗失 provenance 样本引入通用机制？
    必须分别评价：
    - 理论架构价值
    - 当前样本恢复价值
    - 实施与长期维护成本
    - 未来复用概率
    - 新攻击面

---

## 八、安全红线

任何推荐方案都必须满足：

- official bytes 永不因迁移而变化
- 不允许仅靠相同 OHLC / volume_ratio 宣告等价
- 不允许日期特例
- 不允许 method 名称模糊匹配
- 不允许自由文本成为机器证据
- 不允许生成器自行签署 provenance
- 不允许用 official 内容伪装成独立 candidate
- 不允许历史 evidence 被当前 active policy 重解释
- 不允许降低 v3 普通 `semantic_noop` 门槛
- 不允许 Phase C 或 SWP 绕过合法 Phase B authority
- 所有新 identity 均须版本化并绑定 raw SHA
- 未知 method pair、证据缺失、identity 漂移一律 fail-closed
- downstream permissions 始终全 false
- Git 与交易权限始终全 false
- locator-only 历史报告不得升级为 raw authority
- human-only audit record 不得静默升级为 machine authority

---

## 九、成本边界

本轮仅做架构判断。

禁止：

- 修改文件
- 写生产代码
- 写测试
- 跑全量 pytest
- 生成 runtime
- 遍历无关目录
- 重审四日已通过链
- 输出大段通用理论

优先：

- 阅读上述有限材料
- 聚焦 07-31
- 给出当前处置与未来架构双裁决
- 给出最小方案
- 列出阻断条件
- 判断是否值得施工

---

## 十、Finding 标准

P1：

- 方案允许伪造 provenance
- official 自证循环被当作独立证据
- 相同业务值被错误当作跨 method 等价
- v3 普通 `semantic_noop` 安全边界被削弱
- SWP 读入无合法 authority 的事实
- locator-only 报告被升级为 authority

P2：

- 推荐方案 identity 生命周期不成立
- policy/version/SHA 绑定不足
- Phase B / Phase C / SWP 责任不清
- 人工 attestation 可任意绕过
- 新机制复杂度远大于单样本价值
- 当前处置与未来架构被混为一谈

P3：

- 命名、文档或非阻断表达问题

每项 finding 必须包含：

- `finding_id`
- `severity`
- evidence path
- 精确行范围或 JSON pointer
- failure scenario
- consequence
- 最小修订范围

P1 必须给出一条具体伪造或越权执行路径。不得仅凭抽象可能性立项。没有 finding 时写 `NONE`。

---

## 十一、READY 字段门槛

`READY_FOR_RULE_DESIGN = YES`

仅表示未来通用架构方向已唯一，规范边界已足够进入规则设计。

`READY_FOR_CODE_IMPLEMENTATION = YES`

仅当规则、schema、identity、authority 生命周期、Phase B / Phase C / SWP 职责与测试矩阵均已唯一且无 P1/P2 阻断项时才允许。预期本轮固定为 NO。

`READY_FOR_RUNTIME_ACTION = YES`

仅当当前 07-31 已拥有合法、独立、可复算 authority 时才允许。禁止因未来设计存在而填写 YES。

`READY_FOR_COMMIT = YES`

仅当本轮存在已完成且通过审查的仓库变更时才允许。预期本轮固定为 NO。

---

## 十二、固定输出

每个字段单独一行。枚举值必须写在等号右侧，不得把选项另起一行。

```text
ACTUAL_MODEL =
BACKEND =
PROVIDER =
IDENTITY_CONFIDENCE =

HEAD_EXPECTED =
HEAD_ACTUAL =
HEAD_MATCH =
SOURCE_STATUS_SHA_BEFORE =
SOURCE_STATUS_SHA_AFTER =
SOURCE_WORKTREE_UNCHANGED =
REVIEW_SCOPE_RESPECTED =
FILES_MODIFIED = NO

OFFICIAL_FACTS_VALID =
OFFICIAL_SELF_ATTESTATION_SAFE =
CROSS_METHOD_EQUIVALENCE_PROVABLE =
ORIGINAL_PROVENANCE_RECONSTRUCTION_POSSIBLE =
AUTOMATED_AUTHORITY_RECOVERY_POSSIBLE =
HUMAN_AUDIT_USE_ALLOWED =

CURRENT_0731_DISPOSITION = KEEP_DEFERRED | CURRENT_AUTHORITY_RECOVERABLE
FUTURE_GENERAL_ARCHITECTURE = NO_NEW_MECHANISM | DESIGN_CROSS_METHOD_EQUIVALENCE | DESIGN_PROVENANCE_MIGRATION
FUTURE_MECHANISM_APPLICABLE_TO_CURRENT_0731 = YES | NO

MINIMAL_SAFE_DESIGN =
NEW_COMPARISON_MODE_REQUIRED =
NEW_MANIFEST_SCHEMA_REQUIRED =
HUMAN_ATTESTATION_ALLOWED =
HUMAN_ATTESTATION_MACHINE_AUTHORITY =
PHASE_B_AUTHORITY_MODEL =
PHASE_C_MODEL =
SWP_POLICY =

REJECTED_ROUTES =
FAIL_CLOSED_CONDITIONS =

THEORETICAL_ARCHITECTURE_VALUE = HIGH | MEDIUM | LOW
CURRENT_SAMPLE_RECOVERY_VALUE = HIGH | MEDIUM | LOW | NONE
IMPLEMENTATION_VALUE = HIGH | MEDIUM | LOW | NOT_WORTH_BUILDING

P1_COUNT =
P2_COUNT =
P3_COUNT =

VERDICT = KEEP_DEFERRED | DESIGN_ONLY_PROVENANCE_MIGRATION | DESIGN_CROSS_METHOD_EQUIVALENCE | FAIL

READY_FOR_RULE_DESIGN =
READY_FOR_CODE_IMPLEMENTATION = NO
READY_FOR_RUNTIME_ACTION = NO
READY_FOR_COMMIT = NO

STAGED = NO
COMMITTED = NO
PUSHED = NO
```

布尔判断仅使用：

- `YES`
- `NO`
- `PARTIAL`
- `UNKNOWN`

`HEAD_MATCH`、`SOURCE_WORKTREE_UNCHANGED`、四个 READY 字段仅使用 `YES` 或 `NO`。

禁止修改、暂存、commit、push。
