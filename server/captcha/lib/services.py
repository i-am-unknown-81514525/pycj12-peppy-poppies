from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
)
from server.captcha.models import Challenge


class ChallengeService(SQLAlchemyAsyncRepositoryService[Challenge]):  # noqa: D101
    class ChallengeRepository(SQLAlchemyAsyncRepository[Challenge]):
        model_type = Challenge

    repository_type = ChallengeRepository
