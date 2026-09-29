import asyncio
import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from course.runtimes.base import ResearchRuntime
from course.runtimes.managed import ManagedRuntime
from course.runtimes.offline import OfflineRuntime
from course.runtimes.responses import ResponsesRuntime
from course.runtimes.sdk import SDKRuntime
from course.tools import ToolBox


class Item:
    """Small SDK-shaped item, retaining unknown fields such as reasoning content."""

    def __init__(self, **data):
        self.data = data
        self.__dict__.update(data)

    def model_dump(self, **kwargs):
        return deepcopy(self.data)


def response(*items, text="", status="completed", usage=None):
    return SimpleNamespace(output=list(items), output_text=text, status=status, usage=usage)


@pytest.mark.asyncio
async def test_responses_keeps_reasoning_and_matches_tool_result_call_id(settings, valid_brief, page_text):
    requests = []
    responses = iter([
        response(
            Item(type="reasoning", id="reason-1", summary=[], encrypted_content="opaque-reasoning"),
            Item(type="function_call", id="item-1", call_id="call-1", name="read_paper",
                 arguments='{"page":1}'),
            usage={"input_tokens": 10, "output_tokens": 3, "input_tokens_details": {"cached_tokens": 2}},
        ),
        response(Item(type="message", role="assistant", content=[]), text=valid_brief.model_dump_json(),
                 usage={"input_tokens": 20, "output_tokens": 7}),
    ])

    async def create(**request):
        requests.append(deepcopy(request))
        return next(responses)

    client = SimpleNamespace(responses=SimpleNamespace(create=create), close=AsyncMock())
    runtime = ResponsesRuntime(settings, ToolBox(pages={"paper:1": page_text}), client)
    result = await runtime.run("Read the evidence.")
    assert len(requests) == 2
    assert requests[0]["parallel_tool_calls"] is False
    assert requests[0]["store"] is False
    assert requests[0]["text"]["format"]["strict"] is True
    assert requests[1]["input"][1]["encrypted_content"] == "opaque-reasoning"
    output = requests[1]["input"][3]
    assert output["type"] == "function_call_output"
    assert output["call_id"] == "call-1"
    assert json.loads(output["output"])["source_id"] == "paper:1"
    assert result.usage.model_dump() == {"input_tokens": 30, "output_tokens": 10, "cached_tokens": 2}
    assert result.citation_errors == []
    assert len(result.tool_calls) == 1
    assert result.estimated_model_cost_usd is None
    await runtime.close()
    client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_responses_step_limit_prevents_unbounded_tool_loop(settings, page_text):
    settings.max_steps = 2
    create = AsyncMock(return_value=response(Item(
        type="function_call", call_id="next-call", name="read_paper", arguments='{"page":1}',
    )))
    client = SimpleNamespace(responses=SimpleNamespace(create=create))
    runtime = ResponsesRuntime(settings, ToolBox(pages={"paper:1": page_text}), client)
    with pytest.raises(RuntimeError, match="Model-step limit"):
        await runtime.run("Keep reading.")
    assert create.await_count == 2
    assert runtime.broken is True
    with pytest.raises(RuntimeError, match="Start a new session"):
        await runtime.run("Try again.")
    assert create.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("status, text, message", [
    ("incomplete", "{}", "incomplete"),
    ("failed", "", "failed"),
    ("completed", "", "refused or returned no brief"),
])
async def test_responses_rejects_partial_failed_or_refused_outputs(settings, status, text, message):
    client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(
        return_value=response(text=text, status=status),
    )))
    runtime = ResponsesRuntime(settings, ToolBox(pages={}), client)
    with pytest.raises(RuntimeError, match=message):
        await runtime.run("Prepare the brief.")
    assert runtime.broken is True


@pytest.mark.asyncio
async def test_runtime_rejects_fabricated_citations(settings, valid_brief):
    client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(
        return_value=response(text=valid_brief.model_dump_json()),
    )))
    runtime = ResponsesRuntime(settings, ToolBox(pages={}), client)
    with pytest.raises(ValueError, match="Evidence validation failed"):
        await runtime.run("Prepare the brief.")
    assert runtime.broken is True


@pytest.mark.asyncio
async def test_offline_failures_report_missing_evidence_and_reset_tool_budget(settings, monkeypatch):
    from course import tools

    monkeypatch.setattr(tools, "lookup_paper", lambda query: {
        "found": False, "records": [], "source_kind": "secondary CSV summaries",
    })
    toolbox = ToolBox(pages={}, fail_tools={"read_paper"}, max_calls=2)
    runtime = OfflineRuntime(settings, toolbox)
    first = await runtime.run("Find missing evidence.")
    second = await runtime.run("Try a second evidence request.")
    for result in (first, second):
        assert result.brief.claims == []
        assert len(result.brief.not_found) == 2
        assert result.estimated_model_cost_usd == 0
        assert result.model is None
        assert len(result.tool_calls) == 2
    assert len(toolbox.calls) == 4


