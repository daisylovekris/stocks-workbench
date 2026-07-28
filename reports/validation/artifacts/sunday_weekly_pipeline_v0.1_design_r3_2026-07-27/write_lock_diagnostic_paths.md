# 写锁与诊断路径 r3

```text
request_key computed before any input lookup
  -> acquire requests/<request_key> lock
  -> early gate fails: tmp diagnostic -> fsync ->
     requests/<request_key>/diagnostics/diagnostic_<diagnostic_attempt_id>
  -> one O_APPEND diagnostics.jsonl record -> fsync file + parent

complete inputs -> logical_run_key -> candidate -> semantic_completion_key
  -> validate in tmp -> fsync -> final reread under same request lock ->
     atomic rename to completion_<semantic_key>_<completion_attempt_id>
  -> index row with semantic key/input SHA/candidate SHA/attempt/relative path/manifest SHA
  -> fsync index + parent

lock unavailable or diagnostic append/fsync unavailable
  -> tmp evidence -> fsync ->
     requests/<request_key>/lock-errors/diagnostic_<diagnostic_attempt_id>
  -> failed:lock_error; no completion index
```

The lock token and every path component are fixed text or lower-case hex. Old, damaged, or unindexed physical completion directories are never deleted or overwritten. A unique valid orphan may recover its index; duplicate valid orphans sharing one semantic key are blocked as ambiguous.
