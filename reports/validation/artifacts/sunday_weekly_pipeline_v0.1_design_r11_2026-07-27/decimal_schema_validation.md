# Real JSON Schema validation: r11 decimals

Validator: `ajv-cli@5.0.0`, draft 2020-12, against sealed `sunday_weekly_candidate_v0.1.schema.json` context. Each fixture contains a complete candidate; nonnegative values are placed in `metrics.week_open`, signed negatives in `metrics.weekly_change_pct`.

| Value | Expected | AJV result |
|---|---|---|
| `0` | accept | PASS |
| `0.74` | accept | PASS |
| `-0.74` | accept | PASS |
| `1` | accept | PASS |
| `1.25` | accept | PASS |
| `-11.2` | accept | PASS |
| `01` | reject | FAIL |
| `1.0` | reject | FAIL |
| `1.00` | reject | FAIL |
| `-0` | reject | FAIL |
| `1e3` | reject | FAIL |

This is actual validator execution, not a regex prose assertion.
