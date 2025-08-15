from os import getenv
from pathlib import Path
from uuid import UUID

from crypto.jwt_generate import JWTGenerator
from crypto.key import import_private_key
from litestar import Response, get, post, status_codes
from litestar.controller import Controller
from litestar.di import Provide
from server.captcha.lib.dependencies import provide_challenge_service
from server.captcha.lib.services import ChallengeService
from server.captcha.schema.challenge import (
    GenerateChallengeRequest,
    GenerateChallengeResponse,
    GetChallengeResponse,
    SubmitChallengeRequest,
)

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
    ) -> GenerateChallengeResponse:
        """Generate a new captcha challenge.

        Returns:
            GenerateChallengeResponse: The response containing the generated challenge ID.

        """
        temp_new_challenge_data = {
            "website": data.website,
            "session_id": data.session_id,
            "question": "Write a function `calc(x: int)` that calculates 673+x",
            "tasks": "[1, 1529]",
            "answers": "[674, 2202]",
        }

        # TODO: LLM
        # create question
        # create tasks
        # create answers for tasks

        challenge = await challenge_service.create(temp_new_challenge_data)

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
    ) -> Response:
        """Submit a captcha challenge.

        Returns:
            Response: A response indicating whether the challenge was solved correctly or not.

        """
        challenge = await challenge_service.get_one(id=data.challenge_id)

        if challenge.answer_list == data.answers:
            private_key = import_private_key(KEY_PATH / "private.pem")
            jwt_generator = JWTGenerator(issuer="captcha-server.com", private_key=private_key)

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
        """Get the public key for JWT validation.

        Returns:
            Response: A response containing the public key in PEM format.

        """
        try:
            # Read the PEM file content directly
            with (KEY_PATH / "public.pem").open("r") as f:
                public_key_pem = f.read()

            return Response(
                status_code=status_codes.HTTP_200_OK,
                content={"public_key": public_key_pem},
                headers={"Content-Type": "application/json"},
            )
        except (FileNotFoundError, PermissionError) as e:
            return Response(
                status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": f"Public key file error: {e!s}"},
                headers={"Content-Type": "application/json"},
            )
        except OSError as e:
            return Response(
                status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": f"System error accessing public key: {e!s}"},
                headers={"Content-Type": "application/json"},
            )
        except (ValueError, TypeError) as e:
            return Response(
                status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": f"Invalid public key format: {e!s}"},
                headers={"Content-Type": "application/json"},
            )