@pytest.mark.asyncio
async def test_timeout_marks_runtime_broken_and_attempts_cancellation(settings):
    settings.timeout_seconds = 0.01

    class SlowRuntime(ResearchRuntime):
        cancel = AsyncMock()

        async def _run(self, prompt, emit):
            await asyncio.Event().wait()

    runtime = SlowRuntime(settings, ToolBox(pages={}))
    with pytest.raises(TimeoutError):
        await runtime.run("Prepare the brief.")
    assert runtime.broken is True
    runtime.cancel.assert_awaited_once()


class EventStream:
    def __init__(self, events, log):
        self.events = events
        self.log = log

    async def __aenter__(self):
        self.log.append("stream_entered")
        return self

    async def __aexit__(self, *args):
        self.log.append("stream_closed")

    def __aiter__(self):
        return self.iterate()

    async def iterate(self):
        for event in self.events:
            yield Item(**event)


def managed_client(events, items=()):
    log, submitted = [], []

    async def stream(session_id):
        log.append("stream_opened")
        return EventStream(events, log)

    async def create(session_id, **kwargs):
        log.append("event_submitted")
        submitted.extend(deepcopy(kwargs["events"]))

    async def list_items(*args, **kwargs):
        for item in items:
            yield Item(**item)

    sessions = SimpleNamespace(
        events=SimpleNamespace(stream=stream, create=create),
        items=SimpleNamespace(list=list_items), delete=AsyncMock(),
    )
    agents = SimpleNamespace(sessions=sessions, delete=AsyncMock())
    client = SimpleNamespace(beta=SimpleNamespace(agents=agents), close=AsyncMock())
    return client, log, submitted


def managed_runtime(settings, toolbox, client, tmp_path):
    runtime = ManagedRuntime(settings, toolbox, client)
    runtime.session_id = "session-1"
    runtime.agent_id = "agent-1"
    runtime.resource_file = tmp_path / "resource.json"
    return runtime


def assistant_item(turn_id, text):
    return {"type": "message", "role": "assistant", "turn_id": turn_id,
            "content": [{"type": "output_text", "text": text}]}


@pytest.mark.asyncio
async def test_managed_deduplicates_actions_and_waits_for_root_completion(
    settings, page_text, valid_brief, tmp_path,
):
    action = {"type": "function_call", "turn_id": "root-turn", "call_id": "call-1",
              "name": "read_paper", "arguments": '{"page":1}'}
    pending = {"type": "agent.session.requires_action", "session": {"required_actions": [action]}}
    child = {"type": "agent.session.turn.completed", "turn": {"id": "child", "subagent_id": "child-agent"}}
    root = {"type": "agent.session.turn.completed", "turn": {
        "id": "root-turn", "subagent_id": None, "usage": {"input_tokens": 15, "output_tokens": 8},
    }}
    client, log, submitted = managed_client([pending, pending, child, root], [
        assistant_item("earlier-turn", "invalid old output"),
        assistant_item("child", "invalid child output"),
        assistant_item("root-turn", valid_brief.model_dump_json()),
    ])
    runtime = managed_runtime(settings, ToolBox(pages={"paper:1": page_text}), client, tmp_path)
    result = await runtime.run("Read the evidence.")
    assert log[:3] == ["stream_opened", "stream_entered", "event_submitted"]
    assert log[-1] == "stream_closed"
    assert runtime.completed_turn == "root-turn"
    assert len(runtime.tools.calls) == 1
    outputs = [event for event in submitted if event["type"] == "agent.session.input.tool_result"]
    assert len(outputs) == 2
    assert outputs[0] == outputs[1]
    assert outputs[0]["call_id"] == "call-1"
    assert outputs[0]["turn_id"] == "root-turn"
    assert outputs[0]["success"] is True
    assert result.usage.input_tokens == 15
    assert result.usage.output_tokens == 8


@pytest.mark.asyncio
async def test_managed_tool_failure_returns_error_result_and_explicit_missing_evidence(settings, tmp_path):
    events = [
        {"type": "agent.session.requires_action", "session": {"required_actions": [
            {"type": "function_call", "turn_id": "root", "call_id": "call-1",
             "name": "read_paper", "arguments": '{"page":1}'},
        ]}},
        {"type": "agent.session.turn.completed", "turn": {"id": "root", "subagent_id": None}},
    ]
    missing = json.dumps({"title": "Missing evidence", "claims": [], "not_found": ["Reader unavailable"],
                          "limitations": [], "action": "none"})
    client, _, submitted = managed_client(events, [assistant_item("root", missing)])
    runtime = managed_runtime(settings, ToolBox(pages={}, fail_tools={"read_paper"}), client, tmp_path)
    result = await runtime.run("Read unavailable evidence.")
    output = submitted[-1]
    assert output["success"] is False
    assert "error" in output and "output" not in output
    assert result.brief.claims == []
    assert result.brief.not_found


