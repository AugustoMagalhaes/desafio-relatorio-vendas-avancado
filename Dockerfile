FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app


FROM base AS test

COPY pyproject.toml pytest.ini README.md ./
COPY src ./src
COPY tests ./tests

RUN pip install ".[dev]"

CMD ["pytest", "--cov", "--cov-report=term-missing"]


FROM base AS runtime

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install . \
    && useradd --create-home --uid 1000 app \
    && mkdir /data \
    && chown app:app /data

USER app
WORKDIR /data

ENTRYPOINT ["vendas-cli"]
CMD ["--help"]