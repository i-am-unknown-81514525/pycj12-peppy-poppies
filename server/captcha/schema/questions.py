from msgspec import Struct

type Ranges = dict[str, tuple[int, int]]

class Part(Struct):
    """A part in question_set.json."""
    question: str
    validator: str
    range: Ranges

class Question(Part):
    """A question in question_set.json."""
    input: tuple[int, int]


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
