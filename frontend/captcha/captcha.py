import json
import traceback
import urllib.parse
from base64 import b64decode
from typing import TypedDict

import panel as pn
import param
from pyodide.ffi import create_proxy
from pyodide.http import pyfetch
from pyscript import document, window  # type: ignore[reportAttributeAccessIssue]

pn.extension("ace", "codeeditor", sizing_mode="stretch_width")

body = document.body
worker = window.Worker.new("runner.js", type="module")


class GetChallengeResponse(TypedDict):
    """Response schema for /get_challenge endpoint."""

    question: str
    tasks: list[int]


class SolutionCorrectJWTPayload(TypedDict):
    """Payload data of the JWT token returned from /solution endpoint."""

    session_id: str
    challenge_id: str
    nbf: float
    exp: float
    aud: str
    iss: str
    iat: float


def get_challenge_id() -> str:
    """Get challenge_id of the challenge.

    Returns:
        str: The challenge_id extracted from the URL query parameters.

    Raises:
        ValueError: If the challenge_id is not found or is not a valid string.

    """
    parsed = urllib.parse.urlparse(window.location.href).query
    print(parsed)
    query_dict = urllib.parse.parse_qs(parsed)
    print(query_dict)
    challenge_id = query_dict.get("challenge_id")
    if isinstance(challenge_id, list) and len(challenge_id) > 0:
        challenge_id = challenge_id[0]
    if not isinstance(challenge_id, str):
        raise ValueError("Not a running challenge")  # noqa: TRY004
    return challenge_id


async def get_challenge() -> tuple[str, list[int]]:
    """Endpoint to collect challenge data.

    Returns:
        tuple[str, list[int]]: The question string and the associated task list.

    """
    challenge_id = get_challenge_id()
    request = await pyfetch(f"/api/challenge/get-challenge/{challenge_id}")
    if not request.ok:
        return ("Not a question [Question cannot be fetched]", [1])
    response: GetChallengeResponse = await request.json()
    return (response["question"], response["tasks"])


def _to_int(x: str) -> int:
    try:
        return int(x)
    except ValueError:
        return int(float(x))


async def _worker_on_message(e) -> None:  # noqa: ANN001
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
    """Submit the code to be executed locally with the given task."""
    get_challenge_id()
    worker.postMessage(json.dumps({"code": code, "task": task}))


async def send_result(results: list[int]) -> bool:
    """Send the calculated result to CAPTCHA service to obtain the JWT.

    Returns:
        bool: True if the result was successfully sent and a valid JWT was received, False otherwise.

    """
    req_data = json.dumps(
        {
            "challenge_id": get_challenge_id(),
            "answers": list(results),  # in case this is a JsProxy
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
    if len(splitted) != 3:  # noqa: PLR2004
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
    """A trigger on whether the pyodide have been loaded."""

    has_loaded = param.Boolean()

    @param.depends("has_loaded")
    def render(self) -> pn.Spacer | None:
        """Update visibility of component on pyodide load."""
        print(self.has_loaded)
        if self.has_loaded:  # type: ignore[reportGeneralTypeIssues]
            initial_verify.visible = True
            initial_loading.visible = False
        return None
        return pn.Spacer(width=0)


loaded_item = PyodideHasLoaded()
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
code_editor = pn.widgets.CodeEditor(
    value="""
def calc(x: int) -> int:
    # Your implementation here
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


def _set_initial_visibility(status: bool) -> None:  # noqa: FBT001
    initial_label.visible = status
    initial_verify.visible = status


def _set_after_visibility(status: bool) -> None:  # noqa: FBT001
    question.visible = status
    progress_bar.visible = status
    code_editor.visible = status
    submit_button.visible = status
    error_str.visible = status


async def _click_initial_verify(_) -> None:  # noqa: ANN001
    global tasks
    _set_initial_visibility(False)  # noqa: FBT003
    question_loading.visible = True
    _set_after_visibility(True)  # noqa: FBT003
    question_str, tasks = await get_challenge()
    question.object = question_str
    question_loading.visible = False
    _set_after_visibility(True)  # noqa: FBT003
    progress_bar.max = len(tasks) + 2


def _click_submit(_) -> None:  # noqa: ANN001
    code_string: str = code_editor.value  # type: ignore[reportAssignmentType]
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

_set_after_visibility(False)  # noqa: FBT003

pn.Column(
    initial,
    question_loading,
    after,
    loaded_item.render,
    sizing_mode="stretch_width",
).servable(target="captcha")
