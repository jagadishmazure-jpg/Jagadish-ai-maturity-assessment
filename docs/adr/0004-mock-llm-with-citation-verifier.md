# ADR 0004: A mock LLM writes rationales, a verifier checks every citation

**Status:** Accepted

## Context

Rationales help readers, but a language model can invent evidence or overstate a level. The repository
must run offline in CI.

## Decision

Scores come from the rubric. `MockLLM` writes rationales with evidence ids; knobs simulate hallucinated
citations and overclaimed levels. The verifier rejects unknown ids, ids from other categories and level
mismatches, replacing the text with a template and recording the issue.

## Consequences

* Deterministic, offline, testable; the citations eval proves every injected fault is caught.
* A hosted model can be dropped in behind the same verifier.
