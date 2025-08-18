# CodeCaptcha
A CAPTCHA system where the user write a python code to solve a given question.

A normal example:

![Example question](docs-assets/16768e08d0bf01f942995f0077ef5e6718aba3298c7b609dd98cf3825fa0db0a.png)

<details>
<summary>Chaotic example (Note that it is very long):</summary>

This question have 100 steps and AI have failed to solve this :)

![Example question](docs-assets/de19ebabd51028f36f7ee03dbe4365b54726181300998b3bf1fd3954a17966e1.png)

</details>

## How to Run the project with the demo
<details>
<summary>Run with docker (recommended)</summary>

Prerequisite: Have [docker](https://docs.docker.com/engine/install/) installed with `docker compose`
    
### Step 1: Setup `.env`

- `CODECAPTCHA_DOMAIN` to `http://127.0.0.1:9201` 
    - It can be changed depend on the configuration in `docker-compose.yml`. This environment variable is the domain which the **client** access the CAPTCHA server
- `CODECAPTCHA_DOMAIN_INTERNAL` to `http://captcha:8001`
    - If the CAPTCHA endpoint is from `CODECAPTCHA_DOMAIN` can be accessible inside the docker container (such as a publicly accessible domain), this environment variable is not needed

Other configuration can be changed, according to the documentation in `.env.example`. The default value should work for them

### Step 2: Run the project
```bash
docker compose up -d --build
```
The [demo site](http://127.0.0.1:9200) and the [captcha site](http://127.0.0.1:9201) can be access from http://127.0.0.1:9200 and http://127.0.0.1:9201 respectively
</details>
<details>
<summary>Run without docker</summary>

Prerequisite: Have [uv](https://docs.astral.sh/uv/getting-started/installation/) and `python3.12` installed
    
### Step 1: Setup `.venv`
```bash
uv sync
```
    
### Step 2: Setup `.env`
By default, the project can be ran without creating or setting up `.env`, however, you might want to change some configuration. Check for `.env.example` for information to config `.env`.
If you changed `.env` file, or any files in `frontend/`, you must re-setup the project from the next step.
### Step 3: Run the build script
```bash
uv run build.py
```
This configure the frontend code to create a replicate set of file in `dist/` which link the demo assets to the CAPTCHA server endpoint defined in `CODECAPTCHA_DOMAIN`

### Step 4: Run the project
Run in 2 seperate terminal
```bash
# This must be ran first
uv run litestar --app server.captcha.main:app run --port 8001 --reload
# Run the following about 5 to 10 seconds later in the other terminal
uv run litestar --app server.backend.main:app run --port 8000 --reload
```
`--host 0.0.0.0` can be added on either command if it need to be accessible from other IP

The [demo site](http://127.0.0.1:8000) and the [captcha site](http://127.0.0.1:8001) can be access from http://127.0.0.1:8000 and http://127.0.0.1:8001 respectively
</details>
