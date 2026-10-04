# ADR 0002: Score from evidence signals first, questionnaire second

**Status:** Accepted

## Context

Most maturity assessments are surveys. Surveys are cheap but optimistic, and they leave no trail.

## Decision

Each level lists signals. File-based signals (glob plus optional pattern) are collected from
repositories read-only; questions cover what code cannot show. Source weights make artifacts count more
than answers, and answers labelled as sample answers count least.

## Consequences

* Every result cites evidence a reviewer can open.
* People and culture categories rely on answers and are reviewed more often.
* Pattern matching can be gamed by documents; review and confidence are the counterweight.
