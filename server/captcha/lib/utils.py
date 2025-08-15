from typing import Optional

from advanced_alchemy.exceptions import IntegrityError, NotFoundError, RepositoryError
from advanced_alchemy.extensions.litestar.exception_handler import (
    ConflictError,
)
from litestar import Request, Response
from litestar.exceptions import (
    HTTPException,
    NotFoundException,
)
from litestar.exceptions.responses import create_exception_response
from litestar.status_codes import HTTP_409_CONFLICT, HTTP_500_INTERNAL_SERVER_ERROR
from server.captcha.schema.questions import QuestionSet


class _HTTPConflictException(HTTPException):
    """Request conflict with the current state of the target resource."""

    status_code = HTTP_409_CONFLICT


def exception_handler(  # noqa: D103
    request: Request,
    exc: Exception,
) -> Response:
    http_exc: type[HTTPException]

    if isinstance(exc, NotFoundError):
        http_exc = NotFoundException
    elif isinstance(exc, ConflictError | RepositoryError | IntegrityError):
        http_exc = _HTTPConflictException
    else:
        return create_exception_response(
            request,
            HTTPException(
                status_code=getattr(exc, "status_code", HTTP_500_INTERNAL_SERVER_ERROR),
                detail=str(exc),
            ),
        )

    return create_exception_response(request, http_exc(detail=str(exc.detail)))


def question_generator(question_set: QuestionSet, seed: Optional[int] = None):
    raise NotImplementedError("")
