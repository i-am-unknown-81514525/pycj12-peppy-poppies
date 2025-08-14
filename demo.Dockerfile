FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv    \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --only-group backend --compile-bytecode --no-install-project

ADD pyproject.toml /app
ADD uv.lock /app
ADD server/backend /app/server/backend
ADD frontend/demo /app/frontend/demo
ADD crypto /app/crypto

RUN --mount=type=cache,target=/root/.cache/uv    \
    uv sync --locked --only-group backend --compile-bytecode

ADD demo_setdomain.py /app

RUN ["uv", "run", "python3", "demo_setdomain.py"]

VOLUME ["/app/demo_data"]

CMD ["uv", "run", "litestar", "--app", "server.backend.main:app", "run", "--port", "8000", "--host", "0.0.0.0"]
