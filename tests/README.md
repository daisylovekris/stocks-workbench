# validate_review_chain.py Regression Fixtures

This directory contains fixture-based regression tests for `tools/validate_review_chain.py`.

Disciplines:

1. `should_pass` must produce zero findings. P3 noise is still noise.
2. When a new false positive or false negative is found, add a fixture first, then update the validator.
3. Fixture names must identify the rule id and case type clearly.
