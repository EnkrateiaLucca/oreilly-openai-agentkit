import asyncio
import time
from collections.abc import Callable

from course.schemas import ResearchBrief, RunResult, check_citations, render_markdown


class ResearchRuntime:
    name = "base"

    def __init__(self, settings, toolbox, client=None):
        self.settings, self.tools, self.client = settings, toolbox, client
        self.turns = 0
        self.broken = False

    async def run(self, prompt: str, emit: Callable[[dict], None] = lambda _: None) -> RunResult:
        if self.broken:
            raise RuntimeError("Start a new session after an interrupted or invalid run.")
        if not prompt.strip() or len(prompt) > self.settings.max_input_chars:
            raise ValueError("Task is empty or exceeds the input limit.")
        if self.turns >= self.settings.max_user_turns:
            raise RuntimeError("Session turn limit reached. Start a new session.")
        self.turns += 1
        self.tools.begin_turn()
        start, first_call = time.monotonic(), len(self.tools.calls)
        emit({"type": "progress", "message": f"Starting {self.name} turn {self.turns}"})
        try:
            async with asyncio.timeout(self.settings.timeout_seconds):
                brief, usage = await self._run(prompt, emit)
            brief = ResearchBrief.model_validate(brief)
            errors = check_citations(brief, self.tools.sources)
            if errors:
                emit({"type": "validation_failed", "brief": brief.model_dump(), "errors": errors})
                raise ValueError("Evidence validation failed: " + "; ".join(errors))
        except BaseException as exc:
            self.broken = True
            # Closing a managed stream is not cancellation. Cancel explicitly.
            try:
                await self.cancel()
            except Exception:
                exc.add_note(
                    "Cancellation could not be confirmed; inspect the course resource manifest."
                )
            raise
        cost = None
        if self.name == "offline":
            cost = 0.0
        elif (
            usage.input_tokens is not None
            and usage.output_tokens is not None
            and self.settings.input_rate is not None
            and self.settings.output_rate is not None
        ):
            # Simplified model-only estimate; excludes sandbox/tools/cache-write/tier charges.
            cost = (
                usage.input_tokens * self.settings.input_rate
                + usage.output_tokens * self.settings.output_rate
            ) / 1_000_000
        return RunResult(
            runtime=self.name,
            model=None if self.name == "offline" else self.settings.model,
            brief=brief,
            markdown=render_markdown(brief),
            usage=usage,
            latency_seconds=round(time.monotonic() - start, 3),
            estimated_model_cost_usd=cost,
            tool_calls=self.tools.calls[first_call:],
            citation_errors=errors,
        )

    async def cancel(self):
        pass

    async def close(self):
        if self.client is not None:
            await self.client.close()
