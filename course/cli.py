"""Small commands shared by completed lessons, notebooks, and instructor notes."""

import argparse
import asyncio
import importlib.metadata
import json
import os
import platform
import secrets
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from course.actions import Publisher
from course.config import ROOT, Settings, api_client
from course.errors import explain_error
from course.evaluation import evaluate
from course.extraction import extract_paper
from course.prompts import DEFAULT_TASK, FOLLOW_UP
from course.runtimes import make_runtime
from course.tools import ToolBox, lookup_paper, paper_pages


async def preflight(live=False):
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "model": Settings().model,
        "key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ["openai", "openai-agents", "pydantic", "pypdf"]
        },
        "paper_pages_available": len(paper_pages()),
        "fixture_lookup": lookup_paper("Context Engineering")["found"],
        "model_access": "not tested",
        "managed_access": "not tested",
    }
    if live:
        try:
            async with api_client(Settings()) as client:
                response = await client.responses.create(
                    model=Settings().model,
                    input="Reply with the word ready.",
                    max_output_tokens=128,
                    store=False,
                )
                report["model_access"] = {
                    "status": response.status,
                    "usage": response.usage.model_dump() if response.usage else None,
                }
                try:
                    await client.beta.agents.list(limit=1)
                    report["managed_access"] = "agent listing succeeded; sandbox run still required"
                except Exception as exc:
                    report["managed_access"] = explain_error(exc)
        except Exception as exc:
            report["model_access"] = explain_error(exc)
    return report


