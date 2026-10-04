# ADR 0001: Keep the framework model and the scoring rubric separate

**Status:** Accepted

## Context

The framework structure (pillars, categories, levels) is adapted from a CC BY-SA 3.0 IGO source. The
mapping from evidence to levels is new work. Mixing them would blur licensing and make it hard to swap
either one.

## Decision

`framework/framework.yaml` holds the adapted structure and own-words descriptors (CC BY-SA 3.0 IGO).
`rubric/` holds signals, questions and level mappings (MIT). Code reads both and a consistency check
ties them together.

## Consequences

* Licensing is clear per folder; the README states it.
* An organisation can keep the framework and replace the rubric, or the reverse.
* `aimaturity validate` must pass after every change to either.
