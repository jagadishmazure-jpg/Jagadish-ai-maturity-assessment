# Interview guide

## Two minutes

"This is an evidence-based AI maturity assessor. It uses a six-pillar, 29-category framework structure
adapted from UNESCO, scans an organisation's repositories read-only, asks a questionnaire for what code
cannot show, scores each category with a confidence and cited evidence, sends low-confidence items to a
human reviewer with an audit log, and produces gaps, a Month 1 to 12 roadmap and an executive report. I
ran it on my own portfolio: technology is level 4, people and culture level 2, and the people items are
honestly marked as sample answers waiting for review."

## Ten minutes

1. **Framework vs rubric.** The framework (pillars, categories, levels) is adapted under CC BY-SA 3.0 IGO; the rubric that maps evidence to levels is mine and MIT.
2. **Scoring.** Two-thirds of a level's signals and the level below. Confidence = source trust and margin. Show `aimaturity explain --org portfolio --category 6.3`.
3. **Honesty.** Sample answers weigh 0.35 and force review; the report says SAMPLE ANSWERS.
4. **HITL.** No self-review, comment required, digest-bound, hash-chained log. Show the agency override of 4.4.
5. **Roll-up.** Median with critical caps (UNESCO's idea, configurable); overall capped at weakest + 1.
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
| How do you know it is calibrated? | 58 expert labels plus 12 synthetic organisations; exact agreement and within-one gates in CI. The expert set is small and says so. |
| Why critical categories? | The source framework lets organisations mark categories that cap a pillar; it prevents a strong average hiding a missing foundation. |
| What would production need? | Real identities for reviewers, a hosted model behind the same verifier, repository access through a GitHub App, private networking. |
| Why is the portfolio "provisional"? | Twelve categories rest on sample answers or low confidence and nobody has reviewed them. |
