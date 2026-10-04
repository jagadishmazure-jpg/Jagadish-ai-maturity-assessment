"""The three sample assessments: honest labelling, cross-links and expected results."""

import yaml

from aimaturity.agents.assessor import summary
from aimaturity.crosslinks import check_links

PEOPLE = ["2.1", "2.2", "2.3", "2.4", "2.5"]


def test_portfolio_questionnaire_is_labelled_sample(portfolio):
    assert portfolio["org"].answers()["label"] == "sample-answers"
    assert all(e.origin == "sample-answers" for e in portfolio["evidence"] if e.collector == "questionnaire")


def test_portfolio_people_items_never_auto_accepted(portfolio):
    for cid in PEOPLE:
        r = portfolio["results"][cid]
        rests_on_sample = any(s.basis == "sample-answers" and s.present for s in r.signals.values())
        if r.level > 1 or rests_on_sample:
            assert cid in portfolio["review_queue"], cid


def test_portfolio_has_no_seeded_reviews(portfolio):
    assert all(s["review"] is None for s in portfolio["statuses"].values())


def test_portfolio_scans_eight_repositories(portfolio):
    assert len(portfolio["org"].repo_names()) == 8
    assert {e.source for e in portfolio["evidence"]} - {"questionnaire"} == set(portfolio["org"].repo_names())


def test_cross_links_satisfied(portfolio):
    rows = check_links(portfolio)
    assert rows and all(r["ok"] for r in rows)
    assert {r["repo"] for r in rows} == {"agentic-ai-model-risk", "azure-finops", "fabric-enterprise-bi"}


def test_governance_pillar_draws_on_model_risk_repo(portfolio):
    ev = portfolio["evidence_by_id"]
    for cid in ("5.3", "5.5"):
        assert any(ev[i].source == "agentic-ai-model-risk" for i in portfolio["results"][cid].evidence)


def test_cost_and_value_draw_on_finops_repo(portfolio):
    ev = portfolio["evidence_by_id"]
    for cid in ("1.4", "3.2"):
        assert any(ev[i].source == "azure-finops" for i in portfolio["results"][cid].evidence)


def test_data_pillar_draws_on_fabric_repo(portfolio):
    ev = portfolio["evidence_by_id"]
    assert any(ev[i].source == "fabric-enterprise-bi" for i in portfolio["results"]["6.2"].evidence)


def test_portfolio_strongest_pillar_is_technology(portfolio):
    s = summary(portfolio)
    best = max(s["pillars"], key=lambda p: p["mean"])
    assert best["id"] == "P3"


def test_fictional_orgs_use_self_reported_answers(bank, agency):
    for st in (bank, agency):
        assert st["org"].answers()["label"] == "self-reported"
        assert st["org"].config.get("manifest")


def test_bank_and_agency_results(bank, agency):
    assert summary(bank)["overall"]["level"] == 3
    assert summary(agency)["overall"]["level"] == 2


def test_agency_uses_its_own_critical_list(agency):
    assert agency["org"].critical == ["1.1", "2.3", "5.1", "5.2", "6.2"]


def test_seeded_reviews_apply(bank, agency):
    assert bank["statuses"]["2.1"]["status"] == "confirmed"
    assert agency["statuses"]["4.4"]["status"] == "overridden" and agency["statuses"]["4.4"]["final_level"] == 3
    assert agency["statuses"]["1.2"]["status"] == "confirmed"


def test_labels_mostly_agree(bank, agency):
    for st in (bank, agency):
        labels = yaml.safe_load((st["org"].dir / "labels.yaml").read_text())["labels"]
        agree = sum(st["results"][c].level == labels[c] for c in labels) / 29
        assert agree >= 0.85


def test_fictional_names_only(bank, agency):
    assert bank["org"].name == "Kestrel Bay Bank" and agency["org"].name == "Valemont Revenue Agency"
