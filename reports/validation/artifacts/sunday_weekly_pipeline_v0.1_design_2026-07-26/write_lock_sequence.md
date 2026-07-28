# 写入与锁顺序图

```text
acquire weekly(symbol, week_end) lock
  ├─ acquire facts locks in canonical pathname ascending order
  │    └─ safe read facts bytes + SHA snapshot
  ├─ release all facts locks
  ├─ validate calendar / facts / Daily Reviews / Phase C / cutoff
  ├─ recompute metrics; write+fsync tmp/{candidate,manifest,summary,validation}
  ├─ reacquire same facts locks in same order
  │    └─ safe re-read all bytes; every SHA must equal snapshot
  ├─ atomic rename tmp -> final run directory; fsync parent
  ├─ append+fsync one index.jsonl line (final completion marker)
  ├─ release facts locks
  └─ release weekly lock
```

禁止反转顺序，禁止先取 facts lock 再取 weekly lock，禁止 index 先于完整候选目录。若任何最终 SHA 变化，丢弃本次临时产物，写 `blocked_invalid_facts:facts_sha_drift` 证据，不提交候选。

