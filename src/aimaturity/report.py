"""Executive report: Markdown and HTML from the same content, plus a matplotlib radar chart (SVG).

Output is deterministic (fixed SVG hash salt, no timestamps), so the reports checked in under
``samples/<org>/report/`` are drift-checked in CI: ``aimaturity report --all --check``.
"""

from __future__ import annotations

import html
import io
import math
from collections import Counter
from pathlib import Path
from typing import Any

from aimaturity.agents.assessor import summary
from aimaturity.crosslinks import check_links
from aimaturity.framework import LEVEL_NAMES
from aimaturity.roadmap import MONTHS, months_view

ATTRIBUTION = (
    "Framework structure (six pillars, 29 categories, four levels) adapted from UNESCO, *AI Maturity Framework* "
    '(subtitle: "A self-positioning guide for public administrations"), developed by Stratejai for UNESCO, '
    "under CC BY-SA 3.0 IGO (https://creativecommons.org/licenses/by-sa/3.0/igo/). Descriptors, rubric, scoring "
    "and wording are this project's own; UNESCO does not endorse this tool or its results."
)


def radar_svg(pillars: list[dict[str, Any]], targets: list[float], title: str) -> str:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    matplotlib.rcParams.update({"svg.hashsalt": "aimaturity", "svg.fonttype": "none", "font.family": "DejaVu Sans", "font.size": 9})
    labels = [f"{p['id']} {p['name']}" for p in pillars]
    n = len(labels)
    angles = [i * 2 * math.pi / n for i in range(n)] + [0.0]
    fig = plt.figure(figsize=(6.4, 5.6))
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    for vals, style, name in [
        ([float(t) for t in targets], dict(color="#9aa5b1", linestyle="--", linewidth=1.2), "Target"),
        ([p["mean"] for p in pillars], dict(color="#1f6feb", linewidth=2), "Category mean"),
        ([float(p["level"]) for p in pillars], dict(color="#d97706", linewidth=1.5, marker="o"), "Pillar level"),
    ]:
        ax.plot(angles, vals + vals[:1], label=name, **style)
    ax.fill(angles, [p["mean"] for p in pillars] + [pillars[0]["mean"]], color="#1f6feb", alpha=0.12)
    ax.set_xticks(angles[:-1], ["\n".join(_wrap(lbl)) for lbl in labels])
    ax.set_ylim(0, 4)
    ax.set_yticks([1, 2, 3, 4], [f"{i} {LEVEL_NAMES[i]}" for i in (1, 2, 3, 4)], fontsize=7)
    ax.set_title(title, pad=24)
    ax.legend(loc="lower right", bbox_to_anchor=(1.32, -0.08), fontsize=8, frameon=False)
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", metadata={"Date": None, "Creator": None})
    plt.close(fig)
    return buf.getvalue()


def _wrap(text: str, width: int = 18) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        if cur and len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return [*lines, cur]


