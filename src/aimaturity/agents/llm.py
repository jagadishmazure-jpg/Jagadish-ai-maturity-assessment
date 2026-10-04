"""A deterministic stand-in for the LLM that writes category rationales.

The real deployment would call a hosted model; offline, ``MockLLM`` produces the same kind of text
from the scoring facts, and two knobs simulate the failures the verifier must catch:

* ``hallucinate``: cite an evidence id that does not exist.
* ``overclaim``: state a level one higher than the scores support.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from aimaturity.framework import LEVEL_NAMES

CITE = re.compile(r"\[(E\d{3,})\]")


@dataclass
class MockLLM:
    hallucinate: bool = False
    overclaim: bool = False
    calls: int = 0

    def rationale(self, facts: dict) -> str:
        self.calls += 1
        level = min(4, facts["level"] + 1) if self.overclaim else facts["level"]
        cites = list(facts["evidence"][:4])
        if self.hallucinate:
            cites.append("E999")
        parts = [f"Level {level} ({LEVEL_NAMES[level]})."]
        if cites:
            parts.append("Supported by " + ", ".join(f"[{c}]" for c in cites) + ".")
        else:
            parts.append("No artifact or answer supports a level above Basic.")
        if facts["missing"]:
            parts.append(f"Next level needs: {', '.join(facts['missing'])}.")
        parts.append(f"Confidence {facts['confidence']:.2f}.")
        return " ".join(parts)


def template_rationale(facts: dict) -> str:
    """Fallback text the verifier uses when the model output fails a check."""
    return MockLLM().rationale(facts)


def cited_ids(text: str) -> list[str]:
    return CITE.findall(text)


def claimed_level(text: str) -> int | None:
    m = re.match(r"Level (\d)", text)
    return int(m.group(1)) if m else None
