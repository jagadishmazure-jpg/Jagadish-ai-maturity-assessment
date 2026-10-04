import os
import subprocess

import pytest

from aimaturity.collectors import collect, collect_source, number
from aimaturity.orgs import gather, list_orgs, load_org, manifest_sources, read_snapshot, scan
from aimaturity.sources import MAX_BYTES, ManifestSource, RepoSource


def test_three_sample_orgs():
    assert list_orgs() == ["kestrel-bay-bank", "portfolio", "valemont-revenue-agency"]


def test_unknown_org():
    with pytest.raises(KeyError):
        load_org("nope")


@pytest.fixture
def git_repo(tmp_path):
    r = tmp_path / "demo"
    (r / ".github" / "workflows").mkdir(parents=True)
    (r / "infra").mkdir()
    (r / "infra" / "main.tf").write_text('resource "azurerm_resource_group" "x" {}\n')
    (r / ".github" / "workflows" / "ci.yml").write_text("jobs:\n  t:\n    steps:\n      - run: pytest -q\n")
    (r / "SECURITY.md").write_text("# Security\n\nReport a vulnerability privately.\n")
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    subprocess.run(["git", "-C", str(r), "add", "-A"], check=True)
    (r / "untracked.tf").write_text('resource "x" "y" {}\n')
    return r


def test_repo_source_reads_only_tracked_files(git_repo):
    files = RepoSource("demo", git_repo).files()
    assert "infra/main.tf" in files and "untracked.tf" not in files


def test_repo_source_is_read_only(git_repo):
    before = {p: os.stat(p).st_mtime_ns for p in git_repo.rglob("*") if p.is_file() and ".git" not in p.parts}
    collect_source(RepoSource("demo", git_repo))
    after = {p: os.stat(p).st_mtime_ns for p in git_repo.rglob("*") if p.is_file() and ".git" not in p.parts}
    assert before == after


def test_repo_scan_finds_signals(git_repo):
    sigs = {e.signal for e in collect_source(RepoSource("demo", git_repo))}
    assert {"iac_any", "ci_tests"} <= sigs


def test_non_git_folder_falls_back_to_walk(tmp_path):
    (tmp_path / "a.tf").write_text("x")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "b.tf").write_text("x")
    assert RepoSource("plain", tmp_path).files() == ["a.tf"]


def test_large_files_are_skipped(tmp_path):
    (tmp_path / "big.md").write_text("x" * (MAX_BYTES + 1))
    assert RepoSource("plain", tmp_path).read("big.md") == ""


def test_citations_capped_per_signal():
    src = ManifestSource("m", {f"infra/m{i}.tf": "x" for i in range(10)})
    assert sum(e.signal == "iac_any" for e in collect_source(src)) == 3


def test_numbering_is_stable_and_sorted():
    src = ManifestSource("m", {"infra/a.tf": "x", "SECURITY.md": "# Security\nreport a vulnerability"})
    a = collect([src], None)
    b = number(list(reversed(a)))
    assert [e.id for e in a] == [f"E{i:03d}" for i in range(1, len(a) + 1)]
    assert [(e.id, e.signal) for e in a] == [(e.id, e.signal) for e in b]


def test_manifest_builds_files_from_signal_examples():
    srcs = manifest_sources({"repos": [{"name": "r", "signals": ["iac_any", "adr"], "files": {"extra.md": "hi"}}]})
    assert "extra.md" in srcs[0].files() and len(srcs[0].files()) == 3


def test_manifest_orgs_find_their_signals(bank):
    m = bank["org"].manifest()
    declared = {s for r in m["repos"] for s in r["signals"]}
    found = {e.signal for e in bank["evidence"]}
    assert declared <= found


def test_snapshot_round_trip():
    org = load_org("portfolio")
    snap = read_snapshot(org)
    assert snap and {e.source for e in snap} == set(org.repo_names())


def test_gather_adds_questionnaire():
    ev = gather(load_org("portfolio"))
    assert any(e.collector == "questionnaire" for e in ev)
    assert len({e.id for e in ev}) == len(ev)


def test_live_scan_matches_snapshot_when_checkouts_present():
    org = load_org("portfolio")
    from aimaturity import ROOT

    if os.environ.get("AIMATURITY_LIVE") != "1" or not all((ROOT.parent / n).is_dir() for n in org.repo_names()):
        pytest.skip("set AIMATURITY_LIVE=1 with the eight sibling checkouts present to compare the live scan")
    from aimaturity.orgs import live_sources

    live = {(e.signal, e.source, e.path) for e in scan(live_sources(org))}
    assert live == {(e.signal, e.source, e.path) for e in read_snapshot(org)}


def test_missing_checkout_is_reported(tmp_path):
    from aimaturity.orgs import live_sources

    with pytest.raises(FileNotFoundError):
        live_sources(load_org("portfolio"), root=tmp_path)
