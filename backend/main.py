from litestar import Litestar, get, post
from litestar.config.cors import CORSConfig


@get("/")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@post("/solve")
async def solve() -> dict[str, str]:
    """Handle the solving of a challenge."""
    return {"message": "Challenge received successfully"}


cors_config = CORSConfig(allow_origins=["*"])
app = Litestar(
    route_handlers=[health_check, solve],
    cors_config=cors_config,
)
