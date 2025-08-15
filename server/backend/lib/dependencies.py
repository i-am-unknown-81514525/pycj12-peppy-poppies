from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from server.backend.lib.services import UserService


async def provide_user_service(db_session: AsyncSession) -> UserService:
    """Provide a UserService instance."""
    return UserService(session=db_session)