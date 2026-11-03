"""Cross-repository links: which repository should supply evidence for which capabilities.

For the portfolio: governance (GR-1, GR-2, GR-3) draws on the model risk repository, value and cost
(SV-3, FC-1, FC-2) on the FinOps repository, and data (DF-1, DF-2) on the Fabric BI repository. A link is
"satisfied" when the capability's cited evidence includes at least one file from that repository.
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
            rows.append(
                {"repo": repo, "capability": cid, "cited": len(cited), "examples": sorted({ev[i].path for i in cited})[:3], "ok": bool(cited)}
            )
    return rows
