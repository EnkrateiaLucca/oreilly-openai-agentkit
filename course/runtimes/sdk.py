"""The application owns execution; Runner handles the same bounded tool loop."""

import asyncio
import json

from agents import Agent, ModelSettings, OpenAIResponsesModel, RunConfig, Runner, function_tool

from course.config import api_client
from course.prompts import INSTRUCTIONS
from course.runtimes.base import ResearchRuntime
from course.schemas import ResearchBrief, Usage


class SDKRuntime(ResearchRuntime):
    name = "sdk"

    def __init__(self, settings, toolbox, client=None):
        super().__init__(settings, toolbox, client or api_client(settings))
        self.history = []
        self.active_run = None

        @function_tool
        def lookup_paper(query: str) -> str:
            """Search the fixture CSV for related paper records."""
            return json.dumps(self.tools.dispatch("lookup_paper", {"query": query}))

        @function_tool
        def read_paper(page: int) -> str:
            """Read a page of the provided PDF, returning citable evidence."""
            return json.dumps(self.tools.dispatch("read_paper", {"page": page}))

        @function_tool
        def publish_brief(title: str) -> str:
            """Request publication; separate human approval and authorization are required."""
            return json.dumps(self.tools.dispatch("publish_brief", {"title": title}))

        self.agent = Agent(
            name="Research assistant",
            instructions=INSTRUCTIONS,
            model=OpenAIResponsesModel(settings.model, self.client),
            tools=[lookup_paper, read_paper, publish_brief],
            output_type=ResearchBrief,
            model_settings=ModelSettings(
                max_tokens=settings.max_output_tokens, store=False, parallel_tool_calls=False
            ),
        )

    async def _run(self, prompt, emit):
        self.active_run = Runner.run_streamed(
            self.agent,
            self.history + [{"role": "user", "content": prompt}],
            max_turns=self.settings.max_steps,
            run_config=RunConfig(tracing_disabled=True, trace_include_sensitive_data=False),
        )
        async for event in self.active_run.stream_events():
            if event.type == "run_item_stream_event":
                emit({"type": "progress", "message": event.name})
        result = self.active_run
        # This is SDK history, not a managed session ID or a sandbox.
        self.history = result.to_input_list()
        usage = Usage()
        for response in result.raw_responses:
            usage.add(
                {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "input_tokens_details": {
                        "cached_tokens": response.usage.input_tokens_details.cached_tokens
                    },
                }
            )
        return result.final_output, usage

    async def cancel(self):
        if self.active_run:
            self.active_run.cancel()
            async with asyncio.timeout(15):
                async for _ in self.active_run.stream_events():
                    pass
