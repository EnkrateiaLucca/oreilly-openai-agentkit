"""Deterministic rehearsal, explicitly NOT a recorded or simulated model evaluation."""

import re

from course.runtimes.base import ResearchRuntime
from course.schemas import Citation, Claim, ResearchBrief, Usage, normalize


class OfflineRuntime(ResearchRuntime):
    name = "offline"

    async def _run(self, prompt, emit):
        query = re.search(r"lookup=([^;]+)", prompt)
        query = query.group(1) if query else "Context Engineering"
        page = self.tools.dispatch("read_paper", {"page": 1})
        records = self.tools.dispatch("lookup_paper", {"query": query})
        emit({"type": "tool", "name": "read_paper", "message": "Local rehearsal tool"})
        emit({"type": "tool", "name": "lookup_paper", "message": "Local rehearsal tool"})
        claims, missing = [], []
        if page.get("found"):
            quote = normalize(page["text"]).split("\n")[0][:160]
            claims.append(
                Claim(
                    text=f"The supplied page includes: {quote}",
                    evidence=Citation(source_id="paper:1", quote=quote),
                )
            )
        else:
            missing.append("Paper evidence not found; page missing or reader unavailable.")
        if records.get("found"):
            record = records["records"][0]
            quote = normalize(record["abstract_summary"])[:220]
            claims.append(
                Claim(
                    text=f"The secondary record states: {quote}",
                    evidence=Citation(source_id=record["source_id"], quote=quote),
                )
            )
        else:
            missing.append("Related record not found; query unmatched or lookup unavailable.")
        if "one supported claim" in prompt:
            claims = claims[:1]
        action = "none"
        if "publish" in prompt.casefold():
            self.tools.dispatch("publish_brief", {"title": "Research brief"})
            action = "approval_required"
        return ResearchBrief(
            title="Research brief — offline rehearsal",
            claims=claims,
            not_found=missing,
            limitations=[
                "Deterministic rehearsal; no model inference occurred.",
                "CSV records are secondary summaries; verify against the original paper.",
            ],
            action=action,
        ), Usage(input_tokens=0, output_tokens=0, cached_tokens=0)
