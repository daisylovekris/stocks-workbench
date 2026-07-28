# Exact cumulative test matrix r9

| ID | Assertion |
|---|---|
| T01-T17 | Exact finding rows in `cumulative_finding_mapping.md`; no range ID substitutes a finding. |
| T18 | schema safe-read SHA drift blocks; config+schema aligned change creates new input set. |
| T19 | empty metrics / each missing metric / metrics.buy rejected. |
| T20 | top-level and nested forbidden action fields rejected. |
| T21 | `01`, `1.0`, `1.00`, `-0` rejected; only canonical decimals accepted. |
| T22 | unresolved structured item retained and sorted by trade_date/source/field. |
| T23 | review lock path exactly equals Phase C writer function result. |
| T24 | matrix has no range IDs or dangling IDs. |
| T25 | package recomputes from migrated bundle root. |
