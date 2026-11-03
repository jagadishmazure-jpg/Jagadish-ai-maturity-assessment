import pytest

from aimaturity.collectors import collect_questionnaire
from aimaturity.framework import capabilities, capability_signals, criteria, questions


def test_question_capabilities_exist():
    assert all(q["capability"] in capabilities() for q in questions().values())


def test_question_ids_prefixed():
    assert all(q.startswith("q_") for q in questions())


def test_people_capabilities_rely_on_questions():
    for cid in ("PO-1", "PO-2", "PO-3"):
        assert any(s.startswith("q_") for s in criteria(cid, 2) + criteria(cid, 3))


def test_question_capability_is_where_it_is_first_used():
    for qid, q in questions().items():
        assert qid in capability_signals(q["capability"]), qid


def test_questionnaire_has_48_questions():
    assert len(questions()) == 48


@pytest.mark.parametrize(("raw", "strength"), [("yes", 1.0), ("partial", 0.5), ("no", 0.0), (True, 1.0), (False, 0.0)])
def test_answer_strength(raw, strength):
    ev = collect_questionnaire({"label": "self-reported", "answers": {"q_coordinator": raw}})
    assert ev[0].strength == strength
    assert ev[0].origin == "self-reported"


def test_note_is_kept():
    ev = collect_questionnaire({"label": "sample-answers", "answers": {"q_coordinator": {"answer": "yes", "note": "named lead"}}})
    assert "named lead" in ev[0].detail and ev[0].origin == "sample-answers"


def test_unknown_question_rejected():
    with pytest.raises(ValueError):
        collect_questionnaire({"answers": {"q_not_a_question": "yes"}})


def test_default_label_is_self_reported():
    assert collect_questionnaire({"answers": {"q_coe": "no"}})[0].origin == "self-reported"
