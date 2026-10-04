"""Collectors turn an organisation's artifacts and questionnaire answers into evidence items.

Each file-based signal in ``rubric/signals.yaml`` belongs to one collector (docs, people, iac, ci,
ops, governance, data). The collector checks every tracked file against the signal's path globs and
optional content pattern. The questionnaire collector reads answers for things code cannot show.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from functools import cache
from pathlib import PurePosixPath
from typing import Any

from aimaturity.framework import questions, signals

COLLECTORS = {
    "docs": "Vision, roadmap, value, experimentation and decision records",
    "people": "Contribution rules, ownership, learning and onboarding material",
    "iac": "Terraform and Bicep: services, cost guards, identity, policy, secrets",
    "ci": "Pipelines: tests, linting, deployment, OIDC, approvals, eval gates, reproducibility",
    "ops": "Telemetry, alerts, drift, APIs, events, MCP, A2A and shared components",
    "governance": "Security policy, model and risk cards, HITL, audit logs, regulation, fairness",
    "data": "Data needs, catalogues, contracts, quality tests, platforms, synthetic data, domain docs",
    "questionnaire": "Answers for people, culture and partnership items that artifacts cannot show",
}
ANSWER_STRENGTH = {"yes": 1.0, "partial": 0.5, "no": 0.0}


@dataclass(frozen=True)
class Evidence:
    signal: str
    collector: str
    source: str  # repository name, or "questionnaire"
    path: str  # file path inside the repository, or question id
    detail: str  # what matched, in a few words (never a copy of the file)
    strength: float = 1.0  # 1.0 for artifacts and "yes", 0.5 for "partial", 0.0 for "no"
    origin: str = "artifact"  # artifact | self-reported | sample-answers
    id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@cache
def _compiled(signal_id: str) -> re.Pattern[str] | None:
    pat = signals()[signal_id].get("contains")
    return re.compile(pat, re.I | re.M) if pat else None


def matches(signal_id: str, rel_path: str, text: str) -> bool:
    s = signals()[signal_id]
    p = PurePosixPath(rel_path)
    if not any(p.full_match(g) for g in s["paths"]):
        return False
    rx = _compiled(signal_id)
    return rx is None or bool(rx.search(text))


def _detail(signal_id: str, text: str) -> str:
    rx = _compiled(signal_id)
    if rx is None:
        return "file present"
    m = rx.search(text)
    hit = re.sub(r"\s+", " ", m.group(0)).strip() if m else ""
    return f"matched '{hit[:40]}'"


def collect_source(source, max_per_signal: int = 3) -> list[Evidence]:
    """All file-based evidence in one source; at most ``max_per_signal`` citations per signal."""
    out: list[Evidence] = []
    counts: dict[str, int] = {}
    file_signals = [sid for sid in signals()]
    for rel in source.files():
        text = None
        for sid in file_signals:
            if counts.get(sid, 0) >= max_per_signal:
                continue
            s = signals()[sid]
            if not any(PurePosixPath(rel).full_match(g) for g in s["paths"]):
                continue
            if text is None:
                text = source.read(rel)
            if matches(sid, rel, text):
                counts[sid] = counts.get(sid, 0) + 1
                out.append(Evidence(sid, s["collector"], source.name, rel, _detail(sid, text)))
    return out


def collect_questionnaire(answers: dict[str, Any]) -> list[Evidence]:
    origin = answers.get("label", "self-reported")
    out = []
    for qid, a in sorted(answers.get("answers", {}).items()):
        if qid not in questions():
            raise ValueError(f"unknown question {qid}")
        value = a["answer"] if isinstance(a, dict) else a
        note = a.get("note", "") if isinstance(a, dict) else ""
        if isinstance(value, bool):  # YAML 1.1 reads bare yes/no as booleans
            value = "yes" if value else "no"
        strength = ANSWER_STRENGTH[value]
        out.append(Evidence(qid, "questionnaire", "questionnaire", qid, f"answer {value}" + (f": {note}" if note else ""), strength, origin))
    return out


def number(items: list[Evidence]) -> list[Evidence]:
    """Stable ids: sorted by signal, source and path, then E001, E002, ..."""
    ordered = sorted(items, key=lambda e: (e.signal, e.source, e.path))
    return [Evidence(**{**e.as_dict(), "id": f"E{i:03d}"}) for i, e in enumerate(ordered, 1)]


def collect(sources: list, answers: dict[str, Any] | None) -> list[Evidence]:
    items: list[Evidence] = []
    for s in sources:
        items += collect_source(s)
    if answers:
        items += collect_questionnaire(answers)
    return number(items)