def build_content(state: dict[str, Any]) -> dict[str, Any]:
    """Everything the report shows, as plain data (titles, paragraphs, tables)."""
    s = summary(state)
    org = state["org"]
    sched = state["schedule"]
    pill_targets = []
    for p in s["pillars"]:
        ts = [c["target"] for c in s["categories"] if c["pillar"] == p["id"]]
        pill_targets.append(round(sum(ts) / len(ts), 2))
    sections: list[dict[str, Any]] = []
    label = s["questionnaire_label"]
    notes = []
    if label == "sample-answers":
        notes.append(
            "People, culture and partnership answers are SAMPLE ANSWERS (illustrative inputs, not survey results). Categories that rest on them wait for human review."
        )
    if org.config.get("manifest"):
        notes.append("This organisation is fictional; its repositories are synthetic manifests.")
    pending = s["review_queue"]
    status = "final" if s["final"] else f"provisional: {len(pending)} categories wait for human review"
    best = max(s["pillars"], key=lambda p: (p["mean"], p["id"]))
    worst = min(s["pillars"], key=lambda p: (p["mean"], p["id"]))
    quick = [p for p in sched["plan"] if p["kind"] == "quick-win"]
    top = state["items"][:3]
    sections.append(
        {
            "title": "Executive summary",
            "paras": [
                f"Overall maturity: **Level {s['overall']['level']} ({s['overall']['level_name']})**, category mean {s['overall']['mean']} of 4. Assessment status: {status}.",
                f"Strongest pillar: {best['id']} {best['name']} (mean {best['mean']}). Weakest: {worst['id']} {worst['name']} (mean {worst['mean']}).",
                f"Evidence: {s['evidence_count']} items from {len(s['sources'])} repositories and the questionnaire. Roadmap: {len(state['items'])} steps, "
                f"{len(quick)} quick wins in Months 1-3, {len(sched['backlog'])} beyond Month 12.",
                "Top priorities: " + "; ".join(f"{i['id']} {i['name']} (priority {i['priority']})" for i in top) + "."
                if top
                else "No gaps against target.",
                *notes,
            ],
            "radar": True,
        }
    )
    sections.append(
        {
            "title": "Pillars",
            "table": (
                ["Pillar", "Level", "Category mean", "Target (mean)", "Capped by critical"],
                [
                    [f"{p['id']} {p['name']}", f"{p['level']} {p['level_name']}", p["mean"], t, ", ".join(p["capped_by"]) or "-"]
                    for p, t in zip(s["pillars"], pill_targets, strict=True)
                ],
            ),
        }
    )
    sections.append(
        {
            "title": "Categories",
            "table": (
                ["Category", "Level", "Target", "Confidence", "Status", "Evidence"],
                [
                    [
                        f"{c['id']} {c['name']}" + (" (critical)" if c["critical"] else ""),
                        f"{c['level']}" + (f" (computed {c['computed_level']})" if c["level"] != c["computed_level"] else ""),
                        c["target"],
                        f"{c['confidence']:.2f}",
                        c["status"],
                        len(c["evidence"]),
                    ]
                    for c in s["categories"]
                ],
            ),
        }
    )
    rq = [[cid, state["results"][cid].name, "; ".join(state["results"][cid].review_reasons) or "evidence changed since review"] for cid in pending]
    reviewed = [
        [cid, st["review"]["reviewer"], st["status"], st["review"]["comment"]]
        for cid, st in state["statuses"].items()
        if st["status"] in {"confirmed", "overridden"}
    ]
    sections.append(
        {
            "title": "Human review",
            "paras": [f"{len(pending)} pending, {len(reviewed)} signed off. Audit log chain: {'intact' if not s['audit_problems'] else 'BROKEN'}."],
            "table": (["Category", "Name", "Why it needs a human"], rq) if rq else None,
            "table2": (["Category", "Reviewer", "Outcome", "Comment"], reviewed) if reviewed else None,
        }
    )
    gap_rows = [
        [f"{g['category']} {g['name']}", g["current"], g["target"], g["gap"], g["steps"][0]["action"]]
        for g in sorted(state["gaps"], key=lambda g: (-g["gap"], g["category"]))
        if g["gap"] > 0
    ]
    sections.append(
        {
            "title": "Gap analysis",
            "paras": [f"{len(gap_rows)} of 29 categories are below target."],
            "table": (["Category", "Now", "Target", "Gap", "First action"], gap_rows),
        }
    )
    view = months_view(sched)
    sections.append(
        {
            "title": "Roadmap (Month 1-12)",
            "paras": [
                f"Capacity {sched['capacity']} items in flight. Milestones: "
                + "; ".join(f"Month {m['month']}: {m['what']}" for m in sched["milestones"])
                + "."
            ],
            "table": (
                ["Step", "Kind", "Months", "Effort", "Priority", "Waits on"],
                [
                    [
                        f"{p['id']} {p['name']}",
                        p["kind"],
                        f"{p['start']}-{p['end']}" if p["end"] > p["start"] else str(p["start"]),
                        p["effort"],
                        p["priority"],
                        ", ".join(p["depends_on"]) or "-",
                    ]
                    for p in sched["plan"]
                ],
            ),
            "table2": (["Month", "In flight"], [[m, ", ".join(view[m]) or "-"] for m in range(1, MONTHS + 1)]),
            "after": [f"Backlog beyond Month 12: {', '.join(sched['backlog'])}." if sched["backlog"] else "Everything fits in the twelve months."],
        }
    )
    links = check_links(state)
    if links:
        sections.append(
            {
                "title": "Cross-repository evidence",
                "table": (
                    ["Repository", "Category", "Cited files", "Examples"],
                    [[r["repo"], r["category"], r["cited"], ", ".join(r["examples"])] for r in links],
                ),
            }
        )
    by_col = Counter(e.collector for e in state["evidence"])
    by_src = Counter(e.source for e in state["evidence"])
    sections.append(
        {"title": "Evidence", "table": (["Collector", "Items"], sorted(by_col.items())), "table2": (["Source", "Items"], sorted(by_src.items()))}
    )
    sections.append(
        {
            "title": "Method and attribution",
            "paras": [
                "Levels come from evidence signals per category (rubric/categories.yaml); a level needs two thirds of its signals and the level below. "
                "Confidence blends source trust and decision margin; pillars use the median of categories capped by critical categories.",
                ATTRIBUTION,
            ],
        }
    )
    return {
        "title": f"AI maturity report: {s['name']}",
        "subtitle": s["kind"],
        "sections": sections,
        "pillars": s["pillars"],
        "targets": pill_targets,
    }


