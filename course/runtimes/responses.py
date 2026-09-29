"""The tool loop, deliberately visible: model -> Python -> call result -> model."""

import json

from course.config import api_client
from course.prompts import INSTRUCTIONS
from course.runtimes.base import ResearchRuntime
from course.schemas import ResearchBrief, Usage
from course.tools import tool_definitions


class ResponsesRuntime(ResearchRuntime):
    name = "responses"

    def __init__(self, settings, toolbox, client=None):
        super().__init__(settings, toolbox, client or api_client(settings))
        self.history = []

    async def _run(self, prompt, emit):
        self.history.append({"role": "user", "content": prompt})
        usage = Usage()
        for step in range(self.settings.max_steps):
            emit({"type": "progress", "message": f"Model request {step + 1}"})
            response = await self.client.responses.create(
                model=self.settings.model,
                instructions=INSTRUCTIONS,
                input=self.history,
                tools=tool_definitions(),
                parallel_tool_calls=False,
                store=False,
                max_output_tokens=self.settings.max_output_tokens,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "ResearchBrief",
                        "strict": True,
                        "schema": ResearchBrief.model_json_schema(),
                    }
                },
            )
            usage.add(response.usage)
            if response.status != "completed":
                raise RuntimeError(f"Model response was {response.status}; no complete brief.")
            # Preserve ALL output items, including reasoning, for the next request.
            self.history.extend(item.model_dump(exclude_none=True) for item in response.output)
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                if not response.output_text:
                    raise RuntimeError("The model refused or returned no brief.")
                return ResearchBrief.model_validate_json(response.output_text), usage
            for call in calls:
                emit({"type": "tool", "name": call.name, "call_id": call.call_id})
                # THIS line executes the tool. A model function_call does not.
                output = self.tools.dispatch(call.name, call.arguments)
                self.history.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(output),
                    }
                )
        raise RuntimeError("Model-step limit reached before a final brief.")
