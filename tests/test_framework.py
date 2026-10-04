import pytest

from aimaturity.framework import LEVEL_NAMES, categories, category_signals, check_consistency, framework, pillar_of, pillars, rubric

CATS = sorted(categories())


def test_six_pillars_and_29_categories():
    assert len(pillars()) == 6
    assert len(categories()) == 29


def test_category_counts_per_pillar():
    assert [len(p["categories"]) for p in pillars()] == [5, 5, 4, 5, 5, 5]


def test_level_names():
    assert LEVEL_NAMES == {1: "Basic", 2: "Ready", 3: "Dynamic", 4: "Advanced"}
    assert [framework()["levels"][k]["name"] for k in (1, 2, 3, 4)] == ["Basic", "Ready", "Dynamic", "Advanced"]


def test_consistency_is_clean():
    assert check_consistency() == []


def test_default_critical_categories_one_per_pillar():
    crit = rubric()["critical"]
    assert sorted({pillar_of(c) for c in crit}) == ["P1", "P2", "P3", "P4", "P5", "P6"]


def test_threshold_is_two_thirds():
    assert 0.6 < rubric()["threshold"] <= 2 / 3


@pytest.mark.parametrize("cid", CATS)
def test_category_has_descriptors_and_actions(cid):
    c = categories()[cid]
    assert sorted(c["descriptors"]) == [1, 2, 3, 4]
    assert all(len(c["descriptors"][k]) > 30 for k in c["descriptors"])
    assert len(set(c["descriptors"].values())) == 4
    assert sorted(c["actions"]) == [2, 3, 4]
    assert c["summary"] and c["why"]


@pytest.mark.parametrize("cid", CATS)
def test_category_rubric_shape(cid):
    r = categories()[cid]["rubric"]
    assert sorted(r["levels"]) == [2, 3, 4]
    assert all(r["levels"][lvl] for lvl in (2, 3, 4))
    assert set(r["effort"].values()) <= {"S", "M", "L"}
    assert cid not in r["depends_on"]
    assert category_signals(cid)


def test_dependencies_are_acyclic():
    deps = {c: v["rubric"]["depends_on"] for c, v in categories().items()}
    seen, stack = set(), set()

    def visit(n):
        assert n not in stack, f"cycle through {n}"
        if n in seen:
            return
        stack.add(n)
        for d in deps[n]:
            visit(d)
        stack.discard(n)
        seen.add(n)

    for c in deps:
        visit(c)


def test_framework_yaml_carries_attribution():
    src = framework()["source"]
    assert src["license"] == "CC BY-SA 3.0 IGO"
    assert src["license_url"] == "https://creativecommons.org/licenses/by-sa/3.0/igo/"
    assert "UNESCO" in src["work"] and "Stratejai" in src["developed_by"]
