# CodeCaptcha
A CAPTCHA system where the user writes python code to solve a given question.

An normal example:

![Example question](docs-assets/16768e08d0bf01f942995f0077ef5e6718aba3298c7b609dd98cf3825fa0db0a.png)

<details>
<summary>Chaotic example (Note that it is very long):</summary>

This question has 100 steps and AI has failed to solve this :)

![Example question](docs-assets/de19ebabd51028f36f7ee03dbe4365b54726181300998b3bf1fd3954a17966e1.png)

</details>

## How to Run the project with the demo
<details>
<summary>Run with docker (recommended)</summary>

Prerequisite: Have [docker](https://docs.docker.com/engine/install/) installed with `docker compose`
    
### Step 1: Setup `.env`

In contrast to running without docker, `.env` setup is necessary for running in docker, It would fail if the following environment isn't set.

- `CODECAPTCHA_DOMAIN` to `http://127.0.0.1:9201` 
    - It can be changed depending on the configuration in `docker-compose.yml`. This environment variable is the domain in which the **client** accesses the CAPTCHA server
- `CODECAPTCHA_DOMAIN_INTERNAL` to `http://captcha:8001`
    - If the CAPTCHA endpoint is from `CODECAPTCHA_DOMAIN` it can be accessible inside the docker container (such as a publicly accessible domain), then this environment variable is not needed

Other configuration can be changed, according to the documentation in `.env.example`. The default value should work for them

### Step 2: Run the project
```bash
docker compose up -d --build
```
The [demo site](http://127.0.0.1:9200) and the [captcha site](http://127.0.0.1:9201) can be accessed from http://127.0.0.1:9200 and http://127.0.0.1:9201 respectively
</details>
<details>
<summary>Run without docker</summary>

Prerequisites: Have [uv](https://docs.astral.sh/uv/getting-started/installation/) and `python3.12` installed
    
### Step 1: Setup `.venv`
```bash
uv sync
```
    
### Step 2: Setup `.env`
By default, the project can be ran without creating or setting up `.env`, however, you might want to change some configurations. Check `.env.example` for information to configurate `.env`.

Note: If you changed the `.env` file, or any other files in `frontend/`, you must setup the project up from the next step again.

### Step 3: Run the build script
```bash
uv run build.py
```
This configures the frontend code to create a set of files in `dist/` which link the demo assets to the CAPTCHA server endpoint defined in `CODECAPTCHA_DOMAIN`

### Step 4: Run the project
Run in 2 seperate terminals
```bash
# This must be ran first
uv run litestar --app server.captcha.main:app run --port 8001 --reload
# Run the following about 5 to 10 seconds later in the other terminal
uv run litestar --app server.backend.main:app run --port 8000 --reload
```
`--host 0.0.0.0` can be added on either command if it need to be accessible from other IP

The [demo site](http://127.0.0.1:8000) and the [captcha site](http://127.0.0.1:8001) can be accessed from http://127.0.0.1:8000 and http://127.0.0.1:8001 respectively
</details>

## Project structure

- `server/captcha` - The CAPTCHA server, written with Litestar that responsible to generate questions and creating image
- `server/backend` - A basic demo server written with Litestar that handle a theoretical login system that is gated with CAPTCHA
- `frontend/captcha` - Contain the static assets for the CAPTCHA server
  <details>
    <summary>Disclosure</summary>
    
    `frontend/captcha/parse.py` is a patch for micropython as it didn't bundle the `urllib.parse` stdlib. The file contains `urllib.parse` and `ipaddress` standard library from [cpython](https://github.com/python/cpython) and patch for some other feature isn't available in micropython such as `str.isascii` and "too complex" regex which is used by the original code from the standard library, which replacement with equivialent behaviour.

  </details>
- `frontend/demo` - A demo login page for testing
- `crypto` - A module that both CAPTCHA server and demo server used to generate/handle public private key pair, and to generate and validate the JWT(JSON Web Token) using the Ed25519 key.
- `captcha_data` - Contain a font file and the a question set
  <details>
    <summary>Disclosure</summary>
    
    - `captcha_data/JetBrainsMono-Regular.ttf` is a font created by JetBrains, and licensed under SIL Open Font License, Version 1.1 (OFL). The license text is inclued in `captcha_data/OFL.txt` as required by the license. The font is included for the purpose to run the project with minimal setup, and other font can be used. The OFL license is compatible with MIT license according to [FOSSA](https://fossa.com/blog/open-source-licenses-101-sil-open-font-license-ofl/)
    - `captcha_data/question_set.json` is created with a combination of manual effort and AI generation. Approximately 2 million
questions is generated during testing, with only 1 exceed the execution timeout of 0.5s during testing when calculating a prime number, which likely originate from saturated resource usage from other task running on the test device. However some question description might not match the checking criteria(with 1 known case found after the deadline)

  </details>
- `build.py` A build script which put all the file from `frontend/` to `dist/` and replace `[domain]` in specific file to domain defined by environment variable `CODECAPTCHA_DOMAIN` so the client can connect to the correct CAPTCHA serveras given from the static file. This is only needed for the demo server, but for consistency, the CAPTCHA server will also use it.

## Contribution list
<details>
    <summary>harshal6927 (@Harshal6927)</summary>

- Demo server
- CAPTCHA server
- Demo page UI
- Demo login system on the backend
- Setup SQLite database for the servers
</details>
<details>
    <summary>deleted.user0 (@i-am-unknown-81514525)</summary>

- CAPTCHA UI
- CAPTCHA frontend
- Adding login system on the demo frontend
- JWT generation and validation, Ed25519 key generation and handling
- Question generator parser
- Writing question set
- Update image generation
</details>
<details>
    <summary>ununenium817 (@Ununenium817)</summary>
    
- Help writing the CAPTCHA server that was replaced
- Writing question set
- Construct system prompt and code to generate part of question set
</details>
<details>
    <summary>wrybyte (@tayvona)</summary>
    
- Minor UI improvement on demo page
</details>
<details>
    <summary>fiwam (@fiwam)</summary>
    
- Update CAPTCHA frontend to handle image
- Convert the question generated to send image instead of text to client
</details>
<details>
    <summary>dragonsenseiguy (@DragonSenseiGuy)</summary>
    
- Attempt to write the CAPTCHA server that was replaced
- Minor UI improvement for the CAPTCHA frame for usability
- Wrote JWT Validator but was scrapped(due to issues).
- Attempt to write the login systm for demo server that didn't get merged.
</details>

## Framework choice

The project used a combination of Pyscript, Pyodide for the approved framework, with some HTML/js/css when necessary in the CAPTCHA files.
- Pyscript is used in `frontend/captcha/captcha.py` and `frontend/captcha/captcha_handler.py` to handle the communication between 2 site to exchange the JWT token.
- Pyodide is used to run user code in isolation in `frontend/captcha/runner.js`
  Other framework:
- [Panel](https://panel.holoviz.org/) is used as a frontend framework with pyscript as a CAPTCHA UI, defined in `frontend/captcha/captcha.py`
- [Litestar](https://litestar.dev/) is used as backend framework for both the CAPTCHA server and DEMO server in `server/`
- [pyjwt](https://pyjwt.readthedocs.io/) and [cryptography](https://cryptography.io/) is used for Ed25519 key handling, JWT creation and validation in `crypto/`
- [Pillow](https://pillow.readthedocs.io/en/stable/) is used to generate image of question that is sent to the client
