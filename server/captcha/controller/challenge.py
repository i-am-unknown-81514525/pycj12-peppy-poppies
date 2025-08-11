from uuid import UUID

from litestar import get, post
from litestar.controller import Controller
from litestar.di import Provide
from server.captcha.lib.dependencies import provide_challenge_service
from server.captcha.lib.services import ChallengeService
from server.captcha.models import Challenge
from server.captcha.schema.challenge import GenerateChallengeRequest, GenerateChallengeResponse


class ChallengeController(Controller):  # noqa: D101
    path = "/api/auth"
    tags = ["Challenge"]
    dependencies = {
        "challenge_service": Provide(provide_challenge_service),
    }

    @post("/generate-challenge")
    async def generate_challenge(
        self,
        data: GenerateChallengeRequest,
        challenge_service: ChallengeService,
    ) -> GenerateChallengeResponse:
        """Generate a new captcha challenge.

        Returns:
            GenerateChallengeResponse: The response containing the generated challenge ID.

        """
        temp_new_challenge_data = {
            "website": data.website,
            "session_id": data.session_id,
            "question": "Write a function `calc(x: int)` that calculates 673+x",
            "task_json": "[1, 1529]",
        }

        challenge = await challenge_service.create(temp_new_challenge_data)

        return GenerateChallengeResponse(challenge_id=challenge.id)

    @get("/get-challenge/{challenge_id:uuid}")
    async def get_challenge(
        self,
        challenge_service: ChallengeService,
        challenge_id: UUID,
    ) -> Challenge:
        """Get the current captcha challenge.

        Returns:
            Challenge: Alchemy model representing the challenge.

        """
        return await challenge_service.get_one(id=challenge_id)
