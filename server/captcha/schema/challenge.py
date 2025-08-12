from uuid import UUID

from msgspec import Struct


class GenerateChallengeRequest(Struct):  # noqa: D101
    website: str
    session_id: UUID


class GenerateChallengeResponse(Struct):  # noqa: D101
    challenge_id: UUID


class GetChallengeResponse(Struct):  # noqa: D101
    question: str
    tasks: list[int]


class SubmitChallengeRequest(Struct):  # noqa: D101
    challenge_id: UUID
    answers: list[int]
