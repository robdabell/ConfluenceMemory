FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p /models && chown app:app /models

COPY pyproject.toml README.md ./
COPY src ./src
COPY migrations ./migrations
RUN pip install .

USER app
ENTRYPOINT ["knowledge-poc"]
CMD ["--help"]
