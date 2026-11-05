# Image for the scheduled assessment job (Container Apps job). Offline by default; uploads reports
# to the evidence store only when EVIDENCE_STORAGE_ACCOUNT is set (managed identity, no keys).
# Base image pinned by digest (tag kept for readability); Dependabot's docker ecosystem bumps both.
FROM python:3.15-slim@sha256:8c13a3f37a6a5b71498228e902c4b9f51c1f7900d49fabf71f9a650c6120e0d0
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
