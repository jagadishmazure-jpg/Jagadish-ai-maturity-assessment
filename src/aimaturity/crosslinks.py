"""Cross-repository links: which repository should supply evidence for which categories.

For the portfolio: governance (pillar 5) draws on the model risk repository, cost and value
(1.4, 3.2) on the FinOps repository, and data (pillar 6) on the Fabric BI repository. A link is
"satisfied" when the category's cited evidence includes at least one file from that repository.
"""

from __future__ import annotations

from typing import Any


def check_links(state: dict[str, Any]) -> list[dict[str, Any]]:
    links = state["org"].config.get("links", {})
    ev = state["evidence_by_id"]
    rows = []
    for repo, cats in links.items():
        for cid in cats:
            cited = [i for i in state["results"][cid].evidence if ev[i].source == repo]
            rows.append({"repo": repo, "category": cid, "cited": len(cited), "examples": sorted({ev[i].path for i in cited})[:3], "ok": bool(cited)})
    return rows
