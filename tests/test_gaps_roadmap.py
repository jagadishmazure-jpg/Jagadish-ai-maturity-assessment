import pytest

from aimaturity.roadmap import DURATION, MONTHS, months_view, schedule, work_items


@pytest.fixture(params=["portfolio", "kestrel-bay-bank", "valemont-revenue-agency"])
def st(request, portfolio, bank, agency):
    return {"portfolio": portfolio, "kestrel-bay-bank": bank, "valemont-revenue-agency": agency}[request.param]


def test_gap_is_target_minus_final_level(st):
    for g in st["gaps"]:
        assert g["gap"] == max(0, g["target"] - st["statuses"][g["category"]]["final_level"])
        assert len(g["steps"]) == g["gap"]


def test_steps_carry_missing_evidence_and_action(st):
    for g in st["gaps"]:
        for s in g["steps"]:
            assert s["action"] and s["effort"] in DURATION
            assert len(s["missing"]) == len(s["missing_text"])


def test_targets_follow_org_overrides(portfolio, agency):
    assert portfolio["org"].target("3.1") == 4 and portfolio["org"].target("1.1") == 3
    assert agency["org"].target("6.4") == 2 and agency["org"].target("5.2") == 4


def test_work_items_one_per_step(st):
    assert len(st["items"]) == sum(g["gap"] for g in st["gaps"])


def test_items_sorted_by_priority(st):
    pr = [i["priority"] for i in st["items"]]
    assert pr == sorted(pr, reverse=True)


def test_dependencies_exist_and_chain_within_category(st):
    ids = {i["id"] for i in st["items"]}
    for i in st["items"]:
        assert set(i["depends_on"]) <= ids
        if i["to_level"] - 1 > st["statuses"][i["category"]]["final_level"]:
            assert f"{i['category']}->{i['to_level'] - 1}" in i["depends_on"]


def test_quick_win_definition(st):
    for i in st["items"]:
        if i["kind"] == "quick-win":
            assert i["effort"] == "S" and not i["depends_on"]


def test_schedule_respects_dependencies(st):
    end = {p["id"]: p["end"] for p in st["schedule"]["plan"]}
    for p in st["schedule"]["plan"]:
        for d in p["depends_on"]:
            assert d in end and end[d] < p["start"]


def test_schedule_respects_capacity(st):
    cap = st["schedule"]["capacity"]
    assert all(len(v) <= cap for v in months_view(st["schedule"]).values())


def test_quick_wins_start_early(st):
    assert all(p["start"] <= 3 for p in st["schedule"]["plan"] if p["kind"] == "quick-win")


def test_plan_fits_twelve_months_and_durations(st):
    for p in st["schedule"]["plan"]:
        assert 1 <= p["start"] <= p["end"] <= MONTHS
        assert p["end"] - p["start"] + 1 == DURATION[p["effort"]]


def test_every_item_planned_or_backlogged(st):
    planned = {p["id"] for p in st["schedule"]["plan"]}
    assert planned | set(st["schedule"]["backlog"]) == {i["id"] for i in st["items"]}
    assert not planned & set(st["schedule"]["backlog"])


def test_reassessment_milestones(st):
    assert [m["month"] for m in st["schedule"]["milestones"]] == [6, 12]


def test_capacity_one_serialises():
    items = [{"id": f"1.{n}->2", "depends_on": [], "kind": "strategic", "priority": 1, "months": 1} for n in range(1, 4)]
    sch = schedule(items, capacity=1)
    assert [p["start"] for p in sch["plan"]] == [1, 2, 3]


def test_long_item_that_cannot_finish_goes_to_backlog():
    items = [{"id": "1.1->2", "depends_on": [], "kind": "strategic", "priority": 1, "months": 13}]
    assert schedule(items)["backlog"] == ["1.1->2"]


def test_no_gaps_no_items():
    assert work_items([]) == []
