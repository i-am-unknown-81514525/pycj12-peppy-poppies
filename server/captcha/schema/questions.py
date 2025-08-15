from msgspec import Struct

class Range(Struct):
    extras: dict[str, tuple[int, int]]

class RangeWithBase(Range):
    __base__: tuple[int, int]

class _Question(Struct):
    question: str
    validator: str

class Question(_Question):
    range: RangeWithBase

class Part(_Question):
    range: Range

class QuestionSet(Struct):
    construct: list[str]
    base: list[Question]
    part: list[Part]
    init: list[str]
    cont: list[str]

class QuestionSection(Struct):
    question: str
    validator: str

class GeneratedQuestion(Struct):
    question: str
    tasks: list[int]
    solutions: list[int]