def _md_table(t) -> list[str]:
    head, rows = t
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c).replace("|", "/") for c in r) + " |" for r in rows]
    return out


def to_markdown(content: dict[str, Any]) -> str:
    out = [f"# {content['title']}", "", f"_{content['subtitle']}_", ""]
    for sec in content["sections"]:
        out += [f"## {sec['title']}", ""]
        for p in sec.get("paras", []):
            out += [p, ""]
        if sec.get("radar"):
            out += ["![Pillar radar: level, category mean and target](radar.svg)", ""]
        for key in ("table", "table2"):
            if sec.get(key):
                out += [*_md_table(sec[key]), ""]
        for p in sec.get("after", []):
            out += [p, ""]
    return "\n".join(out).rstrip() + "\n"


def _inline(text: str) -> str:
    t = html.escape(text)
    parts = t.split("**")
    t = "".join(f"<strong>{p}</strong>" if i % 2 else p for i, p in enumerate(parts))
    parts = t.split("*")
    return "".join(f"<em>{p}</em>" if i % 2 else p for i, p in enumerate(parts))


def to_html(content: dict[str, Any], svg: str) -> str:
    css = (
        "body{font-family:system-ui,sans-serif;max-width:980px;margin:2rem auto;padding:0 1rem;color:#1f2328}"
        "table{border-collapse:collapse;margin:.5rem 0 1rem}td,th{border:1px solid #d0d7de;padding:4px 8px;font-size:13px;text-align:left}"
        "th{background:#f6f8fa}h2{border-bottom:1px solid #d0d7de;padding-bottom:4px}.radar svg{max-width:640px;height:auto}"
    )
    out = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        f"<title>{html.escape(content['title'])}</title>",
        f"<style>{css}</style></head><body>",
        f"<h1>{html.escape(content['title'])}</h1>",
        f"<p><em>{html.escape(content['subtitle'])}</em></p>",
    ]
    for sec in content["sections"]:
        out.append(f"<h2>{html.escape(sec['title'])}</h2>")
        out += [f"<p>{_inline(p)}</p>" for p in sec.get("paras", [])]
        if sec.get("radar"):
            out.append('<div class="radar">' + svg[svg.index("<svg") :] + "</div>")
        for key in ("table", "table2"):
            if sec.get(key):
                head, rows = sec[key]
                out.append("<table><tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in head) + "</tr>")
                out += ["<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>" for r in rows]
                out.append("</table>")
        out += [f"<p>{_inline(p)}</p>" for p in sec.get("after", [])]
    out.append("</body></html>")
    return "\n".join(out) + "\n"


def render(state: dict[str, Any]) -> dict[str, str]:
    content = build_content(state)
    svg = radar_svg(content["pillars"], content["targets"], state["org"].name)
    return {"report.md": to_markdown(content), "report.html": to_html(content, svg), "radar.svg": svg}


def write(state: dict[str, Any], out_dir: Path | None = None, check: bool = False) -> list[str]:
    """Write (or with ``check`` compare) the three report files; returns the files that differ."""
    out_dir = out_dir or state["org"].dir / "report"
    files = render(state)
    drift = [name for name, text in files.items() if not (out_dir / name).is_file() or (out_dir / name).read_text() != text]
    if not check:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            (out_dir / name).write_text(text)
    return drift
