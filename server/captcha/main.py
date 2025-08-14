from os import getenv
from pathlib import Path

from advanced_alchemy.exceptions import DuplicateKeyError, NotFoundError, RepositoryError
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.exceptions import ClientException, NotAuthorizedException, NotFoundException
from litestar.logging import LoggingConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.static_files import create_static_files_router

from crypto.key import generate_key_pair, export_all
from server.captcha.controller.challenge import ChallengeController
from server.captcha.lib.config import alchemy_plugin
from server.captcha.lib.utils import exception_handler

KEY_PATH = Path(getenv("KEY_PATH", "./captcha_data"))

def ensure_key(app: Litestar):
    if not (KEY_PATH / "public.pem").exists() or not (KEY_PATH / "private.pem").exists():
        (pri, pub) = generate_key_pair()
        export_all(KEY_PATH, pub_key=pub, pri_key=pri)

app = Litestar(
    debug=True,
    route_handlers=[
        ChallengeController,
        create_static_files_router(path="/static", directories=["frontend/captcha"], html_mode=True,)
    ],
    on_startup=[
        ensure_key
    ],
    plugins=[
        alchemy_plugin,
    ],
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
)
