# Semantic Noop Method-Profile v3 Candidate Validation (2026-08-04)

## Context

HEAD: `6432855b001dee50332ecd402affa8421c3cab81`

This candidate implements the Fable external architecture verdict
`REQUIRE_METHOD_AWARE_PROFILES` for semantic_noop: the dynamic recursive v2
exclusion is replaced by a version-controlled, method-aware profile
(`method_profile_timestamp_paths_v3`), while v1 / v2 historical evidence
continues to be recomputed under its recorded mode.

## Fable 外审身份与报告 SHA

Evidence archived byte-for-byte to:

```text
reports/validation/artifacts/semantic_noop_timestamp_paths_v2_fable_review_2026-08-04/
```

| 文件 | size_bytes | sha256 |
|---|---|---|
| `fable_raw.md` | 12082 | `002d9e49723a1f4bde0b1d7760299e83fb614408a2a49d214a487bc311601dfd` |
| `formal_prompt.md` | 9408 | `947a24ac83c7f8a5263de608f3412560d35f4a9b4662cf3816d78356edd26d5d` |
| `run_meta.json` | 1175 | `137902128f100b59838f54dffab2370c4a79ecdbbc4f2440af9d854d4bc040a3` |

- Fable report SHA：`002d9e49723a1f4bde0b1d7760299e83fb614408a2a49d214a487bc311601dfd`（与 `fable_raw.md` 字节一致）
- architecture verdict：`REQUIRE_METHOD_AWARE_PROFILES`
- P1=1 / P2=3 / P3=1
- HEAD before/after：`6432855b001dee50332ecd402affa8421c3cab81`
- status SHA before/after：`0058444cbdf53b1021168c79dc90f35bee49f8e9240d05f07057bc7801dd131f`
- Key 已由用户删除；原审查为只读。
- 原 v2 candidate 报告字节未被修改。

## v2 P1 的具体执行路径（Fable F-1）

生成器（或上游）在 candidate 与 official 双方对称写入未授权叶
`volume_ratio.extra_check.fetched_at`，两个值均为合法但不同的带时区 datetime
（旧测试即用 `08:00:06Z` vs `09:00:06Z`）。v2 动态递归发现路径集合对称、五条
`REQUIRED_V2_TIMESTAMP_PATHS` 存在、全部 ISO 合法，剔除后哈希相等 →
`write_action=semantic_noop`，official 保留旧值，业务时间差异被永久静默；Phase B
completion 与 Phase C 用同一 v2 复算，全链路通过，审计不可见。

本候选已将该用例反转为拒绝：profile 外对称 `fetched_at` 一律
`conflict_blocked`（`test_symmetric_extra_timestamp_leaf_is_blocked_by_v3`）。

## v3 profile 数据结构

权威配置：

```text
rules/semantic_noop_timestamp_profiles_v0.3.json
```

结构：

```json
{
  "schema_version": "semantic_noop_timestamp_profiles_v0.3",
  "profile_version": "v0.3",
  "comparison_mode": "method_profile_timestamp_paths_v3",
  "common_required_paths": [5 条共同必需路径],
  "allow_list_index_paths": false,
  "profiles": {
    "<method>": {
      "required_paths": [...],
      "optional_paths": [...],
      "optional_presence_conditions": {...},
      "allow_list_index_paths": false
    }
  }
}
```

共同必需路径（所有 active profile 的 required_paths 子集，加载时强制校验）：

```text
generated_at
quote_verification.fetched_at
run.fetched_at
volume_ratio.five_day_volume_check.fetched_at
volume_ratio.verification.fetched_at
```

## 四类 method 路径矩阵

路径从真实 facts、frozen fixtures、生成器契约与 Validator 契约归纳，未猜测：

