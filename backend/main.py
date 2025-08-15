from litestar import Litestar, post, get
from litestar.datastructures import State
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from litestar.config.cors import CORSConfig


@get("/")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@post("/solve")
async def solve() -> dict[str, str]:
    """Handles the solving of a challenge."""
    return {"message": "Challenge received successfully"}


cors_config = CORSConfig(allow_origins=["*"])
app = Litestar(
    route_handlers=[health_check, solve],
    cors_config=cors_config,
)
