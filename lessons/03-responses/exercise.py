"""Exercise: implement the application's half of the function-call loop.

Run from the repo root with: uv run python lessons/03-responses/exercise.py
This exercise makes no network request.
"""

from course.tools import ToolBox


def matching_outputs(calls: list[dict], toolbox: ToolBox) -> list[dict]:
    """Return one function_call_output per call, preserving its call_id.

    Each call has name, arguments (a JSON string), and call_id.
    Validate/execute via toolbox.dispatch, then JSON-encode its result.
    """
    raise NotImplementedError("Complete the tool-result mapping, then compare solution.py.")


if __name__ == "__main__":
    calls = [
        {
            "name": "lookup_paper",
            "arguments": '{"query":"no-such-paper-xyz"}',
            "call_id": "class-call-1",
        }
    ]
    print(matching_outputs(calls, ToolBox(pages={})))
