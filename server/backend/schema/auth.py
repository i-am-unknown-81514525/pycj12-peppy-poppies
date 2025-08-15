from uuid import UUID

from msgspec import Struct


class GetChallengeResponse(Struct):  # noqa: D101
    challenge_id: UUID


class LoginRequest(Struct):  # noqa: D101
    username: str
    password: str
    jwt_token: str


class LoginResponse(Struct):  # noqa: D101
    success: bool
    message: str
    user: dict | None = None
    jwt_payload: dict | None = None
