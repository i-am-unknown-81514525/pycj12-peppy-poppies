### Common command

Create `.venv` with dependency
```sh
uv sync --locked --all-extras
```

Update `uv.lock` with new dependencies
```sh
uv sync
```

Check linting
```sh
ruff check
```

Format code
```sh
ruff format
```

Export current `uv.lock` to `pylock.toml`
```sh
uv export --locked -o pylock.toml
```

### Run services locally

```sh
# Install deps
uv sync || pip install -e .

# Run CAPTCHA service (port 8000)
PYTHONPATH=src python -m captcha_service.main

# In another terminal, run demo website (port 9000)
PYTHONPATH=src python -m website_service.main

# Optional: RS256 key paths for real asymmetric JWT
export CAPTCHA_RSA_PRIVATE_KEY_PATH=./private.pem
export CAPTCHA_RSA_PUBLIC_KEY_PATH=./public.pem
# Or HS256 fallback
export CAPTCHA_HS_SECRET=dev-secret
```
