# Candidate semantic contract v0.1

Canonical path: `rules/sunday_weekly_candidate_semantics_v0.1.md`. This file is identity-bearing raw UTF-8 bytes. The orchestrator reads it through `safe_file_read`; its bytes, SHA-256 and contract parse come from the same FD. At both the initial snapshot and final commit it must equal semantic config `candidate_semantics_raw_sha256`; otherwise `blocked_identity_conflict:candidate_semantics_identity_invalid`, all permissions false, retryable.

All facts are current Phase-C-authorized, Phase-B-live-revalidated daily facts. Parse every numeric source token to `Decimal` without binary float conversion; use precision=28 and `ROUND_HALF_EVEN`; execute the stated operation in date order; normalize only at final emission. Emit schema-canonical decimal strings: zero is `0`; never exponent, leading zero, `-0`, or insignificant fractional trailing zero. Amount unit is 亿 CNY.

| Metric | Facts JSON path | Unit | Ordered calculation | Normalize |
|---|---|---|---|---|
| week_open | first `$.quote.open` | CNY | first ascending trading date | final |
| week_high | every `$.quote.high` | CNY | max | final |
| week_low | every `$.quote.low` | CNY | min | final |
| week_close | last `$.quote.close` | CNY | last ascending trading date | final |
| weekly_change_pct | first `$.quote.prev_close`; last `$.quote.close` | percent | `(last_close / first_day_prev_close - 1) * 100` | after multiplication |
| total_amount | every `$.quote.amount` | 亿 CNY | sum in date order | final |
| average_amount | every `$.quote.amount` | 亿 CNY | sum / trading_day_count | after division |
| average_turnover_rate | every `$.quote.turnover_rate` | percent | sum / trading_day_count | after division |
| average_volume_ratio | every `$.volume_ratio.confirmed_value` | ratio | sum / trading_day_count | after division |
| trading_day_count | `$.trading_dates` | count | array length | integer |

`trading_dates` are ascending, unique, exactly the calendar window's trading dates; `trading_day_count` equals their length. `week_start` and `week_end` are the Monday/Friday that bracket the Asia/Shanghai Sunday `as_of_date` window.

`unresolved_fields` has one source only: every verified daily Phase C manifest `unresolved_fields`. Retain `source`, `field`, `value` unchanged, add that day `trade_date`, then sort `(trade_date, source, field)`. Never hand-fill, clear, deduplicate, or infer it. Recursive `safe_value` permits only JSON null/boolean/string/array/object; bare numbers are rejected unless first encoded as canonical decimal strings. Every object depth forbids `buy`, `sell`, `trade_instruction`, `action_signal`, `stop_loss`, `take_profit`, `auto_execute`, `approved`, `rejected`.

Canonical candidate bytes are UTF-8 JSON with `sort_keys=true`, `separators=(',', ':')`. Completion/no-op/index recovery rederive from current sealed inputs and require exact original-byte equality.
