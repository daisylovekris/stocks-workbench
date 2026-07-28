# Canonical package 算法 r2

`review_bundle_manifest.json` 的 `files` 是本包 payload（不含 `review_bundle_manifest.json`、`file_sha256_manifest.md`）的仓库相对 path、size_bytes、SHA-256，按 UTF-8 pathname 升序排列。

`package_sha256` 为 UTF-8 canonical JSON `{"files":[...]}` 的 SHA-256，使用 `sort_keys=true` 和 `separators=(',', ':')`。每个 file 条目仅含 `path`、`size_bytes`、`sha256`；package SHA 与两份身份元数据不进入输入，消除自指循环。`file_sha256_manifest.md` 表中 `Path` 一律相对 `bundle_root`；manifest JSON 中 `files[].path` 一律相对仓库根。任何 byte、路径、大小或排序变化都会改变 package SHA。

SWP candidate 的 canonical digest 与该 review package digest 完全分离；candidate 不得含生成时间、run id、host、pid、路径、锁等待或任何 diagnostic metadata。
