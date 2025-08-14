import anyio
from litestar import Response, get, MediaType
from litestar.controller import Controller
from litestar.status_codes import HTTP_200_OK


class WebController(Controller):
    include_in_schema = False

    @get("/styles.css", operation_id="WebIndex", status_code=HTTP_200_OK)
    async def styles_css(self) -> Response[str]:
        file_path = anyio.Path("frontend/demo/styles.css")

        async with await anyio.open_file(file_path) as file:
            return Response(content=await file.read(), status_code=HTTP_200_OK, media_type=MediaType.CSS)

    @get("/app.js", operation_id="WebIndex", status_code=HTTP_200_OK)
    async def app_js(self) -> Response[str]:
        file_path = anyio.Path("frontend/demo/app.js")

        async with await anyio.open_file(file_path) as file:
            return Response(content=await file.read(), status_code=HTTP_200_OK, media_type="text/javascript")

    @get(["/", "/{path:path}"], operation_id="WebIndex", status_code=HTTP_200_OK)
    async def index(self) -> Response[str]:
        file_path = anyio.Path("frontend/demo/index.html")

        async with await anyio.open_file(file_path) as file:
            return Response(content=await file.read(), status_code=HTTP_200_OK, media_type=MediaType.HTML)
