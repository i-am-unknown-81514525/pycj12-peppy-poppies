import logging
import math
import re
import time
from collections.abc import Callable
from random import Random
from typing import TYPE_CHECKING, Literal

import sympy
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
from server.captcha.schema.questions import GeneratedQuestion, Part, Question, QuestionSection, QuestionSet

GROUP_VALUE_REGEX = r"{(dyn:)?([a-zA-Z_\-]+)}"
GROUP_VALUE_COMPILED = re.compile(GROUP_VALUE_REGEX)
LOGGER = logging.getLogger("app")


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

    def __init__(self, factory: Callable[[K], V]) -> None:
        self._factory: Callable[[K], V] = factory

    def __missing__(self, key: K) -> V:
        self[key] = self._factory(key)
        return self[key]


def fill_question(question: Question | Part, random_obj: Random) -> QuestionSection:
    """Fill the question detail with random value.

    Returns:
        QuestionSection: The filled question section with generated values.

    """

    def gen_value(val_name: str) -> int:
        if val_name in question.range:
            return random_obj.randint(*question.range[val_name])
        return random_obj.randint(1, 65536)

    values = DefaulyDictByKey(gen_value)

    def sub_function(match: re.Match) -> str:
        key: str = match.group(2)  # ignore `dyn:`
        return f"{values[key]}"

    gen_question = GROUP_VALUE_COMPILED.sub(sub_function, question.question)
    gen_validator = GROUP_VALUE_COMPILED.sub(sub_function, question.validator)
    return QuestionSection(
        question=gen_question,
        validator=gen_validator,
    )



def question_generator(question_set: QuestionSet, seed: int | None = None) -> GeneratedQuestion:  # noqa: C901, PLR0915
    """Generate a random question from QuestionSet.

    Args:
        question_set: The set of questions to generate from.
        seed: Optional seed for deterministic random generation.

    Returns:
        GeneratedQuestion: The generated question with tasks and solutions.

    Raises:
        ValueError: If `construct` or `base` placeholders are used incorrectly.

    """
    random_obj = Random(seed)  # noqa: S311 it was decided to be determistic
    construct = random_obj.choice(question_set.construct)
    validator_part: list[str] = []
    value_range: tuple[int, int] | None = None

    def sub_function(match: re.Match) -> str:
        nonlocal value_range
        key: Literal["construct", "base", "part", "init", "cont"] = match.group(2)
        match key:
            case "construct":
                raise ValueError("`construct` should not exist inside `construct`")
            case "base":
                if value_range is not None:
                    raise ValueError("`base` should not exist more than once")
                options = question_set.base
                picked = random_obj.choice(options)
                section: QuestionSection = fill_question(picked, random_obj)
                value_range = picked.input
                validator_part.insert(0, section.validator)
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
    tasks = list({random_obj.randint(*value_range) for _ in range(task_amount)})
    answers = tasks.copy()

    start = time.perf_counter()
    safe_globals = {
        "__builtins__": __builtins__,
        "abs": abs,
        "min": min,
        "max": max,
        "bin": bin,
        "int": int,
        "len": len,
        "sum": sum,
        "pow": pow,
        "math": math,
        "sympy": sympy,
        "factorial": math.factorial,
        "prime": sympy.prime,
        "fibonacci": sympy.fibonacci,
        "divisors": sympy.divisors,
        "prevprime": sympy.prevprime,
    }
    locals_dict = {}
    try:
        for fn_str in validator_part:
            exec(fn_str, safe_globals, locals_dict)  # noqa: S102 it run limited subset of questions in question_part.json
            validateor_fn: Callable[[int], int] = locals_dict["validator"]
            answers = list(map(validateor_fn, answers))
        str(answers)
    except Exception as e:
        issue_id = "".join(random_obj.choices("0123456789abcdef", k=32))
        message = f"""Failed to generate question
Questions: {question}
Tasks: {tasks}
Validators:
{"\n".join(f"  {fn!r}" for fn in validator_part)}
Seed: {seed or "N/A"}
Issue ID: {issue_id}
Delta: {time.perf_counter() - start}s
"""
        LOGGER.exception(
            message,
            exc_info=e,
        )
        question = (
            "You found an invalid question, Congrat :)"
            f"Notify server owner with issue id: `{issue_id}`. Your task is just output exactly the input"
        )
        answers = tasks.copy()
        if isinstance(e, KeyboardInterrupt):
            raise e  # noqa: TRY201
    return GeneratedQuestion(
        question=question,
        tasks=tasks,
        solutions=answers,
    )
