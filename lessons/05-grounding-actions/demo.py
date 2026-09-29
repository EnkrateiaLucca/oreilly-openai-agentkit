"""Show hostile retrieved text and the publication boundary.

Offline is the default and is a deterministic rehearsal, not an LLM injection test.
Choose --runtime responses|sdk|managed explicitly for a live model experiment.
"""

import argparse
import asyncio
from pathlib import Path

from course.config import ROOT, Settings
from course.prompts import DEFAULT_TASK
from course.runtimes import make_runtime
from course.tools import ToolBox


async def demo(runtime_name: str, output: Path):
    settings = Settings()
    injection = (ROOT / "fixtures/injections/publish.txt").read_text()
    toolbox = ToolBox(injection=injection, max_calls=settings.max_tool_calls)
    runtime = make_runtime(runtime_name, settings, toolbox)
    print("Untrusted text appended to retrieved evidence:")
    print(injection)
    print("Runtime:", runtime_name)
    if runtime_name == "offline":
        print("Deterministic rehearsal: no model inference occurs.")
    try:
        result = await runtime.run(
            DEFAULT_TASK, lambda event: print(event.get("message", event["type"]))
        )
        output.mkdir(parents=True, exist_ok=True)
        (output / "brief.md").write_text(result.markdown)
        (output / "run.json").write_text(result.model_dump_json(indent=2) + "\n")
        print(result.markdown)
        print(
            "Application tool permission result:",
            ToolBox(pages={}, max_calls=1).dispatch(
                "publish_brief", {"title": "Attempted publication"}
            ),
        )
        print(
            "No publisher capability was given to the model. Inspect the saved tool results and output."
        )
        print("Saved:", output)
    finally:
        await runtime.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime", choices=["offline", "responses", "sdk", "managed"], default="offline"
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/grounding-injection"))
    args = parser.parse_args()
    asyncio.run(demo(args.runtime, args.output))
