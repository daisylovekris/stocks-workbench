# 身份图 r4

```text
four raw request fields
  -> per-field safe envelope: valid normalized value OR invalid metadata only
  -> canonical JSON -> request_key
  -> locks/sunday_weekly_request_<request_key>.lock
  -> early diagnostics: requests/<request_key>/diagnostics/diagnostic_<attempt>
  -> lock errors: requests/<request_key>/lock-errors/diagnostic_<attempt>

complete inputs -> input_set_sha256 -> logical_run_key
candidate bytes -> candidate_sha256 -> semantic_completion_key
new completion_attempt_id -> completion_<semantic_key>_<attempt>
```

Only fixed literal text and lower-case hexadecimal tokens enter runtime paths. Raw symbol, date, mode, schema version and all invalid raw values are absent from paths, logs and diagnostic prose.
