# Canonical package algorithm r9

`files[].path` is relative to `bundle_root`. Enumerate all review materials except two self-identity manifests, sort UTF-8 relative paths, collect `{path,size_bytes,sha256}`, canonicalize `{"files":[...]}` with sorted keys/compact separators, SHA-256. `base_head` fixes the source revision. Rebuild requires only this bundle root.
