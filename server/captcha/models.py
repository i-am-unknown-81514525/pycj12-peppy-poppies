from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import Mapped


class Challenge(UUIDAuditBase):
    """Represents a captcha challenge."""

    website: Mapped[str]
    session_id: Mapped[UUID]
    question: Mapped[str]
    task_json: Mapped[str]
