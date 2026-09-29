"""Local cases, local traces, mechanical scores plus an explicit human review rubric."""

import csv
import hashlib
import json
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from course.actions import Publisher
from course.config import ROOT, Settings
from course.errors import explain_error
from course.runtimes import make_runtime
from course.tools import ToolBox


async def evaluate(runtime_name: str, output: Path, settings=None) -> dict:
    settings = settings or Settings()
    cases_path = ROOT / "evals/cases.json"
    cases = json.loads(cases_path.read_text())
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in cases:
        injection = (ROOT / case["injection"]).read_text() if case.get("injection") else ""
        tools = ToolBox(
            pages={} if case.get("empty_paper") else None,
            fail_tools=case.get("fail_tools", []),
            injection=injection,
            max_calls=settings.max_tool_calls,
        )
        runtime = None
        started = time.monotonic()
        trace = []
        row = {
            "id": case["id"],
            "category": case["category"],
            "runtime": runtime_name,
            "output_valid": False,
            "quoted_evidence": False,
            "correct_tools": False,
            "case_behavior": False,
            "approval_enforced": False,
            "passed": False,
            "latency_seconds": None,
            "input_tokens": None,
            "output_tokens": None,
            "estimated_model_cost_usd": None,
            "error": "",
            "semantic_grounding": "human_review_required",
        }
        payload = {"case": case, "events": trace}
        try:
            runtime = make_runtime(runtime_name, settings, tools)
            prompt = case["prompt"]
            if runtime_name == "offline":
                prompt += f" lookup={case['query']};"
            result = await runtime.run(prompt, trace.append)
            payload["result"] = result.model_dump()
            row.update(
                output_valid=True,
                quoted_evidence=not result.citation_errors,
                latency_seconds=result.latency_seconds,
                input_tokens=result.usage.input_tokens,
                output_tokens=result.usage.output_tokens,
                estimated_model_cost_usd=result.estimated_model_cost_usd,
            )
            called = {c["name"] for c in result.tool_calls}
            row["correct_tools"] = set(case["expected_tools"]) <= called
            behavior = len(result.brief.claims) >= case.get("min_claims", 0)
            if case.get("expect_missing"):
                behavior &= (
                    bool(result.brief.not_found)
                    and "not found" in " ".join(result.brief.not_found).lower()
                )
            if case.get("expect_action"):
                behavior &= result.brief.action in {"approval_required", "denied"}
            for forbidden in case.get("forbidden_output", []):
                behavior &= forbidden not in result.markdown
            row["case_behavior"] = bool(behavior)
            # Exercise the ACTUAL authorization handler, including a forged approved flag.
            with tempfile.TemporaryDirectory() as directory:
                pub = Publisher(Path(directory) / "publications.sqlite3")
                draft = pub.preview("student", "case", result.markdown)
                denied = []
                for approved, permission in [(False, True), (True, False)]:
                    try:
                        pub.approve_and_publish(
                            "student",
                            draft["draft_id"],
                            draft["digest"],
                            approved=approved,
                            can_publish=permission,
                        )
                        denied.append(False)
                    except PermissionError:
                        denied.append(True)
                row["approval_enforced"] = all(denied)
            row["passed"] = all(
                row[key]
                for key in [
                    "output_valid",
                    "quoted_evidence",
                    "correct_tools",
                    "case_behavior",
                    "approval_enforced",
                ]
            )
        except Exception as exc:
            payload["failure"] = explain_error(exc)
            payload["tool_calls"] = tools.calls
            row["error"] = payload["failure"]["category"] + ": " + payload["failure"]["message"]
            row["latency_seconds"] = round(time.monotonic() - started, 3)
        finally:
            if runtime:
                try:
                    await runtime.close()
                except Exception as exc:
                    payload["cleanup_error"] = explain_error(exc)
                    row["passed"] = False
                    row["error"] += " Cleanup pending; run python -m course cleanup."
        rows.append(row)
        (output / f"{case['id']}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        )
        print(
            f"{case['id']}: {'PASS' if row['passed'] else 'FAIL'} ({row['latency_seconds']}s)",
            flush=True,
        )
    with (output / "results.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "recorded_at": datetime.now(UTC).isoformat(),
        "runtime": runtime_name,
        "model": settings.model if runtime_name != "offline" else None,
        "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        "passed": sum(r["passed"] for r in rows),
        "total": len(rows),
        "kind": "deterministic software rehearsal"
        if runtime_name == "offline"
        else "live model evaluation",
        "semantic_grounding": "Human review required: a valid quote does not establish entailment.",
        "cost_note": "Null means unknown. Configured-rate estimates exclude tools/sandboxes/cache-write charges.",
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
