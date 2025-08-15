import re
from collections.abc import Callable
from typing import Optional, Literal, TYPE_CHECKING
from random import Random

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
from server.captcha.schema.questions import GeneratedQuestion, QuestionSection, QuestionSet, Question, Part

GROUP_VALUE_REGEX = r"{(dyn:)?([a-zA-Z_\-]+)}"
GROUP_VALUE_COMPILED = re.compile(GROUP_VALUE_REGEX)

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

class DefaulyDictByKey[K, V](dict[K, V]):
    """defaultdict but the factory function take the key as parameter would generate new value each time."""
    def __init__(self, factory: Callable[[K], V]):
        self._factory: Callable[[K], V] = factory

    def __missing__(self, key: K) -> V:
        self[key] = self._factory(key)
        return self[key]

def fill_question(question: Question | Part, random_obj: Random) -> QuestionSection:
    def gen_value(val_name: str):
        if val_name in question.range.extras:
            return random_obj.randint(*question.range.extras[val_name])
        return random_obj.randint(1, 65536)
    values = DefaulyDictByKey(gen_value)
    def sub_function(match: re.Match) -> str:
        key: str = match.group(2) # ignore `dyn:`
        return f"{values[key]}"
    gen_question = GROUP_VALUE_COMPILED.sub(sub_function, question.question)
    gen_validator = GROUP_VALUE_COMPILED.sub(sub_function, question.validator)
    return QuestionSection(
        question=gen_question,
        validator=gen_validator
    )



def question_generator(question_set: QuestionSet, seed: Optional[int] = None) -> GeneratedQuestion:
    random_obj = Random(seed)
    construct = random_obj.choice(question_set.construct)
    validator_part: list[str] = []
    value_range: tuple[int, int] | None = None
    def sub_function(match: re.Match) -> str:
        nonlocal value_range
        key: Literal["construct", "base", "part", "init", "cont"] = match.group(2)
        is_dyn: bool = match.group(1) is not None
        match key:
            case "construct":
                raise ValueError("`construct` should not exist inside `construct`")
            case "base":
                if value_range is not None:
                    raise ValueError("`base` should not exist more than once")
                options = question_set.base
                picked = random_obj.choice(options)
                section: QuestionSection = fill_question(picked, random_obj)
                value_range = picked.range.__base__
                validator_part.append(section.validator)
                return section.question
            case "part":
                options = question_set.part
                picked = random_obj.choice(options)
                section: QuestionSection = fill_question(picked, random_obj)
                validator_part.append(section.validator)
                return section.question
            case "init":
                return random_obj.choice(question_set.init)
            case "cont":
                return random_obj.choice(question_set.cont)
            case _:
                return match.group(0)
    question = GROUP_VALUE_COMPILED.sub(sub_function, construct)
    if TYPE_CHECKING:
        value_range = (0, 0)
    if value_range is None:
        raise ValueError("`base` should exist only once")
    task_amount = random_obj.randint(5, 12)
    tasks = list(set(random_obj.randint(*value_range) for _ in range(task_amount)))
    answers = tasks.copy()
    for validator_fn_str in validator_part:
        globals = {}
        locals = {}
        exec(validator_fn_str, globals, locals)
        validateor_fn: Callable[[int], int] = locals["validator"]
        answers = list(map(validateor_fn, answers))
    return GeneratedQuestion(
        question=question,
        tasks=tasks,
        solutions=answers
    )
