# 写入与锁顺序 r2

## Completion 路径

```text
weekly(symbol, week_end) lock
  -> facts locks by canonical pathname ascending
  -> safe snapshot: every classifying calendar/facts/review/Phase-C raw SHA
  -> release facts locks; validate + deterministic candidate assembly in tmp
  -> fsync tmp payloads
  -> reacquire same facts locks in same order; safe final reread + SHA equality
  -> atomic rename tmp -> completions/completion_<logical_run_key>; fsync parent
  -> append+fsync index.jsonl final completion marker
  -> release facts locks; release weekly lock
```

`index_recovered` 在同一 weekly lock 内进行与 normal completion 等强度的 live revalidation 后才可 append index。目录存在从不构成 completion。

## Blocked / failed 诊断路径

```text
gate failure or sanitized runtime failure
  -> allocate unique diagnostic_attempt_id (never input-derived)
  -> write tmp diagnostic.json + validation.json; fsync files + tmp
  -> atomic rename tmp -> diagnostics/diagnostic_<logical_run_key>_<attempt_id>
  -> acquire/hold weekly lock
  -> one O_APPEND record to diagnostics.jsonl; fsync file + parent
```

同输入的每一次失败都有独立 attempt 路径。诊断不写 `index.jsonl`，不创建 candidate/manifest/summary，也不参与任何 completion 判定。

## Lock error 路径

```text
cannot acquire weekly lock, or diagnostics append/fsync fails
  -> allocate unique diagnostic_attempt_id
  -> tmp write + fsync
  -> atomic rename -> lock-errors/diagnostic_<logical_run_key>_<attempt_id>
  -> fsync parent; do not append completion index
```

结果为 `failed:lock_error`。lock-error evidence 也永不参与 completion/no-op/index_recovered。
