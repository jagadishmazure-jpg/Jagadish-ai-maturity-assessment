# Implementation guide

From a clean clone to a full assessment, then to your own organisation, then (optionally) to Azure.

## 1. Run it locally (five minutes)

```bash
git clone https://github.com/jagadishmazure-jpg/Jagadish-ai-maturity-assessment
cd Jagadish-ai-maturity-assessment
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
aimaturity validate
aimaturity orgs
aimaturity assess --org portfolio
pytest -q && aimaturity evals
```

<!-- output: orgs -->
```text
org                      name                       evidence        repos  questionnaire
-----------------------  -------------------------  --------------  -----  --------------
kestrel-bay-bank         Kestrel Bay Bank           manifest        4      self-reported
portfolio                Jagadish Meduri portfolio  repos+snapshot  9      sample-answers
valemont-revenue-agency  Valemont Revenue Agency    manifest        3      self-reported
```
<!-- /output -->

## 2. Read one result end to end

```bash
aimaturity explain --org portfolio --category 5.3   # level, signals, cited files
aimaturity queue --org portfolio                    # what needs a human and why
aimaturity roadmap --org portfolio                  # Month 1-12 plan
open samples/portfolio/report/report.html
```

## 3. Assess your own organisation

1. `mkdir samples/<org>` and write `org.yaml` (see `schemas/org.schema.json`): `name`, `assessor`, either `repos` + `snapshot` or `manifest`, `questionnaire`, `targets`, optional `critical`, `capacity`, `links`.
2. Put your repositories next to this one (or set `path:` per repo) and run `aimaturity collect --org <org> --live --write`.
3. Answer `rubric/questionnaire.yaml` into `samples/<org>/questionnaire.yaml` with `label: self-reported`.
4. `aimaturity validate`, then `aimaturity assess --org <org>`.
5. Review the queue: `aimaturity review --org <org> --category 2.3 --reviewer "<name>" --decision confirm --comment "<evidence seen>"`.
6. `aimaturity report --org <org>` and share `report.html`.

## 4. Tune the rubric

* Move signals between levels or add signals in `rubric/` (every signal needs an example that matches it).
* Change targets and critical categories per organisation in `org.yaml`.
* After every change: `pytest -q && aimaturity evals && aimaturity report --all && python scripts/render_docs.py`.

## 5. Deploy the scheduled job (optional)

Follow [deployment.md](deployment.md): OIDC federated credential, GitHub environments with reviewers,
state storage, then set `DEPLOY_ENABLED=true`. Nothing in this repository is deployed today.

## 6. Checks before a pull request

| Check | Command |
|---|---|
| Lint and format | `ruff check . && ruff format --check .` |
| Tests | `pytest -q` |
| Eval gates | `aimaturity evals` |
| Report drift | `aimaturity report --all --check` |
| Doc drift | `python scripts/render_docs.py --check` |
| Overlap with source texts | `python scripts/overlap_check.py <source.txt>` |
| Terraform | `terraform -chdir=infra/terraform fmt -check && terraform -chdir=infra/terraform test` |
| Bicep | `az bicep build --file infra/bicep/main.bicep` |
