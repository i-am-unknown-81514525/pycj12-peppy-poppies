from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine


class Challenge(SQLModel, table=True):
    """Model for challenges (SQLModel)."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    website: str = Field(max_length=255)
    session_id: str = Field(max_length=255)
    question: str
    task_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GenerateChallengeResponse(SQLModel, table=False):
    """Response shema for /generate_challenge endpoint."""

    challenge_id: uuid.UUID


DATABASE_URL = "sqlite:///./captcha.db"
engine = create_engine(DATABASE_URL, echo=False)

# Create tables
SQLModel.metadata.create_all(engine)


app = FastAPI(title="Captcha Service")


@app.get("/generate_challenge")
def generate_challenge(
    website: Annotated[str, Query(...)],
    session_id: Annotated[str, Query(...)],
) -> GenerateChallengeResponse:
    """Create a challenge."""
    if not website or not session_id:
        raise HTTPException(status_code=400, detail="Both 'website' and 'session_id' query parameters are required.")

    question = "Write a function `calc(x: int)` that calculates 673+x"  # We can change it after we get all the data
    task = [1, 1529]  # We can change it after we get all the data

    # Add to database
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

    return GenerateChallengeResponse(challenge_id=challenge_id)
