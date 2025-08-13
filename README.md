# Setup environment

> Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already.
```bash
uv sync

# windows
.venv\Scripts\activate
# linux / mac
. .venv/bin/activate || source .venv/bin/activate
```


# Create public and private keys

```bash
python .\crypto\_test.py
```

# Run captcha server & frontend

```bash
# litestar
litestar --app server.captcha.main:app run --port 8001 --reload
# uvicorn
uvicorn server.captcha.main:app --reload --port 5500
```

# Run backend server

```bash
litestar --app server.backend.main:app run --port 8000 --reload
```
