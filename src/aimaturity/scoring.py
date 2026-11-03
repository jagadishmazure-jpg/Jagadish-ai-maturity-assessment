"""Score one capability from evidence: maturity level, confidence and the evidence that justifies it.

Rules (see docs/components/scoring-confidence.md and docs/adr/0007-original-agentic-maturity-model.md):

* Level 1 (Explore) needs nothing. Level N is reached when level N-1 is reached, every ``must``
  criterion of level N is fully present and at least ``support_share`` (one half) of its
  ``support`` criteria are present; a level without support criteria is decided by its musts.
  A "partial" answer counts half and never satisfies a ``must``.
* Evidence ceiling: from level 4 (Scale) every ``must`` list holds an artifact signal, so answers alone
  stop at level 3 (Operate). The rubric consistency check enforces it.
* Confidence = 0.5 x evidence trust + 0.3 x decision margin + 0.2 x verifiability, over the criteria
  that decided the level (every level up to the first one that failed). Trust is the mean source
  weight; verifiability is the share of those criteria that are file-based signals, not questions.
* A capability goes to the human review queue when confidence is under 0.6 or when a level it
  reached rests on a sample answer (demo inputs must never pass as facts).
* Source weights: artifact found 1.0, artifact searched for and not found 0.85 (0.5 when no
  repository was scanned), self-reported answer 0.55, sample answer 0.3, unanswered question 0.15.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from aimaturity.collectors import Evidence
from aimaturity.framework import LEVEL_NAMES, STEPS, TOP, capabilities, criteria, is_question, rubric

WEIGHTS = {"artifact": 1.0, "absent-scanned": 0.85, "absent-unscanned": 0.5, "self-reported": 0.55, "sample-answers": 0.3, "unanswered": 0.15}
REVIEW_BELOW = 0.6
CONFIDENCE_MIX = {"trust": 0.5, "margin": 0.3, "verifiability": 0.2}


@dataclass
class SignalState:
    present: float  # 0, 0.5 or 1
    weight: float  # how much we trust what we know about this signal
    basis: str  # key into WEIGHTS
    evidence: list[str] = field(default_factory=list)


@dataclass
class CapabilityResult:
    id: str
    name: str
    dimension: str
    anchor: bool
    level: int
    level_name: str
    confidence: float
    ratios: dict[int, float]  # share of all criteria present, per level
    signals: dict[str, SignalState]
    evidence: list[str]  # ids that justify the level reached
    next_missing: list[str]  # criteria still missing for the next level
    needs_review: bool
    review_reasons: list[str] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)  # must criteria that stopped the next level

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["ratios"] = {str(k): v for k, v in self.ratios.items()}
        return d


def signal_states(capability_id: str, evidence: list[Evidence], scanned_repos: bool) -> dict[str, SignalState]:
    by_signal: dict[str, list[Evidence]] = {}
    for e in evidence:
        by_signal.setdefault(e.signal, []).append(e)
    out: dict[str, SignalState] = {}
    for lvl in STEPS:
        for sid in criteria(capability_id, lvl):
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


def support_share(states: dict[str, SignalState], support: list[str]) -> float:
    return 1.0 if not support else sum(states[s].present for s in support) / len(support)


def level_passes(states: dict[str, SignalState], rule: dict[str, list[str]], need: float) -> bool:
    return all(states[s].present >= 1 for s in rule["must"]) and support_share(states, rule["support"]) >= need


def score_capability(capability_id: str, evidence: list[Evidence], scanned_repos: bool = True) -> CapabilityResult:
    cap = capabilities()[capability_id]
    levels = cap["rubric"]["levels"]
    need = rubric()["support_share"]
    states = signal_states(capability_id, evidence, scanned_repos)
    ratios = {lvl: round(sum(states[s].present for s in criteria(capability_id, lvl)) / len(criteria(capability_id, lvl)), 3) for lvl in STEPS}
    level = 1
    for lvl in STEPS:
        if not level_passes(states, levels[lvl], need):
            break
        level = lvl
    # margin: 0 = the decision sits on the edge, 1 = clear-cut on both sides
    held = 1.0 if level == 1 else (support_share(states, levels[level]["support"]) - need) / (1 - need)
    failed = 1.0 if level == TOP else 1 - ratios[level + 1]
    margin = max(0.0, min(held, failed, 1.0))
    decided = list(dict.fromkeys(s for lvl in range(2, min(level + 1, TOP) + 1) for s in criteria(capability_id, lvl)))
    trust = sum(states[s].weight for s in decided) / len(decided)
    verifiable = sum(not is_question(s) for s in decided) / len(decided)
    mix = CONFIDENCE_MIX
    confidence = round(mix["trust"] * trust + mix["margin"] * margin + mix["verifiability"] * verifiable, 2)
    cited = list(dict.fromkeys(i for lvl in range(2, level + 1) for s in criteria(capability_id, lvl) for i in states[s].evidence))
    if level == TOP:
        missing, blocked = [], []
    else:
        missing = [s for s in criteria(capability_id, level + 1) if states[s].present < 1]
        blocked = [s for s in levels[level + 1]["must"] if states[s].present < 1]
    reasons = []
    if confidence < REVIEW_BELOW:
        reasons.append(f"confidence {confidence:.2f} below {REVIEW_BELOW}")
    sample = sorted(
        {s for lvl in range(2, level + 1) for s in criteria(capability_id, lvl) if states[s].basis == "sample-answers" and states[s].present > 0}
    )
    if sample:
        reasons.append("level rests on sample answers: " + ", ".join(sample))
    return CapabilityResult(
        capability_id,
        cap["name"],
        cap["dimension"],
        cap["anchor"],
        level,
        LEVEL_NAMES[level],
        confidence,
        ratios,
        states,
        cited,
        missing,
        bool(reasons),
        reasons,
        blocked,
    )


def score_all(evidence: list[Evidence], scanned_repos: bool = True) -> dict[str, CapabilityResult]:
    return {cid: score_capability(cid, evidence, scanned_repos) for cid in capabilities()}
