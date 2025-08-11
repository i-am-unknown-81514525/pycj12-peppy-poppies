from __future__ import annotations

import json
import uuid

import jwt
from pydantic import BaseModel
from pathlib import Path
from crypto.key import import_private_key
from crypto.jwt_generate import JWTGenerator
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Body
from sqlmodel import Field, Session, SQLModel, create_engine

KEY_DIR = Path("./crypto/keys")  # modify later
private_key = import_private_key(KEY_DIR / "pri.pem") # modify later
jwt_generator = JWTGenerator(issuer="captcha-server.com", private_key=private_key) # modify later
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


class ChallengeDetailResponse(SQLModel, table=False):
    """Response schema for /get-challenge endpoint."""

    question: str
    task: list[int]


class SolutionRequest(BaseModel):
    solutions: list[int]


class SolutionResponse(SQLModel, table=False):
    token: str


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


@app.get("/get_challenge")
def get_challenge(challenge_id: Annotated[uuid.UUID, Query(...)]) -> ChallengeDetailResponse:
    """Return the challenge details (question and task) for the given challenge_id."""
    with Session(engine) as db_session:
        challenge = db_session.get(Challenge, challenge_id)
        if challenge is None:
            raise HTTPException(status_code=404, detail="Challenge not found")

        try:
            task: list[int] = json.loads(challenge.task_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=500, detail="Corrupted challenge data") from exc

        return ChallengeDetailResponse(question=challenge.question, task=task)


@app.post("/solution", response_model=SolutionResponse)
def submit_solution(solution_req: SolutionRequest = Body(...)) -> SolutionResponse:
    token = jwt_generator.generate(
        website="placeholder-website",  # modify these values later
        session_id="placeholder-session",
        challenge_id="placeholder-challenge",
        solutions=solution_req.solutions,
    )
    return SolutionResponse(token=token)
