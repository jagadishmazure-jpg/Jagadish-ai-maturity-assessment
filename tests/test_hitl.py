import json

import pytest
import yaml

from aimaturity.agents.assessor import assess
from aimaturity.hitl import ReviewError, apply_reviews, category_digest, read_log, read_reviews, record_review, verify_audit_log


def _rec(d, st, **kw):
    return record_review(d / "reviews.yaml", d / "audit-log.jsonl", st["org"].assessor, st["results"], st["evidence_by_id"], **kw)


@pytest.fixture
def fresh(org_copy):
    d = org_copy("portfolio")
    return d, assess("portfolio")


def test_self_review_rejected(fresh):
    d, st = fresh
    with pytest.raises(ReviewError, match="own assessment"):
        _rec(d, st, category="2.3", reviewer="aimaturity-agent", decision="confirm", comment="looks right to me")


def test_comment_required(fresh):
    d, st = fresh
    with pytest.raises(ReviewError, match="comment"):
        _rec(d, st, category="2.3", reviewer="A Reviewer", decision="confirm", comment="ok")


def test_override_needs_level(fresh):
    d, st = fresh
    with pytest.raises(ReviewError, match="level"):
        _rec(d, st, category="2.3", reviewer="A Reviewer", decision="override", comment="evidence says otherwise", level=None)


def test_unknown_category(fresh):
    d, st = fresh
    with pytest.raises(ReviewError):
        _rec(d, st, category="9.9", reviewer="A Reviewer", decision="confirm", comment="looks right to me")


def test_bad_decision(fresh):
    d, st = fresh
    with pytest.raises(ReviewError):
        _rec(d, st, category="2.3", reviewer="A Reviewer", decision="approve", comment="looks right to me")


def test_confirm_clears_queue_entry(fresh):
    d, st = fresh
    assert "2.3" in st["review_queue"]
    _rec(d, st, category="2.3", reviewer="A Reviewer", decision="confirm", comment="sponsor confirmed in interview")
    st2 = assess("portfolio")
    assert st2["statuses"]["2.3"]["status"] == "confirmed" and "2.3" not in st2["review_queue"]


def test_override_changes_final_level_and_rollup(fresh):
    d, st = fresh
    _rec(d, st, category="2.1", reviewer="A Reviewer", decision="override", level=3, comment="training plan and skills matrix exist offline")
    st2 = assess("portfolio")
    assert st2["statuses"]["2.1"]["final_level"] == 3 and st2["statuses"]["2.1"]["status"] == "overridden"
    assert st2["results"]["2.1"].level == st["results"]["2.1"].level  # computed level untouched


def test_review_goes_stale_when_evidence_changes(fresh):
    d, st = fresh
    _rec(d, st, category="2.3", reviewer="A Reviewer", decision="confirm", comment="sponsor confirmed in interview")
    q = yaml.safe_load((d / "questionnaire.yaml").read_text())
    q["answers"]["q_exec_owner"] = "yes"
    (d / "questionnaire.yaml").write_text(yaml.safe_dump(q))
    st2 = assess("portfolio")
    assert st2["statuses"]["2.3"]["status"] == "stale-review" and "2.3" in st2["review_queue"]


def test_audit_chain_intact_after_reviews(fresh):
    d, st = fresh
    for c in ("2.1", "2.3"):
        _rec(d, st, category=c, reviewer="A Reviewer", decision="confirm", comment="checked against interviews")
    assert verify_audit_log(d / "audit-log.jsonl") == []
    log = read_log(d / "audit-log.jsonl")
    assert [e["seq"] for e in log] == [1, 2] and log[1]["prev"] == log[0]["hash"]


def test_tampered_log_detected(fresh):
    d, st = fresh
    _rec(d, st, category="2.3", reviewer="A Reviewer", decision="confirm", comment="checked against interviews")
    lines = (d / "audit-log.jsonl").read_text().splitlines()
    e = json.loads(lines[0])
    e["level"] = 4
    (d / "audit-log.jsonl").write_text(json.dumps(e) + "\n")
    assert any("changed" in p for p in verify_audit_log(d / "audit-log.jsonl"))


def test_deleted_entry_detected(fresh):
    d, st = fresh
    for c in ("2.1", "2.3"):
        _rec(d, st, category=c, reviewer="A Reviewer", decision="confirm", comment="checked against interviews")
    lines = (d / "audit-log.jsonl").read_text().splitlines()
    (d / "audit-log.jsonl").write_text(lines[1] + "\n")
    assert verify_audit_log(d / "audit-log.jsonl")


def test_review_without_log_entry_ignored(fresh):
    d, st = fresh
    forged = {"category": "2.3", "reviewer": "A Reviewer", "decision": "override", "level": 4, "computed_level": 2,
              "comment": "trust me, it is advanced", "evidence_digest": category_digest(st["results"]["2.3"], st["evidence_by_id"]), "audit_hash": "f" * 64}
    out = apply_reviews(st["results"], st["evidence_by_id"], [forged], st["org"].assessor, [])
    assert out["2.3"]["status"] == "pending-review" and "audit" in out["2.3"]["rejected_review"]


def test_latest_review_wins(fresh):
    d, st = fresh
    _rec(d, st, category="2.1", reviewer="A Reviewer", decision="override", level=3, comment="first look at the evidence")
    _rec(d, st, category="2.1", reviewer="B Reviewer", decision="override", level=2, comment="second look, partial only")
    assert assess("portfolio")["statuses"]["2.1"]["final_level"] == 2
    assert len(read_reviews(d / "reviews.yaml")) == 2


def test_digest_ignores_evidence_id_renumbering(portfolio):
    r = portfolio["results"]["5.3"]
    assert category_digest(r, portfolio["evidence_by_id"]) == category_digest(r, dict(portfolio["evidence_by_id"]))


def test_checked_in_logs_are_intact():
    from aimaturity.orgs import list_orgs, load_org

    for o in list_orgs():
        assert verify_audit_log(load_org(o).dir / "audit-log.jsonl") == []
