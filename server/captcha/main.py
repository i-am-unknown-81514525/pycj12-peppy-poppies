from advanced_alchemy.exceptions import DuplicateKeyError, NotFoundError, RepositoryError
from litestar import Litestar
from litestar.static_files import StaticFilesConfig
import os
from litestar.config.cors import CORSConfig
from litestar.exceptions import ClientException, NotAuthorizedException, NotFoundException
from litestar.logging import LoggingConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from server.captcha.controller.challenge import ChallengeController
from server.captcha.lib.config import alchemy_plugin
from server.captcha.lib.utils import exception_handler

app = Litestar(
    debug=True,
    route_handlers=[
        ChallengeController,
    ],
    static_files_config=[
        StaticFilesConfig(
            directories=["frontend/captcha"],
            path="/static/",
            name="captcha-static",
        ),
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
