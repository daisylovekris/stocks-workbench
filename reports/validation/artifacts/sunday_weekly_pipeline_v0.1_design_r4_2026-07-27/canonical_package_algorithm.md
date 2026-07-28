# Canonical package 算法 r4

`review_bundle_manifest.json.files` 列出**全部 bundle 审查材料**：每项的仓库相对 path、size_bytes、SHA-256，按 UTF-8 pathname 升序。特别地，identity-free `snapshots/design_validation_body.md` 是审查材料且必须在 files 中。`package_sha256=sha256(UTF-8 canonical JSON {"files":[...]})`，使用 `sort_keys=true`、`separators=(',', ':')`；条目只含 path/size_bytes/sha256。

`review_bundle_manifest.json` 与 `file_sha256_manifest.md` 是描述并固定 package 的身份元数据，不是被审查的设计材料，因而不进入其自身的 files，避免不可解自指。外层正式验证报告持有 package、review manifest、file manifest 三枚 SHA；它不在 bundle 内。不存在“被排除的报告快照仍为字节封存成员”。任何 bundle 审查材料都必须在 `files`，因此受 package SHA 覆盖。
