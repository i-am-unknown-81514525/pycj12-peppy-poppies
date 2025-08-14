from os import getenv
from pathlib import Path
from shutil import copytree, rmtree

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

rmtree(Path("./dist"), ignore_errors=True)  # remove the folder whether exist or not
copytree(Path("./frontend"), "./dist/frontend")

index_html_path: Path = Path("./dist") / "frontend" / "demo" / "index.html"

if index_html_path.exists():
    with index_html_path.open("r") as fp:
        content = fp.read()

    content = content.replace("[domain]", getenv("CODECAPTCHA_DOMAIN", "localhost:8001"))

    with index_html_path.open("w") as fp:
        fp.write(content)

app_js_path: Path = Path("./dist") / "frontend" / "demo" / "app.js"

if index_html_path.exists():
    with index_html_path.open("r") as fp:
        content = fp.read()

    content = content.replace("[domain]", getenv("CODECAPTCHA_DOMAIN", "localhost:8001"))

    with index_html_path.open("w") as fp:
        fp.write(content)
