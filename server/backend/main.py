from advanced_alchemy.exceptions import DuplicateKeyError, NotFoundError, RepositoryError
from litestar import Litestar
from litestar.exceptions import ClientException, NotAuthorizedException, NotFoundException
from litestar.logging import LoggingConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.static_files import create_static_files_router
from server.backend.lib.config import alchemy_plugin
from server.backend.lib.utils import exception_handler

app = Litestar(
    debug=True,
    route_handlers=[
        create_static_files_router(path="/", directories=["dist/frontend/demo"], html_mode=True),
    ],
    plugins=[alchemy_plugin],
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
)
