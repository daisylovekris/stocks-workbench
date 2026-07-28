# r11 cumulative test matrix

Each ID is one executable design test; no range identifier is used.

| ID | Exact assertion |
|---|---|
| T01 | Legacy Daily Review without facts SHA blocks. |
| T02 | Valid covered 2026 calendar window succeeds. |
| T03 | Weekend inside coverage derives non-trading. |
| T04 | Missing calendar coverage blocks. |
| T05 | Cross-year dual calendars succeed. |
| T06 | Both equal and unequal calendar overlaps block. |
| T07 | Partial whitelist accepts only four named fields. |
| T08 | Missing/nonnumeric metric blocks. |
| T09 | Unknown/null/empty/other Phase C state blocks. |
| T10 | Both accepted Phase C states pass with permissions false. |
| T11 | Invalid request envelope creates atomic diagnostic. |
| T12 | Repeated diagnostic attempts use distinct IDs. |
| T13 | Phase B evidence missing blocks. |
| T14 | Phase B evidence invalid blocks. |
| T15 | Phase C evidence missing blocks. |
| T16 | Phase C evidence invalid blocks. |
| T17 | Phase C index resolver requires exactly one authority. |
| T18 | Safe read rejects symlink/replacement/hash-parse split. |
| T19 | Rebuilt Phase C without runner blocks. |
| T20 | Phase B or Phase C raw SHA change changes input set. |
| T21 | Semantic config raw SHA change changes input set. |
| T22 | Candidate schema raw SHA drift blocks at snapshot and commit. |
| T23 | Candidate semantics raw SHA drift blocks at snapshot and commit. |
| T24 | Same semantic completion supports verified no-op/index recovery only. |
| T25 | Dual legal orphan completions fail closed. |
| T26 | RFC3339 offset/Z conversion uses Shanghai cutoff. |
| T27 | Naive/date-only/free text/unknown time path blocks. |
| T28 | Provenance after cutoff remains admissible. |
| T29 | Request lock then sorted review locks then sorted facts locks is enforced. |
| T30 | AJV draft-2020 validates six accepted and rejects five invalid decimal fixtures. |
| T31 | Empty/missing metrics and forbidden trading/action fields reject. |
| T32 | Recursive unresolved safe_value rejects bare number and nested action field. |
| T33 | Five Phase C manifests generate 20 sorted nonempty unresolved items. |
| T34 | Golden candidate bytes validate against sealed schema. |
| T35 | Golden input-set canonical JSON recomputes to its recorded SHA. |
| T36 | Mapping, status and test matrices have no ranges, dangling IDs, duplicate IDs or omitted finding rows. |
| T37 | Golden candidate raw file bytes equal canonical reserialization bytes; no BOM or terminal LF. |
| T38 | Machine input-set schema validates exact fields and excludes paths/index evidence. |
| T39 | Five true Daily Review SHA values, not Phase C summaries, determine input-set SHA. |
| T40 | Five Phase B candidates and Phase B/C live-validation records match snapshot/raw identities. |
| T41 | Main-rule reason set equals closure-matrix reason set; mapping refs are known; semantic_noop is absent as completion reason. |
| T42 | Eleven AJV fixtures exist uniquely and execution JSON records command, exit code, stdout/stderr summaries. |
