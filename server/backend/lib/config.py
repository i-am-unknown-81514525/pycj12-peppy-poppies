import os
from datetime import UTC, datetime, timedelta
from os import getenv
from typing import Any
from urllib.parse import urlparse

from crypto.jwt_generate import JWTValidator
from crypto.key import load_pem_public_key
from dotenv import load_dotenv
from httpx import Client
from litestar import Litestar, Request
from litestar.connection import ASGIConnection
from litestar.plugins.sqlalchemy import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from litestar.security.jwt import JWTCookieAuth, Token
from litestar.stores.memory import MemoryStore
from server.backend.lib.dependencies import provide_user_service
from server.backend.models import User

load_dotenv(override=True)

captcha_server = getenv("CODECAPTCHA_DOMAIN_INTERNAL")
if not captcha_server:
    captcha_server = getenv("CODECAPTCHA_DOMAIN", "http://localhost:8001")

# Advanced Alchemy
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string="sqlite+aiosqlite:///demo_data/backend.sqlite",
    session_config=AsyncSessionConfig(expire_on_commit=False),
    before_send_handler="autocommit",
    create_all=True,
)
alchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)


# Auth
async def _retrieve_user_handler(
    token: Token,
    _: ASGIConnection[Any, Any, Any, Any],
) -> User | None:
    async with sqlalchemy_config.get_session() as db_session:
        users_service = await anext(provide_user_service(db_session))

        return await users_service.get_one_or_none(id=token.sub)


jwt_cookie_auth = JWTCookieAuth[User](
    retrieve_user_handler=_retrieve_user_handler,
    token_secret=os.getenv("SECRET_KEY", "my_secret_key"),
    default_token_expiration=timedelta(hours=1),
    exclude=["/schema"],
    samesite="strict",
    secure=True,
)

# Memory Store
store = MemoryStore()


async def after_response(request: Request) -> None:
    """Clear expired items from the memory store after a response.

    Args:
        request (Request): The incoming request object.

    """
    now = datetime.now(tz=UTC)
    last_cleared = request.app.state.get("store_last_cleared", now)
    if datetime.now(tz=UTC) - last_cleared > timedelta(seconds=30):
        await store.delete_expired()
    request.app.state["store_last_cleared"] = now


# Load public key from CAPTCHA server and store it in the app state.
def load_pub_key(app: Litestar) -> None:  # noqa: D103
    with Client() as client:
        resp = client.get(f"{captcha_server}/api/challenge/get-public-key")
        data = resp.read()
    key = load_pem_public_key(data, None)

    parsed_url = urlparse(captcha_server)
    domain = parsed_url.netloc or captcha_server

    jwt_validator = JWTValidator(issuer=domain, public_key=key)

    app.state["jwt_validator"] = jwt_validator


async def create_initial_user(_: Litestar) -> None:  # noqa: D103
    async with sqlalchemy_config.get_session() as db_session:
        users_service = await anext(provide_user_service(db_session))

        user = await users_service.get_one_or_none(username="codejam12")

        if not user:
            user = await users_service.create(
                data={
                    "username": "codejam12",
                    "password": "py-discord",
                },
            )
            await db_session.commit()
