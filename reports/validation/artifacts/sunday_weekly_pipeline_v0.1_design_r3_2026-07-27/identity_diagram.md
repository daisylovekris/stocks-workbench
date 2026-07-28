# Request / logical / completion / attempt 身份图

```text
raw request
  -> safe canonical request identity
     {symbol, canonical_as_of_date, mode, candidate_schema_version}
  -> sha256 -> request_key
     | early calendar/facts/review/Phase-C failure
     +-> diagnostic_attempt_id -> requests/<request_key>/diagnostics/diagnostic_<attempt>
     +-> lock failure          -> requests/<request_key>/lock-errors/diagnostic_<attempt>

complete input set only
  -> input_set_sha256
  -> sha256({request_key,input_set_sha256}) -> logical_run_key
  -> candidate_sha256
  -> sha256({logical_run_key,input_set_sha256,candidate_sha256})
       -> semantic_completion_key
  -> completion_attempt_id
       -> runs/<logical_run_key>/completions/
          completion_<semantic_completion_key>_<completion_attempt_id>
```

All directory tokens are fixed literals or lower-case hex digest/attempt tokens. Raw symbol, date and invalid raw parameter data never enter a path. A diagnostic records available_inputs, missing_inputs, raw SHA and optional observed_input_digest; it never invents input_set_sha256.
