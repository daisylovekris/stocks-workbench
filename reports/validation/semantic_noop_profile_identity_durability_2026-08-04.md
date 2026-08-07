# Semantic Noop Profile Identity Durability Validation (2026-08-04)

## Context

HEAD: `1ecfb2fd932230ac86bd890797c15fa7fa37b431`

This round hardens semantic_noop method-profile v3 historical identity lifetime
and configuration parsing per K3 final review (1 P2 + 2 P3).  The v0.3 profile
business path matrix is unchanged and the v0.3 canonical profile SHA is
unchanged:

```text
11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1
```

## K3 findings addressed

| ID | severity | finding | fix |
|---|---|---|---|
| P2-1 | P2 | v3 historical evidence recompute bound to the current active config; no version registry identity | registry `rules/semantic_noop_timestamp_profile_registry_v0.1.json` + manifest `profile_version` dispatch |
| P3-1 | P3 | JSON parsing accepted duplicate keys and unknown fields | `object_pairs_hook` duplicate-key rejection + strict top-level/profile/condition field whitelists |
| P3-2 | P3 | canonical JSON parameters not documented in rules | both v0.3 rule docs now state `ensure_ascii=False`, `sort_keys=True`, `separators=(",", ":")` |

## Registry identity

```json
{
  "schema_version": "semantic_noop_timestamp_profile_registry_v0.1",
  "active_profile_version": "v0.3",
  "profiles": {
    "v0.3": {
      "path": "rules/semantic_noop_timestamp_profiles_v0.3.json",
      "comparison_mode": "method_profile_timestamp_paths_v3",
      "profile_sha256": "11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1",
      "status": "active"
    }
  }
}
```

## 冻结策略

- 一旦某 profile version 产生正式 evidence，其配置文件永久冻结；后续路径矩阵
  变化必须创建新版本文件，禁止原地修改旧版本配置。
- registry 保留所有历史版本映射；`active` 可切换为 `frozen`（历史复算允许、
  新写入禁止）；删除历史配置属于破坏性变更，禁止执行。
- 新 Phase B 写入只从 `active_profile_version` 选取配置。
- 历史 v3 evidence 复算从 manifest `comparison.profile_version` 选取配置，复算
  该版本 canonical SHA 并必须等于 manifest `profile_sha256`；禁止始终读取当前
  active 配置。
- Phase B completion 与 Phase C 使用同一 `oft.load_method_profile_registry()` /
  `oft.resolve_profile_for_version()` 加载与分派。

## 严格 JSON 解析

- `object_pairs_hook` 在任意层级拒绝重复 key。
- 顶层字段全集：`schema_version`、`profile_version`、`comparison_mode`、
  `common_required_paths`、`allow_list_index_paths`、`profiles`。
- active profile 字段全集：`required_paths`、`optional_paths`、
  `optional_presence_conditions`、`allow_list_index_paths`（禁止 reason）。
- blocked profile 字段全集：上述 + `profile_status`、`reason`；required /
  optional / conditions 必须为空，reason 必须为非空字符串。
- condition 字段全集：仅 `present_when_parent`。
- 未知字段一律拒绝；布尔必须为真 `bool`（`allow_list_index_paths` 必须
  `is False`）。
- registry 顶层字段全集：`schema_version`、`active_profile_version`、
  `profiles`；entry 字段全集：`path`、`comparison_mode`、`profile_sha256`、
  `status`。
- registry 路径必须为 `rules/<file>.json` 相对路径，禁止绝对路径、父目录逃逸
  与符号链逃逸；同一 profile SHA 不得映射多个版本；未知 profile_version 一律
  失败。

## canonical 参数

```text
ensure_ascii=False
sort_keys=True
separators=(",", ":")
```

`test_canonical_ensure_ascii_false_recompute` 验证非 ASCII 保留为 UTF-8（无
`\u` 转义）并锁定 v0.3 SHA `11bb039d…`；规则文档同步写明参数。

## 测试矩阵（20 项）

