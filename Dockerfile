FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p /models && chown app:app /models

COPY pyproject.toml README.md ./
COPY src ./src
COPY migrations ./migrations
RUN pip install --index-url https://download.pytorch.org/whl/cpu "torch==2.13.0+cpu" \
    && pip install .

FROM base AS test

COPY tests ./tests
RUN pip install '.[dev]'

USER app
ENTRYPOINT ["pytest"]
CMD ["-q", "-p", "no:cacheprovider"]

FROM base AS runtime

USER app
ENTRYPOINT ["knowledge-poc"]
CMD ["--help"]
