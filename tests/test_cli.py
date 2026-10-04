import json

import pytest

from aimaturity.cli import main, table


@pytest.mark.parametrize(
    "argv",
    [
        ["framework"],
        ["framework", "--pillar", "P5"],
        ["category", "6.2"],
        ["orgs"],
        ["validate"],
        ["collect", "--org", "kestrel-bay-bank"],
        ["collect", "--org", "portfolio"],
        ["assess", "--org", "portfolio"],
        ["explain", "--org", "portfolio", "--category", "5.3"],
        ["gaps", "--org", "valemont-revenue-agency"],
        ["roadmap", "--org", "kestrel-bay-bank"],
        ["links", "--org", "portfolio"],
        ["queue", "--org", "portfolio"],
        ["audit", "--org", "valemont-revenue-agency"],
        ["report", "--all", "--check"],
        ["agent-card"],
        ["mcp-demo"],
    ],
)
def test_command_succeeds(argv, capsys):
    assert main(argv) == 0
    assert capsys.readouterr().out.strip()


def test_assess_json(capsys):
    assert main(["assess", "--org", "kestrel-bay-bank", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["name"] == "Kestrel Bay Bank"


def test_collect_write_requires_live(capsys):
    assert main(["collect", "--org", "portfolio", "--write"]) == 2


def test_report_needs_target(capsys):
    assert main(["report"]) == 2


def test_self_review_rejected_without_writing(capsys, org_copy):
    d = org_copy("portfolio")
    before = (d / "audit-log.jsonl").read_text()
    rc = main(
        [
            "review",
            "--org",
            "portfolio",
            "--category",
            "2.3",
            "--reviewer",
            "aimaturity-agent",
            "--decision",
            "confirm",
            "--comment",
            "fine by me, really",
        ]
    )
    assert rc == 1 and "rejected" in capsys.readouterr().out
    assert (d / "audit-log.jsonl").read_text() == before


def test_review_records(capsys, org_copy):
    d = org_copy("portfolio")
    rc = main(
        [
            "review",
            "--org",
            "portfolio",
            "--category",
            "2.3",
            "--reviewer",
            "Example Reviewer",
            "--decision",
            "confirm",
            "--comment",
            "sponsor confirmed",
        ]
    )
    assert rc == 0 and (d / "audit-log.jsonl").read_text().strip()


def test_links_fail_when_unsatisfied(capsys, org_copy):
    import yaml

    d = org_copy("portfolio")
    cfg = yaml.safe_load((d / "org.yaml").read_text())
    cfg["links"] = {"ai-learning-lab": ["5.4"]}
    (d / "org.yaml").write_text(yaml.safe_dump(cfg))
    assert main(["links", "--org", "portfolio"]) == 1


def test_table_helper():
    out = table([{"a": 1, "b": "xy"}], ["a", "b"])
    assert out.splitlines()[0].split() == ["a", "b"]
