from server.backend.lib.services import UserService
from sqlalchemy.ext.asyncio import AsyncSession


async def provide_user_service(db_session: AsyncSession) -> UserService:
    """Provide a UserService instance."""
    return UserService(session=db_session)
