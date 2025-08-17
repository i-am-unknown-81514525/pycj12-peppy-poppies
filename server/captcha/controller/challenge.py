from pathlib import Path

from typing import TYPE_CHECKING
from uuid import UUID

import os

import platform

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



KEY_PATH = Path(os.getenv("KEY_PATH", "./captcha_data"))


def get_cross_platform_font(font_size: int = 16):
    """Get the best available monospace font across platforms."""
    system = platform.system().lower()
    
    if system == 'windows':
        font_candidates = [
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/cour.ttf", 
            "Consolas", "Courier New"
        ]
    elif system == 'darwin':  # mac
        font_candidates = [
            "/System/Library/Fonts/Monaco.ttf",
            "/System/Library/Fonts/Menlo.ttc", 
            "Monaco", "Menlo"
        ]
    else:  # linux i guess
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "DejaVuSansMono", "monospace"
        ]
    
    for font_path in font_candidates:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, font_size)
            else:
                return ImageFont.truetype(font_path, font_size)
        except (OSError, IOError):
            continue
    
    return ImageFont.load_default()

def text_to_image(text: str, width: int = 800, font_size: int = 16) -> str:
    """Convert text to base64 encoded PNG image."""
    font = get_cross_platform_font(font_size)
    
    chars_per_line = max(40, (width - 40) // (font_size // 2))
    
    wrapped_lines = []
    for line in text.split('\n'):
        if line.strip():
            wrapped = textwrap.fill(line, width=chars_per_line)
            wrapped_lines.extend(wrapped.split('\n'))
        else:
            wrapped_lines.append('')
    
    line_height = font_size + 4
    img_height = max(200, len(wrapped_lines) * line_height + 40)
    
    img = Image.new('RGB', (width, img_height), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width-1, img_height-1], outline='#ddd', width=1)
    
    y_position = 20
    for line in wrapped_lines:
        draw.text((20, y_position), line, fill='black', font=font)
        y_position += line_height
    
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=True)
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

        """Generate a new captcha challenge.

        Returns:

            GenerateChallengeResponse: The response containing the generated challenge ID.

        """

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

        self,

        challenge_service: ChallengeService,

        challenge_id: UUID,

    ) -> GetChallengeResponse:

        """Get the current captcha challenge.

        Returns:

            GetChallengeResponse: The response containing the challenge details.

        """

        challenge = await challenge_service.get_one(id=challenge_id)

        

        question_image = text_to_image(challenge.question)

        

        return GetChallengeResponse(

            question=question_image,  

            tasks=challenge.task_list,

        )



    @post("/submit-challenge")

    async def submit_challenge(

        self,

        challenge_service: ChallengeService,

        data: SubmitChallengeRequest,

        request: Request,

    ) -> Response:

        """Submit a captcha challenge.

        Returns:

            Response: A response indicating whether the challenge was solved correctly or not.

        """

        challenge = await challenge_service.get_one(id=data.challenge_id)

        if challenge.answer_list == data.answers:

            private_key = import_private_key(KEY_PATH / "private.pem")

            jwt_generator = JWTGenerator(issuer=request.headers["Host"], private_key=private_key)

            token = jwt_generator.generate(

                website=challenge.website,

                challenge_id=str(data.challenge_id),

            )

            return Response(

                status_code=status_codes.HTTP_201_CREATED,

                content={"token": token},

            )

        return Response(

            status_code=status_codes.HTTP_400_BAD_REQUEST,

            content="Challenge not solved correctly.",

        )
