from msgspec import Struct, field

class Range(Struct):
    """Range of result that is valid for the question."""
    extras: dict[str, tuple[int, int]]

class RangeWithBase(Range):
    """Additional valid constraint on the tasks given to the human."""
    base: tuple[int, int] = field(name="__base__")

class _Question(Struct):
    question: str
    validator: str

class Question(_Question):
    """A question in question_set.json."""
    range: RangeWithBase

class Part(_Question):
    """A part in question_set.json."""
    range: Range

class QuestionSet(Struct):
    """Schema for question_set.json."""
    construct: list[str]
    base: list[Question]
    part: list[Part]
    init: list[str]
    cont: list[str]

class QuestionSection(Struct):
    """A generated part of question that is either a `base` or `part`."""
    question: str
    validator: str

class GeneratedQuestion(Struct):
    """A fully generated question that include the question in string form, a list of tasks for the user to solve and the list of solutions."""
    question: str
    tasks: list[int]
    solutions: list[int]
