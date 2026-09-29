import csv
import hashlib
import json
from collections import Counter

import pytest

from course.config import ROOT
from course.evaluation import evaluate


def read_rows(output):
    with (output / "results.csv").open(newline="") as stream:
        return list(csv.DictReader(stream))


@pytest.mark.asyncio
async def test_fixed_ten_case_offline_rehearsal_records_measured_results(tmp_path, settings):
    summary = await evaluate("offline", tmp_path, settings)
    rows = read_rows(tmp_path)
    assert len(rows) == summary["total"] == 10
    assert Counter(row["category"] for row in rows) == {
        "normal": 3, "missing_evidence": 2, "tool_failure": 2, "injection": 2, "denied_action": 1,
    }
    assert summary["passed"] == 10
    assert summary["kind"] == "deterministic software rehearsal"
    assert summary["model"] is None
    assert summary["cases_sha256"] == hashlib.sha256((ROOT / "evals/cases.json").read_bytes()).hexdigest()
    assert json.loads((tmp_path / "summary.json").read_text()) == summary
    assert len({row["id"] for row in rows}) == 10
    for row in rows:
        assert row["passed"] == "True"
        assert row["semantic_grounding"] == "human_review_required"
        assert float(row["latency_seconds"]) >= 0
        assert row["input_tokens"] == row["output_tokens"] == "0"
        assert float(row["estimated_model_cost_usd"]) == 0
        trace = json.loads((tmp_path / f"{row['id']}.json").read_text())
        assert trace["case"]["id"] == row["id"]
        assert trace["events"]
        assert trace["result"]["runtime"] == "offline"
        assert trace["result"]["tool_calls"]


@pytest.mark.asyncio
async def test_actual_tool_budget_failure_produces_failed_rows_and_failure_traces(tmp_path, settings):
    settings.max_tool_calls = 1
    summary = await evaluate("offline", tmp_path, settings)
    rows = read_rows(tmp_path)
    assert summary["passed"] == 0
    assert summary["total"] == 10
    for row in rows:
        assert row["passed"] == "False"
        assert row["output_valid"] == "False"
        assert row["quoted_evidence"] == "False"
        assert row["input_tokens"] == row["output_tokens"] == ""
        assert row["estimated_model_cost_usd"] == ""
        assert "budget exhausted" in row["error"]
        trace = json.loads((tmp_path / f"{row['id']}.json").read_text())
        assert "result" not in trace
        assert trace["failure"]["category"] == "local"
        assert len(trace["tool_calls"]) == 1