@pytest.mark.asyncio
@pytest.mark.parametrize("events, message", [
    ([], "disconnected"),
    ([{"type": "agent.session.turn.failed", "turn": {"id": "root", "subagent_id": None}}], "turn failed"),
    ([{"type": "agent.session.environment.failed"}], "session failed"),
    ([{"type": "agent.session.requires_action", "session": {"required_actions": [
        {"type": "unexpected_approval_action"},
    ]}}], "Unexpected managed action"),
])
async def test_managed_disconnect_and_failure_cancel_explicitly(settings, tmp_path, events, message):
    client, log, submitted = managed_client(events)
    runtime = managed_runtime(settings, ToolBox(pages={}), client, tmp_path)
    with pytest.raises(RuntimeError, match=message):
        await runtime.run("Prepare the brief.")
    assert runtime.broken is True
    assert "stream_closed" in log
    assert submitted[-1] == {"type": "agent.session.input.cancel"}


@pytest.mark.asyncio
async def test_managed_completed_turn_requires_a_final_message(settings, tmp_path):
    client, _, submitted = managed_client([
        {"type": "agent.session.turn.completed", "turn": {"id": "root", "subagent_id": None}},
    ])
    runtime = managed_runtime(settings, ToolBox(pages={}), client, tmp_path)
    with pytest.raises(RuntimeError, match="no final assistant message"):
        await runtime.run("Prepare the brief.")
    assert submitted[-1] == {"type": "agent.session.input.cancel"}


@pytest.mark.asyncio
async def test_managed_cleanup_deletes_owned_resources_and_manifest(settings, tmp_path):
    client, _, _ = managed_client([])
    runtime = managed_runtime(settings, ToolBox(pages={}), client, tmp_path)
    runtime.record_resources()
    assert json.loads(runtime.resource_file.read_text()) == {"agent_id": "agent-1", "session_id": "session-1"}
    await runtime.close()
    client.beta.agents.sessions.delete.assert_awaited_once_with("session-1")
    client.beta.agents.delete.assert_awaited_once_with("agent-1")
    client.close.assert_awaited_once()
    assert runtime.session_id is None
    assert runtime.agent_id is None
    assert not runtime.resource_file.exists()


@pytest.mark.asyncio
async def test_failed_managed_cleanup_retains_manifest_and_closes_client(settings, tmp_path):
    client, _, _ = managed_client([])
    client.beta.agents.sessions.delete.side_effect = RuntimeError("service unavailable")
    runtime = managed_runtime(settings, ToolBox(pages={}), client, tmp_path)
    runtime.record_resources()
    with pytest.raises(RuntimeError, match="service unavailable"):
        await runtime.close()
    assert runtime.resource_file.exists()
    assert json.loads(runtime.resource_file.read_text())["session_id"] == "session-1"
    client.beta.agents.delete.assert_not_awaited()
    client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_sdk_runner_has_bounded_turns_no_tracing_and_local_history(
    settings, valid_brief, page_text, monkeypatch,
):
    from course.runtimes import sdk

    async def stream_events():
        yield SimpleNamespace(type="run_item_stream_event", name="tool_called")

    saved_history = [{"role": "user", "content": "Read the evidence."},
                     {"role": "assistant", "content": valid_brief.model_dump_json()}]
    streamed = SimpleNamespace(
        stream_events=stream_events,
        final_output=valid_brief,
        to_input_list=lambda: saved_history,
        raw_responses=[SimpleNamespace(usage=SimpleNamespace(
            input_tokens=30, output_tokens=12,
            input_tokens_details=SimpleNamespace(cached_tokens=4),
        ))],
        cancel=Mock(),
    )
    runner = Mock(return_value=streamed)
    monkeypatch.setattr(sdk.Runner, "run_streamed", runner)
    toolbox = ToolBox(pages={"paper:1": page_text})
    toolbox.sources["paper:1"] = page_text
    client = SimpleNamespace(close=AsyncMock())
    runtime = SDKRuntime(settings, toolbox, client)
    emitted = []
    result = await runtime.run("Read the evidence.", emitted.append)
    kwargs = runner.call_args.kwargs
    assert kwargs["max_turns"] == settings.max_steps
    assert kwargs["run_config"].tracing_disabled is True
    assert kwargs["run_config"].trace_include_sensitive_data is False
    assert runtime.history == saved_history
    assert result.usage.input_tokens == 30
    assert result.usage.output_tokens == 12
    assert result.usage.cached_tokens == 4
    assert {"type": "progress", "message": "tool_called"} in emitted
    await runtime.cancel()
    streamed.cancel.assert_called_once()


@pytest.mark.asyncio
async def test_sdk_cancel_is_called_when_stream_is_interrupted(settings, monkeypatch):
    from course.runtimes import sdk

    async def stream_events():
        raise asyncio.CancelledError()
        yield  # This mock has the SDK's asynchronous-iterator interface.

    streamed = SimpleNamespace(stream_events=stream_events, cancel=Mock())
    monkeypatch.setattr(sdk.Runner, "run_streamed", Mock(return_value=streamed))
    runtime = SDKRuntime(settings, ToolBox(pages={}), SimpleNamespace(close=AsyncMock()))
    with pytest.raises(asyncio.CancelledError):
        await runtime.run("Read the evidence.")
    assert runtime.broken is True
    streamed.cancel.assert_called_once()
