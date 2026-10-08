# Image for the scheduled assessment job (Container Apps job). Offline by default; uploads reports
# to the evidence store only when EVIDENCE_STORAGE_ACCOUNT is set (managed identity, no keys).
# Base image pinned by digest (tag kept for readability); Dependabot's docker ecosystem bumps both.
FROM python:3.13-slim@sha256:bf44cdfcb76cd3b41e879bc058fc37ec5872002ccfde7fcb765e218cde0cd79c
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
