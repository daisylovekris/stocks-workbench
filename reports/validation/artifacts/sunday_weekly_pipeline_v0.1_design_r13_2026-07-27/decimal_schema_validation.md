# r12 AJV evidence

Eleven exact fixture files are sealed in ajv_fixtures; ajv_execution.json records the literal command template, per-fixture exit code and stdout/stderr summaries. Validator: npx --yes ajv-cli@5.0.0 validate --spec=draft2020.

Accepted (exit 0): 0, 0.74, -0.74, 1, 1.25, -11.2.

Rejected (exit 1): 01, 1.0, 1.00, -0, 1e3.

The input-set and exact golden candidate were separately validated by the same AJV draft-2020 command.
