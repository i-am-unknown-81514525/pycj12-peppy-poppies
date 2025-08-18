from uuid import UUID

from msgspec import Struct


class GetChallengeResponse(Struct):  # noqa: D101
    challenge_id: UUID


class LoginRequest(Struct):  # noqa: D101
    username: str
    password: str
    captcha_jwt: str


class GetUser(Struct):  # noqa: D101
    username: str
