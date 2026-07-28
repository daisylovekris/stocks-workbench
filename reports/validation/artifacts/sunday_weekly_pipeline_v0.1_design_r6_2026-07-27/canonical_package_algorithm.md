# Canonical package 算法 r6

`review_bundle_manifest.json.files` includes every r6 review material: rules/config snapshots, identity-free body, Fable, implementation/rule evidence snapshots, module map, mapping, matrix, lock document and prompt. Entries are repository-relative path/size/SHA sorted by UTF-8 path. Package SHA is canonical compact sorted JSON `{ "files": [...] }` SHA-256. The two identity metadata manifests do not self-include; no review material is excluded.
