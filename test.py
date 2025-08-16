from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from msgspec.json import decode
from server.captcha.lib.utils import QuestionSet, question_generator

load_dotenv()

CONFIG_PATH = Path(getenv("KEY_PATH", "./captcha_data"))

with (CONFIG_PATH / "question_set.json").open("rb") as fp:
    question_set = decode(fp.read(), type=QuestionSet)

i = 0
while True:
    question_generator(question_set, i)
    i += 1
    if i % 100 == 0:
        print(i)
