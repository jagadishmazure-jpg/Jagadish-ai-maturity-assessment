"""Schema and consistency checks for the framework, rubric and every sample organisation."""

from __future__ import annotations

import json

import jsonschema
import yaml

from aimaturity import SCHEMAS
from aimaturity.framework import check_consistency, questions
from aimaturity.orgs import list_orgs, load_org


def _schema(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text())


def validate_all() -> list[str]:
    errs = list(check_consistency())
    for org_id in list_orgs():
        org = load_org(org_id)
        for e in jsonschema.Draft202012Validator(_schema("org.schema.json")).iter_errors(org.config):
            errs.append(f"{org_id}/org.yaml: {e.message}")
        if org.config.get("questionnaire"):
            ans = org.answers()
            for e in jsonschema.Draft202012Validator(_schema("answers.schema.json")).iter_errors(ans):
                errs.append(f"{org_id}/questionnaire.yaml: {e.message}")
            errs += [f"{org_id}: unknown question {q}" for q in ans.get("answers", {}) if q not in questions()]
        if org.config.get("snapshot"):
            snap = json.loads((org.dir / org.config["snapshot"]).read_text())
            for e in jsonschema.Draft202012Validator(_schema("snapshot.schema.json")).iter_errors(snap):
                errs.append(f"{org_id}/snapshot: {e.message}")
        if org.config.get("labels"):
            labels = yaml.safe_load((org.dir / org.config["labels"]).read_text())["labels"]
            if len(labels) != 29:
                errs.append(f"{org_id}: labels must cover all 29 categories")
    return errs
