import json
import urllib.parse
from base64 import b64decode
from typing import TypedDict

from pyodide.ffi import create_proxy
from pyodide.http import pyfetch
from pyscript import document, window, display, when  # type: ignore[reportAttributeAccessIssue]
import panel as pn
import param

pn.extension("ace", "codeeditor", sizing_mode="stretch_width")

body = document.body
worker = window.Worker.new("/static/runner.js", type="module")

class GetChallengeResponse(TypedDict):
    """Response schema for /get_challenge endpoint."""

    question: str
    task: list[int]


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
    """Get challenge_id of the challenge."""
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
    """Endpoint to collect challenge data."""
    challenge_id = get_challenge_id()
    request = await pyfetch(f"/api/challenge/get-challenge/{challenge_id}")
    response: GetChallengeResponse = await request.json()
    return (response["question"], response["task"])

async def worker_on_message(e) -> None:
    content: str = e.data
    key, value = content.split(";", maxsplit=1)
    challenge_id = get_challenge_id()
    if key == "result":
        result = await send_result(json.loads(value))
        progress_bar.value = progress_bar.max
        if result:
            progress_bar.bar_color = "success"
        else:
            progress_bar.bar_color = "danger"
    elif key == "load":
        progress_bar.value = 1
    elif key == "run":
        progress_bar.value = 1 + int(value)
    elif key == "pyodide-loaded":
        print("Pyodide loaded")
        loaded_item.has_loaded = True


async def submit(code: str, task: list[int]) -> None:
    """Submit the code to be executed locally with the given task."""
    challenge_id = get_challenge_id()
    worker.postMessage(json.dumps({"code": code, "task": task}))


async def send_result(results: list[int]) -> bool:
    """Send the calculated result to CAPTCHA service to obtain the JWT."""
    challenge_id = get_challenge_id()
    req_data = json.dumps(
        {
            "solutions": list(results),  # in case this is a JsProxy
        },
    )
    response = await pyfetch(f"/api/challenge/submit-challenge/{challenge_id}", method="POST", body=req_data)
    if not response.ok:
        return False
    jwt = await response.text()
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

window.get_challenge = create_proxy(get_challenge)
window.submit = create_proxy(submit)
worker.onmessage = create_proxy(worker_on_message)

class PyodideHasLoaded(param.Parameterized):
    has_loaded = param.Boolean()

    @param.depends("has_loaded")
    def render(self):
        print(self.has_loaded)
        if self.has_loaded:  # type: ignore[reportGeneralTypeIssues]
            initial_verify.visible = True
            initial_loading.visible = False


loaded_item = PyodideHasLoaded()
initial_label = pn.pane.Str("Verify for are human")
initial_verify = pn.widgets.Button(name='Verify', button_type='primary', visible=False)
question = pn.pane.Str("")
initial_loading = pn.indicators.LoadingSpinner(size=20, value=True, color="secondary", bgcolor='light', visible=True)
question_loading = pn.indicators.LoadingSpinner(size=20, value=True, color="secondary", bgcolor='light', visible=False)
code_editor = pn.widgets.CodeEditor(value="""
def calc(x: int) -> int:
    # Your implementation here
    pass
""", language='python', theme='monokai', name="Put your solution here:")
submit_button = pn.widgets.Button(name='Submit', button_type='primary', visible=False)
progress_bar = pn.indicators.Progress(name='Progress', value=0, width=200, max=3, bar_color="primary")
tasks: list[int] = []

def _set_initial_visibility(status: bool):
    initial_label.visible = status
    initial_verify.visible = status

def _set_after_visibility(status: bool):
    question.visible = status
    progress_bar.visible = status
    code_editor.visible = status
    submit_button.visible = status

async def click_initial_verify(_):
    global tasks
    _set_initial_visibility(False)
    question_loading.visible = True
    question_str, tasks = await get_challenge()
    question.object = question_str
    question_loading.visible = False
    _set_after_visibility(True)
    progress_bar.max = len(tasks) + 2


async def click_submit():
    code_string: str = code_editor.value  # type: ignore[reportAssignmentType]
    submit_button.disabled = True
    await submit(code_string, tasks)


initial_verify.on_click(click_initial_verify)

initial = pn.Row(
    initial_label,
    initial_verify,
    initial_loading,
    loaded_item.render,
)

after = pn.Column(
    question,
    code_editor,
    progress_bar,
    submit_button
)

_set_after_visibility(False)

pn.Column(
    initial,
    question_loading,
    after,
).servable(target="captcha")
# pn.pane.Str("Hello from Panel!").servable(target="captcha")
