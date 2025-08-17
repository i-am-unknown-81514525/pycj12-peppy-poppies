from collections.abc import AsyncGenerator

from server.backend.lib.services import UserService
from sqlalchemy.ext.asyncio import AsyncSession


async def provide_user_service(  # noqa: D103
    db_session: AsyncSession | None = None,
) -> AsyncGenerator[UserService, None]:
    async with UserService.new(
        session=db_session,
        error_messages={
            "not_found": "No event user with the given ID.",
        },
    ) as service:
        yield service
