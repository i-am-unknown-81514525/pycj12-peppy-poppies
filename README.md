# Setup environment

> Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already

### 1: Create `.env` with template from `.env.example`

### 2: Install dependencies
```bash
uv sync
```

### 3: Activate virtual environment
```bash
# windows
.venv\Scripts\activate

# linux / mac
. .venv/bin/activate || source .venv/bin/activate
```

# Run project without docker

> Make sure you have activated the virtual environment before running the commands below, and you have installed the dependencies using `uv sync` command.

### 1: Build the project
```bash
uv run python build.py
```

### 2: Start website backend
```bash
# In terminal 1
litestar --app server.backend.main:app run --port 8000 --reload
```

### 3: Open another terminal and start captcha server
```bash
# In terminal 2
litestar --app server.captcha.main:app run --port 8001 --reload
```

# Run project with docker
```bash
# Remember, for docker, the default port is picked to :9201 for captcha server, so you must create the `.env` for it to work
docker compose up -d --build
```

# Test creditials
```bash
username: codejam12
password: py-discord
```

<!--
# Potential dependency when using `math` group (gmpy2)
```bash
sudo apt-get install libgmp-dev libmpfr-dev libmpc-dev # Ubuntu/Debian alike

# macOS
brew install gmp
brew install libmpc
brew install mpfr
```
-->