async def demo(args):
    settings = Settings()
    runtime = make_runtime(
        args.runtime,
        settings,
        ToolBox(
            fail_tools=[args.failure] if args.failure else [], max_calls=settings.max_tool_calls
        ),
    )
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    recording = {
        "kind": "deterministic rehearsal" if args.runtime == "offline" else "recorded live API run",
        "runtime": args.runtime,
        "recorded_at": datetime.now(UTC).isoformat(),
        "turns": [],
    }
    events = []
    try:
        for index, prompt in enumerate([args.prompt] + ([FOLLOW_UP] if args.follow_up else []), 1):
            events = []

            def emit(event, events=events):
                events.append(event)
                print(event.get("message", event.get("name", "progress")), flush=True)

            result = await runtime.run(prompt, emit)
            (output / f"brief-{index}.md").write_text(result.markdown)
            (output / f"run-{index}.json").write_text(result.model_dump_json(indent=2) + "\n")
            recording["turns"].append(
                {"prompt": prompt, "events": events, "result": result.model_dump()}
            )
            # Save before cleanup, including the first turn if the follow-up fails.
            (output / "recording.json").write_text(
                json.dumps(recording, indent=2, ensure_ascii=False) + "\n"
            )
            print(result.markdown)
        print(f"Saved brief and trace to {output}")
    except Exception as exc:
        (output / "failure.json").write_text(
            json.dumps(
                {
                    "failure": explain_error(exc),
                    "events": events,
                    "tool_calls": runtime.tools.calls,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
        raise
    finally:
        await runtime.close()


def actions():
    with tempfile.TemporaryDirectory() as directory:
        pub = Publisher(Path(directory) / "mock.sqlite3")
        draft = pub.preview(
            "teacher", "demo", "# Reviewed classroom brief\n\nA local mock action.\n"
        )
        print("1. Preview:", draft["markdown"])
        for approved, permission in [(False, True), (True, False)]:
            try:
                pub.approve_and_publish(
                    "teacher",
                    draft["draft_id"],
                    draft["digest"],
                    approved=approved,
                    can_publish=permission,
                )
            except PermissionError:
                print(f"2. Denied: approved={approved}, permission={permission}")
        for _ in range(2):
            print(
                "3. Explicit test approval:",
                pub.approve_and_publish(
                    "teacher", draft["draft_id"], draft["digest"], approved=True, can_publish=True
                ),
            )


async def cleanup():
    from openai import ConflictError, NotFoundError

    # Operates only on resources created and recorded by this course.
    async with api_client(Settings()) as client:
        for path in sorted((ROOT / ".runtime/resources").glob("*.json")):
            ids = json.loads(path.read_text())
            if session_id := ids.get("session_id"):
                try:
                    await client.beta.agents.sessions.events.create(
                        session_id, events=[{"type": "agent.session.input.cancel"}]
                    )
                except NotFoundError:
                    pass
                for attempt in range(3):
                    try:
                        await client.beta.agents.sessions.delete(session_id)
                        break
                    except NotFoundError:
                        break
                    except ConflictError:
                        if attempt == 2:
                            raise RuntimeError(
                                "Session still busy; retry cleanup after it settles."
                            ) from None
                        await asyncio.sleep(attempt + 1)
            if agent_id := ids.get("agent_id"):
                try:
                    await client.beta.agents.delete(agent_id)
                except NotFoundError:
                    pass
            path.unlink()
            print("Cleaned course resources from", path.name)


def access():
    path = ROOT / ".runtime/access.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        accounts = {
            name: {"token": secrets.token_urlsafe(32), "can_publish": name == "teacher"}
            for name in ["teacher", "student"]
        }
        # Atomic exclusive creation; private from the moment it exists.
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
            json.dump(accounts, stream, indent=2)
    print("Classroom tokens are stored in .runtime/access.json (ignored, mode 600).")
    print(
        "Open that file locally to copy a teacher or student token into the app. Never use an API key as a login token."
    )


def parser():
    p = argparse.ArgumentParser(description="Building Agents with OpenAI classroom commands")
    sub = p.add_subparsers(dest="command", required=True)
    check = sub.add_parser("preflight")
    check.add_argument("--live", action="store_true")
    check.add_argument("--output", type=Path)
    run = sub.add_parser("demo")
    run.add_argument(
        "--runtime", choices=["offline", "managed", "responses", "sdk"], default="offline"
    )
    run.add_argument("--prompt", default=DEFAULT_TASK)
    run.add_argument("--follow-up", action="store_true")
    run.add_argument("--failure", choices=["lookup_paper", "read_paper"])
    run.add_argument("--output", default="outputs/demo")
    extract = sub.add_parser("extract")
    extract.add_argument("--live", action="store_true")
    ev = sub.add_parser("evaluate")
    ev.add_argument(
        "--runtime", choices=["offline", "managed", "responses", "sdk"], default="offline"
    )
    ev.add_argument("--output", type=Path, default=Path("outputs/evaluation"))
    replay = sub.add_parser("replay")
    replay.add_argument("--path", type=Path, default=ROOT / "fixtures/fallback/recording.json")
    sub.add_parser("actions")
    sub.add_parser("cleanup")
    sub.add_parser("access")
    return p


async def execute(args):
    if args.command == "demo":
        await demo(args)
    elif args.command == "preflight":
        report = await preflight(args.live)
        rendered = json.dumps(report, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n")
        print(rendered)
        if (
            args.live
            and isinstance(report["model_access"], dict)
            and "category" in report["model_access"]
        ):
            return 1
    elif args.command == "extract":
        print((await extract_paper(live=args.live)).model_dump_json(indent=2))
    elif args.command == "evaluate":
        result = await evaluate(args.runtime, args.output)
        print(json.dumps(result, indent=2))
        return 0 if result["passed"] == result["total"] else 1
    elif args.command == "replay":
        recording = json.loads(args.path.read_text())
        print("REPLAY —", recording["kind"], recording["recorded_at"])
        for turn in recording["turns"]:
            print("\nTASK:", turn["prompt"])
            for event in turn["events"]:
                print(event.get("message", event.get("name", "progress")))
            print(turn["result"]["markdown"])
    elif args.command == "cleanup":
        await cleanup()
    elif args.command == "actions":
        actions()
    elif args.command == "access":
        access()
    return 0


def main():
    try:
        code = asyncio.run(execute(parser().parse_args()))
    except Exception as exc:
        print(json.dumps(explain_error(exc), indent=2), file=sys.stderr)
        code = 1
    raise SystemExit(code)
