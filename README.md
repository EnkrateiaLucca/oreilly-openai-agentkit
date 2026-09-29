# Building Agents with OpenAI

Build a research assistant that reads a paper, searches related records, and produces a cited Markdown brief. Teach the same task through the **managed Agents API**, a visible **Responses tool loop**, and the **Agents SDK**, then evaluate it and serve it through an authenticated application.

**Three hours of teaching, breaks extra.** Python 3.11+ and `uv` are required. Node 22.12+ is needed only to rebuild the slides. A project API key and model/runtime access are needed for live demos; the offline rehearsal runs without them.

## Start here

```bash
uv sync --extra class --extra app --extra dev
uv run python -m course preflight
uv run python -m course demo --runtime offline --follow-up --output outputs/first-run
uv run python -m course evaluate --runtime offline --output evals/results/first-run
```

Keep your API key in the server environment or a local, ignored `.env`. Use `.env.example` as a template; do not overwrite an existing `.env` or put its contents in a notebook, screenshot, or commit. `OPENAI_MODEL` selects one model across live runtimes; the course default is `gpt-6-luna`.

Before live teaching, run `uv run python -m course preflight --live`, then rehearse the selected runtime. Live calls send the task and supplied evidence to OpenAI and may incur charges. Access to one API does not establish access to every runtime.

**Read [verification.md](docs/verification.md) for what was actually tested.** Offline is a deterministic teaching simulation. Its passing results do not verify live model quality or access. The signed-in playground requires a separate instructor check.

## Teach the course

| Elapsed | Lesson | Deliverable |
|---|---|---|
| 0:00–0:15 | [00 · Setup & map](lessons/00-setup/README.md) | Working rehearsal and runtime map |
| 0:15–0:35 | [01 · Playground](lessons/01-playground/README.md) | Evidence-backed answer and a missing-information case |
| 0:35–1:05 | [02 · Managed agent](lessons/02-managed/README.md) | Session, streamed events, follow-up, cleanup |
| 1:05–1:30 | [03 · Responses](lessons/03-responses/README.md) | Typed extraction and explicit tool loop |
| 1:30–1:55 | [04 · Agents SDK](lessons/04-sdk/README.md) | Same task with Agent, tools, and Runner |
| 1:55–2:15 | [05 · Grounding & actions](lessons/05-grounding-actions/README.md) | Evidence boundaries and approved mock publication |
| 2:15–2:40 | [06 · Evaluate & repair](lessons/06-evaluate/README.md) | Ten fixed cases and a repair cycle |
| 2:40–3:00 | [07 · Ship & recap](lessons/07-ship/README.md) | Authenticated app and exit demonstration |

- [Course guide](docs/course-guide.md): complete teaching sequence, demos, exercises, solutions, and fallbacks.
- [Instructor guide](docs/instructor-guide.md): copyable bullets, timing, transitions, and recovery cues.
- [Slide deck](presentation/slides.html) · [Slide PDF](presentation/slides.pdf) · [Marp source](presentation/slides.md) · [Printable handout](presentation/handout.html).
- [Official sources](docs/sources.md): current documentation and migration references.
- [Original accepted plan](docs/original-plan.md): preserved for comparison.

The teaching source is [docs/course.json](docs/course.json). `python scripts/build_materials.py` regenerates the course guide, instructor guide, eight lesson notes, Marp source, and handout from the same sequence. `python scripts/build_materials.py --check` detects drift.

## Run the completed demos

Run commands from the repository root. Choose one live runtime at a time:

```bash
uv run python -m course demo --runtime managed --follow-up --output outputs/managed
uv run python -m course demo --runtime responses --follow-up --output outputs/responses
uv run python -m course demo --runtime sdk --follow-up --output outputs/sdk
uv run python -m course demo --runtime responses --failure lookup_paper --output outputs/failure
uv run python -m course extract
uv run python -m course extract --live
uv run python -m course actions
uv run python -m course replay
uv run python -m course cleanup
```

The managed path uses an OpenAI-hosted environment for the paper and file work. The application handles function calls, validates arguments, collects final output, and cleans up demonstration resources. The Responses path makes that loop explicit; the SDK path uses `Agent`, `function_tool`, and `Runner` inside the application. They share tools and output contracts, not interchangeable state objects. [Official runtime comparison](https://developers.openai.com/api/docs/guides/agents).

Run the notebooks with `make notebooks`:

- [Responses introduction](notebooks/0.0-intro-responses-api.ipynb)
- [Paper data extraction](notebooks/1.0-paper-data-extraction.ipynb)

## Run the application

```bash
uv run python -m course access
make backend
```

In a second terminal, run `make app`. Sign in with a generated classroom token, start in offline mode, create a brief, follow up, and download the result. See the [application guide](demos/research-report-app/README.md) for details.

The separate FastAPI backend holds the API key, enforces session ownership and work limits, and streams progress to Streamlit. Publication is a **local mock action**: preview → explicit approval → server authorization → one SQLite transaction. The model cannot grant approval or publish by itself. This classroom server is not a production deployment; production requires real identity, TLS, shared durable state, and operational controls.

## Evaluate and rehearse

```bash
make test
make rehearse
uv run python -m course evaluate --runtime offline --output evals/results/rehearsal
uv run python -m course evaluate --runtime responses --output evals/results/live-responses
```

The ten fixed cases cover **3 normal tasks, 2 missing-evidence cases, 2 tool failures, 2 injection attempts, and 1 denied action**. Results record mechanical evidence checks, tool use, validity, approval behavior, latency, usage when available, and a model-cost estimate only when rates are configured. A quotation appearing in a source does not prove the accompanying claim; semantic review remains required. Managed sandbox/tool charges are separate from a token-based estimate.

`make slides` rebuilds the HTML deck. The handout is printable from a browser; PDF exports, when provided, are presentation conveniences rather than a runtime requirement.

## Repository map

| Path | Purpose |
|---|---|
| `course/` | Shared configuration, tools, schemas, runtimes, CLI, evaluation, backend, mock actions |
| `lessons/00-setup` … `07-ship` | Completed demo instructions, student exercises, worked solutions |
| `notebooks/` | Two core notebooks, ready for offline rehearsal and explicit live cells |
| `assets/` | Original paper PDF and paper-record CSV |
| `fixtures/` | SEC extracts and reproducible fallback fixtures |
| `evals/` | Versioned cases and local result tables |
| `demos/research-report-app/` | Streamlit interface for the authenticated course backend |
| `presentation/` | Generated deck, handout, and Automata theme |
| `optional/` | Retrieval/triage extensions, advanced notebooks, finance and video examples |
| `archive/` | Historical Agent Builder, hosted workflow ChatKit, and previous course materials |

Core setup has no hosted Evals, prompt-object, Agent Builder workflow-ID, finance, video, MCP, voice, or subagent requirement. Historical examples are preserved and clearly separated; see [archive](archive/README.md) and [optional extensions](optional/README.md).
