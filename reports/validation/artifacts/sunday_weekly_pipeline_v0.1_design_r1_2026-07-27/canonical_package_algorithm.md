# Canonical package 算法

`review_bundle_manifest.json` 的 `files` 是本包 payload（不含 `review_bundle_manifest.json`、`file_sha256_manifest.md`）的仓库相对路径、size_bytes、SHA-256，按 UTF-8 pathname 升序排列。

`package_sha256` 的输入是 UTF-8 编码 canonical JSON：`{"files":[...]}`，`sort_keys=true`、`separators=(',', ':')`。每个 file 条目仅含 `path`、`size_bytes`、`sha256`，`package_sha256` 自身和两份身份元数据不进入输入，避免自指循环。任何 byte、路径、大小或排序变化都会改变 package SHA。

候选的 deterministic canonical digest 与审查包 package digest 分离：前者不得包含生成时间、run id、host、pid、路径、锁等待或 diagnostics 等易变运行 metadata。
