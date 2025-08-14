from uuid import UUID

from msgspec import Struct


class GetChallengeResponse(Struct):  # noqa: D101
    challenge_id: UUID
