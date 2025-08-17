from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
)
from server.backend.models import User


class UserService(SQLAlchemyAsyncRepositoryService[User]):  # noqa: D101
    class UserRepository(SQLAlchemyAsyncRepository[User]):
        model_type = User

    repository_type = UserRepository
