from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import DateTime, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""



# Create Data Base
class Challenge(Base):
    """Model for challenges."""

    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    website: Mapped[str] = mapped_column(String(255))
    session_id: Mapped[str] = mapped_column(String(255))
    question: Mapped[str] = mapped_column(Text)
    task_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


DATABASE_URL = "sqlite:///./captcha.db"
engine = create_engine(DATABASE_URL, echo=False, future=True)

# Create tables
Base.metadata.create_all(engine)


app = FastAPI(title="Captcha Service")


@app.get("/generate_challenge")
def generate_challenge(website: Annotated[str, Query(...)], session_id: Annotated[str, Query(...)]) -> dict[str, Any]:
    """Generate a challenge for the website."""
    if not website or not session_id:
        raise HTTPException(status_code=400, detail="Both 'website' and 'session_id' query parameters are required.")

    question = "Write a function `calc(x: int)` that calculates 673+x"  # We can change it after we get all the data
    task = [1, 1529]  # We can change it after we get all the data

    # Add to Data Base
    with Session(engine) as db_session:
        record = Challenge(
            website=website,
            session_id=session_id,
            question=question,
            task_json=json.dumps(task),
        )
        db_session.add(record)
        db_session.flush()
        challenge_id = record.id
        db_session.commit()

    return {"challenge_id": challenge_id}
