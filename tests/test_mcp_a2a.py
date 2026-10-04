import json

import pytest
from mcp import Client

from aimaturity import ROOT
from aimaturity.mcp_server import TOOL_NAMES, build_server, demo


async def _call(name, args):
    async with Client(build_server()) as c:
        return (await c.call_tool(name, args)).structured_content


async def test_tools_listed_and_read_only():
    async with Client(build_server()) as c:
        tools = (await c.list_tools()).tools
    assert sorted(t.name for t in tools) == sorted(TOOL_NAMES)
    assert all(t.annotations.read_only_hint and not t.annotations.destructive_hint for t in tools)


def test_no_tool_can_write():
    verbs = ("record", "sign", "write", "delete", "update", "set_", "create")
    assert not [n for n in TOOL_NAMES if n.startswith(verbs)]


async def test_list_pillars():
    res = await _call("list_pillars", {})
    assert len(res["result"]) == 6


async def test_get_category():
    res = await _call("get_category", {"category_id": "5.1"})
    assert res["critical"] and set(res["evidence_needed"]) == {"2", "3", "4"}


async def test_list_orgs():
    res = await _call("list_orgs", {})
    assert {o["id"] for o in res["result"]} == {"portfolio", "kestrel-bay-bank", "valemont-revenue-agency"}


async def test_assess():
    res = await _call("assess", {"org_id": "kestrel-bay-bank"})
    assert res["overall"]["level"] == 3 and len(res["pillars"]) == 6


async def test_category_result():
    res = await _call("category_result", {"org_id": "valemont-revenue-agency", "category_id": "4.4"})
    assert res["status"] == "overridden"


async def test_gaps_and_roadmap():
    gaps = await _call("gaps", {"org_id": "portfolio", "min_gap": 2})
    assert all(g["gap"] >= 2 for g in gaps["result"])
    rm = await _call("roadmap", {"org_id": "portfolio"})
    assert rm["plan"] and [m["month"] for m in rm["milestones"]] == [6, 12]


async def test_review_queue():
    res = await _call("review_queue", {"org_id": "portfolio"})
    assert any(r["category"] == "2.3" for r in res["result"])


async def test_evidence_lookup():
    ok = await _call("evidence", {"org_id": "portfolio", "evidence_id": "E001"})
    assert ok["id"] == "E001"
    bad = await _call("evidence", {"org_id": "portfolio", "evidence_id": "E99999"})
    assert "error" in bad


async def test_demo_script():
    lines = await demo()
    assert lines[1] == "all read-only: True" and any("overridden" in x for x in lines)


@pytest.fixture(scope="module")
def card():
    return json.loads((ROOT / "a2a" / "agent-card.json").read_text())


def test_card_required_fields(card):
    for k in ("protocolVersion", "name", "description", "url", "version", "capabilities", "defaultInputModes", "defaultOutputModes", "skills"):
        assert k in card


def test_card_skills_unique_and_described(card):
    ids = [s["id"] for s in card["skills"]]
    assert len(ids) == len(set(ids)) >= 5
    assert all(s["description"] and s["tags"] and s["examples"] for s in card["skills"])


def test_card_url_is_not_a_live_endpoint(card):
    assert card["url"].startswith("https://") and ".invalid/" in card["url"]


def test_card_declares_auth_and_attribution(card):
    assert card["security"] and "CC BY-SA 3.0 IGO" in card["description"]
