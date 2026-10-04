# Image for the scheduled assessment job (Container Apps job). Offline by default; uploads reports
# to the evidence store only when EVIDENCE_STORAGE_ACCOUNT is set (managed identity, no keys).
FROM python:3.13-slim
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
RUN pip install --no-cache-dir ".[azure]" && chown -R assessor /app
USER assessor
ENTRYPOINT ["aimaturity-scheduled"]
CMD ["--out", "/tmp/out"]
