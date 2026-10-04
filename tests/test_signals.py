import re

import pytest

from aimaturity.collectors import COLLECTORS, matches
from aimaturity.framework import signals

SIGS = sorted(signals())


@pytest.mark.parametrize("sid", SIGS)
def test_example_satisfies_its_own_rule(sid):
    ex = signals()[sid]["example"]
    assert matches(sid, ex["path"], ex["content"])


@pytest.mark.parametrize("sid", SIGS)
def test_signal_is_well_formed(sid):
    s = signals()[sid]
    assert s["collector"] in COLLECTORS and s["collector"] != "questionnaire"
    assert s["description"] and s["paths"]
    if s.get("contains"):
        re.compile(s["contains"])


def test_signal_ids_are_not_questions():
    assert not any(s.startswith("q_") for s in SIGS)


def test_path_outside_globs_does_not_match():
    assert not matches("iac_any", "notes/random.txt", "resource x")


def test_content_rule_must_match():
    sid = next(s for s in SIGS if signals()[s].get("contains"))
    assert not matches(sid, signals()[sid]["example"]["path"], "nothing relevant here")


def test_every_collector_has_signals():
    used = {signals()[s]["collector"] for s in SIGS}
    assert used == set(COLLECTORS) - {"questionnaire"}
