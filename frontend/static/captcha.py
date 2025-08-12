import json
import urllib.parse
from base64 import b64decode
from typing import TypedDict

from pyodide.ffi import create_proxy
from pyodide.http import pyfetch
from pyscript import document, window, display, when  # type: ignore[reportAttributeAccessIssue]
import panel as pn
import param

body = document.body
worker = window.Worker.new("/static/runner.js", {"type": "module"})

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
    query_dict = urllib.parse.parse_qs(parsed)
    challenge_id = query_dict.get("challenge_id")
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
    key, value = content.split(",", maxsplit=1)
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
    has_loaded = param.Boolean(precedence=-1.0)

    @param.depends("has_loaded")
    def render(self):
        if self.has_loaded:  # type: ignore[reportGeneralTypeIssues]
            return initial_verify
        else:
            return pn.indicators.LoadingSpinner(size=20, value=True, color="secondary", bgcolor='light')


loaded_item = PyodideHasLoaded()
initial_verify = pn.widgets.Button(name='Verify', button_type='primary')
question = pn.pane.Str("")
question_loading = pn.indicators.LoadingSpinner(size=20, value=True, color="secondary", bgcolor='light', visible=False)
code_editor = pn.widgets.CodeEditor(value="""
def calc(x: int) -> int:
    # Your implementation here
    pass
""", language='python', theme='monokai', name="Put your solution here:")
submit_button = pn.widgets.Button(name='Submit', button_type='primary', visible=False)
progress_bar = pn.indicators.Progress(name='Progress', value=0, width=200, max=3, bar_color="primary")
tasks: list[int] = []

async def click_initial_verify(_):
    global tasks
    initial.visible = False
    question_loading.visible = True
    question_str, tasks = await get_challenge()
    question.object = question_str
    question_loading.visible = False
    after.visible = True
    progress_bar.max = len(tasks) + 2


async def click_submit():
    code_string: str = code_editor.value  # type: ignore[reportAssignmentType]
    submit_button.disabled = True
    await submit(code_string, tasks)


initial_verify.on_click(click_initial_verify)

initial = pn.Row(
    pn.pane.Str("Very for are human"),
    pn.panel(loaded_item)
)

after = pn.Column(
    question,
    code_editor,
    progress_bar,
    submit_button
)

pn.Column(
    initial,
    question_loading,
    after
).servable(target="captcha")
