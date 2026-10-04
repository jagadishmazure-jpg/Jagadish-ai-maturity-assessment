import pytest

from aimaturity.collectors import Evidence, number
from aimaturity.framework import categories, is_question, rubric, signals
from aimaturity.scoring import REVIEW_BELOW, WEIGHTS, score_all, score_category


def ev_for(sids, origin="self-reported", strength=1.0):
    items = []
    for s in sids:
        if is_question(s):
            items.append(Evidence(s, "questionnaire", "questionnaire", s, "answer", strength, origin))
        else:
            items.append(Evidence(s, signals()[s]["collector"], "repo", signals()[s]["example"]["path"], "file present"))
    return number(items)


def levels(cid, upto):
    return [s for lvl in range(2, upto + 1) for s in rubric()["categories"][cid]["levels"][lvl]]


@pytest.mark.parametrize("cid", sorted(categories()))
def test_no_evidence_is_basic(cid):
    r = score_category(cid, [])
    assert r.level == 1 and r.evidence == []


@pytest.mark.parametrize("cid", sorted(categories()))
def test_all_evidence_is_advanced(cid):
    r = score_category(cid, ev_for(levels(cid, 4)))
    assert r.level == 4 and r.next_missing == []


@pytest.mark.parametrize("cid", ["1.1", "3.2", "5.1", "6.2"])
def test_each_level_reached_exactly(cid):
    for lvl in (2, 3):
        assert score_category(cid, ev_for(levels(cid, lvl))).level == lvl


def test_level_needs_level_below():
    # level 3 and 4 signals of 3.2 without its level 2 signal
    r3 = rubric()["categories"]["3.2"]["levels"]
    r = score_category("3.2", ev_for(r3[3] + r3[4]))
    assert r.level == 1


def test_two_of_three_passes():
    lv3 = rubric()["categories"]["3.2"]["levels"][3]
    sids = rubric()["categories"]["3.2"]["levels"][2] + lv3[: -(len(lv3) // 3)]
    assert score_category("3.2", ev_for(sids)).level == 3


def test_partial_answer_counts_half():
    r = score_category("2.3", ev_for(["q_project_sponsors"], strength=0.5))
    assert r.ratios[2] == 0.5 and r.level == 1


def test_confidence_bounds_and_review_flag():
    for cid in categories():
        r = score_category(cid, [])
        assert 0 <= r.confidence <= 1
        assert r.needs_review == (r.confidence < REVIEW_BELOW or bool(r.review_reasons))


def test_sample_answers_always_go_to_review():
    r = score_category("2.3", ev_for(["q_project_sponsors"], origin="sample-answers"))
    assert r.level == 2 and r.needs_review
    assert any("sample answers" in x for x in r.review_reasons)


def test_self_reported_answers_trusted_more_than_samples():
    a = score_category("2.3", ev_for(["q_project_sponsors"], origin="self-reported"))
    b = score_category("2.3", ev_for(["q_project_sponsors"], origin="sample-answers"))
    assert a.confidence > b.confidence


def test_unanswered_questions_lower_confidence():
    answered = score_category("2.3", ev_for(["q_project_sponsors", "q_exec_owner"], strength=0.0))
    unanswered = score_category("2.3", [])
    assert answered.confidence > unanswered.confidence


def test_unscanned_absence_weighs_less():
    a = score_category("3.2", [], scanned_repos=True)
    b = score_category("3.2", [], scanned_repos=False)
    assert a.confidence > b.confidence


def test_weights_order():
    assert WEIGHTS["artifact"] > WEIGHTS["absent-scanned"] > WEIGHTS["self-reported"] > WEIGHTS["sample-answers"] > WEIGHTS["unanswered"]


def test_cited_evidence_belongs_to_reached_levels():
    ev = ev_for(levels("5.3", 2))
    r = score_category("5.3", ev)
    assert set(r.evidence) == {e.id for e in ev}


def test_next_missing_lists_next_level_gaps():
    r = score_category("5.3", ev_for(levels("5.3", 2)))
    assert set(r.next_missing) == set(rubric()["categories"]["5.3"]["levels"][3])


def test_score_all_covers_every_category():
    assert len(score_all([])) == 29


def test_as_dict_is_json_friendly():
    import json

    json.dumps(score_category("1.1", []).as_dict())
