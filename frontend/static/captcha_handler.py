import urllib.parse
from datetime import UTC, datetime, timedelta
from typing import TypedDict

from pyodide.ffi import JsProxy, create_proxy
from pyscript import document, window  # type: ignore[reportAttributeAccessIssue]

cookieStore = window.cookieStore  # noqa: N816

COOKIE_REQ_AUTH = "CODECAPTCHA_REQUIRE_AUTH"
COOKIE_CHALLENGE_ID = "CODECAPTCHA_CHALLENGE_ID"
COOKIE_JWT = "CODECAPTCHA_JWT"


class Cookie(TypedDict):
    """A Cookie dictionary with just `name` and `value`."""

    name: str
    value: str


curr_script = window.document.currentScript
DOMAIN = curr_script.getAttribute(
    "domain",
)  # <script type="py" domain"[domain]" src="[domain]/static/captcha_handler.py"></script>


async def on_load() -> None:
    """Check for `CODECAPTCHA_REQUIRE_AUTH` and `CODECAPTCHA_CHALLENGE_ID` on script load."""
    all_cookie = await cookieStore.getAll()
    cookie_list: list[Cookie] = []
    for cookie in all_cookie:
        name: str = cookie.name
        value: str = cookie.value
        cookie_list.append({"name": name, "value": value})
    _process_cookie(cookie_list)


def on_cookie_change(event: JsProxy) -> None:  # event: CookieChangeEvent
    """Check for `CODECAPTCHA_REQUIRE_AUTH` and `CODECAPTCHA_CHALLENGE_ID` on cookie changes (such as API requests)."""
    if window.location.href == "/challenge":
        return
    cookie_list: list[Cookie] = []
    for cookie in event.changed:  # type: ignore[reportAttributeAccessIssue]
        name: str = cookie.name
        value: str = cookie.value
        cookie_list.append({"name": name, "value": value})
    _process_cookie(cookie_list)


def _process_cookie(cookies: list[Cookie]) -> None:
    req_auth = False
    challenge_id = ""
    for cookie in cookies:
        name = cookie["name"]
        value = cookie["value"]
        if name == COOKIE_REQ_AUTH and value.lower().strip() == "true":
            req_auth = True
        if name == COOKIE_CHALLENGE_ID:
            challenge_id = value.strip()
    if req_auth and challenge_id:
        loc = window.location
        redirect = f"{loc.pathname}{loc.search}{loc.hash}"
        encoded_redirect = urllib.parse.quote(redirect)
        url = f"/challenge?redirect={encoded_redirect}&=challenge_id={challenge_id}"
        window.location.href = url


def handle_message(message: JsProxy) -> None:
    """Handle JWT token from inner frame."""
    if message.origin != DOMAIN:  # type: ignore[reportAttributeAccessIssue]
        return
    content: str = message.data  # type: ignore[reportAttributeAccessIssue]
    expire_date = datetime.now(UTC) + timedelta(days=1)
    expire_str = expire_date.strftime("%a, %d %b %Y %H:%H:%S GMT")
    document.cookie = f"{COOKIE_JWT}={content}; expires={expire_str}; path=/"
    # delete the cookie or at least set it to false since auth successed
    document.cookie = f"{COOKIE_REQ_AUTH}=false;Max-Age=0; path=/"
    parsed = urllib.parse.urlparse(window.location.href).query
    query_dict = urllib.parse.parse_qs(parsed)
    redirect = query_dict.get("redirect", "/")
    if isinstance(redirect, list):
        redirect = redirect[0] if len(redirect) > 0 else "/"
    window.location.href = urllib.parse.unquote(redirect)


if window.location.href == "/challenge":
    body = document.body
    parsed = urllib.parse.urlparse(window.location.href).query
    query_dict = urllib.parse.parse_qs(parsed)
    challenge_id = query_dict.get("challenge_id")
    iframe = document.createElement("iframe")
    iframe.src = f"{DOMAIN}/challenge?challenge_id{challenge_id}"
    iframe.id = "code_captcha_iframe"
    iframe.style.height = "100vw"
    iframe.style.height = "100vh"
    iframe.setAttribute("frameborder", "0")
    body.appendChild(iframe)
    window.addEventListener("message", create_proxy(handle_message))
else:
    await on_load()  # type: ignore  # noqa: F704, PLE1142, PGH003
    cookieStore.addEventListener("change", create_proxy(on_cookie_change))
