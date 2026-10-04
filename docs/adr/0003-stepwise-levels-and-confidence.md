# ADR 0003: Stepwise levels with a two-thirds threshold and a confidence score

**Status:** Accepted

## Context

A level should mean the practices below it are in place. A cumulative rule that lets higher evidence
compensate for a missing foundation was tried; it lowered agreement with labels and produced many
borderline confidences.

## Decision

A level needs at least two thirds of its own signals and the level below. Confidence is 0.6 x mean
source weight + 0.4 x decision margin; below 0.6, or resting on sample answers, means human review.

## Consequences

* Easy to explain; matches the step structure of the source framework.
* One missing foundation artifact can drop a category several levels; the stability eval measures how
  often and enforces that only categories using the removed evidence can move.
