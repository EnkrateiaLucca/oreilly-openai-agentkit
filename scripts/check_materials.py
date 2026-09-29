"""Validate clean notebooks, local course links, and forbidden live configuration IDs."""

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []
for path in (ROOT / "notebooks").glob("*.ipynb"):
    nb = json.loads(path.read_text())
    for index, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code":
            if cell.get("outputs") or cell.get("execution_count") is not None:
                errors.append(f"{path.name} cell {index} has saved outputs")
            source = "".join(cell["source"])
            try:
                ast.parse(source)
            except SyntaxError as error:
                errors.append(f"{path.name} cell {index}: {error}")
for directory in ["docs", "lessons"]:
    for path in (ROOT / directory).rglob("*.md"):
        if path.name in {"original-plan.md"}:
            continue
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if target.startswith(("https://", "http://", "#", "mailto:", "app://")):
                continue
            target = target.split("#")[0].split(" ")[0]
            if target and not (path.parent / target).exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link {target}")
for directory in ["course", "lessons", "notebooks", "demos"]:
    for path in (ROOT / directory).rglob("*"):
        if path.is_file() and path.suffix in {".py", ".md", ".ipynb", ".tsx", ".ts"}:
            if re.search(r"\b(?:wf_|pmpt_)[a-zA-Z0-9]{10,}", path.read_text()):
                errors.append(f"{path.relative_to(ROOT)}: stale hosted workflow/prompt ID")
if errors:
    raise SystemExit("\n".join(errors))
print("Course links, notebook sources, and active configuration IDs checked.")
