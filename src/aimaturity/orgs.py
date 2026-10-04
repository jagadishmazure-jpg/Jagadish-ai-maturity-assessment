"""Organisation configs under ``samples/<org>/org.yaml`` and how their evidence is gathered.

Three evidence modes:

* ``repos`` + ``snapshot``: real checkouts scanned read-only (``--live``), or the checked-in snapshot
  of that scan so CI works without the checkouts.
* ``manifest``: a synthetic organisation described as repositories of files. A repository can list
  ``signals`` (files are built from each signal's example) and explicit ``files``.
* ``questionnaire``: answers for items code cannot show, labelled self-reported or sample-answers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from aimaturity import ROOT, SAMPLES
from aimaturity.collectors import Evidence, collect_questionnaire, collect_source, number
from aimaturity.framework import rubric, signals
from aimaturity.sources import ManifestSource, RepoSource


@dataclass
class Org:
    id: str
    dir: Path
    config: dict[str, Any]

    @property
    def name(self) -> str:
        return self.config["name"]

    @property
    def assessor(self) -> str:
        return self.config["assessor"]

    @property
    def critical(self) -> list[str]:
        return self.config.get("critical", rubric()["critical"])

    def target(self, category_id: str) -> int:
        t = self.config.get("targets", {})
        cats, pills = t.get("categories", {}), t.get("pillars", {})
        return int(cats.get(category_id, pills.get(category_id.split(".")[0], t.get("default", 3))))

    def answers(self) -> dict[str, Any] | None:
        q = self.config.get("questionnaire")
        return yaml.safe_load((self.dir / q).read_text()) if q else None

    def repo_names(self) -> list[str]:
        if "repos" in self.config:
            return [r["name"] for r in self.config["repos"]]
        return [r["name"] for r in self.manifest()["repos"]]

    def manifest(self) -> dict[str, Any]:
        return yaml.safe_load((self.dir / self.config["manifest"]).read_text())


def list_orgs() -> list[str]:
    return sorted(p.parent.name for p in SAMPLES.glob("*/org.yaml"))


def load_org(org_id: str) -> Org:
    d = SAMPLES / org_id
    if not (d / "org.yaml").is_file():
        raise KeyError(f"unknown org {org_id}; known: {', '.join(list_orgs())}")
    return Org(org_id, d, yaml.safe_load((d / "org.yaml").read_text()))


def manifest_sources(manifest: dict[str, Any]) -> list[ManifestSource]:
    out = []
    for repo in manifest["repos"]:
        files: dict[str, str] = {}
        for sid in repo.get("signals", []):
            ex = signals()[sid]["example"]
            files[ex["path"]] = files.get(ex["path"], "") + ex["content"]
        for path, content in (repo.get("files") or {}).items():
            files[path] = files.get(path, "") + content
        out.append(ManifestSource(repo["name"], files))
    return out


def live_sources(org: Org, root: Path | None = None) -> list[RepoSource]:
    root = root or ROOT.parent
    out = []
    for r in org.config["repos"]:
        p = (root / r.get("path", r["name"])).resolve()
        if not p.is_dir():
            raise FileNotFoundError(f"{r['name']}: no checkout at {p}")
        out.append(RepoSource(r["name"], p))
    return out


def scan(sources: list) -> list[Evidence]:
    items: list[Evidence] = []
    for s in sources:
        items += collect_source(s)
    return items


def write_snapshot(org: Org, items: list[Evidence]) -> Path:
    rows = sorted(({k: v for k, v in e.as_dict().items() if k not in {"id", "strength", "origin"}} for e in items), key=lambda r: (r["source"], r["path"], r["signal"]))
    path = org.dir / org.config["snapshot"]
    path.write_text(json.dumps({"repos": org.repo_names(), "evidence": rows}, indent=1) + "\n")
    return path


def read_snapshot(org: Org) -> list[Evidence]:
    data = json.loads((org.dir / org.config["snapshot"]).read_text())
    return [Evidence(**r) for r in data["evidence"]]


def gather(org: Org, live: bool = False, root: Path | None = None) -> list[Evidence]:
    """Numbered evidence for an org: artifacts (live scan, snapshot or manifest) plus questionnaire."""
    if "manifest" in org.config:
        items = scan(manifest_sources(org.manifest()))
    elif live:
        items = scan(live_sources(org, root))
    else:
        items = read_snapshot(org)
    answers = org.answers()
    if answers:
        items += collect_questionnaire(answers)
    return number(items)