| # | 场景 | 测试 |
|---|---|---|
| 1 | v0.3 active 新写入使用 v0.3 | `test_v03_active_new_write_uses_v03` |
| 2 | v0.3 frozen 历史 evidence 仍可复算 | `test_v03_frozen_history_recomputable_and_active_switch_preserves_history` |
| 3 | active 切换模拟 v0.4 后旧 v0.3 evidence 仍通过 | 同上 |
| 4 | 新写入改用模拟 v0.4 | `test_new_write_uses_simulated_v04` |
| 5 | 未知 profile_version 阻断 | `test_unknown_profile_version_blocked` |
| 6 | registry 记录 SHA 与配置不符阻断 | `test_registry_sha_mismatch_blocked` |
| 7 | manifest profile SHA 与历史配置不符阻断 | `test_manifest_profile_sha_mismatch_historical_blocked` |
| 8 | 历史配置缺失阻断 | `test_missing_historical_config_blocked` |
| 9 | registry 路径逃逸阻断 | `test_registry_path_escape_blocked` |
| 10 | registry 重复 key 阻断 | `test_registry_duplicate_key_blocked` |
| 11 | profile JSON 重复 key 阻断 | `test_profile_json_duplicate_key_blocked` |
| 12 | 顶层未知字段阻断 | `test_unknown_top_level_field_blocked` |
| 13 | profile 条目未知字段阻断 | `test_unknown_profile_field_blocked` |
| 14 | condition 未知字段阻断 | `test_unknown_condition_field_blocked` |
| 15 | blocked profile 携带 required path 阻断 | `test_blocked_profile_with_required_path_blocked` |
| 16 | blocked profile 缺少 reason 阻断 | `test_blocked_profile_missing_reason_blocked` |
| 17 | active profile 携带 reason 阻断 | `test_active_profile_with_reason_blocked` |
| 18 | canonical 参数含 ensure_ascii=False 的复算测试 | `test_canonical_ensure_ascii_false_recompute` |
| 19 | v1 / v2 历史复算不受 registry 影响 | `test_v1_v2_recompute_unaffected_by_registry` |
| 20 | Phase B / Phase C 对 v3 历史版本分派结果等价 | `test_phase_b_phase_c_historical_version_dispatch_equivalent` |

模拟 v0.4 仅写测试临时目录，未新增正式 v0.4 配置。

## 测试命令与结果

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q -p no:cacheprovider tests/test_run_daily_facts_after_close.py tests/test_review_manifest.py
# 369 passed

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q -p no:cacheprovider tests
# 630 passed, 28 subtests passed
```

全程未运行 `--write-official`、未生成 Phase B / Phase C 正式 runtime 对象、
未修改 facts、日复盘、卡组、index、weekly、calendar；v0.3 业务路径矩阵与
canonical SHA 未变化。

## 工作区边界

候选机制累计修改/新增：

```text
M tools/official_facts_transaction.py
M tools/phase_b_completion.py
M tools/review_manifest.py
M tests/test_run_daily_facts_after_close.py
M tests/test_review_manifest.py

?? rules/run_daily_facts_after_close_phase_b_v0.3.md
?? rules/review_manifest_phase_c_v0.3.md
?? rules/semantic_noop_timestamp_profile_registry_v0.1.json
?? reports/validation/semantic_noop_method_profile_v3_candidate_2026-08-04.md
?? reports/validation/semantic_noop_profile_identity_durability_2026-08-04.md
```

评审范围外既有脏项（`tests/test_codex_auto_routing.sh`、
`tools/codex-auto.sh`）保持原状。Index 为空，未暂存、未 commit、未 push。

## Fixed summary

```
PROFILE_REGISTRY_CREATED=YES
ACTIVE_PROFILE_VERSION=v0.3
V03_PROFILE_SHA_UNCHANGED=YES

HISTORICAL_PROFILE_DISPATCH_IMPLEMENTED=YES
V03_FROZEN_EVIDENCE_RECOMPUTABLE=YES
ACTIVE_VERSION_SWITCH_PRESERVES_V03_HISTORY=YES
UNKNOWN_PROFILE_VERSION_BLOCKED=YES
MISSING_HISTORICAL_CONFIG_BLOCKED=YES

DUPLICATE_JSON_KEYS_BLOCKED=YES
UNKNOWN_TOP_LEVEL_FIELDS_BLOCKED=YES
UNKNOWN_PROFILE_FIELDS_BLOCKED=YES
UNKNOWN_CONDITION_FIELDS_BLOCKED=YES
BLOCKED_PROFILE_SCHEMA_ENFORCED=YES

CANONICAL_ENSURE_ASCII_FALSE_DOCUMENTED=YES

V1_COMPATIBILITY_PASS=YES
V2_COMPATIBILITY_PASS=YES
V3_PHASE_B_PHASE_C_EQUIVALENT=YES

TARGETED_TESTS_PASS=YES
FULL_TESTS_PASS=YES

P1_COUNT=0
P2_COUNT=0
P3_COUNT=0

READY_FOR_K3_RE_REVIEW=YES
READY_FOR_RUNTIME_EVIDENCE_REMEDIATION=NO
READY_FOR_COMMIT=NO

INDEX_EMPTY=YES
STAGED=NO
COMMITTED=NO
PUSHED=NO
```
