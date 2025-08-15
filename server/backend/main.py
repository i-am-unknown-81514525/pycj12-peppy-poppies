from os import getenv

from advanced_alchemy.exceptions import DuplicateKeyError, NotFoundError, RepositoryError
from crypto.key import load_pem_public_key
from httpx import Client
from litestar import Litestar
from litestar.datastructures import State
from litestar.exceptions import ClientException, NotAuthorizedException, NotFoundException
from litestar.logging import LoggingConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.static_files import create_static_files_router
from server.backend.controller.auth import AuthController
from server.backend.lib.config import alchemy_plugin
from server.backend.lib.utils import exception_handler

CAPTCHA_SERVER = getenv("CODECAPTCHA_DOMAIN_INTERNAL", getenv("CODECAPTCHA_DOMAIN", "http://localhost:8001"))


def load_pub_key(app: Litestar) -> None:  # noqa: D103
    with Client() as client:
        resp = client.get(f"{CAPTCHA_SERVER}/api/challenge/get-public-key")
        data = resp.read()
    key = load_pem_public_key(data, None)
    app.state["pub_key"] = key


app = Litestar(
    debug=True,
    route_handlers=[
        AuthController,
        create_static_files_router(path="/", directories=["dist/frontend/demo"], html_mode=True),
    ],
    plugins=[alchemy_plugin],
    on_startup=[load_pub_key],
    openapi_config=OpenAPIConfig(
        title="Backend API",
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
    state=State(),
)
