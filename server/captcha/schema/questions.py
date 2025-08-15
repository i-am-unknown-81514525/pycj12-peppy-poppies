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
    base: Question
    part: Part
    init: list[str]
    cont: list[str]
