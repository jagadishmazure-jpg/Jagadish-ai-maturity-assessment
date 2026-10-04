"""Score one category from evidence: maturity level, confidence and the evidence that justifies it.

Rules (see docs/components/scoring-confidence.md):

* Level 1 (Basic) needs nothing. Level N is reached when level N-1 is reached and the present share of
  level N's signals is at least the rubric threshold (0.66, two thirds). A "partial" answer counts half.
* Confidence = 0.6 x mean source weight + 0.4 x decision margin, over the signals that decided the
  level (all levels up to the first one that failed).
* A category goes to the human review queue when confidence is under 0.6 or when a level it reached
  rests on a sample answer (demo inputs must never pass as facts).
* Source weights: artifact found 1.0, artifact searched for and not found 0.8 (0.5 when no repository
  was scanned), self-reported answer 0.6, sample answer 0.35, unanswered question 0.2.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from aimaturity.collectors import Evidence
from aimaturity.framework import LEVEL_NAMES, categories, is_question, rubric

WEIGHTS = {"artifact": 1.0, "absent-scanned": 0.8, "absent-unscanned": 0.5, "self-reported": 0.6, "sample-answers": 0.35, "unanswered": 0.2}
REVIEW_BELOW = 0.6


@dataclass
class SignalState:
    present: float  # 0, 0.5 or 1
    weight: float  # how much we trust what we know about this signal
    basis: str  # key into WEIGHTS
    evidence: list[str] = field(default_factory=list)


@dataclass
class CategoryResult:
    id: str
    name: str
    pillar: str
    critical: bool
    level: int
    level_name: str
    confidence: float
    ratios: dict[int, float]
    signals: dict[str, SignalState]
    evidence: list[str]  # ids that justify the level reached
    next_missing: list[str]  # signals still missing for the next level
    needs_review: bool
    review_reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["ratios"] = {str(k): v for k, v in self.ratios.items()}
        return d


def signal_states(category_id: str, evidence: list[Evidence], scanned_repos: bool) -> dict[str, SignalState]:
    by_signal: dict[str, list[Evidence]] = {}
    for e in evidence:
        by_signal.setdefault(e.signal, []).append(e)
    out: dict[str, SignalState] = {}
    for lvl in (2, 3, 4):
        for sid in rubric()["categories"][category_id]["levels"][lvl]:
            if sid in out:
                continue
            items = by_signal.get(sid, [])
            if is_question(sid):
                if items:
                    a = items[0]
                    out[sid] = SignalState(a.strength, WEIGHTS[a.origin], a.origin, [a.id] if a.strength > 0 else [])
                else:
                    out[sid] = SignalState(0.0, WEIGHTS["unanswered"], "unanswered")
            elif items:
                out[sid] = SignalState(1.0, WEIGHTS["artifact"], "artifact", [e.id for e in items])
            else:
                basis = "absent-scanned" if scanned_repos else "absent-unscanned"
                out[sid] = SignalState(0.0, WEIGHTS[basis], basis)
    return out


def score_category(category_id: str, evidence: list[Evidence], scanned_repos: bool = True) -> CategoryResult:
    cat = categories()[category_id]
    t = rubric()["threshold"]
    levels = cat["rubric"]["levels"]
    states = signal_states(category_id, evidence, scanned_repos)
    ratios = {lvl: round(sum(states[s].present for s in levels[lvl]) / len(levels[lvl]), 3) for lvl in (2, 3, 4)}
    level = 1
    for lvl in (2, 3, 4):
        if ratios[lvl] >= t:
            level = lvl
        else:
            break
    # margin: how far the deciding ratios sit from the threshold (0 = on the edge, 1 = clear-cut)
    held = 1.0 if level == 1 else (ratios[level] - t) / (1 - t)
    failed = 1.0 if level == 4 else (t - ratios[level + 1]) / t
    margin = max(0.0, min(held, failed, 1.0))
    decided = [s for lvl in range(2, min(level + 1, 4) + 1) for s in levels[lvl]]
    decided = list(dict.fromkeys(decided))
    mean_w = sum(states[s].weight for s in decided) / len(decided)
    confidence = round(0.6 * mean_w + 0.4 * margin, 2)
    cited = list(dict.fromkeys(i for lvl in range(2, level + 1) for s in levels[lvl] for i in states[s].evidence))
    missing = [] if level == 4 else [s for s in levels[level + 1] if states[s].present < 1]
    reasons = []
    if confidence < REVIEW_BELOW:
        reasons.append(f"confidence {confidence:.2f} below {REVIEW_BELOW}")
    sample = sorted({s for lvl in range(2, level + 1) for s in levels[lvl] if states[s].basis == "sample-answers" and states[s].present > 0})
    if sample:
        reasons.append("level rests on sample answers: " + ", ".join(sample))
    return CategoryResult(
        category_id, cat["name"], cat["pillar"], cat["critical"], level, LEVEL_NAMES[level], confidence, ratios, states, cited, missing,
        bool(reasons), reasons,
    )


def score_all(evidence: list[Evidence], scanned_repos: bool = True) -> dict[str, CategoryResult]:
    return {cid: score_category(cid, evidence, scanned_repos) for cid in categories()}
