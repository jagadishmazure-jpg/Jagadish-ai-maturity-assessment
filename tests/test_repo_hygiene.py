"""Repository hygiene: complete docs, current outputs, no dates, licensing, no PDF."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".venv", ".pytest_cache", ".ruff_cache", "__pycache__", ".terraform", "refs", "out", "evidence"}
MD = sorted(p for p in ROOT.rglob("*.md") if not SKIP_PARTS & set(p.parts))
SECTIONS = [
    "Purpose", "Architecture", "How it works", "Key files", "Code excerpts", "Configuration", "Commands",
    "Real output", "Tests and gates", "Guardrails", "Security and governance", "Observability",
    "Failure modes", "Mapping to Azure services", "Limitations", "Interview talking points", "Adopt this",
]  # fmt: skip
FULL_DIRS = {"dimensions": 8, "components": 13, "samples": 3, "infra": 4}
FULL_DOCS = sorted(p for d in FULL_DIRS for p in (ROOT / "docs" / d).glob("*.md") if p.name != "README.md")
MONTHS = r"\b(January|February|March|April|June|July|August|September|October|November|December)\b"
SUFFIXES = {".md", ".py", ".json", ".yml", ".yaml", ".tf", ".bicep", ".hcl", ".sh", ".toml", ".jsonl", ".tfvars", ".html"}
TEXT_FILES = [p for p in ROOT.rglob("*") if p.is_file() and not SKIP_PARTS & set(p.parts) and p.suffix in SUFFIXES and ".egg-info" not in str(p)]
# Built-in Azure role definition ids (public, identical in every tenant) used by the Bicep job module.
BUILTIN_ROLE_IDS = {"ba92f5b4-2d11-453d-a403-e96b0029c9fe", "4633458b-17de-408a-b874-0445c86b69e6"}


def folders():
    tracked = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True
    ).stdout.split()
    return sorted({(ROOT / f).parent for f in tracked if not SKIP_PARTS & set(Path(f).parts)})


# .github has no README on purpose: GitHub would show .github/README.md instead of the root README.
@pytest.mark.parametrize("folder", [f for f in folders() if f != ROOT / ".github"], ids=lambda p: str(p.relative_to(ROOT)) or ".")
def test_every_folder_has_a_readme_with_a_file_table(folder):
    readme = folder / "README.md"
    assert readme.exists(), f"{folder} has no README.md"
    if folder != ROOT:
        assert "| File | What it does |" in readme.read_text()


def test_folder_readmes_list_every_child():
    for readme in ROOT.rglob("README.md"):
        if SKIP_PARTS & set(readme.parts) or readme.parent == ROOT:
            continue
        text = readme.read_text()
        for child in readme.parent.iterdir():
            if child.name in {"README.md", "__pycache__", ".terraform", ".terraform.lock.hcl"} or child.name.endswith(".egg-info"):
                continue
            name = child.name + ("/" if child.is_dir() else "")
            assert f"`{name}`" in text, f"{readme.relative_to(ROOT)} does not list {name}"


@pytest.mark.parametrize("doc", MD, ids=lambda p: str(p.relative_to(ROOT)))
def test_no_dates_in_markdown(doc):
    t = re.sub(r"@\d{4}-\d{2}-\d{2}(-preview)?", "", doc.read_text())
    assert not re.search(r"\b\d{4}-\d{2}-\d{2}\b", t), "ISO date"
    assert not re.search(r"(?<![\w$,.])20[1-3]\d(?![\w,.%])", t), "year"
    assert not re.search(MONTHS, t), "month name"
    assert "Date:" not in t


def test_no_todos_or_placeholders():
    for p in MD:
        t = p.read_text()
        for word in ("TODO", "TBD", "FIXME", "lorem ipsum", "coming soon"):
            assert word not in t, f"{word} in {p}"


def test_full_doc_set_exists():
    for d, n in FULL_DIRS.items():
        assert len([p for p in FULL_DOCS if p.parent.name == d]) == n, d
    for top in ("implementation-guide", "interview-guide", "best-practices", "architecture", "deployment", "adopt-this"):
        assert (ROOT / "docs" / f"{top}.md").exists(), top


@pytest.mark.parametrize("doc", FULL_DOCS, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_full_doc_has_all_sections_in_order(doc):
    t = doc.read_text()
    pos = [t.find(f"## {i}. {s}") for i, s in enumerate(SECTIONS, 1)]
    assert all(x >= 0 for x in pos), [s for s, x in zip(SECTIONS, pos, strict=True) if x < 0]
    assert pos == sorted(pos)
    assert "```mermaid" in t and "<!-- output:" in t
    assert "<!-- code:" in t
    for svc in ("Foundry", "Purview", "Azure Policy", "Azure Monitor"):
        assert svc in t, f"{doc.name} does not map to {svc}"
    adopt = t[pos[-1] :].split("\n", 1)[1].strip()
    assert len(adopt) > 80, "Adopt this section is too thin"


DIMENSION_DOCS = sorted(p for p in (ROOT / "docs/dimensions").glob("*.md") if p.name != "README.md")


def test_one_dimension_doc_per_dimension():
    from aimaturity.framework import dimensions

    assert sorted(p.stem.split("-")[0].upper() for p in DIMENSION_DOCS) == sorted(d["id"] for d in dimensions())


@pytest.mark.parametrize("dimension", DIMENSION_DOCS, ids=lambda p: p.stem)
def test_dimension_docs_cover_their_rubric(dimension):
    from aimaturity.framework import capabilities, capability_signals, dimension_weights

    t = dimension.read_text()
    did = dimension.stem.split("-")[0].upper()
    assert f"weight {dimension_weights()[did]:.2f}" in t
    for cid, c in capabilities().items():
        if c["dimension"] == did:
            assert f"**{cid} " in t
            for s in capability_signals(cid):
                assert f"`{s}`" in t, f"{cid} {s}"


def test_doc_outputs_and_excerpts_are_current():
    r = subprocess.run([sys.executable, "scripts/render_docs.py", "--check"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_no_secrets_or_real_identifiers():
    guid = re.compile(r"\b(?!00000000-)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
    bad = [re.compile(p, re.I) for p in (r"AccountKey=", r"-----BEGIN", r"client_secret\s*=", r"@gmail\.com", r"meijer", r"datasparx")]
    for p in TEXT_FILES:
        if p.name == "test_repo_hygiene.py":
            continue
        t = p.read_text(errors="ignore")
        found = {m.group(0).lower() for m in guid.finditer(t)} - BUILTIN_ROLE_IDS
        assert not found, f"GUID-like identifier in {p}: {found}"
        for b in bad:
            assert not b.search(t), f"{b.pattern} in {p}"


def test_no_pdf_is_committed():
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    assert not [f for f in tracked if f.lower().endswith(".pdf")]
    assert "*.pdf" in (ROOT / ".gitignore").read_text().splitlines()
    assert "*.pdf" in (ROOT / ".dockerignore").read_text()


def test_whole_repository_is_mit_licensed():
    assert (ROOT / "LICENSE").read_text().startswith("MIT License")
    assert not (ROOT / "framework/LICENSE.md").exists()
    assert "MIT" in (ROOT / "README.md").read_text()
    assert "MIT" in (ROOT / "framework/framework.yaml").read_text().split("model:")[0]


def test_framework_design_is_documented_in_an_adr():
    t = (ROOT / "docs/adr/0007-original-agentic-maturity-model.md").read_text()
    for s in ("Explore", "Prove", "Operate", "Scale", "Optimise", "must", "support", "anchor", "Readiness Index"):
        assert s in t, s


def test_companies_are_fictional():
    t = (ROOT / "README.md").read_text()
    assert "fictional" in t and "Kestrel Bay Bank" in t and "Valemont Revenue Agency" in t


def test_changelog_has_only_unreleased():
    assert re.findall(r"^## (.+)$", (ROOT / "CHANGELOG.md").read_text(), re.M) == ["Unreleased"]


def test_seven_adrs_without_date_lines():
    adrs = sorted((ROOT / "docs/adr").glob("0*.md"))
    assert len(adrs) == 7
    for a in adrs:
        t = a.read_text()
        assert "**Status:**" in t and "Date" not in t


def test_root_files_exist():
    for f in ("README.md", "SECURITY.md", "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE", "Dockerfile", ".checkov.yaml"):
        assert (ROOT / f).exists(), f


def test_readme_has_recruiter_section_and_honest_test_count():
    t = (ROOT / "README.md").read_text()
    assert "## At a glance (for recruiters)" in t
    m = re.search(r"\*\*(\d+) automated tests\*\*", t)
    assert m and int(m.group(1)) >= 200


def test_readme_says_sample_answers_and_nothing_deployed():
    t = (ROOT / "README.md").read_text()
    assert "sample answers" in t.lower() and "DEPLOY_ENABLED" in t
