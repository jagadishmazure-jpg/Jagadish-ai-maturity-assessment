import random

import pytest

from aimaturity.evals import calibration, citations, run_all, stability, synthetic_org, thresholds


@pytest.fixture(scope="module")
def results():
    return {r["gate"]: r for r in run_all()}


@pytest.mark.parametrize("gate", ["stability", "citations", "calibration"])
def test_gate_passes(results, gate):
    assert results[gate]["ok"], results[gate]


def test_shuffle_invariance(results):
    assert results["stability"]["shuffle_identical"]


def test_dropout_is_local(results):
    assert results["stability"]["nonlocal_moves"] == 0


def test_citation_completeness_is_total(results):
    assert results["citations"]["completeness"] == 1.0 and results["citations"]["valid_ids"] == 1.0


def test_verifier_catches_every_injected_fault(results):
    assert results["citations"]["verifier_catch"] == 1.0 and results["citations"]["injected"] > 0


def test_calibration_thresholds(results):
    t = thresholds()["calibration"]
    c = results["calibration"]
    assert c["exact"] >= t["exact_min"] and c["within_one"] >= t["within_one_min"]
    assert c["high_conf_accuracy"] >= c["low_conf_accuracy"]


def test_calibration_uses_labelled_samples(results):
    assert results["calibration"]["by_source"]["kestrel-bay-bank"] == 29
    assert results["calibration"]["by_source"]["valemont-revenue-agency"] == 29


def test_synthetic_org_is_deterministic():
    a, ta = synthetic_org(random.Random(1), 0)
    b, tb = synthetic_org(random.Random(1), 0)
    assert ta == tb and [e.as_dict() for e in a] == [e.as_dict() for e in b]


def test_gates_fail_when_thresholds_impossible():
    t = thresholds()
    assert not calibration({**t["calibration"], "exact_min": 1.01})["ok"]
    assert not citations({**t["citations"], "verifier_catch_min": 1.01})["ok"]
    assert not stability({**t["stability"], "dropout_mean_categories": -1})["ok"]
