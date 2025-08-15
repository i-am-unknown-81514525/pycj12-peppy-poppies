import tempfile
from os import getenv
from pathlib import Path
from uuid import uuid4

import httpx
from crypto.jwt_generate import JWTValidator
from crypto.key import import_public_key
from litestar import Request, Response, get, post, status_codes
from litestar.controller import Controller
from litestar.di import Provide
from server.backend.lib.dependencies import provide_user_service
from server.backend.lib.services import UserService
from server.backend.schema.auth import GetChallengeResponse, LoginRequest

CAPTCHA_SERVER = getenv("CODECAPTCHA_DOMAIN_INTERNAL", getenv("CODECAPTCHA_DOMAIN", "localhost:8001"))


class AuthController(Controller):
    """Authentication controller for handling login and JWT validation."""

    path = "/api/auth"
    tags = ["Auth"]
    dependencies = {
        "user_service": Provide(provide_user_service),
    }

    @get("/get-challenge")
    async def get_challenge(self, request: Request) -> GetChallengeResponse:
        """Get a challenge ID from CAPTCHA server.

        Returns:
            GetChallengeResponse: A response with the challenge ID.

        """
        host = request.headers["Host"]
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"http://{CAPTCHA_SERVER}/api/challenge/generate-challenge",
                headers={"Content-Type": "application/json"},
                json={"website": host, "session_id": uuid4().hex},
            )
            resp_json = resp.json()
            return GetChallengeResponse(challenge_id=resp_json["challenge_id"])

    @post("/login")
    async def login(
        self,
        data: LoginRequest,
        user_service: UserService,
        request: Request,
    ) -> Response:
        """Login endpoint that validates credentials and JWT token.

        Args:
            data: Login request containing username, password, and JWT token
            user_service: User service for authentication
            request: HTTP request object

        Returns:
            Response: Login response with success status and user info

        """
        # First validate the JWT token from captcha
        try:
            # Get public key from captcha server
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"http://{CAPTCHA_SERVER}/api/challenge/get-public-key")
                if not resp.is_success:
                    return Response(
                        status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                        content={"error": "Failed to retrieve public key from captcha server"},
                        headers={"Content-Type": "application/json"},
                    )

                public_key_data = resp.json()
                public_key_pem = public_key_data["public_key"]

                # Save public key temporarily to validate JWT using secure temp file
                with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as temp_file:
                    temp_file.write(public_key_pem)
                    temp_key_path = Path(temp_file.name)

                try:
                    # Import and validate JWT
                    public_key = import_public_key(temp_key_path)
                    jwt_validator = JWTValidator(public_key)

                    # Validate the JWT token
                    host = request.headers.get("Host", "localhost")
                    payload = jwt_validator.validate(data.jwt_token, audience=host)
                finally:
                    # Clean up temp file
                    temp_key_path.unlink(missing_ok=True)

        except (ValueError, KeyError, TypeError) as e:
            return Response(
                status_code=status_codes.HTTP_401_UNAUTHORIZED,
                content={"error": f"Invalid JWT token: {e!s}"},
                headers={"Content-Type": "application/json"},
            )
        except (ConnectionError, TimeoutError) as e:
            return Response(
                status_code=status_codes.HTTP_503_SERVICE_UNAVAILABLE,
                content={"error": f"Captcha service unavailable: {e!s}"},
                headers={"Content-Type": "application/json"},
            )
        except (OSError, RuntimeError) as e:
            return Response(
                status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": f"System error during authentication: {e!s}"},
                headers={"Content-Type": "application/json"},
            )

        # Now validate user credentials
        user = await user_service.authenticate_user(data.username, data.password)
        if not user:
            return Response(
                status_code=status_codes.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid username or password"},
                headers={"Content-Type": "application/json"},
            )

        # Return success response
        return Response(
            status_code=status_codes.HTTP_200_OK,
            content={
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                },
                "jwt_payload": payload,
            },
            headers={"Content-Type": "application/json"},
        )
