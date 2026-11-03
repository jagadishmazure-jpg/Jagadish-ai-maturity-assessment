# ADR 0001: Keep the maturity model and the scoring rubric separate

**Status:** Accepted

## Context

The maturity model says what good looks like: dimensions, capabilities, level descriptors, actions and
the standards crosswalk. The rubric says how evidence proves a level: signals, questions, must and
support criteria, effort, dependencies and anchors. They change for different reasons and are read by
different people: leaders read descriptors, engineers tune evidence rules.

## Decision

`framework/framework.yaml` holds the Enterprise Agentic AI Maturity Model (see ADR 0007).
`rubric/` holds signals, questions and the per-level evidence rules. Code reads both, and
`check_consistency()` ties them together: same capabilities, weights that sum to one, an anchor per
dimension, an artifact in every Scale and Optimise must list, and every signal used.

## Consequences

* A descriptor can be reworded without touching scoring, and an evidence rule can be tightened without
  touching the model; the calibration gate shows whether the two still agree.
* An organisation can keep the model and replace the rubric with its own evidence, or the reverse.
* `aimaturity validate` and the consistency test must pass after every change to either.
