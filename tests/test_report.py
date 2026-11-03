import re

import pytest

from aimaturity.report import METHOD, build_content, render, to_markdown, write

ORGS = ["portfolio", "kestrel-bay-bank", "valemont-revenue-agency"]


@pytest.fixture(scope="module")
def states():
    from aimaturity.agents.assessor import assess

    return {o: assess(o) for o in ORGS}


@pytest.mark.parametrize("org", ORGS)
def test_checked_in_report_matches_fresh_render(states, org):
    stale = write(states[org], check=True)
    assert stale == []


@pytest.mark.parametrize("org", ORGS)
def test_report_is_deterministic(states, org):
    assert render(states[org]) == render(states[org])


@pytest.mark.parametrize("org", ORGS)
def test_markdown_sections(states, org):
    md = render(states[org])["report.md"]
    for h in [
        "Executive summary",
        "Dimensions",
        "Capabilities",
        "Human review",
        "Gap analysis",
        "Roadmap (Month 1-12)",
        "Evidence",
        "Method",
    ]:
        assert f"## {h}" in md
    assert "radar.svg" in md


@pytest.mark.parametrize("org", ORGS)
def test_html_embeds_radar_and_method(states, org):
    html = render(states[org])["report.html"]
    assert "<svg" in html and "Enterprise Agentic AI Maturity Model" in html
    assert html.startswith("<!doctype html>")


@pytest.mark.parametrize("org", ORGS)
def test_radar_svg_has_no_timestamp(states, org):
    svg = render(states[org])["radar.svg"]
    assert "<dc:date>" not in svg and svg.lstrip().startswith("<?xml")


@pytest.mark.parametrize("org", ORGS)
def test_report_has_no_calendar_dates(states, org):
    md = render(states[org])["report.md"]
    assert not re.search(r"\b20[1-3]\d-\d\d-\d\d\b", md)
    assert not re.search(r"\b(January|February|March|April|June|July|August|September|October|November|December)\b", md)


def test_portfolio_report_flags_sample_answers(states):
    assert "SAMPLE ANSWERS" in render(states["portfolio"])["report.md"]


def test_fictional_reports_say_fictional(states):
    for o in ORGS[1:]:
        assert "fictional" in render(states[o])["report.md"]


def test_portfolio_report_lists_cross_links(states):
    md = render(states["portfolio"])["report.md"]
    assert "## Cross-repository evidence" in md and "agentic-ai-model-risk" in md


def test_method_states_the_scoring_rules():
    for phrase in ["eight weighted dimensions", "23 capabilities", "Explore to Optimise", "must", "anchor", "Readiness Index"]:
        assert phrase in METHOD


@pytest.mark.parametrize("org", ORGS)
def test_executive_summary_reports_readiness_index(states, org):
    md = render(states[org])["report.md"]
    assert re.search(r"Agentic Readiness Index \*\*\d+(\.\d)? / 100\*\*", md)


def test_markdown_table_escapes_pipes(states):
    c = build_content(states["portfolio"])
    c["sections"].append({"title": "x", "table": (["a"], [["p|q"]])})
    assert "p/q" in to_markdown(c)


def test_write_into_tmp(states, tmp_path):
    written = write(states["kestrel-bay-bank"], out_dir=tmp_path)
    assert set(written) == {"report.md", "report.html", "radar.svg"}
    stale = write(states["kestrel-bay-bank"], out_dir=tmp_path, check=True)
    assert stale == []
