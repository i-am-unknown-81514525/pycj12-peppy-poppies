import urllib.parse
from typing import Any

import js  # type: ignore[reportMissingModuleSource]
from pyodide.ffi import create_proxy, JsProxy

cookieStore = js.window.cookieStore

COOKIE_REQ_AUTH = "CODECAPTCHA_REQUIRE_AUTH"
COOKIE_CHALLENGE_ID = "CODECAPTCHA_CHALLENGE_ID"
COOKIE_JWT = "CODECAPTCHA_JWT"

def on_cookie_change(event: JsProxy) -> None: # event: CookieChangeEvent
    if js.window.location.href == "/challenge":
        return
    req_auth = False
    challenge_id = ""
    for cookie in event.changed:  # type: ignore[reportAttributeAccessIssue]
        name: str = cookie.name
        value: str = cookie.value
        if (name == COOKIE_REQ_AUTH and value.lower().strip() == "true"):
            req_auth = True
        if (name == COOKIE_CHALLENGE_ID):
            challenge_id = value.strip()
    if (req_auth and challenge_id):
        loc = js.window.location
        redirect = f"{loc.pathname}{loc.search}{loc.hash}"
        encoded_redirect = urllib.parse.quote(redirect)
        url = f"/challenge?redirect={encoded_redirect}&=challenge_id={challenge_id}"
        js.window.location.href = url


cookieStore.addEventListener("change", create_proxy(on_cookie_change))
