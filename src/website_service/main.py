from __future__ import annotations

import os
import secrets
import time
from typing import Any

import httpx
from fastapi import Cookie, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from jose import jwt


CAPTCHA_ORIGIN = os.environ.get("CAPTCHA_ORIGIN", "http://localhost:8000")
WEBSITE_ORIGIN = os.environ.get("WEBSITE_ORIGIN", "http://localhost:9000")
WEBSITE_HOST = os.environ.get("WEBSITE_HOST", "website.app")

app = FastAPI(title="Demo Website Using CAPTCHA")


def session_cookie_name() -> str:
    return "sid"


def token_cookie_name() -> str:
    return "captcha_jwt"


async def fetch_public_key(client: httpx.AsyncClient) -> dict[str, Any]:
    r = await client.get(f"{CAPTCHA_ORIGIN}/public_key", timeout=10)
    r.raise_for_status()
    return r.json()


@app.get("/", response_class=HTMLResponse)
async def home(sid: str | None = Cookie(default=None), captcha_jwt: str | None = Cookie(default=None)) -> HTMLResponse:
    # If no session, create one and redirect to trigger challenge setup
    if not sid:
        new_sid = secrets.token_urlsafe(16)
        resp = RedirectResponse(url="/begin", status_code=307)
        resp.set_cookie(session_cookie_name(), new_sid, httponly=True, samesite="Lax")
        return resp

    # Show homepage content: if no token, ask user to solve captcha; else show gated content
    if not captcha_jwt:
        body = f"""
        <h1>Welcome</h1>
        <p>You need to pass the Python CAPTCHA to continue.</p>
        <a href=\"/begin\">Start CAPTCHA</a>
        """
        return HTMLResponse(content=body)

    # Verify token locally
    async with httpx.AsyncClient() as client:
        jwk = await fetch_public_key(client)
    try:
        if jwk.get("alg") == "RS256" and jwk.get("pem"):
            claims = jwt.decode(captcha_jwt, jwk["pem"], algorithms=["RS256"], audience=WEBSITE_HOST)
        else:
            # HS256 dev fallback
            claims = jwt.decode(captcha_jwt, os.environ.get("CAPTCHA_HS_SECRET", ""), algorithms=["HS256"], audience=WEBSITE_HOST)
    except Exception:
        # Invalid token -> clear cookie
        resp = RedirectResponse("/begin", status_code=307)
        resp.delete_cookie(token_cookie_name())
        return resp

    gated = f"""
    <h1>Gated Content</h1>
    <p>Session: {sid}</p>
    <pre>{claims}</pre>
    <a href=\"/reset\">Reset</a>
    """
    return HTMLResponse(content=gated)


@app.get("/begin")
async def begin(request: Request, sid: str | None = Cookie(default=None)):
    if not sid:
        # Create session cookie then reload
        new_sid = secrets.token_urlsafe(16)
        resp = RedirectResponse(url="/begin", status_code=307)
        resp.set_cookie(session_cookie_name(), new_sid, httponly=True, samesite="Lax")
        return resp

    # Ask CAPTCHA to generate a challenge
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{CAPTCHA_ORIGIN}/generate_challenge",
            json={"website": WEBSITE_HOST, "session_id": sid},
            timeout=10,
        )
        r.raise_for_status()
        challenge_id = r.json()["challenge_id"]

    # Redirect to our local route that renders the iframe to the CAPTCHA challenge
    return RedirectResponse(url=f"/challenge?challenge_id={challenge_id}", status_code=307)


@app.get("/challenge", response_class=HTMLResponse)
async def render_challenge(challenge_id: str = Query(...), sid: str | None = Cookie(default=None)) -> HTMLResponse:
    if not sid:
        return RedirectResponse("/", status_code=307)
    # Embed the CAPTCHA page in an iframe; provide redirect back to '/handle' which will persist the token
    iframe_src = f"{CAPTCHA_ORIGIN}/challenge?redirect={WEBSITE_ORIGIN}/handle&challenge_id={challenge_id}&session_id={sid}"
    html = f"""
    <h1>Complete CAPTCHA</h1>
    <iframe src=\"{iframe_src}\" width=\"100%\" height=\"500\" style=\"border:1px solid #ccc;border-radius:8px\"></iframe>
    """
    return HTMLResponse(content=html)


@app.get("/handle")
async def handle_redirect(token: str | None = None, session_id: str | None = None, hash: str | None = None):
    # Token may be in query param (from iframe success) or in URL fragment (not sent to server).
    # For simplicity, accept query "token"; in prod, consider postMessage + Storage API.
    if not token:
        # No token -> go home (will show require-captcha notice)
        return RedirectResponse("/", status_code=307)
    resp = RedirectResponse("/", status_code=307)
    resp.set_cookie(token_cookie_name(), token, httponly=True, samesite="Lax")
    return resp


@app.get("/reset")
async def reset():
    resp = RedirectResponse("/", status_code=307)
    resp.delete_cookie(token_cookie_name())
    resp.delete_cookie(session_cookie_name())
    return resp


def create_app() -> FastAPI:
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("website_service.main:app", host="0.0.0.0", port=9000, reload=True)


