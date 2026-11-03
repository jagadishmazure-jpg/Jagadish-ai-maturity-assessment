import pytest

from aimaturity.framework import (
    LEVEL_NAMES,
    STEPS,
    TOP,
    capabilities,
    capability_signals,
    check_consistency,
    criteria,
    dimension_of,
    dimension_weights,
    dimensions,
    framework,
    is_question,
    rubric,
)

CAPS = sorted(capabilities())
DIMS = ["SV", "DF", "PL", "AE", "SI", "GR", "PO", "FC"]


def test_eight_dimensions_and_23_capabilities():
    assert [d["id"] for d in dimensions()] == DIMS
    assert len(capabilities()) == 23


def test_capability_counts_per_dimension():
    assert [len(d["capabilities"]) for d in dimensions()] == [3, 3, 3, 3, 3, 3, 3, 2]


def test_capability_ids_follow_dimension():
    for cid in CAPS:
        assert cid.split("-")[0] == dimension_of(cid)


def test_level_names():
    assert LEVEL_NAMES == {1: "Explore", 2: "Prove", 3: "Operate", 4: "Scale", 5: "Optimise"}
    assert [framework()["levels"][k]["name"] for k in range(1, 6)] == list(LEVEL_NAMES.values())
    assert TOP == 5 and STEPS == (2, 3, 4, 5)


def test_weights_sum_to_one_and_favour_risk_dimensions():
    w = dimension_weights()
    assert abs(sum(w.values()) - 1.0) < 1e-9
    assert min(w["AE"], w["SI"], w["GR"]) >= max(w["SV"], w["PO"], w["FC"])


def test_consistency_is_clean():
    assert check_consistency() == []


def test_default_anchor_capabilities_one_per_dimension():
    anchors = rubric()["anchors"]
    assert len(anchors) == len(DIMS)
    assert sorted(dimension_of(c) for c in anchors) == sorted(DIMS)


def test_support_share_is_half():
    assert rubric()["support_share"] == 0.5


def test_evidence_ceiling_needs_artifacts_from_scale():
    assert rubric()["ceiling_from"] == 4
    for cid in CAPS:
        for lvl in (4, 5):
            assert any(not is_question(s) for s in rubric()["capabilities"][cid]["levels"][lvl]["must"]), (cid, lvl)


def test_model_metadata_names_the_author():
    m = framework()["model"]
    assert m["short"] == "EAMM" and m["author"] == "Jagadish Meduri"


@pytest.mark.parametrize("cid", CAPS)
def test_capability_has_descriptors_and_actions(cid):
    c = capabilities()[cid]
    assert sorted(c["descriptors"]) == [1, 2, 3, 4, 5]
    assert all(len(c["descriptors"][k]) > 20 for k in c["descriptors"])
    assert len(set(c["descriptors"].values())) == 5
    assert sorted(c["actions"]) == [2, 3, 4, 5]
    assert c["summary"] and c["why"]


@pytest.mark.parametrize("cid", CAPS)
def test_capability_rubric_shape(cid):
    r = capabilities()[cid]["rubric"]
    assert sorted(r["levels"]) == list(STEPS)
    assert all(r["levels"][lvl]["must"] for lvl in STEPS)
    assert all(isinstance(r["levels"][lvl]["support"], list) for lvl in STEPS)
    assert criteria(cid, 2)[0] == r["levels"][2]["must"][0]
    assert set(r["effort"].values()) <= {"S", "M", "L"}
    assert cid not in r["depends_on"]
    assert capability_signals(cid)


@pytest.mark.parametrize("cid", CAPS)
def test_capability_maps_to_three_standards(cid):
    m = capabilities()[cid]["maps_to"]
    assert set(m) == {"nist_ai_rmf", "iso_42001", "eu_ai_act"}
    assert m["nist_ai_rmf"] and m["iso_42001"]


def test_dependencies_are_acyclic():
    deps = {c: v["rubric"]["depends_on"] for c, v in capabilities().items()}
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


def test_framework_has_no_external_source_block():
    assert "source" not in framework()
