# 写锁与诊断路径 r4

唯一锁为：

```text
<runtime>/locks/sunday_weekly_request_<request_key>.lock
```

```text
compute safe-envelope request_key
 -> acquire the single request-key lock
 -> early failure: tmp + fsync -> requests/<request_key>/diagnostics/diagnostic_<attempt>
 -> O_APPEND diagnostics.jsonl + fsync

complete input set -> validate tmp -> final reread under same lock
 -> rename -> runs/<logical_run_key>/completions/completion_<semantic_key>_<attempt>
 -> index six exact identity fields + fsync

cannot acquire lock / diagnostic append failure
 -> tmp + fsync -> requests/<request_key>/lock-errors/diagnostic_<attempt>
 -> failed:lock_error, never a completion index
```

No raw request data enters a pathname. Old/damaged orphan completion directories are preserved and never overwritten; duplicate valid same-semantic orphans are fail-closed.
