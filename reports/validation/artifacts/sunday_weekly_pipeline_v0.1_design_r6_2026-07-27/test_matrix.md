# 测试矩阵 r6

| ID | 情形 | 断言 |
|---|---|---|
| X01 | 真实 Phase B `runs/<date>/<run_id>/manifest.json` | validator 接受真实布局。 |
| X02 | 真实 Phase C `reviews/<date>/review_index.jsonl` | index 是唯一入口。 |
| X03 | Phase C index 指向合法 runner | Phase C resolver 后才复验 Phase B。 |
| X04 | 同日多个 Phase B manifests | 仅使用 Phase C 已认证引用。 |
| X05 | index path/manifest SHA 非法 | `phase_c_evidence_invalid`。 |
| X06 | suffix review directory | index canonical path 正确定位。 |
| X07 | 两个冲突合法 authority | `ambiguous_phase_c_authority` fail-closed。 |
| X08 | rebuild_from_official 无 Phase B | `phase_b_evidence_missing`，全 false。 |
| X09 | semantic config exact bytes | raw SHA 重算完全一致。 |
| X10 | semantic config 字段变更 | 新 input set。 |
| X11 | 静态路径扫描 | 不存在 `/phase-b/<symbol_sha256>/` 或 `/phase-c/<symbol_sha256>/`。 |
