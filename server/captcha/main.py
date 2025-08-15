from os import getenv
from pathlib import Path

import sympy  # noqa: F401 preload sympy
from advanced_alchemy.exceptions import DuplicateKeyError, NotFoundError, RepositoryError
from crypto.key import export_all, generate_key_pair, import_all
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.datastructures import State
from litestar.exceptions import ClientException, NotAuthorizedException, NotFoundException
from litestar.logging import LoggingConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.static_files import create_static_files_router
from msgspec.json import decode, encode
from server.captcha.controller.challenge import ChallengeController
from server.captcha.lib.config import alchemy_plugin
from server.captcha.lib.utils import exception_handler
from server.captcha.schema.questions import Question, QuestionSet

CONFIG_PATH = Path(getenv("KEY_PATH", "./captcha_data"))


def ensure_key(app: Litestar) -> None:  # noqa: D103
    if not (CONFIG_PATH / "public.pem").exists() or not (CONFIG_PATH / "private.pem").exists():
        (pri, pub) = generate_key_pair()
        export_all(CONFIG_PATH, pub_key=pub, pri_key=pri)
    (pri, pub) = import_all(CONFIG_PATH)
    app.state["pub_key"] = pub
    app.state["pri_key"] = pri


def ensure_questions(app: Litestar) -> None:  # noqa: D103
    if not (CONFIG_PATH / "question_set.json").exists():
        with (CONFIG_PATH / "question_set.json").open("wb") as fp:
            fp.write(
                encode(
                    QuestionSet(
                        construct=["{init} {dyn:base}"],
                        base=[
                            Question(
                                question="{y}+x",
                                validator="validator=lambda x:{y}+x",
                                range={"y": (-65536, 65536)},
                                input=(1, 65536),
                            ),
                        ],
                        part=[],
                        init=["Write a function `calc(x: int) -> int` to calculate"],
                        cont=[", then"],
                    ),
                ),
            )
    with (CONFIG_PATH / "question_set.json").open("rb") as fp:
        question_set = decode(fp.read(), type=QuestionSet)
    app.state["question_set"] = question_set


app = Litestar(
    debug=True,
    route_handlers=[
        ChallengeController,
        create_static_files_router(path="/static", directories=["dist/frontend/captcha"], html_mode=True),
    ],
    on_startup=[ensure_key, ensure_questions],
    plugins=[alchemy_plugin],
    openapi_config=OpenAPIConfig(
        title="Captcha API",
        version="dev",
        path="/api/schema",
        render_plugins=[ScalarRenderPlugin()],
    ),
    logging_config=LoggingConfig(
        disable_stack_trace={
            400,
            401,
            403,
            404,
            405,
            429,
            NotFoundError,
            DuplicateKeyError,
            ClientException,
            NotAuthorizedException,
            NotFoundException,
        },
        log_exceptions="always",
    ),
    exception_handlers={
        Exception: exception_handler,
        RepositoryError: exception_handler,
    },
    cors_config=CORSConfig(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
    state=State(),
)
