from os import getenv
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

import anyio
from crypto.jwt_generate import JWTGenerator
from crypto.key import import_private_key
from litestar import Request, Response, get, post, status_codes
from litestar.controller import Controller
from litestar.di import Provide
from litestar.status_codes import HTTP_200_OK
from server.captcha.lib.dependencies import provide_challenge_service
from server.captcha.lib.services import ChallengeService
from server.captcha.lib.utils import question_generator
from server.captcha.schema.challenge import (
    GenerateChallengeRequest,
    GenerateChallengeResponse,
    GetChallengeResponse,
    SubmitChallengeRequest,
)

if TYPE_CHECKING:
    from server.captcha.schema.questions import GeneratedQuestion, QuestionSet

KEY_PATH = Path(getenv("KEY_PATH", "./captcha_data"))


class ChallengeController(Controller):  # noqa: D101
    path = "/api/challenge"
    tags = ["Challenge"]
    dependencies = {
        "challenge_service": Provide(provide_challenge_service),
    }

    @post("/generate-challenge")
    async def generate_challenge(
        self,
        data: GenerateChallengeRequest,
        challenge_service: ChallengeService,
        request: Request,
    ) -> GenerateChallengeResponse:
        """Generate a new captcha challenge.

        Returns:
            GenerateChallengeResponse: The response containing the generated challenge ID.

        """
        question_set: QuestionSet = request.app.state["question_set"]
        question: GeneratedQuestion = question_generator(question_set)

        challenge = await challenge_service.create(
            {
                "website": data.website,
                "session_id": data.session_id,
                "question": question.question,
                "tasks": str(question.tasks),
                "answers": str(question.solutions),
            },
        )

        return GenerateChallengeResponse(challenge_id=challenge.id)

    @get("/get-challenge/{challenge_id:uuid}")
    async def get_challenge(
        self,
        challenge_service: ChallengeService,
        challenge_id: UUID,
    ) -> GetChallengeResponse:
        """Get the current captcha challenge.

        Returns:
            GetChallengeResponse: The response containing the challenge details.

        """
        challenge = await challenge_service.get_one(id=challenge_id)

        return GetChallengeResponse(
            question=challenge.question,
            tasks=challenge.task_list,
        )

    @post("/submit-challenge")
    async def submit_challenge(
        self,
        challenge_service: ChallengeService,
        data: SubmitChallengeRequest,
        request: Request,
    ) -> Response:
        """Submit a captcha challenge.

        Returns:
            Response: A response indicating whether the challenge was solved correctly or not.

        """
        challenge = await challenge_service.get_one(id=data.challenge_id)

        if challenge.answer_list == data.answers:
            private_key = import_private_key(KEY_PATH / "private.pem")
            jwt_generator = JWTGenerator(issuer=request.headers["Host"], private_key=private_key)

            token = jwt_generator.generate(
                website=challenge.website,
                challenge_id=str(data.challenge_id),
            )

            return Response(
                status_code=status_codes.HTTP_201_CREATED,
                content={"token": token},
            )

        return Response(
            status_code=status_codes.HTTP_400_BAD_REQUEST,
            content="Challenge not solved correctly.",
        )

    @get("/get-public-key")
    async def get_public_key(self) -> Response:
        """Get CAPTCHA server public key.

        Returns:
            Response: A response of the server public key used to sign the JWT.

        """
        async with await anyio.open_file(KEY_PATH / "public.pem") as file:
            return Response(content=await file.read(), status_code=HTTP_200_OK, media_type="application/x-pem-file")
