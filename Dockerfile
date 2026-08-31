FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p /models && chown app:app /models

COPY pyproject.toml ./
RUN pip install --index-url https://download.pytorch.org/whl/cpu "torch==2.13.0+cpu" \
    && python -c "import subprocess,sys,tomllib; p=tomllib.load(open('pyproject.toml','rb')); subprocess.check_call([sys.executable,'-m','pip','install',*p['project']['dependencies']])"

COPY README.md ./
COPY src ./src
RUN pip install --no-deps .

COPY migrations ./migrations

FROM base AS test

RUN python -c "import subprocess,sys,tomllib; p=tomllib.load(open('pyproject.toml','rb')); subprocess.check_call([sys.executable,'-m','pip','install',*p['project']['optional-dependencies']['dev']])"
COPY tests ./tests

USER app
ENTRYPOINT ["pytest"]
CMD ["-q", "-p", "no:cacheprovider"]

FROM base AS runtime

USER app
ENTRYPOINT ["knowledge-poc"]
CMD ["--help"]
