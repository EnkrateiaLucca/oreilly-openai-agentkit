"""Completed local exercise: execute functions and correlate each result."""

import json

from course.tools import ToolBox


def matching_outputs(calls: list[dict], toolbox: ToolBox) -> list[dict]:
    outputs = []
    for call in calls:
        result = toolbox.dispatch(call["name"], call["arguments"])
        outputs.append(
            {
                "type": "function_call_output",
                "call_id": call["call_id"],
                "output": json.dumps(result),
            }
        )
    return outputs


if __name__ == "__main__":
    calls = [
        {
            "name": "lookup_paper",
            "arguments": '{"query":"no-such-paper-xyz"}',
            "call_id": "class-call-1",
        },
        {"name": "unregistered_tool", "arguments": "{}", "call_id": "class-call-2"},
    ]
    outputs = matching_outputs(calls, ToolBox(pages={}))
    assert [v["call_id"] for v in outputs] == ["class-call-1", "class-call-2"]
    assert json.loads(outputs[0]["output"])["found"] is False
    assert "error" in json.loads(outputs[1]["output"])
    print(json.dumps(outputs, indent=2))
