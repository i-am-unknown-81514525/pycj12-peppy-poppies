from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import Mapped


class User(UUIDAuditBase):
    """Represents a user in the system."""

    username: Mapped[str]
    password: Mapped[str]

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
