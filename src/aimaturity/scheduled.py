"""Entry point of the scheduled Container Apps job (``aimaturity-scheduled``).

Runs every sample assessment offline, writes reports and a JSON summary per organisation into
``--out`` (default ``out/``), and, when ``EVIDENCE_STORAGE_ACCOUNT`` is set and the optional
``azure`` extra is installed, uploads them to the evidence store with the job's managed identity
(``DefaultAzureCredential``; no keys). Without the variable it is a pure local run.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from aimaturity.agents.assessor import assess, summary
from aimaturity.orgs import list_orgs
from aimaturity.report import write


def run(out: Path, orgs: list[str] | None = None) -> list[Path]:
    files: list[Path] = []
    for org_id in orgs or list_orgs():
        state = assess(org_id)
        d = out / org_id
        write(state, out_dir=d)
        (d / "summary.json").write_text(json.dumps(summary(state), indent=1) + "\n")
        files += sorted(d.iterdir())
    return files


def upload(files: list[Path], out: Path, account: str, prefix: str) -> int:  # pragma: no cover - needs Azure
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient

    svc = BlobServiceClient(f"https://{account}.blob.core.windows.net", credential=DefaultAzureCredential())
    container = svc.get_container_client("reports")
    for f in files:
        with f.open("rb") as fh:
            container.upload_blob(f"{prefix}/{f.relative_to(out).as_posix()}", fh, overwrite=True)
    return len(files)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="aimaturity-scheduled")
    ap.add_argument("--out", default="out")
    ap.add_argument("--org", action="append")
    a = ap.parse_args(argv)
    out = Path(a.out)
    files = run(out, a.org)
    print(f"wrote {len(files)} files under {out}")
    account = os.environ.get("EVIDENCE_STORAGE_ACCOUNT")
    if account:
        prefix = os.environ.get("RUN_ID") or os.environ.get("CONTAINER_APP_JOB_EXECUTION_NAME") or "latest"
        print(f"uploaded {upload(files, out, account, prefix)} files to {account}/reports/{prefix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
