# Official documentation and verification sources

Documentation checked **September 29, 2026**. These references support the teaching design; a documentation page does not prove that this project's credentials can use a feature. See [verification.md](verification.md) for measured runtime results and [api-audit.md](api-audit.md) for the implementation review.

| Topic | Official source | Applied in this course |
|---|---|---|
| Runtime ownership | [Agents](https://developers.openai.com/api/docs/guides/agents) | Managed API, Responses, and SDK are alternatives with different state resources. |
| Managed concepts | [Agents API overview](https://developers.openai.com/api/docs/guides/agents-api/overview) | Saved configuration, sessions, and execution environments are distinct. |
| Managed lifecycle | [Agents API quickstart](https://developers.openai.com/api/docs/guides/agents-api/quickstart) | Create configuration/session, stream events, continue work, and clean up. |
| Configuration | [Configuring agents](https://developers.openai.com/api/docs/guides/agents-api/configuration) | Shared instructions, tool declarations, model choice, and output schema. |
| Managed functions | [Function tools](https://developers.openai.com/api/docs/guides/agents-api/tools/functions) | Application handlers return results for the pending turn/call IDs. |
| Managed visibility | [Observability and usage](https://developers.openai.com/api/docs/guides/agents-api/observability) | Events, stored items, usage, and completion inspection. |
| Visible model loop | [Function calling](https://developers.openai.com/api/docs/guides/function-calling) | Preserve model output items, execute validated functions, return matching call results. |
| Typed output | [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) | Validate field/type contracts separately from factual accuracy. |
| SDK orchestration | [Agents SDK](https://developers.openai.com/api/docs/guides/agents/sdk) · [Quickstart](https://developers.openai.com/api/docs/guides/agents/quickstart) | Agent, function tools, Runner, and application-owned execution. |
| SDK state | [Running agents](https://developers.openai.com/api/docs/guides/agents/running-agents) · [Results and state](https://developers.openai.com/api/docs/guides/agents/results) | Choose one continuation strategy and keep runtime state types distinct. |
| Direct file context | [PDF file inputs](https://developers.openai.com/api/docs/guides/pdf-files) | Compare direct file context with local extracted-page tools. |
| Collection retrieval | [File search](https://developers.openai.com/api/docs/guides/tools-file-search) | Explain collection retrieval; distinguish it from the local literal-search baseline. |
| Evaluation | [Evaluate agent workflows](https://developers.openai.com/api/docs/guides/agent-evals) | Separate trace inspection from repeatable assessment. The core course uses local cases/results. |
| UI extension | [ChatKit](https://developers.openai.com/api/docs/guides/chatkit) · [Advanced integrations](https://developers.openai.com/api/docs/guides/custom-chatkit) | Optional protocol adapter to the course's authenticated backend. |
| Model and prices | [Model catalog](https://developers.openai.com/api/docs/models) · [Pricing](https://developers.openai.com/api/docs/pricing) | One configurable model; access checked separately. Cost stays unknown when rates are unset. |
| Runtime errors | [Error codes](https://developers.openai.com/api/docs/guides/error-codes) | Distinguish transport, authentication, quota, rate limiting, and access errors. |
| Retired course dependencies | [Agent Builder migration](https://developers.openai.com/api/docs/guides/agent-builder/migrate-from-agent-builder) · [Deprecations](https://developers.openai.com/api/docs/deprecations) | Archive Builder/workflow-ID material; keep prompts and evaluation cases in code. |

## What was deliberately not inferred

- The [Agents playground](https://platform.openai.com/agents/new) browser check reached a login page. Signed-in controls, export, tool access, and their relationship to API sessions need an instructor run-through before class.
- Access to a basic model request or agent listing is narrower than a successful paper-bearing managed session. The verification report distinguishes them.
- A schema-valid result and a matching quotation are insufficient to establish factual entailment. Human semantic review remains part of the evaluation exercise.
- Model-token estimates exclude sandbox, hosted tool, and other non-model charges. Unconfigured rates stay unknown; they are never filled with guessed prices.
- A deterministic fallback is labeled as simulation, and any genuine recorded API run must identify its runtime/model and capture metadata.

## Migration notes

The documented shutdown date for Agent Builder is November 30, 2026. Hosted Evals becomes read-only October 31, then shuts down November 30, 2026; prompt objects also shut down November 30. Historical code is preserved in `archive/` and excluded from core setup. [Migration guide](https://developers.openai.com/api/docs/guides/agent-builder/migrate-from-agent-builder) · [Deprecations](https://developers.openai.com/api/docs/deprecations).
