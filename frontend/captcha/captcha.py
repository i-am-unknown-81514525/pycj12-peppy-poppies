import json
import traceback
import urllib.parse
from base64 import b64decode
from typing import TypedDict

import panel as pn
import param
from pyodide.ffi import create_proxy
from pyodide.http import pyfetch
from pyscript import document, window

pn.extension("ace", "codeeditor", sizing_mode="stretch_width")

body = document.body
worker = window.Worker.new("runner.js", type="module")


class GetChallengeResponse(TypedDict):
    question: str
    tasks: list[int]


class SolutionCorrectJWTPayload(TypedDict):
    session_id: str
    challenge_id: str
    nbf: float
    exp: float
    aud: str
    iss: str
    iat: float


def get_challenge_id() -> str:
    parsed = urllib.parse.urlparse(window.location.href).query
    print(parsed)
    query_dict = urllib.parse.parse_qs(parsed)
    print(query_dict)
    challenge_id = query_dict.get("challenge_id")
    if isinstance(challenge_id, list) and len(challenge_id) > 0:
        challenge_id = challenge_id[0]
    if not isinstance(challenge_id, str):
        raise ValueError("Not a running challenge")
    return challenge_id


async def get_challenge() -> tuple[str, list[int]]:
    challenge_id = get_challenge_id()
    request = await pyfetch(f"/api/challenge/get-challenge/{challenge_id}")
    if not request.ok:
        error_image = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48dGV4dCB4PSIyMCIgeT0iNDAiIGZvbnQtZmFtaWx5PSJtb25vc3BhY2UiIGZvbnQtc2l6ZT0iMTQiPkVycm9yOiBRdWVzdGlvbiBjYW5ub3QgYmUgZmV0Y2hlZDwvdGV4dD48L3N2Zz4="
        return (error_image, [1])
    response: GetChallengeResponse = await request.json()
    return (response["question"], response["tasks"])


<<<<<<< HEAD
def _to_int(x: str) -> int:
    try:
        return int(x)
    except ValueError:
        return int(float(x))


async def _worker_on_message(e) -> None:  # noqa: ANN001
=======
async def _worker_on_message(e) -> None:
>>>>>>> 7f71c10 (Update captcha.py to accomodate images)
    content: str = e.data
    key, value = content.split(";", maxsplit=1)
    get_challenge_id()
    if key == "result":
        values = []
        try:
            values = list(map(_to_int, json.loads(value)))
        except Exception:  # noqa: BLE001 alternative logging method
            print("Conversion failed: ")
            error_str.object = traceback.format_exc()
            progress_bar.bar_color = "danger"
            submit_button.disabled = False
        result = await send_result(values)
        progress_bar.value = progress_bar.max
        if result:
            progress_bar.bar_color = "success"
        else:
            progress_bar.bar_color = "danger"
    elif key == "load":
        progress_bar.value = 1
    elif key == "start":
        progress_bar.bar_color = "primary"
        progress_bar.value = 0
        error_str.object = ""
    elif key == "run":
        progress_bar.value = 1 + int(value)
    elif key == "error":
        progress_bar.bar_color = "danger"
        submit_button.disabled = False
        error_str.object = value

    elif key == "pyodide-loaded":
        print("Pyodide loaded")
        loaded_item.has_loaded = True


def submit(code: str, task: list[int]) -> None:
    get_challenge_id()
    worker.postMessage(json.dumps({"code": code, "task": task}))


async def send_result(results: list[int]) -> bool:
    req_data = json.dumps(
        {
            "challenge_id": get_challenge_id(),
            "answers": list(results),
        },
    )
    response = await pyfetch(
        "/api/challenge/submit-challenge",
        method="POST",
        body=req_data,
    )
    if not response.ok:
        submit_button.disabled = False
        return False
    try:
        jwt = (await response.json())["token"]
    except json.JSONDecodeError:
        submit_button.disabled = False
        return False
    splitted = jwt.split(".")
    if len(splitted) != 3:
        submit_button.disabled = False
        return False
    payload_str = b64decode(splitted[1] + "=" * (4 - len(splitted[1]) % 4)).decode()
    payload: SolutionCorrectJWTPayload = json.loads(payload_str)
    origin = payload["aud"]
    if not origin.startswith("http://") and not origin.startswith("https://"):
        origin = f"https://{origin}"
    window.parent.postMessage(jwt, origin)
    return True


