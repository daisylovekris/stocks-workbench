# 股票小工坊 v0.3 Phase B：method-aware semantic_noop 时间路径 profile

## 边界

Phase B 仍只负责受控 official facts 写入；不创建或启用 launchd，不生成 review
manifest，不修改 review、current 卡、index、weekly。runner 默认不写正式文件，
必须显式选择 `--dry-run` 或 `--write-official` 之一。

本版本将 semantic_noop 的比较模式升级为
`method_profile_timestamp_paths_v3`，并保留 v1 / v2 历史 evidence 的原模式复算。

## semantic_noop 比较模式

新写入使用模式：

```text
method_profile_timestamp_paths_v3
```

排除集合只来源于受版本控制的权威 profile 配置：

```text
rules/semantic_noop_timestamp_profiles_v0.3.json
```

profile SHA（对配置解析结果的确定性 canonical JSON 计算，`sort_keys=True`、
`separators=(",", ":")`）：

```text
11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1
```

canonical JSON 参数：

```text
ensure_ascii=False
sort_keys=True
separators=(",", ":")
```

## 配置永久冻结与版本注册表

- 版本注册表：`rules/semantic_noop_timestamp_profile_registry_v0.1.json`
  （`active_profile_version` 当前为 `v0.3`）。
- 新 Phase B 写入只从 registry 的 `active_profile_version` 选取配置；只有状态为
  `active` 的版本允许新写入。
- 一旦某 profile version 产生正式 evidence，其配置文件永久冻结；后续路径矩阵
  变化必须创建新版本文件，禁止原地修改旧版本配置。
- registry 保留所有历史版本映射；`active` 可切换为 `frozen`（允许历史复算、
  禁止新写入）。
- 历史 manifest 始终按自身 `comparison.profile_version` 与
  `profile_sha256` 复算，禁止始终读取当前 active 配置。
- 删除历史配置属于破坏性变更，禁止执行。
- 未知 profile_version、registry 与配置身份不一致、历史配置缺失一律
  fail-closed。

## 共同必需路径

以下五条路径是所有 active profile 的 required_paths 子集（配置校验强制）：

- `generated_at`
- `quote_verification.fetched_at`
- `run.fetched_at`
- `volume_ratio.five_day_volume_check.fetched_at`
- `volume_ratio.verification.fetched_at`

## 已注册 method profile

逐一盘点四个已注册 volume_ratio verification method：

| method | 状态 | required timestamp paths |
|---|---|---|
| `same_day_snapshot_plus_sohu_five_day_cross_check` | active | 共同 5 条 + `volume_ratio.snapshot_ohlc_check.fetched_at` |
| `historical_five_day_volume_cross_check` | active | 共同 5 条 + `volume_ratio.source_volume_checks.sohu_history.fetched_at` + `volume_ratio.source_volume_checks.tencent_history.fetched_at` |
| `archived_tencent_snapshot_plus_sohu_historical_reverification` | active | 共同 5 条 + `volume_ratio.historical_ohlc_check.fetched_at` + `volume_ratio.legacy_verification.fetched_at` |
| `legacy_manual_confirmation` | blocked | 无法形成唯一 profile（无真实 v0.2 样本；生成器合并保留来源证据结构；automation_evidence 条件性出现），一律 fail-closed |

所有 profile 的 `optional_paths` 当前为空；`allow_list_index_paths=false` 全局与逐
method 生效。optional path 的存在条件由 `optional_presence_conditions[path]` 声明
（形如 `{"present_when_parent": "<对象路径>"}`），仅当条件对象在 payload 中存在时
该 optional path 才进入合法集合。

## fail-closed 规则

以下任一情况必须 `conflict_blocked` / `reason_code=official_conflict`，不得形成
`semantic_noop`，不得计算有效 semantic SHA：

- candidate 与 official 的 `volume_ratio.verification.method` 缺失或不相同；
- method 未知（无 profile 条目）或 profile 状态为 `blocked`；
- profile 内 required path 在任一侧缺失；
- 任一侧 discovered timestamp path 超出该侧合法集合（required ∪ 条件成立的
  optional）；
- candidate 与 official 的 discovered 路径集合或合法集合不对称；
- 出现列表索引 timestamp path（如 `a[0].fetched_at`）；
- 任一 discovered 时间值不是字符串或不是带时区合法 datetime；
- profile_version / profile_sha256 与权威配置不一致；
- 非时间业务字段、missing、needs_manual_check 或任何其它字段不同。

## comparison evidence 字段

`semantic_noop` evidence 必须完整记录：

`comparison_mode`、`profile_version`、`profile_sha256`、`verification_method`、
`required_paths`、`optional_paths`、`candidate_discovered_paths`、
`official_discovered_paths`、`candidate_missing_required_paths`、
`official_missing_required_paths`、`candidate_extra_paths`、
`official_extra_paths`、`all_values_valid_timezone_datetime`、
`candidate_raw_sha256`、`official_raw_sha256`、`candidate_semantic_sha256`、
`official_semantic_sha256`、`semantic_equal`、`official_changed`。

## v1 / v2 历史兼容

- v1 evidence（`comparison_mode=approved_timestamp_paths_v1`）仍按固定六路径规则
  复算，六路径必须双方存在、值为合法带时区 datetime；
- v2 evidence（`comparison_mode=symmetric_timestamp_leaf_paths_v2`）仍按旧动态
  递归规则复算（对称集合 + `REQUIRED_V2_TIMESTAMP_PATHS`）；
- 禁止用 v3 重解释历史 v1 / v2 manifest；dispatch 按 evidence 自身 mode 显式分派。

## 正式写入

`semantic_noop` 仅在 profile 校验全部通过、现场复算一致且 evidence 与 manifest
逐字段一致时返回；official 字节保持不变，`outcome=official_unchanged`，
`official_changed=false`。其它 existing-official 策略（identical_noop、created、
sealed_blocked、manual_blocked、conflict_blocked）与 v0.2 一致。
