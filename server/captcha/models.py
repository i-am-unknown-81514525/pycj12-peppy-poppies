import json
from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import Mapped


class Challenge(UUIDAuditBase):
    """Represents a captcha challenge."""

    website: Mapped[str]
    session_id: Mapped[UUID]
    question: Mapped[str]
    tasks: Mapped[str]
    answers: Mapped[str]

    @property
    def task_list(self) -> list[int]:
        """Convert tasks from string to a list of integers."""
        return json.loads(self.tasks)

    @property
    def answer_list(self) -> list[int]:
        """Convert answers from string to a list of integers."""
        return json.loads(self.answers)
