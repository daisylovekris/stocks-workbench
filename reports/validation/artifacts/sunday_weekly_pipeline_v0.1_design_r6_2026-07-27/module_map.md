# 跨阶段模块地图 r6

| Path | Bytes | SHA-256 | SWP reuse | 不得改变的边界 |
|---|---:|---|---|---|
| `tools/run_daily_facts_after_close.py` | runtime snapshot | `ea383fd67eb0e05235fb1ec0592e09dd7540642bbdccd59ba06094892cb6bfbe` | Phase B `runs/<date>/<run_id>/manifest.json` layout | SWP 不扫描或选择 runs。 |
| `tools/phase_b_completion.py` | runtime snapshot | `6628f70ce7cef35eaf8b7884c6fba8c1f2b769ee5e133195973f67dafca4f292` | `validate_completion_manifest` | full live evidence validation, not a shortcut. |
| `tools/review_manifest.py` | runtime snapshot | `fa7b6fb47588a9df2561fd6967d5a16db24f6c72e76b40c00cfd9f700ebcd8b7` | `read_index`, `inspect_index_entry` | index is authority; manifest path/SHA identity checks remain. |
| `rules/run_daily_facts_after_close_phase_b_v0.2.md` | rule snapshot | `65ae9a711fb6e3785c9e58deb7d1eaa46908be0e64808425843c1110369c1813` | Phase B completion contract | official write/read controls unchanged. |
| `rules/review_manifest_phase_c_v0.2.md` | rule snapshot | `1d9ed3101594b12cea127f459b6e195d94098912fa6308508be74d1f441b0cc8` | reviews index / rebuild semantics | review_index final-marker and rebuild policy unchanged. |
