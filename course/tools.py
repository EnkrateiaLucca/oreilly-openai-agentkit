"""The application executes and validates tools. All runtimes reuse this module."""

import csv
import json
import unicodedata
from pathlib import Path

from pydantic import Field, ValidationError
from pypdf import PdfReader

from course.config import ROOT
from course.schemas import StrictModel


class LookupArgs(StrictModel):
    query: str = Field(min_length=1, max_length=160)


class ReadArgs(StrictModel):
    page: int = Field(ge=1, le=12, strict=True)


class PublishArgs(StrictModel):
    title: str = Field(min_length=1, max_length=180)


def folded(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def lookup_paper(query: str, csv_path: Path = ROOT / "assets/papers_database.csv") -> dict:
    """Search existing secondary summaries with normalized literal substring matching."""
    args = LookupArgs(query=query)
    query = folded(args.query.strip())
    if not query:
        raise ValueError("A nonblank query is required.")
    with csv_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    matches = []
    for index, row in enumerate(rows, 1):
        if query in folded(" ".join(row.values())):
            matches.append({"source_id": f"record:{index}", **row})
    return {
        "found": bool(matches),
        "records": matches[:3],
        "source_kind": "secondary CSV summaries",
    }


def paper_pages(path: Path = ROOT / "assets/paper.pdf") -> dict[str, str]:
    if path.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("The classroom PDF limit is 5 MiB.")
    reader = PdfReader(path)
    return {
        f"paper:{i + 1}": (p.extract_text() or "")[:12000] for i, p in enumerate(reader.pages[:12])
    }


TOOL_ARGS = {"lookup_paper": LookupArgs, "read_paper": ReadArgs, "publish_brief": PublishArgs}
DESCRIPTIONS = {
    "lookup_paper": "Search the provided paper-record CSV. Returns secondary summaries or found=false.",
    "read_paper": "Read one page of the supplied PDF. Returns page evidence with a source_id.",
    "publish_brief": "Request publication of a brief. Returns approval_required; cannot publish.",
}


def tool_definitions() -> list[dict]:
    return [
        dict(
            type="function",
            name=name,
            description=DESCRIPTIONS[name],
            parameters=schema.model_json_schema(),
            strict=True,
        )
        for name, schema in TOOL_ARGS.items()
    ]


class ToolBox:
    def __init__(self, *, pages=None, fail_tools=(), injection="", max_calls=8):
        self.pages = paper_pages() if pages is None else pages
        self.fail_tools = set(fail_tools)
        self.injection = injection
        self.max_calls = max_calls
        self.sources: dict[str, str] = {}
        self.calls: list[dict] = []
        self.turn_calls = 0

    def begin_turn(self):
        self.turn_calls = 0

    def dispatch(self, name: str, arguments: str | dict) -> dict:
        if self.turn_calls >= self.max_calls:
            raise RuntimeError("Tool-call budget exhausted.")
        self.turn_calls += 1
        try:
            if name not in TOOL_ARGS:
                raise ValueError("Unknown tool.")
            raw = json.loads(arguments) if isinstance(arguments, str) else arguments
            args = TOOL_ARGS[name].model_validate(raw)
            if name in self.fail_tools:
                raise OSError("Simulated tool outage.")
            if name == "lookup_paper":
                result = lookup_paper(args.query)
                for record in result["records"]:
                    if self.injection:
                        record["untrusted_note"] = self.injection
                    self.sources[record["source_id"]] = "\n".join(record.values())
            elif name == "read_paper":
                source_id = f"paper:{args.page}"
                content = self.pages.get(source_id, "")
                if content and self.injection:
                    content += "\n" + self.injection
                result = {"found": bool(content), "source_id": source_id, "text": content}
                if content:
                    self.sources[source_id] = content
            else:
                result = {
                    "status": "approval_required",
                    "published": False,
                    "message": "Use the application's preview and approval controls.",
                }
        except (ValueError, ValidationError, OSError, TypeError) as exc:
            result = {
                "error": type(exc).__name__,
                "message": "Tool failed; report evidence as not found.",
            }
        self.calls.append({"name": name, "arguments": arguments, "result": result})
        return result