| method | 状态 | required timestamp paths | 归纳依据 |
|---|---|---|---|
| `same_day_snapshot_plus_sohu_five_day_cross_check` | active | 共同 5 + `volume_ratio.snapshot_ohlc_check.fetched_at`（共 6） | 真实 07-22/23/24/31 facts、Validator `_check_same_day_snapshot_volume_ratio_evidence` |
| `historical_five_day_volume_cross_check` | active | 共同 5 + `volume_ratio.source_volume_checks.sohu_history.fetched_at` + `volume_ratio.source_volume_checks.tencent_history.fetched_at`（共 7） | 真实 07-13/15-21/27-31 facts、Validator `_check_historical_volume_ratio_evidence` |
| `archived_tencent_snapshot_plus_sohu_historical_reverification` | active | 共同 5 + `volume_ratio.historical_ohlc_check.fetched_at` + `volume_ratio.legacy_verification.fetched_at`（共 7） | 真实 07-14 facts、Validator `_check_archived_volume_ratio_evidence` |
| `legacy_manual_confirmation` | blocked（阻断项） | 无唯一 profile | 无真实 v0.2 样本；v0.1 frozen fixture 的 verification 无 `fetched_at`；生成器 merge 保留来源证据结构且 `automation_evidence.fetched_at` 条件性出现；Validator 契约不约束 fetched_at 路径 |

`archived_snapshot_source.original_fetched_at` 不是 `fetched_at` 叶子，不计入发现集。
所有 profile 的 `optional_paths` 为空；`allow_list_index_paths=false` 全局与逐
method 生效。optional path 条件格式为
`{"present_when_parent": "<对象路径>"}`。

## profile version 与 SHA

```text
profile_version = v0.3
profile_sha256   = 11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1
```

SHA 由配置解析结果的确定性 canonical JSON 计算
（`sort_keys=True`、`separators=(",", ":")`，2119 字节），由
`load_method_profile_config()` 在运行时从权威文件读取并复算。

## v3 语义

- candidate 与 official 必须使用同一 `volume_ratio.verification.method`；
- 排除集合只来源于 profile 的 `required_paths ∪（条件成立的 optional_paths）`；
- discovered 路径集合必须与 profile 合法集合严格一致，且两侧一致；
- 未知 method、blocked profile、profile 缺失、required 缺失、profile 外时间路径、
  列表索引路径、值非法、method 不一致 → `semantic_equal=false`、semantic SHA 为
  `null`、不形成 `semantic_noop`；
- evidence 记录 19 个字段（comparison_mode、profile_version、profile_sha256、
  verification_method、required_paths、optional_paths、
  candidate_discovered_paths、official_discovered_paths、
  candidate_missing_required_paths、official_missing_required_paths、
  candidate_extra_paths、official_extra_paths、
  all_values_valid_timezone_datetime、candidate_raw_sha256、official_raw_sha256、
  candidate_semantic_sha256、official_semantic_sha256、semantic_equal、
  official_changed）。

## v1 / v2 历史兼容

- v1（`approved_timestamp_paths_v1`）：固定六路径复算，六路径必须双方存在；
- v2（`symmetric_timestamp_leaf_paths_v2`）：旧动态递归规则复算（对称集合 +
  `REQUIRED_V2_TIMESTAMP_PATHS`）；
- 新写入默认 v3；dispatch 按 evidence 自身 mode 显式分派，禁止 v3 重解释历史
  v1 / v2 manifest。

真实样本（07-27 official `b8c7b2b8…` vs remediation 候选 `0b8a2da5…`）：
v1 `semantic_equal=false`（dead path 复现）、v2 `semantic_equal=true`、v3
`semantic_equal=true`（semantic SHA `1427bf87…`），三模式 dispatch 行为符合预期。

## Phase B / Phase C 等价性

`phase_b_completion` 与 `review_manifest` 对 v3 校验：同一 19 字段全集、同一
profile_version / profile_sha256（对照权威配置）、同一 verification_method /
required / optional、同一现场复算结果（`comparison == recomputed`）。v1 / v2
分支同样保持两处等价。

## Lucien 复核修正说明

- Lucien 复核发现 Phase C v0.3 规则将实际 19 个 evidence 字段误写为 18；
  本轮已修正文字，代码字段全集未变化。

## K3 终审章节（profile 身份寿命与配置解析加固）

### K3 独立测试结果（本轮回溯范围）

K3 终审针对 v3 历史身份寿命与配置解析提出 1 个 P2 与 2 个 P3；本轮按裁决完成
加固，测试与文档同步更新。具体发现（均以本轮修复前代码为准）：

### P2-1：历史 evidence 复算绑定当前 active 配置

