import time

from pyscript import document, window  # type: ignore[reportAttributeAccessIssue]
from pyscript.ffi import create_proxy  # type: ignore[reportAttributeAccessIssue]

try:
    from typing import TYPE_CHECKING, TypedDict
    from urllib.parse import parse_qs, quote, unquote, urlparse

    class Cookie(TypedDict):  # type: ignore[reportRedeclaration]
        """A Cookie dictionary with just `name` and `value`."""

        name: str
        value: str
except ImportError:  # micropython
    TYPE_CHECKING = False
    if TYPE_CHECKING:
        from urllib.parse import parse_qs, quote, unquote, urlparse

        class Cookie(TypedDict):
            """A Cookie dictionary with just `name` and `value`."""

            name: str
            value: str
    else:

        class Cookie:
            """A Cookie dictionary with just `name` and `value`."""

            name: str
            value: str

        import mip  # type: ignore[reportMissingImport]

        mip.install(
            "https://gist.githubusercontent.com/i-am-unknown-81514525/088e4a1a19246b440d98515d0cbce44d/raw/f82fd0eaeaad55d49fa82aac858309f9b9b81816/parse.py",
        )
        from parse import parse_qs, quote, unquote, urlparse

cookieStore = window.cookieStore  # noqa: N816

COOKIE_REQ_AUTH = "CODECAPTCHA_REQUIRE_AUTH"
COOKIE_CHALLENGE_ID = "CODECAPTCHA_CHALLENGE_ID"
COOKIE_JWT = "CODECAPTCHA_JWT"


curr_script = window.document.currentScript
DOMAIN: str = curr_script.getAttribute(
    "domain",
)  # <script type="py" domain="[domain]" src="[domain]/static/captcha_handler.py"></script>
MIN_MODE: bool = (
    curr_script.getAttribute(
        "min_mode",
    ).lower()
    == "true"
)


async def on_load() -> None:
    """Check for `CODECAPTCHA_REQUIRE_AUTH` and `CODECAPTCHA_CHALLENGE_ID` on script load."""
    all_cookie = await cookieStore.getAll()
    cookie_list: list[Cookie] = []
    for cookie in all_cookie:
        name: str = cookie.name
        value: str = cookie.value
        cookie_list.append({"name": name, "value": value})
    _process_cookie(cookie_list)


def on_cookie_change(event) -> None:  # event: CookieChangeEvent # noqa: ANN001
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
        encoded_redirect = quote(redirect)
        url = f"/challenge?redirect={encoded_redirect}&=challenge_id={challenge_id}"
        window.location.href = url


def handle_message(message) -> None:  # noqa: ANN001
    """Handle JWT token from inner frame."""
    print(f"[captcha_handler.py] {message.origin}: {message.data}")
    if message.origin != DOMAIN:  # type: ignore[reportAttributeAccessIssue]
        return
    content: str = message.data  # type: ignore[reportAttributeAccessIssue]
    expire_date = time.time() + 86400
    expire_str = time.strftime("%a, %d %b %Y %H:%H:%S GMT", time.gmtime(expire_date))
    document.cookie = f"{COOKIE_JWT}={content}; expires={expire_str}; path=/"
    # delete the cookie or at least set it to false since auth successed
    document.cookie = f"{COOKIE_REQ_AUTH}=false;Max-Age=0; path=/"
    parsed = urlparse(window.location.href).query
    query_dict = parse_qs(parsed)
    redirect = query_dict.get("redirect", None)
    if isinstance(redirect, list):
        redirect = redirect[0] if len(redirect) > 0 else None
    if redirect is not None:
        window.location.href = unquote(redirect)
    print("[captcha_handler.py]: captchaCompleted")
    window.postMessage("captchaCompleted")


window.handle_message = create_proxy(handle_message)
if window.location.href == "/challenge":
    window.addEventListener("message", create_proxy(handle_message))
if not MIN_MODE:
    if window.location.href == "/challenge":
        body = document.body
        parsed = urlparse(window.location.href).query
        query_dict = parse_qs(parsed)
        challenge_id = query_dict.get("challenge_id")
        iframe = document.createElement("iframe")
        iframe.src = f"{DOMAIN}/static/captcha.html?challenge_id{challenge_id}"
        iframe.id = "code_captcha_iframe"
        iframe.style.height = "100vw"
        iframe.style.height = "100vh"
        iframe.setAttribute("frameborder", "0")
        body.appendChild(iframe)
    else:
        await on_load()  # type: ignore  # noqa: F704, PLE1142, PGH003
        cookieStore.addEventListener("change", create_proxy(on_cookie_change))
