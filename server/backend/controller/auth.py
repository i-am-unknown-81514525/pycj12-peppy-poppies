from os import getenv
from uuid import uuid4

import httpx
from litestar import Request, get
from litestar.controller import Controller
from server.backend.schema.auth import GetChallengeResponse

CAPTCHA_SERVER = getenv("CODECAPTCHA_DOMAIN_INTERNAL", getenv("CODECAPTCHA_DOMAIN", "localhost:8001"))


class AuthController(Controller):  # noqa: D101
    path = "/api/auth"
    tags = ["Auth"]

    @get("/get-challenge")
    async def get_challenge(self, request: Request) -> GetChallengeResponse:
        """Get a challenge ID from CAPTCHA server.

        Returns:
            GetChallengeResponse: A response with the challenge ID.

        """
        host = request.headers["Host"]
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{CAPTCHA_SERVER}/api/challenge/generate-challenge",
                headers={"Content-Type": "application/json"},
                json={"website": host, "session_id": uuid4().hex},
            )
            resp_json = resp.json()
            return GetChallengeResponse(challenge_id=resp_json["challenge_id"])