- 修复前：`build_semantic_comparison_v3` 直接 `load_method_profile_config()`
  读取当前配置，v3 历史 evidence 复算没有版本身份；一旦 active 切换或配置
  演进，历史 manifest 无法证明其复算依据的授权集合。
- 修复：新增版本注册表
  `rules/semantic_noop_timestamp_profile_registry_v0.1.json`；新写入只取
  `active_profile_version`；历史复算按 manifest `comparison.profile_version`
  分派，复算该版本 canonical SHA 并与 manifest `profile_sha256` 比对；禁止始终
  读取当前 active 配置。

### P3-1：JSON 解析未检测重复 key 与未知字段

- 修复前：`load_method_profile_config` 使用 `json.loads` 无
  `object_pairs_hook`，任意层级重复 key 静默接受；顶层、profile 条目、
  optional condition 字段未严格白名单。
- 修复：`_parse_strict_json_object` 在任意层级拒绝重复 key；顶层/条目/condition
  字段全集严格限定，未知字段立即失败；布尔必须为真 `bool`；blocked profile
  强制 required/optional/conditions 为空且 reason 非空，active profile 禁止
  reason。

### P3-2：canonical 参数未在规则文档明确

- 修复前：canonical JSON 参数仅存在于代码，规则文档未写明。
- 修复：两份 v0.3 规则文档明确写出
  `ensure_ascii=False`、`sort_keys=True`、`separators=(",", ":")`，并补充
  配置永久冻结与注册表规范；新增复算测试锁定参数与 SHA。

### registry 身份

```text
schema_version        = semantic_noop_timestamp_profile_registry_v0.1
active_profile_version = v0.3
v0.3 path              = rules/semantic_noop_timestamp_profiles_v0.3.json
v0.3 status            = active
v0.3 profile_sha256    = 11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1
```

registry 严格校验：路径必须为 `rules/<file>.json` 相对路径、禁止绝对路径/父目录
逃逸/符号链逃逸；version、配置内 `profile_version`、`comparison_mode`、SHA 必须
一致；同一 SHA 不得映射多个版本；active_profile_version 必须存在且状态为
`active`；未知 version 一律失败。

### v0.3 冻结策略

- 一旦某 profile version 产生正式 evidence，其配置文件永久冻结；路径矩阵变化
  必须创建新版本文件，禁止原地修改旧版本。
- registry 保留所有历史版本映射；`active` 可切换为 `frozen`（历史复算允许、
  新写入禁止）。
- 删除历史配置属于破坏性变更，禁止执行。

### 重复 key 与未知字段拒绝

任意层级重复 key、顶层未知字段、profile 条目未知字段、condition 未知字段、
blocked profile 携带 required/optional/conditions 或缺少 reason、active profile
携带 reason，全部在加载时拒绝并 fail-closed。

### canonical 参数补全

```text
ensure_ascii=False
sort_keys=True
separators=(",", ":")
```

测试 `test_canonical_ensure_ascii_false_recompute` 锁定参数（非 ASCII 保留为
UTF-8 而非 `\u` 转义）与 v0.3 SHA（`11bb039d…`）。

