"""Managed session lifecycle, pending function calls, and root-turn completion."""

import asyncio
import base64
import json
import uuid

from openai import ConflictError

from course.config import ROOT, api_client
from course.prompts import INSTRUCTIONS
from course.runtimes.base import ResearchRuntime
from course.schemas import ResearchBrief, Usage
from course.tools import tool_definitions


def managed_agent_config(settings):
    return {
        "model": settings.model,
        "name": "Class research assistant",
        "instructions": INSTRUCTIONS + "\nYour sandbox contains /workspace/paper.pdf, paper.txt, "
        "and papers_database.csv. Inspect the workspace with a command. Use read_paper and "
        "lookup_paper for citation IDs. Do not delegate. Return the brief as JSON.",
        "tools": [{k: v for k, v in t.items() if k != "strict"} for t in tool_definitions()],
        "text": {"format": {"type": "json_schema", "schema": ResearchBrief.model_json_schema()}},
    }


class ManagedRuntime(ResearchRuntime):
    name = "managed"

    def __init__(self, settings, toolbox, client=None):
        super().__init__(settings, toolbox, client or api_client(settings))
        self.session_id = None
        self.agent_id = None
        self.completed_turn = None
        self.results = {}
        self.resource_file = ROOT / ".runtime" / "resources" / f"{uuid.uuid4().hex}.json"

    def record_resources(self):
        self.resource_file.parent.mkdir(parents=True, exist_ok=True)
        self.resource_file.write_text(
            json.dumps({"agent_id": self.agent_id, "session_id": self.session_id})
        )

    async def start(self):
        # Saved definition = reusable configuration. Session = conversation and environment.
        agent = await self.client.beta.agents.create(**managed_agent_config(self.settings))
        self.agent_id = agent.id
        self.record_resources()
        files = [
            ("paper.txt", json.dumps(self.tools.pages).encode()),
            ("papers_database.csv", (ROOT / "assets/papers_database.csv").read_bytes()),
        ]
        if self.tools.pages:
            files.append(
                (
                    "paper.pdf",
                    getattr(self, "paper_bytes", None) or (ROOT / "assets/paper.pdf").read_bytes(),
                )
            )
        session = await self.client.beta.agents.sessions.create(
            agent_id=self.agent_id,
            environment={
                "type": "openai_hosted",
                "container_size": "small",
                "network": {"access": "disabled"},
                "files": [
                    {
                        "type": "inline",
                        "path": f"/workspace/{name}",
                        "data": base64.b64encode(content).decode(),
                    }
                    for name, content in files
                ],
            },
        )
        self.session_id = session.id
        self.record_resources()

    async def _run(self, prompt, emit):
        if not self.session_id:
            await self.start()
        sessions = self.client.beta.agents.sessions
        completed = None
        # Open FIRST: streams do not replay events that occurred before connection.
        stream = await sessions.events.stream(self.session_id)
        async with stream:
            await sessions.events.create(
                self.session_id,
                idempotency_key=str(uuid.uuid4()),
                events=[
                    {
                        "type": "agent.session.input.message",
                        "input": [
                            {"role": "user", "content": [{"type": "input_text", "text": prompt}]}
                        ],
                    }
                ],
            )
            async for event in stream:
                data = event.model_dump()
                kind = data["type"]
                emit({"type": "progress", "message": kind})
                if kind == "agent.session.requires_action":
                    for action in data["session"].get("required_actions", []):
                        if action["type"] != "function_call":
                            raise RuntimeError(
                                "Unexpected managed action; stop and inspect the session."
                            )
                        key = (action["turn_id"], action["call_id"])
                        if key not in self.results:
                            output = self.tools.dispatch(action["name"], action["arguments"])
                            self.results[key] = output
                            emit(
                                {
                                    "type": "tool",
                                    "name": action["name"],
                                    "call_id": action["call_id"],
                                }
                            )
                        output = self.results[key]
                        result = {
                            "type": "agent.session.input.tool_result",
                            "turn_id": key[0],
                            "call_id": key[1],
                            "success": "error" not in output,
                        }
                        if "error" in output:
                            result["error"] = output["message"]
                        else:
                            result["output"] = json.dumps(output)
                        await sessions.events.create(self.session_id, events=[result])
                if kind in {"error", "agent.session.failed", "agent.session.environment.failed"}:
                    raise RuntimeError(
                        f"Managed session failed ({kind}). Inspect saved session history."
                    )
                turn = data.get("turn") or {}
                if turn.get("subagent_id") is not None:
                    continue
                if kind in {"agent.session.turn.failed", "agent.session.turn.cancelled"}:
                    raise RuntimeError(
                        f"Managed turn failed ({kind}). Inspect saved session history."
                    )
                if kind == "agent.session.turn.completed":
                    completed = turn
                    break
        if completed is None:
            raise RuntimeError(
                "Stream disconnected before completion. Inspect saved items before retrying."
            )
        self.completed_turn = completed["id"]
        usage = Usage()
        usage.add(completed.get("usage"))
        messages = []
        # Auto-pagination is essential. The first page need not contain the final message.
        async for item in sessions.items.list(self.session_id, order="asc"):
            data = item.model_dump()
            if (
                data.get("turn_id") == self.completed_turn
                and data.get("type") == "message"
                and data.get("role") == "assistant"
            ):
                text = "".join(
                    c.get("text", "")
                    for c in data.get("content", [])
                    if c.get("type") == "output_text"
                )
                if text:
                    messages.append(text)
        if not messages:
            raise RuntimeError("Completed turn contained no final assistant message.")
        return ResearchBrief.model_validate_json(messages[-1]), usage

    async def cancel(self):
        if self.session_id:
            # Bounded separately: cancellation must still run after the main deadline.
            async with asyncio.timeout(15):
                await self.client.beta.agents.sessions.events.create(
                    self.session_id, events=[{"type": "agent.session.input.cancel"}]
                )

    async def close(self):
        try:
            if self.session_id:
                for attempt in range(3):
                    try:
                        await self.client.beta.agents.sessions.delete(self.session_id)
                        self.session_id = None
                        self.record_resources()
                        break
                    except ConflictError:
                        if attempt == 2:
                            raise RuntimeError("Cleanup pending. Run python -m course cleanup.") from None
                        await asyncio.sleep(attempt + 1)
            if self.agent_id:
                await self.client.beta.agents.delete(self.agent_id)
                self.agent_id = None
            self.resource_file.unlink(missing_ok=True)
        finally:
            await super().close()
