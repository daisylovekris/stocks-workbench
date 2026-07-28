# 锁与两类写入路径 r1

## 成功 / completion 路径

```text
weekly(symbol, week_end) lock
  -> facts locks by canonical pathname ascending
  -> safe snapshot: all calendar/facts/review/Phase-C raw SHA
  -> release facts locks; validate + deterministic candidate assembly in tmp
  -> fsync tmp payloads
  -> reacquire same facts locks in same order; safe final reread + SHA equality
  -> atomic rename tmp -> completion run directory; fsync parent
  -> append+fsync index.jsonl final completion marker
  -> release facts locks; release weekly lock
```

`index_recovered` follows this same completion-grade live validation before its index append. No directory is promoted from existence alone.

## Blocked / failed 诊断路径

```text
detect a gate failure or sanitized runtime failure
  -> write tmp diagnostic/{diagnostic.json,validation.json}; fsync files + tmp
  -> atomic rename tmp diagnostic -> diagnostic run directory; fsync parent
  -> append+fsync one diagnostics.jsonl record
```

诊断路径不写 `index.jsonl`，不创建 candidate/manifest/summary，也不参与任一完成判定；新 run 不受其压制。锁只协调合约 writer，安全读取与最终复读仍为必过门。
