# Optional extensions

Finish the eight core lessons first. Nothing in this folder is required for first-run setup.

## Small current exercises

```bash
uv run python optional/triage.py --message "I cannot sign in"
uv run python optional/retrieval.py --query revenue --limit 3
```

- [Triage](triage.py): a deterministic, typed support-routing exercise preserves the useful old Builder branching lesson. Add a structured model classifier only after defining the categories, unknown behavior, and escalation policy.
- [SEC retrieval](retrieval.py): literal local search over the retained filing extracts. It returns labeled evidence and an explicit not-found result. It is not hosted file search, semantic retrieval, or current financial advice.
- [ChatKit with your own backend](chatkit/README.md): replace the archived workflow-ID route with a protocol adapter to the authenticated backend. This is an extension design exercise, not part of the completed Streamlit app.

## Preserved advanced examples

- `notebooks/1.1-data-analysis-finance.ipynb`: finance analysis.
- `notebooks/2.0-agentic-workflow-struct-out.ipynb`: larger structured workflow.
- `notebooks/2.1-intro-responses-api.ipynb` and `2.2-building-with-responses-api.ipynb`: prior expanded Responses material.
- `notebooks/2.3-intro-conversations-api.ipynb` and `2.4-building-with-conversations-api.ipynb`: Conversations lifecycle and advanced state patterns.
- `demos/video-script-app/`, `demos/dashboard-agent/`, and `demos/paper-chat-app/`: historical exploratory apps.

These preserved examples have separate assumptions and were not converted into core lessons. Inspect their paths, models, dependencies, API compatibility, and costs before using them. Do not install their requirements into the locked core environment by default.

MCP, skills, subagents, and voice are further extensions. Add one only when the task needs it, and define its permissions and evaluation cases first. [Official tools and runtime overview](https://developers.openai.com/api/docs/guides/agents).
