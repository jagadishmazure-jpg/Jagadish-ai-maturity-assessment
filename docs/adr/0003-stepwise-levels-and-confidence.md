# ADR 0003: Stepwise levels with must and support criteria, and a confidence score

**Status:** Accepted

## Context

A level should mean the practices below it are in place. A cumulative rule that lets higher evidence
compensate for a missing foundation lowered agreement with labels and produced many borderline
confidences. A plain share-of-signals threshold had a different problem: it treated a defining
practice (an evaluation gate in CI) the same as a nice-to-have (a changelog).

## Decision

Each level from Prove to Optimise lists **must** criteria and optional **support** criteria. A level is
reached when the level below is reached, every must is fully present (a partial answer never satisfies
a must) and at least half of the support criteria are present (a partial answer counts half).

Confidence is 0.5 x evidence trust + 0.3 x decision margin + 0.2 x verifiability, over the criteria that
decided the level. Below 0.6, or resting on sample answers, the capability goes to human review.

## Consequences

* A report can say exactly which must blocked the next level (`blocked_by`), which turns into a roadmap
  item without interpretation.
* One missing foundation artifact can drop a capability several levels; the stability eval measures how
  often and enforces that only capabilities using the removed evidence can move.
* Verifiability rewards file-based evidence over answers, so two capabilities at the same level can
  carry different confidence for an honest reason.