worker.onmessage = create_proxy(_worker_on_message)


class PyodideHasLoaded(param.Parameterized):
    has_loaded = param.Boolean()

    @param.depends("has_loaded")
<<<<<<< HEAD
    def render(self) -> pn.Spacer | None:
        """Update visibility of component on pyodide load."""
=======
    def render(self) -> None:
>>>>>>> 7f71c10 (Update captcha.py to accomodate images)
        print(self.has_loaded)
        if self.has_loaded:
            initial_verify.visible = True
            initial_loading.visible = False
        return None
        return pn.Spacer(width=0)

#changed some stuff to accomodate the images, the margins can be wiggled with

loaded_item = PyodideHasLoaded()
<<<<<<< HEAD
initial_label = pn.pane.Str(
    "Verify you are human",
    align=("start", "center"),
    styles={"text-wrap": "pretty"},
    min_width=150,
)
initial_verify = pn.widgets.Button(
    name="Verify",
    button_type="primary",
    visible=False,
    align=("end", "center"),
)
question = pn.pane.Str("", styles={"text-wrap": "pretty"}, sizing_mode="stretch_width")
initial_loading = pn.indicators.LoadingSpinner(
    size=20,
    value=True,
    color="secondary",
    bgcolor="light",
    visible=True,
)
question_loading = pn.indicators.LoadingSpinner(size=20, value=True, color="secondary", bgcolor="light", visible=False)
=======
initial_label = pn.pane.Str("Verify for are human", margin=(0, 25), align=("start", "center"))
initial_verify = pn.widgets.Button(name="Verify", button_type="primary", visible=False, align=("end", "center"))

question = pn.pane.Image(
    sizing_mode="stretch_width",
    height=300,
    margin=(10, 0)
)

initial_loading = pn.indicators.LoadingSpinner(size=18, value=True, color="secondary", bgcolor="light", visible=True)
question_loading = pn.indicators.LoadingSpinner(size=18, value=True, color="secondary", bgcolor="light", visible=False)
>>>>>>> 7f71c10 (Update captcha.py to accomodate images)
code_editor = pn.widgets.CodeEditor(
    value="""
def calc(x: int) -> int:
    pass
""",
    language="python",
    theme="monokai",
    name="Put your solution here:",
    sizing_mode="stretch_width",
)
submit_button = pn.widgets.Button(name="Submit", button_type="primary", visible=False, sizing_mode="stretch_width")
progress_bar = pn.indicators.Progress(
    name="Progress",
    value=0,
    max=3,
    bar_color="primary",
    sizing_mode="stretch_width",
)
error_str = pn.pane.Str("", sizing_mode="stretch_width")
tasks: list[int] = []


def _set_initial_visibility(status: bool) -> None:
    initial_label.visible = status
    initial_verify.visible = status


def _set_after_visibility(status: bool) -> None:
    question.visible = status
    progress_bar.visible = status
    code_editor.visible = status
    submit_button.visible = status
    error_str.visible = status


async def _click_initial_verify(_) -> None:
    global tasks
    _set_initial_visibility(False)
    question_loading.visible = True
    _set_after_visibility(True)

    question_image_data, tasks = await get_challenge()

    question.object = question_image_data

    question_loading.visible = False
    _set_after_visibility(True)
    progress_bar.max = len(tasks) + 2


def _click_submit(_) -> None:
    code_string: str = code_editor.value
    print(f"{code_string=} {code_editor.value_input=}")
    submit_button.disabled = True
    submit(code_string, tasks)


initial_verify.on_click(_click_initial_verify)
submit_button.on_click(_click_submit)

initial = pn.Row(
    initial_label,
    initial_verify,
    initial_loading,
    sizing_mode="stretch_width",
)


after = pn.Column(question, code_editor, progress_bar, submit_button, error_str)

_set_after_visibility(False)

pn.Column(
    initial,
    question_loading,
    after,
    loaded_item.render,
    sizing_mode="stretch_width",
).servable(target="captcha")
