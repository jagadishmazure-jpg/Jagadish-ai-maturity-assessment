# Interview guide

## Two minutes

"This is an evidence-based AI maturity assessor. It scores against my Enterprise Agentic AI Maturity
Model (eight weighted dimensions, 23 capabilities, five levels from Explore to Optimise, crosswalked to
NIST AI RMF, ISO/IEC 42001 and the EU AI Act), scans an organisation's repositories read-only, asks a
questionnaire for what code cannot show, scores each capability with a confidence and cited evidence, sends low-confidence items to a
human reviewer with an audit log, and produces gaps, a Month 1 to 12 roadmap and an executive report. I
ran it on my own portfolio: platform, agent engineering and security reach Scale, the operating model is
at Explore, so the overall level is Prove with a readiness index of 57.1, and the people items are
honestly marked as sample answers waiting for review."

## Ten minutes

1. **Model vs rubric.** The model (dimensions, weights, capabilities, descriptors, crosswalk) says what good looks like; the rubric says how evidence proves a level. ADR 0007 explains why the dimensions, levels and weights are what they are.
2. **Scoring.** Every must, half the support and the level below; from Scale up a must has to be a file. Confidence = trust, margin and verifiability. Show `aimaturity explain --org portfolio --capability DF-3`.
3. **Honesty.** Sample answers weigh 0.3 and force review; the report says SAMPLE ANSWERS.
4. **HITL.** No self-review, comment required, digest-bound, hash-chained log. Show the agency override of PO-2.
5. **Roll-up.** Floored mean per dimension capped by anchor capabilities (configurable); weighted overall capped at weakest dimension + 1; a 0-100 readiness index that moves before levels do.
6. **Roadmap.** Quick wins defined in code; dependencies; capacity; backlog; no dates.
7. **Evals.** Stability (shuffle, local dropout), citations (verifier catches injected faults), calibration against labels.

## Thirty minutes

Walk the architecture diagram, open `src/aimaturity/scoring.py` and `hitl.py`, run the MCP demo, show the
Terraform test and the gated deploy workflow, then discuss limitations.

## Questions to expect

| Question | Short answer |
|---|---|
| Can a document game the score? | Yes, a well-written file can satisfy a pattern. Confidence, review and evidence citations make that visible, and patterns ask for checkable content (targets, owners). |
| Why not let the LLM score? | Scores must be reproducible and explainable. The LLM writes rationales; a verifier checks them. |
| How do you know it is calibrated? | 46 expert labels plus 12 synthetic organisations; exact agreement and within-one gates in CI. The expert set is small and says so. |
| Why anchors? | A dimension cannot sit two levels above its own foundation; anchors stop a strong average hiding a missing one, and each organisation can choose its own. |
| Why these weights? | Agent engineering, security and governance weigh most because an agent that acts on systems fails expensively when they are weak (ADR 0007). |
| Is a high level a compliance claim? | No. The crosswalk shows which clauses a capability helps evidence; it is not a conformity assessment. |
| What would production need? | Real identities for reviewers, a hosted model behind the same verifier, repository access through a GitHub App, private networking. |
| Why is the portfolio "provisional"? | Nine capabilities rest on sample answers or low confidence and nobody has reviewed them. |
