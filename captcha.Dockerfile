FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv    \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --only-group backend  --only-group math --compile-bytecode --no-install-project

ADD pyproject.toml /app
ADD uv.lock /app
ADD server/captcha /app/server/captcha
ADD frontend/captcha /app/frontend/captcha
ADD crypto /app/crypto

RUN --mount=type=cache,target=/root/.cache/uv    \
    uv sync --locked --only-group backend --only-group math --compile-bytecode

ADD build.py /app
ARG CODECAPTCHA_DOMAIN
ENV CODECAPTCHA_DOMAIN=$CODECAPTCHA_DOMAIN
RUN ["uv", "run", "--no-sync", "python3", "build.py"]

VOLUME ["/app/captcha_data"]

CMD ["uv", "run", "--no-sync", "litestar", "--app", "server.captcha.main:app", "run", "--port", "8001", "--host", "0.0.0.0"]
