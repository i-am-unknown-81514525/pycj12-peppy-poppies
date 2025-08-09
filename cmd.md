### Common command

Create `.venv` with dependency
```sh
uv sync --locked --all-extras
```

Run the captcha API (dev)
```sh
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
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
