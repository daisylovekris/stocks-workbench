# Canonical package 算法 r5

`review_bundle_manifest.json.files` contains every r5 review material, including rule/body/Fable/golden snapshots, inventory, semantic config, mapping, status, tests, lock document and prompt. Each entry is repository-relative path, size_bytes and SHA-256 sorted by UTF-8 path. `package_sha256` is SHA-256 of canonical JSON `{"files":[...]}` with sorted keys and compact separators.

The review manifest and readable file manifest are identity metadata and do not self-include. The outer formal report alone records all three SHA. No review material is excluded from package SHA.
