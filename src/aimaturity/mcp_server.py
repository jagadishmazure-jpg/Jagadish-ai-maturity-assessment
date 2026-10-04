"""Read-only MCP server over the framework and the sample assessments.

Tools (all ``readOnlyHint``): list_pillars, get_category, list_orgs, assess, category_result,
gaps, roadmap, review_queue, evidence. There is no tool that records a review: agents can ask
for an assessment and its evidence, only a named human can sign a category off (``aimaturity review``).

    aimaturity mcp          # stdio transport, for an MCP client
    aimaturity mcp-demo     # scripted in-memory session
"""

from __future__ import annotations

from functools import cache
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from aimaturity.agents.assessor import assess as _assess
from aimaturity.agents.assessor import summary
from aimaturity.framework import LEVEL_NAMES, categories, pillars
from aimaturity.gaps import describe
from aimaturity.orgs import list_orgs as _list_orgs
from aimaturity.orgs import load_org

RO = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
TOOL_NAMES = ["list_pillars", "get_category", "list_orgs", "assess", "category_result", "gaps", "roadmap", "review_queue", "evidence"]


@cache
def _state(org_id: str) -> dict[str, Any]:
    return _assess(org_id)


def build_server() -> MCPServer:
    server = MCPServer("ai-maturity-assessment")

    @server.tool(annotations=RO)
    def list_pillars() -> list[dict[str, Any]]:
        """The six pillars with their category ids and names."""
        return [{"id": p["id"], "name": p["name"], "categories": [{"id": c["id"], "name": c["name"]} for c in p["categories"]]} for p in pillars()]

    @server.tool(annotations=RO)
    def get_category(category_id: str) -> dict[str, Any]:
        """One category: summary, level descriptors 1-4, the evidence each level needs, critical flag."""
        c = categories()[category_id]
        return {
            "id": c["id"],
            "name": c["name"],
            "pillar": c["pillar"],
            "summary": c["summary"],
            "critical": c["critical"],
            "descriptors": {f"{k} {LEVEL_NAMES[k]}": v for k, v in c["descriptors"].items()},
            "evidence_needed": {str(lvl): [{"signal": s, "means": describe(s)} for s in ids] for lvl, ids in c["rubric"]["levels"].items()},
        }

    @server.tool(annotations=RO)
    def list_orgs() -> list[dict[str, Any]]:
        """Sample organisations that can be assessed."""
        return [{"id": o, "name": load_org(o).name, "kind": load_org(o).config.get("kind", "")} for o in _list_orgs()]

    @server.tool(annotations=RO)
    def assess(org_id: str) -> dict[str, Any]:
        """Overall and pillar levels, review status and evidence count for one organisation."""
        s = summary(_state(org_id))
        return {k: s[k] for k in ("org", "name", "overall", "pillars", "review_queue", "final", "evidence_count", "questionnaire_label")}

    @server.tool(annotations=RO)
    def category_result(org_id: str, category_id: str) -> dict[str, Any]:
        """Level, confidence, status, rationale and cited evidence ids for one category."""
        s = summary(_state(org_id))
        return next(c for c in s["categories"] if c["id"] == category_id)

    @server.tool(annotations=RO)
    def gaps(org_id: str, min_gap: int = 1) -> list[dict[str, Any]]:
        """Categories below target, largest gap first, with the missing evidence per step."""
        rows = [g for g in _state(org_id)["gaps"] if g["gap"] >= min_gap]
        return sorted(rows, key=lambda g: (-g["gap"], g["category"]))

    @server.tool(annotations=RO)
    def roadmap(org_id: str) -> dict[str, Any]:
        """The Month 1-12 plan: steps with start and end month, kind, dependencies; backlog; milestones."""
        sch = _state(org_id)["schedule"]
        keep = ("id", "name", "kind", "start", "end", "effort", "priority", "depends_on", "action")
        return {"plan": [{k: p[k] for k in keep} for p in sch["plan"]], "backlog": sch["backlog"], "milestones": sch["milestones"]}

    @server.tool(annotations=RO)
    def review_queue(org_id: str) -> list[dict[str, Any]]:
        """Categories waiting for a human reviewer and why."""
        st = _state(org_id)
        return [{"category": c, "name": st["results"][c].name, "reasons": st["results"][c].review_reasons} for c in st["review_queue"]]

    @server.tool(annotations=RO)
    def evidence(org_id: str, evidence_id: str) -> dict[str, Any]:
        """One evidence item: signal, collector, repository and path (or question), detail, origin."""
        e = _state(org_id)["evidence_by_id"].get(evidence_id)
        return e.as_dict() if e else {"error": f"unknown evidence id {evidence_id}"}

    return server


async def demo() -> list[str]:
    """Scripted session used by ``aimaturity mcp-demo``: what a planning agent would ask."""
    from mcp import Client

    lines = []
    async with Client(build_server()) as client:
        tools = await client.list_tools()
        lines.append("tools: " + ", ".join(sorted(t.name for t in tools.tools)))
        lines.append(f"all read-only: {all(t.annotations and t.annotations.read_only_hint for t in tools.tools)}")
        res = (await client.call_tool("assess", {"org_id": "valemont-revenue-agency"})).structured_content
        lines.append(f"{res['name']}: overall {res['overall']['level']} ({res['overall']['level_name']}); queue {res['review_queue']}")
        for p in res["pillars"]:
            lines.append(f"  {p['id']} {p['name']:<30} level {p['level']} mean {p['mean']}")
        cat = (await client.call_tool("category_result", {"org_id": "valemont-revenue-agency", "category_id": "4.4"})).structured_content
        lines.append(f"4.4: computed {cat['computed_level']}, final {cat['level']} ({cat['status']})")
        first = cat["evidence"][0]
        ev = (await client.call_tool("evidence", {"org_id": "valemont-revenue-agency", "evidence_id": first})).structured_content
        lines.append(f"  {first}: {ev['source']} {ev['path']} ({ev['origin']})")
        rm = (await client.call_tool("roadmap", {"org_id": "valemont-revenue-agency"})).structured_content
        lines.append("quick wins: " + ", ".join(p["id"] for p in rm["plan"] if p["kind"] == "quick-win"))
    return lines
