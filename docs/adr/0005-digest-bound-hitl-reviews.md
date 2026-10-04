# ADR 0005: Digest-bound human reviews with a hash-chained audit log

**Status:** Accepted

## Context

Low-confidence results need a person. A sign-off should not outlive the evidence it judged, and the
agent must not approve its own work.

## Decision

Reviews confirm or override, need a comment, cannot come from the assessor, and store a digest of the
category's evidence. Every review is appended to a hash-chained log. A changed digest makes the review
stale; a broken chain makes the assessment non-final. The MCP server has no review tool.

## Consequences

* Accountability and tamper evidence without a database.
* Reviewer identity is a string in the demo; production would use Entra ID.
