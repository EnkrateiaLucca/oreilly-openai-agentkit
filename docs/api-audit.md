# OpenAI API implementation audit

Reviewed on 2026-09-29 against current official OpenAI documentation and the installed `openai==3.16.2` and `openai-agents==0.22.3` packages. This is a source and API-contract audit, not a claim that live requests passed. No API calls were made by this review and no credential file was opened.

## Findings and resolution

1. **Resolved — managed structured-output configuration:** the Agents API `text.format` schema accepts `type` and `schema`. The Responses-specific `name` and `strict` fields were removed from `managed_agent_config` and retained in the Responses runtime. This now matches the installed `openai/types/beta/text_format_param.py` and the official expanded `text` parameter. [Create an agent](https://developers.openai.com/api/reference/python/resources/beta/subresources/agents/methods/create)
2. **Resolved — SDK cancellation cleanup:** cancellation now drains `stream_events()` after `RunResultStreaming.cancel()` within a separate 15-second cleanup deadline, as required by the installed `agents/result.py::RunResultStreaming.cancel`. [Running agents](https://developers.openai.com/api/docs/guides/agents/running-agents)
3. **Resolved — SDK cached-token reporting:** SDK usage now retains `response.usage.input_tokens_details.cached_tokens` as well as total input/output.
4. **Resolved — cost wording:** the calculation is now described as a simplified model-only estimate. GPT-6 Luna also has cache-write pricing; sandbox, tools, processing tiers, and other billing dimensions are outside this calculation. [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [Managed usage](https://developers.openai.com/api/docs/guides/agents-api/observability)
5. **Resolved — specific quota codes and ambiguous 429 responses:** `course/errors.py` now recognizes specific credit, organization/project spend, and organization usage-limit codes plus the broader `insufficient_quota` type, including nested API error bodies. Its wording covers usage limits and its help links select billing, organization limits, or project settings from the error code. Unidentified `429` responses remain ambiguous. [Error codes](https://developers.openai.com/api/docs/guides/error-codes)
6. **Resolved — throttle classification:** the documented `slow_down` code and `rate_limit_error` type now select the temporary-throttling guidance rather than billing guidance. [Error codes](https://developers.openai.com/api/docs/guides/error-codes)

Final local verification passed ten error-routing/help-link cases and the lint check for `course/errors.py`, with no network request or credential access.

## Verified contracts

### Managed Agents API

- Saved agents hold reusable configuration; sessions hold conversation and environment state. Creating a saved agent and then a session with its `agent_id` is supported. Subagent tools are disabled by default. [Agent configuration](https://developers.openai.com/api/docs/guides/agents-api/configuration)
- The hosted environment supports inline base64 files, `/workspace` paths, disabled network access, and `container_size: "small"`. The current hosted-sandbox guide documents container size even though the installed Python typed environment definition omits it; the SDK preserves extra dictionary fields. Do not remove the setting solely because it is absent from that type declaration. [Hosted sandboxes](https://developers.openai.com/api/docs/guides/agents-api/environments/openai-hosted)
- Creation-time inline files are limited to 5 MiB each and 10 MiB in aggregate. The classroom PDF limit is 5 MiB; the other two inputs are small fixture data. [Files and artifacts](https://developers.openai.com/api/docs/guides/agents-api/environments/files)
- Open the stream before submitting follow-up input. A stream does not replay prior events. A closed stream or idle session alone is not completion. Checking root `agent.session.turn.completed`, while rejecting failure and cancellation events, is appropriate. [Events and items](https://developers.openai.com/api/docs/guides/agents-api/sessions/events)
- `agent.session.requires_action` carries `session.required_actions`. Function results use `agent.session.input.tool_result`, the pending action's `turn_id` and `call_id`, and either serialized string `output` with `success: true`, or `error` with `success: false`. Removing the Responses-only tool `strict` flag is correct. [Function tools](https://developers.openai.com/api/docs/guides/agents-api/tools/functions)
- Saved session items contain `type`, `role`, `turn_id`, and content blocks. Iterating the async paginated collection in ascending order, filtering the completed turn, and collecting assistant `output_text` is consistent with the SDK. Prefer `phase: "final_answer"` when present; legacy messages may have no phase. [Saved session history](https://developers.openai.com/api/docs/guides/agents-api/sessions/events)
- Turn usage can be absent or change after completion. Keep unknown counts as unknown; they are not zero and are not a final bill. Both the installed completed event and its nested turn expose optional usage. A top-level event-usage fallback can preserve counts when nested usage is absent. [Managed usage](https://developers.openai.com/api/docs/guides/agents-api/observability)
- Sending a cancellation event is necessary; closing the stream does not cancel execution. Deleting the session requests hosted-sandbox cleanup, and bounded retry of `409` is documented. Keeping a local resource manifest permits later cleanup when deletion fails. [Hosted sandbox lifecycle](https://developers.openai.com/api/docs/guides/agents-api/environments/openai-hosted)
- The public agent/session configuration has no `max_steps` or `max_output_tokens` request parameter. Those settings apply to the Responses and SDK adapters. The managed adapter instead has the application deadline, user-turn cap, and application-function-call cap; these do not establish a strict token or hosted-command budget. [Create an agent](https://developers.openai.com/api/reference/python/resources/beta/subresources/agents/methods/create)

### Responses API and Agents SDK

- The Responses adapter executes functions in application code and returns each result with the original `call_id`. It preserves every response output item, including reasoning, rather than rebuilding history from visible text. Current reasoning documentation says `store: false` returns encrypted reasoning content by default; the legacy `include=["reasoning.encrypted_content"]` option is not required. [Reasoning models](https://developers.openai.com/api/docs/guides/reasoning)
- The schema has an object root, required fields, nested object definitions with `additionalProperties: false`, arrays, strings, and an enum. Schema validation and quote matching remain distinct from checking whether a claim follows from its evidence. Incomplete responses and refusals must not be treated as successful briefs. [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- `Runner.run_streamed`, `Agent.output_type`, `ModelSettings`, `OpenAIResponsesModel`, `RunConfig`, and `result.to_input_list()` exist in the installed SDK. Consuming the complete stream before reading final output and using `to_input_list()` for the next turn follows the documented conversation strategy. [Running agents](https://developers.openai.com/api/docs/guides/agents/running-agents), [Results and state](https://developers.openai.com/api/docs/guides/agents/results)
- The shared `gpt-6-luna` default supports function calling and structured outputs through Responses. Its published standard text rates for prompts up to 272K input tokens are $0.10 input and $0.50 output per million tokens, with separate cached-input/cache-write rates. The course leaves rates configurable; model availability for a particular project still requires a live request. [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)

## Runtime troubleshooting boundary

Apply the OpenAI API Troubleshooting skill to concrete request failures: distinguish DNS/transport failures before an API response from authentication, quota, temporary rate limits, and access failures. `429` alone does not identify the remedy. Inspect the API error code: quota/spend exhaustion requires billing or limit changes, while rate-limit/overload conditions call for pacing and bounded backoff. Do not relabel an execution-environment approval block as an OpenAI authentication or billing failure. [Error codes](https://developers.openai.com/api/docs/guides/error-codes)

Live classroom verification remains separate: confirm project/model access, first tool result, valid cited output, one follow-up turn, explicit cancellation, and cleanup for each selected live runtime. Offline and mock checks cannot establish these external-service outcomes.

## Pricing snapshot for evaluation reports

For `gpt-6-luna`, Standard processing and prompts up to 272K input tokens, the published prices checked on 2026-09-29 are:

| Token category | USD per million tokens |
| --- | ---: |
| Input | 0.10 |
| Cached input | 0.01 |
| Cache writes | 0.125 |
| Output | 0.50 |

Record these rates and the date alongside an evaluation result instead of treating them as permanent application defaults. The course's two-rate formula remains a simplified estimate: it does not separate cached input from uncached input or account for cache writes and other charges. [GPT-6 Luna pricing](https://developers.openai.com/api/docs/models/gpt-6-luna)
