# Module map r9

| Path | Size/SHA source | Reused contract |
|---|---|---|
| `tools/safe_file_read.py` | sealed snapshot | same-FD safe bytes |
| `tools/review_manifest.py` | sealed snapshot | pure validation + review_lock_path |
| `tools/phase_b_completion.py` | sealed snapshot | completion live validation |
| `tools/run_daily_facts_after_close.py` | sealed snapshot | real Phase B layout |
| Phase B/C rules | sealed snapshots | canonical external path/lock boundaries |
