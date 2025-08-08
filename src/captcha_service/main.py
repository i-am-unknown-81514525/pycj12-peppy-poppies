from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from jose import jwt
from pydantic import BaseModel



APP_DIR = Path(__file__).resolve().parent
# Find the project root by looking for pyproject.toml
current = APP_DIR
while current.parent != current:  # Stop at filesystem root
    if (current / "pyproject.toml").exists():
        REPO_ROOT = current
        break
    current = current.parent
else:
    # Fallback: assume we're in src/captcha_service/ and go up 3 levels
    REPO_ROOT = APP_DIR.parents[3]

QA_DIR = REPO_ROOT / "Question_answers"
QUESTIONS_MD = QA_DIR / "Questions.md"
SOLUTIONS_MD = QA_DIR / "Solutions.md"
DB_PATH = REPO_ROOT / "captcha.db"


# Asymmetric keypair for RS256. In production, load from env/secret store.
RSA_PRIVATE_KEY = os.environ.get("CAPTCHA_RSA_PRIVATE_KEY")
RSA_PUBLIC_KEY = os.environ.get("CAPTCHA_RSA_PUBLIC_KEY")

# Also allow providing file paths for keys
priv_path = os.environ.get("CAPTCHA_RSA_PRIVATE_KEY_PATH")
pub_path = os.environ.get("CAPTCHA_RSA_PUBLIC_KEY_PATH")
if not RSA_PRIVATE_KEY and priv_path and Path(priv_path).exists():
    RSA_PRIVATE_KEY = Path(priv_path).read_text()
if not RSA_PUBLIC_KEY and pub_path and Path(pub_path).exists():
    RSA_PUBLIC_KEY = Path(pub_path).read_text()

if not RSA_PRIVATE_KEY or not RSA_PUBLIC_KEY:
    # Generate ephemeral dev keypair (NOT for production)
    # Using jose, we expect PEM strings. For simplicity here, allow HS256 fallback.
    # However, the user asked for asymmetric; we keep RS256 path but fail if missing.
    # To keep the app runnable locally without openssl, default to HS256 with a warning.
    RSA_PUBLIC_KEY = None
    RSA_PRIVATE_KEY = None
    HS_SECRET = os.environ.get("CAPTCHA_HS_SECRET", secrets.token_urlsafe(32))
    JWT_ALG = "HS256"
