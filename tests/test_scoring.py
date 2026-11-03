import json

import pytest

from aimaturity.collectors import Evidence, number
from aimaturity.framework import STEPS, capabilities, criteria, is_question, rubric, signals
from aimaturity.scoring import CONFIDENCE_MIX, REVIEW_BELOW, WEIGHTS, score_all, score_capability

CAPS = sorted(capabilities())


def ev_for(sids, origin="self-reported", strength=1.0):
    items = []
    for s in sids:
        if is_question(s):
            items.append(Evidence(s, "questionnaire", "questionnaire", s, "answer", strength, origin))
        else:
            items.append(Evidence(s, signals()[s]["collector"], "repo", signals()[s]["example"]["path"], "file present"))
    return number(items)


def upto(cid, top):
    return list(dict.fromkeys(s for lvl in range(2, top + 1) for s in criteria(cid, lvl)))


def rule(cid, lvl):
    return rubric()["capabilities"][cid]["levels"][lvl]


@pytest.mark.parametrize("cid", CAPS)
def test_no_evidence_is_explore(cid):
    r = score_capability(cid, [])
    assert r.level == 1 and r.level_name == "Explore" and r.evidence == []


@pytest.mark.parametrize("cid", CAPS)
def test_all_evidence_is_optimise(cid):
    r = score_capability(cid, ev_for(upto(cid, 5)))
    assert r.level == 5 and r.level_name == "Optimise" and r.next_missing == [] and r.blocked_by == []


@pytest.mark.parametrize("cid", CAPS)
def test_each_level_reached_exactly(cid):
    for lvl in STEPS[:-1]:
        assert score_capability(cid, ev_for(upto(cid, lvl))).level == lvl


@pytest.mark.parametrize("cid", CAPS)
def test_musts_alone_reach_a_level_without_support(cid):
    for lvl in STEPS:
        if not rule(cid, lvl)["support"]:
            sids = upto(cid, lvl - 1) + rule(cid, lvl)["must"]
            assert score_capability(cid, ev_for(sids)).level >= lvl


def test_level_needs_level_below():
    sids = rule("SV-2", 3)["must"] + rule("SV-2", 4)["must"] + rule("SV-2", 4)["support"]
    assert score_capability("SV-2", ev_for(sids)).level == 1


def test_missing_must_blocks_even_with_full_support():
    r = score_capability("SV-1", ev_for(rule("SV-1", 2)["support"]))
    assert r.level == 1 and r.blocked_by == rule("SV-1", 2)["must"]


def test_half_the_support_is_enough():
    lv4 = rule("SV-2", 4)
    assert len(lv4["support"]) == 2
    one = upto("SV-2", 3) + lv4["must"] + lv4["support"][:1]
    none = upto("SV-2", 3) + lv4["must"]
    assert score_capability("SV-2", ev_for(one)).level == 4
    assert score_capability("SV-2", ev_for(none)).level == 3


def test_partial_answer_never_satisfies_a_must():
    r = score_capability("PO-1", ev_for(["q_project_sponsors", "q_coordinator"], strength=0.5))
    assert r.level == 1 and r.ratios[2] == 0.5 and r.blocked_by == ["q_project_sponsors"]


def test_partial_answer_counts_half_as_support():
    sids = ev_for(["vision_statement"]) + ev_for(["q_goal_field"], strength=0.5)
    assert score_capability("SV-1", number(sids)).level == 2


def test_answers_alone_stop_at_operate():
    qs = [s for s in upto("PO-1", 5) if is_question(s)]
    r = score_capability("PO-1", ev_for(qs))
    assert r.level == 3 and "codeowners" in r.blocked_by


def test_blocked_by_names_the_next_must():
    r = score_capability("SV-1", ev_for(upto("SV-1", 2)))
    assert r.level == 2 and r.blocked_by == ["vision_targets"]
    assert set(r.next_missing) == set(criteria("SV-1", 3))


def test_confidence_bounds_and_review_flag():
    for cid in CAPS:
        r = score_capability(cid, [])
        assert 0 <= r.confidence <= 1
        assert r.needs_review == (r.confidence < REVIEW_BELOW or bool(r.review_reasons))


def test_confidence_mix_sums_to_one():
    assert abs(sum(CONFIDENCE_MIX.values()) - 1.0) < 1e-9


def test_sample_answers_always_go_to_review():
    r = score_capability("PO-1", ev_for(["q_project_sponsors", "q_coordinator"], origin="sample-answers"))
    assert r.level == 2 and r.needs_review
    assert any("sample answers" in x for x in r.review_reasons)


def test_self_reported_answers_trusted_more_than_samples():
    sids = ["q_project_sponsors", "q_coordinator"]
    a = score_capability("PO-1", ev_for(sids, origin="self-reported"))
    b = score_capability("PO-1", ev_for(sids, origin="sample-answers"))
    assert a.confidence > b.confidence


def test_unanswered_questions_lower_confidence():
    answered = score_capability("PO-1", ev_for(["q_project_sponsors", "q_coordinator"], strength=0.0))
    unanswered = score_capability("PO-1", [])
    assert answered.confidence > unanswered.confidence


def test_unscanned_absence_weighs_less():
    a = score_capability("PL-2", [], scanned_repos=True)
    b = score_capability("PL-2", [], scanned_repos=False)
    assert a.confidence > b.confidence


def test_artifacts_are_more_verifiable_than_answers():
    art = score_capability("SV-1", ev_for(upto("SV-1", 2)))
    ans = score_capability("PO-1", ev_for(upto("PO-1", 2)))
    assert art.confidence > ans.confidence


def test_weights_order():
    assert WEIGHTS["artifact"] > WEIGHTS["absent-scanned"] > WEIGHTS["self-reported"] > WEIGHTS["sample-answers"] > WEIGHTS["unanswered"]


def test_cited_evidence_belongs_to_reached_levels():
    ev = ev_for(upto("GR-2", 3))
    r = score_capability("GR-2", ev)
    assert r.level == 3 and set(r.evidence) == {e.id for e in ev}


def test_score_all_covers_every_capability():
    assert len(score_all([])) == 23


def test_as_dict_is_json_friendly():
    d = score_capability("SV-1", []).as_dict()
    json.dumps(d)
    assert set(d["ratios"]) == {"2", "3", "4", "5"}
