# Canonical package 算法 r3

本 bundle 包含全部列出的材料。为消除“最终验证报告必须写入三枚自身身份 SHA”产生的不可解自指循环，sealing input 是 `review_bundle_manifest.json.files` 所列文件，且**排除** `review_bundle_manifest.json`、`file_sha256_manifest.md` 与 `snapshots/reports/validation/sunday_weekly_pipeline_v0.1_design_r3_2026-07-27.md`。后者仍是 bundle 的必备、字节封存成员，但不参与 package SHA；它记录完成后从零复算得到的三枚 SHA。

`files` 条目是仓库相对 path、size_bytes、SHA-256，按 UTF-8 pathname 升序。`package_sha256=sha256(UTF-8 canonical JSON {"files":[...]})`，采用 `sort_keys=true`、`separators=(',', ':')`。条目只含 path/size_bytes/sha256。`file_sha256_manifest.md` 的表中 path 相对 bundle_root；它列出 sealing input，故本身和报告快照不在表中。任何 sealing input 的 byte、路径、大小或排序变动都会改变 package SHA。

SWP candidate digest 与本审查包 digest 分离；candidate 不得含生成时间、host、路径、任意 attempt id 或 diagnostics metadata。
