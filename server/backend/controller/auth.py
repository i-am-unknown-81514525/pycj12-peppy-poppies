from datetime import timedelta
from uuid import uuid4

import httpx
from litestar import Request, Response, get, post
from litestar.controller import Controller
from litestar.datastructures import Cookie
from litestar.di import Provide
from litestar.exceptions import NotFoundException, PermissionDeniedException
from server.backend.lib.config import captcha_server, jwt_cookie_auth, store
from server.backend.lib.dependencies import provide_user_service
from server.backend.lib.services import UserService
from server.backend.schema.auth import GetChallengeResponse, GetUser, LoginRequest


class AuthController(Controller):  # noqa: D101
    path = "/api/auth"
    tags = ["Auth"]
    dependencies = {
        "user_service": Provide(provide_user_service),
    }

    @get("/get-challenge", exclude_from_auth=True)
    async def get_challenge(self, request: Request) -> GetChallengeResponse:
        """Get a challenge ID from CAPTCHA server.

        Returns:
            GetChallengeResponse: A response with the challenge ID.

        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{captcha_server}/api/challenge/generate-challenge",
                headers={"Content-Type": "application/json"},
                json={"website": request.headers["Host"], "session_id": uuid4().hex},
            )

            resp_json = resp.json()

            await store.set(
                key=resp_json["challenge_id"],
                value="valid",
                expires_in=timedelta(hours=1),
            )

            return GetChallengeResponse(challenge_id=resp_json["challenge_id"])

    @post("/login", exclude_from_auth=True)
    async def login(self, request: Request, data: LoginRequest, user_service: UserService) -> Response:
        """Handle user login.

        This method is a placeholder for the actual login logic.

        Raises:
            PermissionDeniedException: If the challenge ID is invalid or expired.
            NotFoundException: If the user is not found or credentials are invalid.

        Returns:
            Response: The response containing the JWT token.

        """
        host: str | list[str] = request.headers["Host"]
        if isinstance(host, str) and not host.startswith("http://") and not host.startswith("https://"):
            host = [host, f"http://{host}", f"https://{host}"]
        try:
            jwt_data = request.app.state["jwt_validator"].validate(
                website=host,
                jwt_token=data.captcha_jwt,
            )
        except Exception as e:
            raise PermissionDeniedException("Invalid JWT token") from e

        is_valid = await store.get(key=jwt_data["challenge_id"]) == b"valid"

        if not is_valid:
            raise PermissionDeniedException("Invalid token or challenge expired.")

        await store.delete(key=jwt_data["challenge_id"])  # each challenge_id can only be used once

        user = await user_service.get_one_or_none(username=data.username, password=data.password)

        if not user:
            raise NotFoundException("User not found or invalid credentials.")

        return jwt_cookie_auth.login(
            identifier=str(user.id),
            send_token_as_response_body=True,
        )

    @get("/logout", exclude_from_auth=True)
    async def logout(self) -> Response:
        """Log out the user by clearing the authentication token cookie.

        Returns:
            Response: A response that clears the 'token' cookie.

        """
        return Response(
            content=None,
            cookies=[Cookie(key="token", value=None, expires=0)],
        )

    @get("/me")
    async def get_user(
        self,
        request: Request,
        user_service: UserService,
    ) -> GetUser:
        """Retrieve the currently authenticated user's information.

        Args:
            request (Request): The current request object containing user info.
            users_service (UserService): Service to convert user to schema.

        Returns:
            GetUser: The schema representation of the authenticated user.

        """
        return user_service.to_schema(request.user, schema_type=GetUser)
