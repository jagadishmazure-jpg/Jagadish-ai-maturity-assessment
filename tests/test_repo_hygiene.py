"""Repository hygiene: complete docs, current outputs, no dates, attribution, no PDF, own wording."""

import os
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
FULL_DIRS = {"pillars": 6, "components": 13, "samples": 3, "infra": 4}
FULL_DOCS = sorted(p for d in FULL_DIRS for p in (ROOT / "docs" / d).glob("*.md") if p.name != "README.md")
MONTHS = r"\b(January|February|March|April|June|July|August|September|October|November|December)\b"
SUFFIXES = {".md", ".py", ".json", ".yml", ".yaml", ".tf", ".bicep", ".hcl", ".sh", ".toml", ".jsonl", ".tfvars", ".html"}
TEXT_FILES = [p for p in ROOT.rglob("*") if p.is_file() and not SKIP_PARTS & set(p.parts) and p.suffix in SUFFIXES and ".egg-info" not in str(p)]
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/3.0/igo/"
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


@pytest.mark.parametrize("pillar", sorted((ROOT / "docs/pillars").glob("p*.md")), ids=lambda p: p.stem)
def test_pillar_docs_cover_their_rubric_and_attribution(pillar):
    from aimaturity.framework import categories, category_signals

    t = pillar.read_text()
    pid = "P" + pillar.stem[1]
    assert LICENSE_URL in t and "UNESCO" in t
    for cid, c in categories().items():
        if c["pillar"] == pid:
            assert f"**{cid} " in t
            for s in category_signals(cid):
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


def test_source_pdf_is_never_committed():
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    assert not [f for f in tracked if f.lower().endswith(".pdf")]
    assert "*.pdf" in (ROOT / ".gitignore").read_text().splitlines()
    ignored = subprocess.run(["git", "check-ignore", "-q", "framework/source.pdf"], cwd=ROOT)
    assert ignored.returncode == 0, "a PDF under framework/ would not be ignored"
    assert "*.pdf" in (ROOT / ".dockerignore").read_text()


def test_readme_attribution_and_license_split():
    t = (ROOT / "README.md").read_text()
    for s in ("UNESCO", "Stratejai", "CC BY-SA 3.0 IGO", LICENSE_URL, "`framework/`", "MIT"):
        assert s in t, s
    assert "adapted under CC BY-SA 3.0 IGO" in t
    assert "same license" in t


def test_framework_folder_carries_its_license():
    assert LICENSE_URL in (ROOT / "framework/LICENSE.md").read_text()
    assert "CC BY-SA 3.0 IGO" in (ROOT / "framework/framework.yaml").read_text().split("pillars:")[0]
    assert "CC BY-SA 3.0 IGO" in (ROOT / "framework/README.md").read_text()


def test_overlap_script_detects_copies(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    from overlap_check import shingles, words

    a = shingles(words("one two three four five six seven eight nine https://example.org/x"), 8)
    assert ("one", "two", "three", "four", "five", "six", "seven", "eight") in a
    assert not any("example" in w for sh in a for w in sh)


def test_no_eight_word_overlap_with_source_text():
    src = Path(os.environ.get("AIMATURITY_SOURCE_TEXT", "/tmp/unesco-aimf.txt"))
    if not src.is_file():
        pytest.skip("source text not present (the PDF is never committed); run scripts/overlap_check.py locally")
    r = subprocess.run([sys.executable, "scripts/overlap_check.py", str(src)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:]


def test_companies_are_fictional():
    t = (ROOT / "README.md").read_text()
    assert "fictional" in t and "Kestrel Bay Bank" in t and "Valemont Revenue Agency" in t


def test_changelog_has_only_unreleased():
    assert re.findall(r"^## (.+)$", (ROOT / "CHANGELOG.md").read_text(), re.M) == ["Unreleased"]


def test_six_adrs_without_date_lines():
    adrs = sorted((ROOT / "docs/adr").glob("0*.md"))
    assert len(adrs) == 6
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
