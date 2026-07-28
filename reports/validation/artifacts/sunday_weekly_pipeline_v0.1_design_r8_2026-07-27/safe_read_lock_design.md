# Safe-read and Phase C concurrency design r8

Same-FD safe reads cover index, review manifest, runner and official files. Lock order is request-key orchestration → review locks canonical order → official facts locks canonical order. Initial snapshot and final commit use the same order. Under final locks re-resolve authority; exactly one remains required. Tests cover index append, 1→2 authority, suffix review, facts+Phase C change, reverse-order detection, and two SWP processes plus a Phase C writer.
