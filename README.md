# Setup environment

> Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already.
```bash
uv sync

# windows
.venv\Scripts\activate
# linux / mac
. .venv/bin/activate || source .venv/bin/activate
```

# Run the whole thing without docker
```bash
 # Make sure you have both activate venv, if you have, skip this
. .venv/bin/activate
 # Make sure you have both frontend and dev group, if you have, skip this
uv sync --locked --group frontend --group dev

# Create .env with template from .env.example

uv run python build.py
```
Now go to 2 different terminal
```sh
litestar --app server.backend.main:app run --port 8000 --reload # In terminal 1
```
```sh
```bash
# litestar
litestar --app server.captcha.main:app run --port 8001 --reload # In terminal 2
```

# Run the whole thing without docker
```sh
# Create .env with template from .env.example
# Remember, for docker, the default port is picked to :9201 for captcha server, so you must create the .env for it to work
docker compose up -d --build
```

# Run captcha server only

```bash
litestar --app server.captcha.main:app run --port 8001 --reload
```

# Run backend server only

```bash
litestar --app server.backend.main:app run --port 8000 --reload
```
