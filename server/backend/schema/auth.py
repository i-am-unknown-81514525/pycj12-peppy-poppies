from uuid import UUID

from msgspec import Struct

class GetChallengeResponse(Struct):
    challenge_id: UUID
