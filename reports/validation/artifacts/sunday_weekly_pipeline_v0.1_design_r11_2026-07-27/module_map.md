# r11 module map

| Path | Size | SHA-256 | Reused contract | Boundary |
|---|---:|---|---|---|
| `tools/safe_file_read.py` | 3087 | `464f6b3b0cb0e17e96deedf1152201c86cb9070535030824fdfa77b1906689da` | same-FD bytes/SHA/parse | SWP may not add an alternate read path. |
| `tools/review_manifest.py` | 69330 | `fa7b6fb47588a9df2561fd6967d5a16db24f6c72e76b40c00cfd9f700ebcd8b7` | `review_lock_path`, Phase C schema rules | SWP does not copy lock hashing or mutate resolver. |
| `tools/phase_b_completion.py` | 15467 | `6628f70ce7cef35eaf8b7884c6fba8c1f2b769ee5e133195973f67dafca4f292` | `validate_completion_manifest` | SWP does not scan/select runners. |
| `rules/sunday_weekly_pipeline_v0.1.md` | 23213 | `f86b99c0cde0c4d6e4fc77dcb8d7e151d2679acd3dfb124ffb19052eb222899a` | orchestration contract | design only; no runtime implementation. |
| `rules/sunday_weekly_pipeline_semantic_config_v0.1.json` | 1458 | `4c00ed89d04efa457dae306d0a1db3ae0546a97f32342876cb622c1017b17996` | raw semantic identity | changes require new input set. |
| `rules/sunday_weekly_candidate_v0.1.schema.json` | 3515 | `b4a05b9418f951b80ab3d55c6fcd4ab068fef43bb2b9e8691a32029c1c87b0b3` | candidate validation | same-FD identity only. |
| `rules/sunday_weekly_candidate_semantics_v0.1.md` | 2920 | `300f08340889676d7d6bac92dc29cd1b0ff11ed742ad8d0e107da9e19f1cd086` | metric/unresolved semantics | same-FD identity only. |
