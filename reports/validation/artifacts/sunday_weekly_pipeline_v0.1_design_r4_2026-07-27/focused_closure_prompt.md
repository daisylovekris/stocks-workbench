# Focused Closure Prompt r4

只审 Sunday Weekly Pipeline v0.1 design r4，只读取本 bundle；不读取 r3 包、其他外部材料或实现代码，也不要求 runner、Git、网络或 Fable 调用。

调用任务必须在 bundle 外提供并先核对：`package_sha256`、`review_bundle_manifest_sha256`、`file_sha256_manifest_sha256`。核对后审所有 manifest.files 材料，尤其 `snapshots/design_validation_body.md`、规则快照、finding mapping、时间标准、身份图、状态/测试矩阵和写锁路径；确认没有审查材料逃离 package SHA 覆盖。

重点反证：mapping 的每个 test ID 是否真实存在且语义一致；facts_pack_v0.2 的时间字段是否按内部 normalized source_kind 正确处理；四字段 invalid envelope 是否不泄漏原值；全规则是否只有 request-key lock。输出 `P1`、`P2`、`P3`、`FOCUSED_CLOSURE_READY`，未闭合项必须给出 bundle 内精确文件/条款/测试缺口。
