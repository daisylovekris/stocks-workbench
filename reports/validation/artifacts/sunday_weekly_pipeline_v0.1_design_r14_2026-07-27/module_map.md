# r14 module map

| path | size | SHA-256 | reused contract | boundary |
|---|---:|---|---|---|
| snapshots/rules/sunday_weekly_pipeline_v0.1.md | 23456 | 733da074ff9e3d6b85fc2da1da70d95d3a9e201b6968555a248a2a5a1506db33 | final state tuple contract | design-only rule |
| snapshots/rules/sunday_weekly_pipeline_semantic_config_v0.1.json | 1739 | d1d174025b34d1c2fa9c2b9660944f2a1f6403ca7712023aad9e343ac57a0ba4 | semantic identities | no guessed paths |
| snapshots/rules/sunday_weekly_input_set_v0.1.schema.json | 1312 | 2bf047907dabf0006c60aa8934b8a64a020040f3c120d95839ebc427cf6634a1 | input-set schema | same-FD identity |
| snapshots/rules/sunday_weekly_input_set_v0.1.md | 2122 | 9a04b88c54d5a6458aa3b8ffc7b4531c3d46830e490c20c209e70957686934da | input-set contract | same-FD identity |
| phase_b_actual_validator_execution.json | 6633 | c864aa42090699514e8eefc28d8eb44631286a71d3450bda895c0257dfb05f70 | actual validator execution | read-only evidence |
| phase_c_authority_derivation_ledger.json | 5782 | de7f2fd3570dfc7b0025123fd200aa43480ed453d6c53004da696378198f0383 | authority derivation | not validator execution |
| r14_tuple_static_validation.json | 5388 | b821333f6e75f4b62f3378ca92fe88bdc53863e6f19830025d7dafc7738fd57b | tuple static validation | closure evidence |
