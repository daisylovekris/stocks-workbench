# 股票小工坊 v0.3 Phase C：method-aware semantic_noop evidence 校验

## 边界

Phase C 仍是 official facts 的确定性只读模型：不修改 review、card、index、
weekly、facts 或 Git 文件；runtime review manifest 与 append-only index 是唯一
提交物。下游权限（review/current_cards/index/weekly/git/trading）全部保持
`false`。

## semantic_noop evidence 校验

Phase C 与 Phase B 对 semantic_noop 使用同一比较模式与同一现场复算：

```text
method_profile_timestamp_paths_v3
```

校验项与 Phase B 完全等价：

- comparison 字段全集相同（v3 的 19 个 evidence 字段）；
- 同一 profile 身份：`profile_version` 与 `profile_sha256` 必须等于权威配置
  `rules/semantic_noop_timestamp_profiles_v0.3.json` 的当前值
  （profile SHA `11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1`，
  对配置 canonical JSON 计算；canonical 参数为 `ensure_ascii=False`、
  `sort_keys=True`、`separators=(",", ":")`）；
- 同一 `verification_method` 与同一 required/optional 集合；
- 同一 live recomputation：Phase C 用 manifest 记录的 mode 重新调用比较器，结果
  必须与 manifest evidence 逐字段相等；
- candidate 与 official 必须使用同一 method；未知 method、blocked profile、
  profile 外时间路径、列表索引路径、required 缺失、值非法、非时间差异全部
  fail-closed，映射为 incident review / `needs_manual_review`。

## v1 / v2 历史兼容

- `comparison_mode=approved_timestamp_paths_v1`：按固定六路径规则复算；
- `comparison_mode=symmetric_timestamp_leaf_paths_v2`：按旧动态递归规则复算；
- 不得用 v3 重解释历史 v1 / v2 manifest；mode 未知即拒绝。

## 配置永久冻结与版本注册表

- 版本注册表：`rules/semantic_noop_timestamp_profile_registry_v0.1.json`。
- 历史 v3 evidence 复算从 registry 按 manifest 记录的 `profile_version` 选取
  配置，复算该配置 canonical SHA 并必须等于 manifest 记录的
  `profile_sha256`；禁止始终读取当前 active 配置。
- 一旦某 profile version 产生正式 evidence，其配置文件永久冻结；路径矩阵变化
  必须创建新版本文件，禁止原地修改旧版本配置。
- registry 保留所有历史版本映射；`active` 可切换为 `frozen`；删除历史配置属于
  破坏性变更，禁止执行。
- 未知 profile_version、registry/配置身份不一致、历史配置缺失一律 fail-closed。

## review state

与 v0.2 一致：`ready_for_human_review` 仅当 facts 完整、Validator 通过、
Phase B 完成事务成立、无 incident；`rebuild-from-official` 或任何 incident 一律
`needs_manual_review`。
