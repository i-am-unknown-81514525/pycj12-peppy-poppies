import urllib.parse
from typing import TypedDict

from pyodide.http import pyfetch
from pyscript import document, window  # type: ignore[reportAttributeAccessIssue]

body = document.body


class GetChallengeResponse(TypedDict):
    """Response schema for /get_challenge endpoint."""

    question: str
    task: list[int]


async def get_challenge() -> tuple[str, list[int]]:
    """Endpoint to collect challenge data."""
    parsed = urllib.parse.urlparse(window.location.href).query
    query_dict = urllib.parse.parse_qs(parsed)
    challenge_id = query_dict.get("challenge_id")
    request = await pyfetch(f"/get_challenge?challenge_id={challenge_id}")
    response: GetChallengeResponse = await request.json()
    return (response["question"], response["task"])


window.get_challenge = get_challenge
