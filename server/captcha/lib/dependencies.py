from collections.abc import AsyncGenerator

from server.captcha.lib.services import ChallengeService
from sqlalchemy.ext.asyncio import AsyncSession


async def provide_challenge_service(  # noqa: D103
    db_session: AsyncSession | None = None,
) -> AsyncGenerator[ChallengeService, None]:
    async with ChallengeService.new(
        session=db_session,
        error_messages={
            "not_found": "No event challenge with the given ID.",
        },
    ) as service:
        yield service