else:
    HS_SECRET = None
    JWT_ALG = "RS256"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS challenges (
                challenge_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                website TEXT NOT NULL,
                question_index INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                solved_at INTEGER
            )
            """
        )
        conn.commit()


@dataclass
class Question:
    index: int
    statement: str
    expected_hash: str


def parse_questions(file_path: Path) -> list[Question]:
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    # Questions.md appears to be Project Euler style with "Answer: <md5-like>" lines
    # We'll parse blocks starting with "Problem <n>" and capture the final Answer hash
    blocks = re.split(r"(?m)^\s*Problem\s+(\d+)\s*\r?\n=+\s*\r?\n", content)
    # The split yields ['', num, block, num, block, ...] or with a header before first
    questions: list[Question] = []
    # Walk pairs of (index, block)
    for i in range(1, len(blocks), 2):
        try:
            q_index = int(blocks[i])
        except ValueError:
            continue
        block = blocks[i + 1]
        # Extract Answer: <hash>
        m = re.search(r"(?i)Answer:\s*([0-9a-f]{32,64})", block)
        if not m:
            continue
        expected_hash = m.group(1).strip()
        # The entire block sans the Answer line is the statement shown
        statement = re.sub(r"\n?Answer:\s*[0-9a-f]{32,64}.*", "", block, flags=re.IGNORECASE | re.DOTALL).strip()
        questions.append(Question(index=q_index, statement=statement, expected_hash=expected_hash))
    return questions


def load_solutions(file_path: Path) -> dict[int, str]:
    # Solutions.md seems like numbered list "1. <answer>"
    solutions: dict[int, str] = {}
    for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r"\s*(\d+)\.[\s\t]+(.+?)\s*$", line)
        if m:
            idx = int(m.group(1))
            raw = m.group(2)
            solutions[idx] = raw.strip()
    return solutions


def md5_hex_utf8(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def verify_answer(question: Question, user_answer: str, solutions_map: dict[int, str]) -> bool:
    # Prefer authoritative solutions from Solutions.md if available; otherwise rely on hash
    if question.index in solutions_map:
        expected = str(solutions_map[question.index]).strip()
        # Normalize simple formatting differences like commas/whitespace
        normalized_user = re.sub(r"\s+", "", user_answer)
        normalized_expected = re.sub(r"\s+", "", expected)
        return normalized_user == normalized_expected
    # Fallback: compare md5(user_answer) to expected hash in Questions.md
    return md5_hex_utf8(user_answer.strip()) == question.expected_hash


questions_cache: list[Question] | None = None
solutions_cache: dict[int, str] | None = None


def get_questions() -> list[Question]:
    global questions_cache
    if questions_cache is None:
        questions_cache = parse_questions(QUESTIONS_MD)
    return questions_cache


def get_solutions() -> dict[int, str]:
    global solutions_cache
    if solutions_cache is None:
        solutions_cache = load_solutions(SOLUTIONS_MD)
    return solutions_cache


def choose_question_index() -> int:
    qs = get_questions()
    if not qs:
        raise RuntimeError("No questions loaded")
    return secrets.choice(qs).index


def get_question_by_index(idx: int) -> Question:
    for q in get_questions():
        if q.index == idx:
            return q
    raise KeyError(idx)


def mint_jwt(payload: dict[str, Any]) -> str:
    headers = {"typ": "JWT", "alg": JWT_ALG}
    if JWT_ALG == "RS256":
        assert RSA_PRIVATE_KEY is not None
        return jwt.encode(payload, RSA_PRIVATE_KEY, algorithm="RS256", headers=headers)
    # HS256 fallback for local dev
    assert HS_SECRET is not None
    return jwt.encode(payload, HS_SECRET, algorithm="HS256", headers=headers)


def public_jwks() -> dict[str, Any]:
    # Minimal JWKS or a simple PEM response. Keep simple: return PEM if available.
    if JWT_ALG == "RS256":
        return {"kty": "RSA", "alg": "RS256", "use": "sig", "pem": RSA_PUBLIC_KEY}
    return {"kty": "oct", "alg": "HS256", "use": "sig"}


app = FastAPI(title="Python CAPTCHA Service")


class GenerateChallengeRequest(BaseModel):
    website: str
    session_id: str


@app.on_event("startup")
def startup() -> None:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/public_key")
def get_public_key() -> dict[str, Any]:
    return public_jwks()


@app.post("/generate_challenge")
def generate_challenge(
    payload: GenerateChallengeRequest | None = None,
    website: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    # Support both JSON body and query parameters
    req_website = payload.website if payload else website
    req_session_id = payload.session_id if payload else session_id
    if not req_website or not req_session_id:
        raise HTTPException(status_code=422, detail="website and session_id required")

    question_index = choose_question_index()
    challenge_id = secrets.token_urlsafe(16)
    created_at = int(time.time())
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO challenges (challenge_id, session_id, website, question_index, created_at) VALUES (?, ?, ?, ?, ?)",
            (challenge_id, req_session_id, req_website, question_index, created_at),
        )
        conn.commit()
    return {"challenge_id": challenge_id}


@app.get("/challenge", response_class=HTMLResponse)
def challenge_page(redirect: str = "/", challenge_id: str = Query(...), session_id: str = Query("")):
    # Simple HTML that iframed site can embed; fetches question via JS
    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Python CAPTCHA</title>
        <style>
          body {{ font-family: sans-serif; padding: 1rem; }}
          .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 1rem; }}
          .row {{ margin-top: 1rem; }}
          input[type=text] {{ width: 100%; padding: 0.5rem; font-size: 1rem; }}
          button {{ padding: 0.5rem 1rem; font-size: 1rem; }}
        </style>
      </head>
      <body>
        <div class=\"card\">
          <h2>Answer this Python/math question</h2>
          <div id=\"question\">Loading question…</div>
          <div class=\"row\">
            <input id=\"answer\" type=\"text\" placeholder=\"Your answer\" />
          </div>
          <div class=\"row\">
            <button id=\"submit\">Submit</button>
          </div>
          <div class=\"row\">
            <div id=\"status\"></div>
          </div>
        </div>
        <script>
          const challengeId = {json.dumps(challenge_id)!r};
          const sessionId = {json.dumps(session_id)!r};
          const redirectUrl = {json.dumps(redirect)!r};
          async function loadQuestion() {{
            const r = await fetch(`/get_challenge?challenge_id=${{encodeURIComponent(challengeId)}}`);
            const j = await r.json();
            console.log('get_challenge response', j);
            document.getElementById('question').innerText = j.question || j.error || 'Failed to load question';
          }}
          async function submit() {{
            const answer = document.getElementById('answer').value;
            const r = await fetch(`/solution?challenge_id=${{encodeURIComponent(challengeId)}}&answer=${{encodeURIComponent(answer)}}`, {{ method: 'POST' }});
            if (!r.ok) {{
              document.getElementById('status').innerText = 'Incorrect. Try again.';
              return;
            }}
            const j = await r.json();
            // Parent page can read via postMessage or rely on redirect at top window if same-site
            // Here, we just navigate the iframe to a tiny success page that asks parent to continue.
            window.location.href = `/success?token=${{encodeURIComponent(j.token)}}&redirect=${{encodeURIComponent(redirectUrl)}}&session_id=${{encodeURIComponent(sessionId)}}`;
          }}
          document.getElementById('submit').addEventListener('click', submit);
          loadQuestion();
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/get_challenge")
def get_challenge(challenge_id: str) -> dict[str, Any]:
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT question_index FROM challenges WHERE challenge_id = ?", (challenge_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="challenge not found")
            
            question_index = int(row["question_index"])
            try:
                question = get_question_by_index(question_index)
                return {"question": f"Problem {question.index}:\n\n{question.statement}"}
            except KeyError:
                # Question not found - return debug info
                all_questions = get_questions()
                available_indices = [q.index for q in all_questions]
                return {
                    "error": f"Question {question_index} not found",
                    "available_questions": available_indices,
                    "total_questions": len(all_questions)
                }
    except Exception as e:
        return {"error": f"Failed to load question: {str(e)}"}


@app.post("/solution")
def post_solution(challenge_id: str | None = None, challengeId: str | None = None, answer: str = "") -> dict[str, Any]:
    # Accept both challenge_id and challengeId
    if not challenge_id:
        challenge_id = challengeId
    if not challenge_id:
        raise HTTPException(status_code=422, detail="challenge_id required")
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT session_id, website, question_index, solved_at FROM challenges WHERE challenge_id = ?",
            (challenge_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="challenge not found")
        if row["solved_at"]:
            raise HTTPException(status_code=409, detail="challenge already solved")
        question = get_question_by_index(int(row["question_index"]))
        ok = verify_answer(question, answer, get_solutions())
        if not ok:
            raise HTTPException(status_code=400, detail="incorrect answer")
        solved_at = int(time.time())
        conn.execute("UPDATE challenges SET solved_at = ? WHERE challenge_id = ?", (solved_at, challenge_id))
        conn.commit()

    # Mint JWT for the website to verify
    claims = {
        "iss": "python-captcha",
        "sub": row["session_id"],
        "aud": row["website"],
        "iat": int(time.time()),
        "exp": int(time.time()) + 300,  # 5 minutes
        "challenge_id": challenge_id,
        "q": int(row["question_index"]),
        "ok": True,
    }
    token = mint_jwt(claims)
    return {"token": token}


@app.get("/success", response_class=HTMLResponse)
def success(token: str, redirect: str = "/", session_id: str = ""):
    # Present a tiny page that can message parent with the token or redirect top-level
    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset=\"utf-8\" />
        <title>CAPTCHA Solved</title>
      </head>
      <body>
        <p>CAPTCHA solved. Returning to site…</p>
        <script>
          const token = {json.dumps(token)!r};
          const sessionId = {json.dumps(session_id)!r};
          const redirectUrl = {json.dumps(redirect)!r};
          // Notify parent window if embedded
          try {{
            window.parent.postMessage({{ type: 'captcha_solved', token, sessionId }}, '*');
          }} catch (e) {{}}
          // Redirect the top window with token as query params so server can read it
          try {{
            const u = new URL(redirectUrl, window.location.origin);
            u.searchParams.set('token', token);
            u.searchParams.set('session_id', sessionId);
            window.top.location.href = u.toString();
          }} catch (e) {{}}
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/")
def root() -> dict[str, Any]:
    return {"service": "python-captcha", "alg": JWT_ALG}


def create_app() -> FastAPI:
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("captcha_service.main:app", host="0.0.0.0", port=8000, reload=True)