### 修复后的测试结果

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q -p no:cacheprovider tests/test_run_daily_facts_after_close.py tests/test_review_manifest.py
# 369 passed

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q -p no:cacheprovider tests
# 630 passed, 28 subtests passed
```

v0.3 canonical profile SHA 未变化（`11bb039d…`）。模拟 v0.4 仅存在于测试临时
目录，未新增正式 v0.4 配置。

## 测试矩阵覆盖（20 项）

| # | 场景 | 测试 |
|---|---|---|
| 1 | same-day profile 合法 noop | `test_write_official_same_day_profile_semantic_noop` |
| 2 | historical profile 合法 noop | `test_historical_semantic_noop_07_27_structure` |
| 3 | archived profile 合法路径 | `test_archived_profile_legal_paths` |
| 4 | legacy manual（无法唯一 → fail-closed） | `test_legacy_manual_profile_is_fail_closed_blocked` |
| 5 | 未知 method 阻断 | `test_unknown_method_profile_is_fail_closed` |
| 6 | profile 缺失阻断 | `test_profile_missing_is_fail_closed` |
| 7 | method 单侧不同阻断 | `test_method_mismatch_is_fail_closed` |
| 8 | required path 单侧缺失阻断 | `test_required_timestamp_path_deletion_blocks_semantic_noop` |
| 9 | required path 双侧缺失阻断 | 同上（both） |
| 10 | optional path 单侧出现阻断 | `test_optional_path_single_side_appearance_is_fail_closed` |
| 11 | profile 外对称 fetched_at 阻断 | `test_symmetric_extra_timestamp_leaf_is_blocked_by_v3` |
| 12 | extra_check.fetched_at 用例改为阻断 | 同上 |
| 13 | 列表内 fetched_at 阻断 | `test_list_index_timestamp_path_is_fail_closed` |
| 14 | profile SHA 篡改（Phase B）阻断 | `_mutate_semantic_completion("profile_sha256_tampered")` |
| 15 | profile SHA 篡改（Phase C）阻断 | `test_phase_c_rejects_tampered_v3_profile_sha` |
| 16 | 非时间业务字段差异阻断 | `test_write_official_business_change_remains_conflict` 等 |
| 17 | 合法 v1 evidence 通过 | `test_v1_legacy_phase_b_manifest_still_completes`、`test_phase_c_accepts_legacy_v1_semantic_noop` |
| 18 | 合法 v2 evidence 通过 | `test_v2_legacy_phase_b_manifest_still_completes`、`test_phase_c_accepts_legacy_v2_semantic_noop` |
| 19 | v1/v2/v3 各自篡改均拒绝 | v1/v2/v3 tamper 测试（Phase B + Phase C） |
| 20 | Phase B / Phase C 等价 | `test_phase_b_semantic_noop_manifest_is_accepted_by_phase_c_with_real_validator`、`test_historical_semantic_noop_accepted_by_phase_c`、`test_phase_c_accepts_v3_semantic_noop_with_profile_identity` |

## 阻断项（按 Fable 裁决与任务要求）

`legacy_manual_confirmation` 无法从现有证据形成唯一 profile：真实 v0.2 样本缺失、
v0.1 frozen fixture 的 verification 无 `fetched_at`、生成器 merge 保留来源证据结构、
`automation_evidence.fetched_at` 仅在抓取候选存在时出现。按任务规则保持
fail-closed（`profile_status=blocked`），任何 legacy-manual method 的 v3 比较均
`semantic_equal=false`；待未来权威样本或正式规则修订后再形成唯一 profile。

## 测试命令与结果

> 注：以下为 K3 修复前的旧结果，已过时；最终结果以“K3 终审章节”的
> 修复后测试结果为准（369 passed / 630 passed, 28 subtests passed）。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q -p no:cacheprovider tests/test_run_daily_facts_after_close.py tests/test_review_manifest.py
# 350 passed

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q -p no:cacheprovider tests
# 611 passed, 28 subtests passed
```

全程未运行 `--write-official`、未生成 Phase B / Phase C runtime 对象（测试仅写
临时目录）、未修改五份 facts、日复盘或回填报告。

## 工作区边界

新增/修改：

```text
M tools/official_facts_transaction.py
M tools/phase_b_completion.py
M tools/review_manifest.py
M tests/test_run_daily_facts_after_close.py
M tests/test_review_manifest.py
?? rules/run_daily_facts_after_close_phase_b_v0.3.md
?? rules/review_manifest_phase_c_v0.3.md
?? rules/semantic_noop_timestamp_profiles_v0.3.json
?? rules/semantic_noop_timestamp_profile_registry_v0.1.json
?? reports/validation/artifacts/semantic_noop_timestamp_paths_v2_fable_review_2026-08-04/{fable_raw.md, formal_prompt.md, run_meta.json, manifest.json}
?? reports/validation/semantic_noop_method_profile_v3_candidate_2026-08-04.md
?? reports/validation/semantic_noop_profile_identity_durability_2026-08-04.md
```

评审范围外既有脏项（`tests/test_codex_auto_routing.sh`、`tools/codex-auto.sh`）
保持原状。Index 为空，未暂存、未 commit、未 push。

## Fixed summary

```
P1_COUNT=0
P2_COUNT=0
P3_COUNT=0

READY_FOR_K3_RE_REVIEW=YES
READY_FOR_RUNTIME_EVIDENCE_REMEDIATION=NO
READY_FOR_COMMIT=NO
```
