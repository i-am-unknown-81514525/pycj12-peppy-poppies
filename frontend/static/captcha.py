import json
import urllib.parse
from base64 import b64decode
from typing import TypedDict

from pyodide.ffi import create_proxy
from pyodide.http import pyfetch
from pyscript import document, window  # type: ignore[reportAttributeAccessIssue]

body = document.body


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


async def get_challenge() -> tuple[str, list[int]]:
    """Endpoint to collect challenge data."""
    parsed = urllib.parse.urlparse(window.location.href).query
    query_dict = urllib.parse.parse_qs(parsed)
    challenge_id = query_dict.get("challenge_id")
    request = await pyfetch(f"/get_challenge?challenge_id={challenge_id}")
    response: GetChallengeResponse = await request.json()
    return (response["question"], response["task"])


async def send_result(results: list[int]) -> bool:
    """Send the calculated result to CAPTCHA service to obtain the JWT."""
    parsed = urllib.parse.urlparse(window.location.href).query
    query_dict = urllib.parse.parse_qs(parsed)
    challenge_id = query_dict.get("challenge_id")
    req_data = json.dumps(
        {
            "solutions": list(results),  # in case this is a JsProxy
        }
    )
    response = await pyfetch(f"/solution?challenge_id={challenge_id}", method="POST", body=req_data)
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
window.send_result = create_proxy(send_result)
