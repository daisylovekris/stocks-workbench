# Canonical package algorithm r8

From any r8 bundle root, recursively enumerate every regular review material except `review_bundle_manifest.json` and `file_sha256_manifest.md`; sort UTF-8 relative paths; derive each `{path,size_bytes,sha256}`; canonicalize `{"files":[...]}` with sorted keys and compact separators; SHA-256 it. `review_bundle_manifest.json.package_hash_algorithm` records this exact method. No old package is needed.
