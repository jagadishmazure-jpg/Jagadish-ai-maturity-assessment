# Image for the scheduled assessment job (Container Apps job). Offline by default; uploads reports
# to the evidence store only when EVIDENCE_STORAGE_ACCOUNT is set (managed identity, no keys).
# Base image pinned by digest (tag kept for readability); Dependabot's docker ecosystem bumps both.
FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AIMATURITY_HOME=/app
RUN useradd --create-home --uid 10001 assessor
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY framework ./framework
COPY rubric ./rubric
COPY samples ./samples
COPY schemas ./schemas
COPY evals ./evals
COPY a2a ./a2a
# pip is only needed to install the package; it is not shipped in the runtime image.
RUN pip install --no-cache-dir ".[azure]" && python -m pip uninstall -y pip && chown -R assessor /app
USER assessor
ENTRYPOINT ["aimaturity-scheduled"]
CMD ["--out", "/tmp/out"]
