# ADR 0007: Design of the Enterprise Agentic AI Maturity Model

**Status:** Accepted

## Context

I wanted a maturity model for the work I actually do: putting AI agents and LLM applications into
production inside regulated enterprises. General AI-readiness frameworks stop at "we have a strategy and
some data". They say little about the things that decide whether an agent is safe to let act on real
systems: tool permissions, agent identity, evaluation gates, prompt and model versioning, runtime cost
and who signs off a release. They also score mostly from interviews, so two assessors reach different
answers for the same organisation.

My goals for the model were:

1. Cover the agent lifecycle end to end, from the business case to cost per task.
2. Make every level checkable from evidence (files, pipelines, policies) where evidence can exist.
3. Keep the result explainable: for any score, name the criterion that blocked the next level.
4. Map every capability to NIST AI RMF, ISO/IEC 42001 and the EU AI Act, so the output feeds a
   compliance conversation directly.

## Decision

### Eight weighted dimensions

| Id | Dimension | Weight | Why it is its own dimension |
|---|---|---|---|
| SV | Strategy & Value | 0.12 | Agents need a funded thesis and measured value, or they stay demos |
| DF | Data Foundation | 0.13 | Retrieval quality and data contracts cap what any agent can do |
| PL | Platform & LLMOps | 0.13 | A paved road (IaC, release gates, observability) is what makes the second agent cheap |
| AE | Agent Engineering | 0.14 | Tool design, evaluation and human-in-the-loop are agent-specific and usually missing |
| SI | Security & Identity | 0.14 | An agent with credentials is a new identity and a new attack surface |
| GR | Governance, Risk & Compliance | 0.14 | Inventory, risk tiering and transparency are what regulators ask for first |
| PO | People & Operating Model | 0.10 | Ownership, skills and an operating cadence keep agents alive after launch |
| FC | FinOps & Cost | 0.10 | Token and run cost grow per task, not per seat, and need their own controls |

Agent Engineering, Security & Identity and Governance weigh most because an agent that can act on
systems fails expensively when those are weak. Each dimension has three capabilities (FinOps has two),
23 in total, each with its own descriptors, actions, dependencies and crosswalk.

### Five levels named after what the organisation is doing

**Explore** (individuals try tools), **Prove** (bounded pilots with an owner and success criteria),
**Operate** (agents in production on a paved road with gates and monitoring), **Scale** (a shared
platform and federated guardrails serve many teams), **Optimise** (telemetry, evaluation, cost and risk
data steer the portfolio automatically). Verbs instead of adjectives, so a leader can tell from the
name what changes between two levels.

### Must and support criteria with an evidence ceiling

Every level from Prove upwards lists **must** criteria and optional **support** criteria. A level is
reached when the level below is reached, every must is fully present and at least half of the support
criteria are present. Answers can carry the early levels, but from Scale upwards every must list
contains at least one artifact signal: a claim of scale without a file to show for it stays at Operate.
Details and confidence are in ADR 0003.

### Anchors and a weighted rollup

Each dimension has an **anchor** capability, the foundation the others stand on (for example DF-2
data contracts and quality, SI-1 agent identity). A dimension level is the floor of its capability mean,
capped one level above its weakest anchor. The overall level is the floor of the weighted mean of
dimension levels, capped one level above the weakest dimension. The 0-100 **Agentic Readiness Index**
is the weighted progress across dimensions, 100 x sum of weight x (dimension mean - 1) / 4, so
progress inside a level is visible even when the level does not move.

## Consequences

* Scores are reproducible from the same evidence, and the stability and calibration evals gate every
  change to the model, the rubric or the descriptors.
* The anchor and dimension caps make the overall level conservative by design: one neglected
  dimension holds the organisation back, which is the conversation I want the report to start.
* Anchors can be overridden per organisation in `org.yaml` (the agency sample does); the weights are
  part of the model, so changing them needs a new ADR and a fresh calibration run.
* The crosswalk is a mapping for orientation, not a conformity claim; a capability at Optimise does
  not certify ISO/IEC 42001 or EU AI Act compliance.
