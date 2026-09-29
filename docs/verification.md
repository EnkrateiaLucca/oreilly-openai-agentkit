# Verification record — September 29, 2026

This record distinguishes software checks, API access, and live model behavior. It describes what was actually run, not a guarantee of another project's access.

| Check | Result | Evidence |
|---|---|---|
| Fresh frozen Python 3.11.9 installation | Passed | `uv sync --frozen --extra class --extra app --extra dev` in a new environment |
| Python 3.13.5 environment | Passed | The same pinned OpenAI 3.16.2 / Agents SDK 0.22.3 dependencies |
| Local and mocked runtime tests | 116 passed | `python -m pytest -q`; auth, ownership, limits, tool loops, citations, failure, and approval/idempotency coverage |
| Ten fixed offline evaluation cases | 10/10 mechanical checks | [Summary](../evals/results/offline/summary.json), [table](../evals/results/offline/results.csv), per-case JSON traces in the same folder |
| Core notebooks | Both executed offline | `python scripts/verify_notebooks.py`; tracked notebooks have no saved outputs |
| Official API contract audit | All findings resolved | [API audit](api-audit.md), reviewed with OpenAI Docs and OpenAI API Troubleshooting skills |
| Live model access | Passed | Synthetic “reply ready” request using `gpt-6-luna`; [safe access report](verification/access-check.json) |
| Managed API access | Agent listing succeeded | Same access report; this does not establish hosted-sandbox execution |
| Research app in browser | Passed offline | Sign-in, new session, PDF/CSV brief, evidence, preview, disabled-until-approved publish, and repeat-publish idempotency |
| Agents playground | Sign-in required | `/agents/new` redirected to `/login?next=%2Fagents%2Fnew`; signed-in controls/export were not inspected |
| Deck / handout | HTML + 45-page slide PDF built; layout inspected | `scripts/build_materials.py --check`, pinned Marp build, no observed slide overflow |
| Rehearsal recording | Captured and replayed | [Recording](../fixtures/fallback/recording.json), clearly labeled deterministic; contains two turns and local tool results |

## Checks that remain before a fully live class

The paper-based live demo/evaluation run was blocked by automatic approval review because it would transmit repository PDF/CSV fixtures to OpenAI. A separate request for explicit fixture-transfer approval was made. The API key was loaded by the application; its file or value was never displayed. No blocked transfer was attempted through another route.

Until approval and execution, do **not** describe the managed hosted-sandbox research run, Responses/SDK paper run, live extraction, or ten-case live evaluation as verified. Their request contracts and failure handling have local/mock coverage. The default rehearsal is designed to remain useful without live access.

After authorizing fixture transfer, run from the activated environment:

```bash
python -m course demo --runtime managed --follow-up --output outputs/managed
python -m course demo --runtime responses --follow-up --output outputs/responses
python -m course demo --runtime sdk --follow-up --output outputs/sdk
python -m course extract --live
python -m course evaluate --runtime responses --output evals/results/live-responses
python -m course cleanup
```

Review every claim against its quote and the original evidence. Keep latency, usage, estimated cost, and exact failure information in the local run artifacts. Inspect the signed-in playground immediately before teaching; use the documented API or offline fallback when access is unavailable. Read [the evaluation rubric](../evals/README.md) before interpreting a passing score.

## Operational limits

- The model is configurable in one place; the verification used `gpt-6-luna`. Model/project permissions can change.
- Responses/SDK: at most six model steps, eight local tool calls, 2,400 output tokens per request, four user turns, and a 120-second application deadline by default.
- Managed: the local function-call count and application deadline apply; no native model-step or token cap is claimed. Closing the stream alone is not cancellation. The code sends a cancellation event on interruption and retains resource IDs when cleanup needs retrying. Use project spend controls as well.
- Token-based estimates are approximate. Missing usage/rates stay unknown, and sandbox/tool/cache-write/tier charges are excluded. See [current pricing](https://developers.openai.com/api/docs/pricing).
- This is a local classroom server with bearer tokens, per-user session ownership, a four-run concurrency cap, two sessions per user, a 20-session total cap, and 15-minute idle expiry. Conversation state is in memory; the mock publication transaction is durable SQLite. Production identity, distributed state, PDF processing isolation, and operational monitoring are separate deployment work.
- Archived and optional historical notebooks are preserved as references and not represented as release-tested core lessons. Their saved outputs were cleared.
