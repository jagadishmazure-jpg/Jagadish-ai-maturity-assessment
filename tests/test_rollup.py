import pytest

from aimaturity.framework import capabilities, dimension_weights
from aimaturity.rollup import dimension_rollup, overall, readiness_index


def all_at(level):
    return dict.fromkeys(capabilities(), level)


def dim(rows, did):
    return next(r for r in rows if r["id"] == did)


@pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
def test_uniform_levels(level):
    rows = dimension_rollup(all_at(level), [])
    assert all(r["level"] == level and r["mean"] == level for r in rows)
    assert overall(rows)["level"] == level


def test_dimension_rows_carry_weights():
    rows = dimension_rollup(all_at(3), [])
    assert [r["id"] for r in rows] == list(dimension_weights())
    assert {r["id"]: r["weight"] for r in rows} == dimension_weights()


def test_dimension_level_is_floor_of_mean():
    lv = all_at(2)
    lv.update({"SV-1": 3, "SV-2": 4})  # mean 3.0
    assert dim(dimension_rollup(lv, []), "SV")["level"] == 3
    lv["SV-2"] = 3  # mean 2.67
    row = dim(dimension_rollup(lv, []), "SV")
    assert row["mean"] == 2.67 and row["level"] == 2


def test_anchor_capability_caps_dimension():
    lv = all_at(5)
    lv["GR-1"] = 2  # mean 4.0, anchor caps at 3
    gr = dim(dimension_rollup(lv, ["GR-1"]), "GR")
    assert gr["level"] == 3 and gr["capped_by"] == ["GR-1"]


def test_non_anchor_low_capability_does_not_cap():
    lv = all_at(5)
    lv["GR-3"] = 2
    gr = dim(dimension_rollup(lv, ["GR-1"]), "GR")
    assert gr["level"] == 4 and gr["capped_by"] == []


def test_overall_capped_by_weakest_dimension():
    lv = all_at(5)
    for c in ("FC-1", "FC-2"):
        lv[c] = 1
    o = overall(dimension_rollup(lv, []))
    assert o["level"] == 2 and o["capped"]


def test_overall_uses_dimension_weights():
    lv = all_at(3)
    for c in ("SI-1", "SI-2", "SI-3", "GR-1", "GR-2", "GR-3", "AE-1", "AE-2", "AE-3"):
        lv[c] = 4
    o = overall(dimension_rollup(lv, []))
    assert o["mean"] == round(3 + 0.14 * 3, 2) and o["level"] == 3


def test_overall_mean_and_name():
    o = overall(dimension_rollup(all_at(2), []))
    assert o["mean"] == 2 and o["level_name"] == "Prove"


@pytest.mark.parametrize(("level", "index"), [(1, 0.0), (3, 50.0), (5, 100.0)])
def test_readiness_index_spans_0_to_100(level, index):
    rows = dimension_rollup(all_at(level), [])
    assert readiness_index(rows) == index and overall(rows)["index"] == index


def test_readiness_index_moves_before_levels():
    lv = all_at(2)
    lv["AE-1"] = 3
    rows = dimension_rollup(lv, [])
    assert overall(rows)["level"] == 2
    assert readiness_index(rows) > readiness_index(dimension_rollup(all_at(2), []))
