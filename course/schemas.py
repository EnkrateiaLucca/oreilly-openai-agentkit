"""Schema validation and source checks are distinct from factual verification."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Citation(StrictModel):
    source_id: str
    quote: str


class Claim(StrictModel):
    text: str
    evidence: Citation


class ResearchBrief(StrictModel):
    title: str
    claims: list[Claim]
    not_found: list[str]
    limitations: list[str]
    action: Literal["none", "approval_required", "denied"]


class PaperData(StrictModel):
    title: str
    authors: list[str]
    abstract_summary: str
    supporting_quote: str
    missing_fields: list[str]


class Usage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None

    def add(self, value):
        if value is None:
            return
        data = value if isinstance(value, dict) else value.model_dump()
        for key in ("input_tokens", "output_tokens"):
            if data.get(key) is not None:
                setattr(self, key, (getattr(self, key) or 0) + data[key])
        detail = data.get("input_tokens_details") or {}
        if detail.get("cached_tokens") is not None:
            self.cached_tokens = (self.cached_tokens or 0) + detail["cached_tokens"]


class RunResult(BaseModel):
    runtime: str
    model: str | None
    brief: ResearchBrief
    markdown: str
    usage: Usage = Field(default_factory=Usage)
    latency_seconds: float
    estimated_model_cost_usd: float | None = None
    tool_calls: list[dict] = Field(default_factory=list)
    citation_errors: list[str] = Field(default_factory=list)
    # Passing quote checks does not prove that a paraphrase follows from that quote.
    semantic_review: str = "required"


def normalize(text: str) -> str:
    return " ".join(text.split())


def check_citations(brief: ResearchBrief, sources: dict[str, str]) -> list[str]:
    errors = []
    if not brief.claims and not brief.not_found:
        errors.append("No claims and no explicit missing evidence.")
    for claim in brief.claims:
        source = sources.get(claim.evidence.source_id)
        quote = normalize(claim.evidence.quote)
        if not source or len(quote) < 12 or quote not in normalize(source):
            errors.append(f"Unsupported quotation: {claim.evidence.source_id}")
    return errors


def safe_text(value: str) -> str:
    # Keep model text as text: no HTML, links, images, or Markdown impersonation.
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", value.replace("<", "&lt;"))


def render_markdown(brief: ResearchBrief) -> str:
    lines = [f"# {safe_text(brief.title)}", "", "## Supported claims", ""]
    for index, claim in enumerate(brief.claims, 1):
        lines += [f"- {safe_text(claim.text)} [{index}]", ""]
    for heading, values in [("Not found", brief.not_found), ("Limitations", brief.limitations)]:
        lines += [f"## {heading}", ""] + [f"- {safe_text(v)}" for v in values] + [""]
    lines += ["## Evidence", ""]
    for index, claim in enumerate(brief.claims, 1):
        lines += [
            f"[{index}] {safe_text(claim.evidence.source_id)}: “{safe_text(claim.evidence.quote)}”",
            "",
        ]
    lines += [f"Action: {brief.action}", ""]
    return "\n".join(lines)
