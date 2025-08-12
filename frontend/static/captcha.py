import json
import urllib.parse
from base64 import b64decode
from typing import TypedDict

from pyodide.ffi import create_proxy
from pyodide.http import pyfetch
from pyscript import document, window, display, when  # type: ignore[reportAttributeAccessIssue]
import panel as pn

body = document.body
worker = window.Worker.new("/static/runner.js", {"type": "module"})
status: dict[str, int] = {}  # -1: failed, 0: success, 1: starting, 2: loading code, >=100: running test (idx:v-100)

class GetChallengeResponse(TypedDict):
    """Response schema for /get_challenge endpoint."""

    question: str
    task: list[int]


class SolutionCorrectJWTPayload(TypedDict):
    """Payload data of the JWT token returned from /solution endpoint."""

    session_id: str
    challenge_id: str
    nbf: float
    exp: float
    aud: str
    iss: str
    iat: float


def get_challenge_id() -> str:
    """Get challenge_id of the challenge."""
    parsed = urllib.parse.urlparse(window.location.href).query
    query_dict = urllib.parse.parse_qs(parsed)
    challenge_id = query_dict.get("challenge_id")
    if not isinstance(challenge_id, str):
        raise ValueError("Not a running challenge")
    return challenge_id

async def get_challenge() -> tuple[str, list[int]]:
    """Endpoint to collect challenge data."""
    challenge_id = get_challenge_id()
    request = await pyfetch(f"/api/challenge/get-challenge/{challenge_id}")
    response: GetChallengeResponse = await request.json()
    return (response["question"], response["task"])

async def worker_on_message(e) -> None:
    content: str = e.data
    key, value = content.split(",", maxsplit=1)
    challenge_id = get_challenge_id()
    if key == "result":
        result = await send_result(json.loads(value))
        status[challenge_id] = 0 if result else -1
    elif key == "load":
        status[challenge_id] = 2
    elif key == "run":
        status[challenge_id] = 100 + int(value)


async def submit(code: str, task: list[int]) -> None:
    """Submit the code to be executed locally with the given task."""
    challenge_id = get_challenge_id()
    status[challenge_id] = 1
    worker.postMessage(json.dumps({"code": code, "task": task}))


async def send_result(results: list[int]) -> bool:
    """Send the calculated result to CAPTCHA service to obtain the JWT."""
    challenge_id = get_challenge_id()
    req_data = json.dumps(
        {
            "solutions": list(results),  # in case this is a JsProxy
        },
    )
    response = await pyfetch(f"/api/challenge/submit-challenge/{challenge_id}", method="POST", body=req_data)
    if not response.ok:
        return False
    jwt = await response.text()
    splitted = jwt.split(".")
    if len(splitted) != 3:  # noqa: PLR2004
        return False
    payload_str = b64decode(splitted[1] + "=" * (4 - len(splitted[1]) % 4)).decode()
    payload: SolutionCorrectJWTPayload = json.loads(payload_str)
    origin = payload["aud"]
    if not origin.startswith("http://") and not origin.startswith("https://"):
        origin = f"https://{origin}"
    window.parent.postMessage(jwt, origin)
    return True

window.get_challenge = create_proxy(get_challenge)
window.submit = create_proxy(submit)
worker.onmessage = create_proxy(worker_on_message)
