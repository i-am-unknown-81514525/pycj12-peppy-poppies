from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from server.backend.models import User


class UserService(SQLAlchemyAsyncRepositoryService[User]):
    """Service for managing users."""

    class UserRepository(SQLAlchemyAsyncRepository[User]):
        model_type = User

    repository_type = UserRepository

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """Authenticate a user by username and password.

        Args:
            username: The username to authenticate
            password: The password to verify

        Returns:
            User if authentication successful, None otherwise
        """
        try:
            user = await self.get_one(username=username)
            if user and user.is_active and user.verify_password(password):
                return user
        except Exception:
            pass
        return None