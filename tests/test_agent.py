import pytest

from aimaturity.agents.assessor import NODES, assess, build_graph, summary
from aimaturity.agents.graph import END, StateGraph, StepLimitExceeded
from aimaturity.agents.llm import MockLLM, cited_ids, claimed_level, template_rationale


def test_trace_visits_every_node_in_order(portfolio):
    assert portfolio["trace"] == NODES and portfolio["status"] == "done"


def test_clean_run_has_no_verification_issues(portfolio, bank, agency):
    assert portfolio["verification_issues"] == bank["verification_issues"] == agency["verification_issues"] == []


def test_rationales_cite_only_category_evidence(portfolio):
    for cid, text in portfolio["rationales"].items():
        assert set(cited_ids(text)) <= set(portfolio["results"][cid].evidence)
        assert claimed_level(text) == portfolio["results"][cid].level


@pytest.mark.parametrize("knob", ["hallucinate", "overclaim"])
def test_verifier_catches_bad_rationales(knob):
    st = assess("kestrel-bay-bank", llm=MockLLM(**{knob: True}))
    assert st["verification_issues"]
    for cid, text in st["rationales"].items():
        assert "E999" not in text and claimed_level(text) == st["results"][cid].level


def test_mock_llm_is_deterministic():
    facts = {"level": 2, "evidence": ["E001", "E002"], "missing": ["adr"], "confidence": 0.7}
    assert MockLLM().rationale(facts) == MockLLM().rationale(facts) == template_rationale(facts)


def test_mock_llm_counts_calls(portfolio):
    llm = MockLLM()
    assess("valemont-revenue-agency", llm=llm)
    assert llm.calls == 29


def test_basic_rationale_without_evidence():
    text = MockLLM().rationale({"level": 1, "evidence": [], "missing": ["x"], "confidence": 0.3})
    assert "Basic" in text and cited_ids(text) == []


def test_graph_compile_rejects_unknown_nodes():
    g = StateGraph().add_node("a", lambda s: s).add_edge("a", "ghost")
    with pytest.raises(ValueError):
        g.compile(entry="a")


def test_step_limit():
    g = StateGraph().add_node("a", lambda s: s).add_edge("a", "a")
    with pytest.raises(StepLimitExceeded):
        g.compile(entry="a", max_steps=3).invoke({})


def test_interrupt_stops_graph():
    g = StateGraph().add_node("a", lambda s: {**s, "interrupt": True}).add_node("b", lambda s: s).add_edge("a", "b").add_edge("b", END)
    out = g.compile(entry="a").invoke({})
    assert out["status"] == "awaiting-human" and out["trace"] == ["a"]


def test_build_graph_has_all_nodes():
    assert set(build_graph().nodes) == set(NODES)


def test_summary_shape(bank):
    s = summary(bank)
    assert len(s["categories"]) == 29 and len(s["pillars"]) == 6
    assert {"overall", "review_queue", "final", "evidence_count"} <= set(s)


def test_final_only_when_queue_empty(portfolio, bank):
    assert portfolio["final"] is False and portfolio["review_queue"]
    assert bank["final"] == (not bank["review_queue"])
