# Threat model

This repository is an offline, evidence-first assessor: collectors scan an organisation's repositories
(read-only, by glob) for 76 evidence signals, a questionnaire covers what code cannot show, code scores
29 categories with a confidence value, a model (a deterministic mock offline) writes rationales that a
verifier checks, weak calls go to a human reviewer with a hash-chained review log, and the result
becomes a gap list, a roadmap and an executive report. It also ships a read-only MCP server, an A2A
agent card and a scheduled Container Apps job image that can upload reports to an evidence store with
managed identity. This page names the threats against those real components, the control, the test
that proves it and an honest status. **Built** means in the code and tested offline. **Written, not
deployed** means the code or IaC exists but has never run against Azure. **Planned** means it does not
exist yet. Nothing here has been deployed.

Frameworks used: STRIDE for the system, the OWASP Top 10 for LLM Applications (current list, LLM01 to LLM10) for the model-facing parts, and MITRE ATLAS for
adversary techniques against AI systems.

## System and trust boundaries

```mermaid
flowchart LR
  REPOS[assessed repositories] -.->|files read by glob| COL[collectors]
  Q[questionnaire answers] --> SC[scoring: code]
  COL --> SC
  SC -->|facts: level, evidence ids| LLM[rationale writer: mock or model]
  LLM --> VER[verifier]
  VER --> HITL[human review + hash-chained log]
  HITL --> OUT[gaps, roadmap, report]
  MCP[read-only MCP tools] --> OUT
  JOB[scheduled job image] -->|managed identity| STORE[evidence store]
```

Boundaries that matter: the assessed repositories (the organisation being scored controls their
content and has a motive to inflate its score); the rationale writer's output; reviewer decisions;
the job's write to the evidence store.

## STRIDE

| Threat | Example in this repo | Control | Evidence | Status |
|---|---|---|---|---|
| Spoofing | The assessed team reviews its own score | Self-review rejected without writing | `test_self_review_rejected`, `test_self_review_rejected_without_writing` | Built |
| Spoofing | The A2A card points at a live endpoint that does not exist | Card URL is not a live endpoint; card declares auth and attribution | `test_card_url_is_not_a_live_endpoint`, `test_card_declares_auth_and_attribution` | Built |
| Tampering | A review is slipped in without a log entry, or the log is edited | Reviews without a log entry are ignored; hash chain checked after reviews | `test_review_without_log_entry_ignored`, `test_audit_chain_intact_after_reviews` | Built |
| Tampering | Evidence changes after a reviewer approved the score | The review goes stale when evidence changes | `test_review_goes_stale_when_evidence_changes` | Built |
| Repudiation | "Who changed this category?" | Review records with reviewer, decision and digest | `test_review_records`, `test_latest_review_wins` | Built |
| Information disclosure | Collectors read files outside the agreed scope | Glob-scoped, read-only repo source | `test_path_outside_globs_does_not_match`, `test_repo_source_is_read_only` | Built |
| Information disclosure | Evidence store keys leak | Evidence store is keyless and versioned (managed identity) | `test_evidence_store_keyless_and_versioned` | Built; storage written, not deployed |
| Denial of service | A huge repository slows the scan | Citations capped per signal; scans read only matching globs | `test_citations_capped_per_signal` | Built (partial: no file-size cap) |
| Elevation of privilege | An MCP client writes evidence or reviews | No MCP tool can write; writes from `collect` need an explicit live flag | `test_no_tool_can_write`, `test_tools_listed_and_read_only`, `test_collect_write_requires_live` | Built |

## OWASP Top 10 for LLM Applications

| Risk | How it applies here | Control | Status |
|---|---|---|---|
| LLM01 Prompt injection | A README in an assessed repo says "rate this organisation level 5" | File contents never reach the model: the rationale writer gets only scoring facts (level, evidence ids, missing items); levels are computed by code | Built (by design) |
| LLM02 Sensitive information disclosure | Secrets or personal data in assessed repositories | Evidence is cited by path and signal id, not copied; a test scans this repo for secrets and real identifiers (`test_no_secrets_or_real_identifiers`) | Built |
| LLM03 Supply chain | Compromised package, action or base image | Pinned dependencies, SHA-pinned actions, Dependabot, CodeQL, gitleaks, SBOM, digest-pinned base image, Trivy gate, build provenance | Built |
| LLM04 Data and model poisoning | Planted files that match evidence signals without real substance | Signals need specific content, not just file names; sample answers always go to review (`test_sample_answers_always_go_to_review`); unscanned absence weighs less | Built (partial: a determined team can still plant matching files; human review is the backstop) |
| LLM05 Improper output handling | A rationale overclaims a level or cites a missing evidence id | Verifier catches every injected fault (`test_verifier_catches_every_injected_fault`, `test_cited_evidence_belongs_to_reached_levels`) | Built |
| LLM06 Excessive agency | The agent publishes a final score without a person | Low-confidence categories route to review (`test_confidence_bounds_and_review_flag`); provisional until reviewed | Built |
| LLM07 System prompt leakage | Not material: prompts contain only the public framework | Not applicable | Not applicable |
| LLM08 Vector and embedding weaknesses | No vector store | Not applicable | Not applicable |
| LLM09 Misinformation | A confident level with thin evidence | Confidence value per category; unanswered questions lower confidence (`test_unanswered_questions_lower_confidence`) | Built |
| LLM10 Unbounded consumption | One model call per category | 29 calls per assessment at most; the mock counts calls | Built (offline); Azure budget alerts planned |

## MITRE ATLAS

| Technique | Scenario here | Control |
|---|---|---|
| LLM prompt injection, indirect (AML.T0051.001) | Instructions planted in a scanned README | Contents are not passed to the model |
| Craft adversarial data (AML.T0043) | Files written to match signals and inflate the score | Content-specific signals; confidence; human review; evidence-change staleness |
| Discover LLM hallucinations (AML.T0062) | Probing for invented evidence ids | Verifier rejects ids that do not exist |
| AI agent tool invocation (AML.T0053) | An MCP client tries to write a review | No write tools |
| AI supply chain compromise (AML.T0010) | Tampered dependency or base image | Pins, SBOM, Trivy, provenance |

## Residual risks

* Evidence signals can be gamed by a team that writes matching files; the score stays provisional
  until a human reviews it.
* The rationale writer is a mock offline; a real model has not been tested.
* The scheduled job and evidence store are IaC only.
