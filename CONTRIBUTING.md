# Contributing

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
```

## Before you open a pull request

```bash
ruff check . && ruff format --check .
pytest -q
aimaturity validate
aimaturity evals
aimaturity report --all --check
python scripts/render_docs.py --check
```

CI runs the same steps, plus Terraform, Bicep and Docker checks.

## Rules of the road

- **Changing a score is a rubric change.** Edit `rubric/signals.yaml` or `rubric/categories.yaml`,
  then re-render reports and docs (`aimaturity report --all`, `python scripts/render_docs.py`) and
  commit the outputs together. The calibration gate must still pass.
- **Wording in `framework/` stays original.** It is adapted under CC BY-SA 3.0 IGO; do not paste
  text from the source document. Run `python scripts/overlap_check.py <source-text>` locally; it must
  report zero shared 8-word sequences.
- **Never commit the source PDF.** `*.pdf` is ignored and a test enforces it.
- **Fictional organisations only** in samples, with no real people, emails or identifiers.
- **No dates in docs.** Plans use Month 1 to Month 12.
- **Every folder has a README** listing its files, and component docs keep all 17 sections.
- Keep commits small and focused, and add an entry under `## Unreleased` in `CHANGELOG.md`.
