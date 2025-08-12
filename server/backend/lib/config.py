from litestar.plugins.sqlalchemy import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)

sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string="sqlite+aiosqlite:///backend.sqlite",
    session_config=AsyncSessionConfig(expire_on_commit=False),
    before_send_handler="autocommit",
    create_all=True,
)
alchemy_plugin = SQLAlchemyPlugin(config=sqlalchemy_config)
