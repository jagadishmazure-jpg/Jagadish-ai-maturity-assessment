from aimaturity.framework import categories
from aimaturity.rollup import overall, pillar_rollup


def all_at(level):
    return dict.fromkeys(categories(), level)


def test_uniform_levels():
    rows = pillar_rollup(all_at(3), [])
    assert all(r["level"] == 3 and r["mean"] == 3 for r in rows)
    assert overall(rows)["level"] == 3


def test_median_floors():
    lv = all_at(2)
    lv.update({"1.1": 3, "1.2": 3, "1.3": 4})
    p1 = pillar_rollup(lv, [])[0]
    assert p1["median"] == 3 and p1["level"] == 3


def test_even_count_median_floors():
    lv = all_at(1)
    lv.update({"3.1": 2, "3.2": 3, "3.3": 3})  # P3 has four categories: median 2.5
    p3 = pillar_rollup(lv, [])[2]
    assert p3["median"] == 2.5 and p3["level"] == 2


def test_critical_category_caps_pillar():
    lv = all_at(4)
    lv["5.1"] = 2
    p5 = pillar_rollup(lv, ["5.1"])[4]
    assert p5["level"] == 2 and p5["capped_by"] == ["5.1"]


def test_non_critical_low_category_does_not_cap():
    lv = all_at(4)
    lv["5.2"] = 1
    assert pillar_rollup(lv, ["5.1"])[4]["level"] == 4


def test_overall_capped_by_weakest_pillar():
    lv = all_at(4)
    for c in ("2.1", "2.2", "2.3", "2.4", "2.5"):
        lv[c] = 1
    o = overall(pillar_rollup(lv, []))
    assert o["level"] == 2 and o["capped"]


def test_overall_mean_reported():
    o = overall(pillar_rollup(all_at(2), []))
    assert o["mean"] == 2 and o["level_name"] == "Ready"
