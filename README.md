# Setup environment

> Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already.
```bash
uv sync

# windows
.venv\Scripts\activate
# linux / mac
source .venv/bin/activate
```


# Create public and private keys

```bash
py .\crypto\_test.py
```

# Run captcha server

```bash
litestar --app server.captcha.main:app run --port 8001 --reload
```

# Run backend server

```bash
litestar --app server.captcha.main:app run --port 8000 --reload
```
