import os
from datetime import timedelta
from typing import Any

from dotenv import load_dotenv
from litestar.connection import ASGIConnection
from litestar.plugins.sqlalchemy import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from litestar.security.jwt import JWTCookieAuth, Token
from server.captcha.lib.dependencies import provide_challenge_service
from server.captcha.models import Challenge

load_dotenv(override=True)

# Advanced Alchemy
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string="sqlite+aiosqlite:///captcha.sqlite",
    session_config=AsyncSessionConfig(expire_on_commit=False),
    before_send_handler="autocommit",
    create_all=True,
)
alchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)


# Auth
async def _retrieve_challenge_handler(
    token: Token,
    _: ASGIConnection[Any, Any, Any, Any],
) -> Challenge | None:
    async with sqlalchemy_config.get_session() as db_session:
        challenges_service = await anext(provide_challenge_service(db_session))

        return await challenges_service.get_one_or_none(id=token.sub)


jwt_cookie_auth = JWTCookieAuth[Challenge](
    retrieve_user_handler=_retrieve_challenge_handler,
    token_secret=os.getenv("SECRET_KEY", "my_secret_key"),
    default_token_expiration=timedelta(hours=1),
    exclude=["/schema"],
    samesite="strict",
    secure=True,
)
