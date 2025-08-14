from os import getenv
from pathlib import Path

index_html_path: Path = Path(".") / "frontend" / "demo" / "index.html"

with index_html_path.open("r") as fp:
    content = fp.read()

content = content.replace("[domain]", getenv("CODECAPTCHA_DOMAIN", "localhost:9201"))

with index_html_path.open("w") as fp:
    fp.write(content)
