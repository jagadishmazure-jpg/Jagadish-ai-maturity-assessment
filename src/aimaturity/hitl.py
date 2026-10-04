"""Human-in-the-loop review of low-confidence categories, with a hash-chained audit log.

* Categories under the confidence bar (0.6) are queued; an assessment is not final while any are pending.
* A review confirms the computed level or overrides it, and needs a comment. The reviewer cannot
  be the assessor (separation of duties).
* Each review is bound to a digest of the category's evidence. When the evidence changes, the review
  goes stale and the category returns to the queue.
* Every review is appended to ``audit-log.jsonl``; each entry carries the hash of the previous one, so
  edits or deletions break the chain and ``verify_audit_log`` reports them.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from aimaturity.collectors import Evidence
from aimaturity.scoring import CategoryResult

GENESIS = "0" * 64
DECISIONS = ("confirm", "override")


class ReviewError(ValueError):
    """A review that breaks a rule (self-review, empty comment, bad level, unknown category)."""


def category_digest(result: CategoryResult, evidence: dict[str, Evidence]) -> str:
    """Stable fingerprint of what the category was scored on (paths and answers, not evidence ids)."""
    rows = []
    for sid, st in sorted(result.signals.items()):
        refs = sorted(f"{evidence[i].source}:{evidence[i].path}" for i in st.evidence)
        rows.append([sid, st.present, st.basis, refs])
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()[:16]


def _entry_hash(entry: dict[str, Any]) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def read_log(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def verify_audit_log(path: Path) -> list[str]:
    problems, prev = [], GENESIS
    for n, e in enumerate(read_log(path), 1):
        if e.get("seq") != n:
            problems.append(f"entry {n}: sequence {e.get('seq')} out of order")
        if e.get("prev") != prev:
            problems.append(f"entry {n}: previous hash does not match")
        if _entry_hash(e) != e.get("hash"):
            problems.append(f"entry {n}: content changed after it was written")
        prev = e.get("hash", "")
    return problems


def read_reviews(path: Path) -> list[dict[str, Any]]:
    return (yaml.safe_load(path.read_text()) or {}).get("reviews", []) if path.is_file() else []


def validate_review(review: dict[str, Any], assessor: str, results: dict[str, CategoryResult]) -> None:
    if review["category"] not in results:
        raise ReviewError(f"unknown category {review['category']}")
    if review["reviewer"].strip().lower() == assessor.strip().lower():
        raise ReviewError("the assessor cannot review their own assessment")
    if review["decision"] not in DECISIONS:
        raise ReviewError(f"decision must be one of {DECISIONS}")
    if len(review.get("comment", "").strip()) < 10:
        raise ReviewError("a review needs a comment of at least 10 characters")
    if review["decision"] == "override" and review.get("level") not in (1, 2, 3, 4):
        raise ReviewError("an override needs a level from 1 to 4")


def record_review(
    reviews_path: Path, log_path: Path, assessor: str, results: dict[str, CategoryResult], evidence: dict[str, Evidence], **review: Any
) -> dict[str, Any]:
    """Validate, append to the reviews file and the audit log, return the stored review."""
    validate_review(review, assessor, results)
    res = results[review["category"]]
    stored = {
        "category": review["category"], "reviewer": review["reviewer"], "decision": review["decision"],
        "level": review["level"] if review["decision"] == "override" else res.level, "computed_level": res.level,
        "comment": review["comment"].strip(), "evidence_digest": category_digest(res, evidence),
    }
    log = read_log(log_path)
    entry = {"seq": len(log) + 1, "action": "review", **stored, "prev": log[-1]["hash"] if log else GENESIS}
    entry["hash"] = _entry_hash(entry)
    stored["audit_hash"] = entry["hash"]
    with log_path.open("a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    reviews = read_reviews(reviews_path) + [stored]
    reviews_path.write_text(yaml.safe_dump({"reviews": reviews}, sort_keys=False, width=120))
    return stored


def apply_reviews(
    results: dict[str, CategoryResult], evidence: dict[str, Evidence], reviews: list[dict[str, Any]], assessor: str, log: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Status and final level per category. The latest valid review for a category wins."""
    logged = {e["hash"] for e in log}
    latest: dict[str, dict[str, Any]] = {}
    rejected: dict[str, str] = {}
    for r in reviews:
        try:
            validate_review(r, assessor, results)
        except ReviewError as err:
            rejected[r.get("category", "?")] = str(err)
            continue
        if r.get("audit_hash") not in logged:
            rejected[r["category"]] = "review has no matching audit log entry"
            continue
        latest[r["category"]] = r
    out = {}
    for cid, res in results.items():
        r = latest.get(cid)
        if r and r["evidence_digest"] == category_digest(res, evidence):
            status = "overridden" if r["decision"] == "override" and r["level"] != res.level else "confirmed"
            out[cid] = {"status": status, "final_level": r["level"], "review": r}
        elif r:
            out[cid] = {"status": "stale-review", "final_level": res.level, "review": r}
        elif res.needs_review:
            out[cid] = {"status": "pending-review", "final_level": res.level, "review": None}
        else:
            out[cid] = {"status": "auto", "final_level": res.level, "review": None}
        if cid in rejected and out[cid]["status"] in {"pending-review", "auto"}:
            out[cid]["rejected_review"] = rejected[cid]
    return out


def queue(statuses: dict[str, dict[str, Any]]) -> list[str]:
    return [cid for cid, s in statuses.items() if s["status"] in {"pending-review", "stale-review"}]
