from os import getenv
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID
import base64
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
import textwrap

from crypto.jwt_generate import JWTGenerator
from crypto.key import import_private_key
from litestar import Request, Response, get, post, status_codes
from litestar.controller import Controller
from litestar.di import Provide
from server.captcha.lib.dependencies import provide_challenge_service
from server.captcha.lib.services import ChallengeService
from server.captcha.lib.utils import question_generator
from server.captcha.schema.challenge import (
    GenerateChallengeRequest,
    GenerateChallengeResponse,
    GetChallengeResponse,
    SubmitChallengeRequest,
)

if TYPE_CHECKING:
    from server.captcha.schema.questions import GeneratedQuestion, QuestionSet

KEY_PATH = Path(getenv("KEY_PATH", "./captcha_data"))

def text_to_image(text: str, width: int = 800, font_size: int = 16) -> str:
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

#Wrapred the text to fit the image width

    wrapped_lines = []
    for line in text.split('\n'):
        if line.strip():
            wrapped = textwrap.fill(line, width=80)
            wrapped_lines.extend(wrapped.split('\n'))
        else:
            wrapped_lines.append('')
    
    line_height = font_size + 4
    img_height = max(200, len(wrapped_lines) * line_height + 40)
    
    img = Image.new('RGB', (width, img_height), color='white')
    draw = ImageDraw.Draw(img)
    
    y_position = 20
    for line in wrapped_lines:
        draw.text((20, y_position), line, fill='black', font=font)
        y_position += line_height
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_data = buffer.getvalue()
    buffer.close()
    
    img_base64 = base64.b64encode(img_data).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"


class ChallengeController(Controller):
    path = "/api/challenge"
    tags = ["Challenge"]
    dependencies = {
        "challenge_service": Provide(provide_challenge_service),
    }

    @post("/generate-challenge")
    async def generate_challenge(
        self,
        data: GenerateChallengeRequest,
        challenge_service: ChallengeService,
        request: Request,
    ) -> GenerateChallengeResponse:
        question_set: QuestionSet = request.app.state["question_set"]
        question: GeneratedQuestion = question_generator(question_set)
        challenge = await challenge_service.create(
            {
                "website": data.website,
                "session_id": data.session_id,
                "question": question.question,
                "tasks": str(question.tasks),
                "answers": str(question.solutions),
            },
        )
        return GenerateChallengeResponse(challenge_id=challenge.id)

    @get("/get-challenge/{challenge_id:uuid}")
    async def get_challenge(
