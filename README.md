# O'Reilly Live Training - OpenAI AgentKit

Welcome to the O'Reilly Live Training on OpenAI AgentKit! This course covers the full OpenAI agent stack — from raw API calls with the Responses API, through the Agents SDK, up to the AgentKit product platform (Agent Builder, ChatKit, Connector Registry, and Evals). You'll build real demo applications along the way.

## Setup

**Using uv (Recommended)**

This project uses [uv](https://github.com/astral-sh/uv), a fast Python package installer and resolver. The Makefile handles most setup automatically.

1. **Install uv:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **One-command setup:**
   ```bash
   make all
   ```
   This creates a virtual environment in `.venv`, installs dependencies, and sets up Jupyter kernel.

3. **Activate the environment:**
   ```bash
   source .venv/bin/activate
   ```

4. **Setup your OpenAI API key:**
   - Get your API key from [OpenAI Platform](https://platform.openai.com/)
   - Create a `.env` file in the project root:
   ```bash
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```

**Using Pip (Traditional Method)**

1. **Create a Virtual Environment:**
   Navigate to your project directory. Make sure you have Python 3.11+ installed!
   ```bash
   python -m venv .venv
   ```

2. **Activate the Virtual Environment:**
   - **On macOS and Linux:** `source .venv/bin/activate`
   - **On Windows:** `.\.venv\Scripts\activate`

3. **Install Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r ./requirements/requirements.txt
   ```

4. **Setup Jupyter Kernel:**
   ```bash
   python -m ipykernel install --user --name=openai-agentkit
   ```

5. **Setup your OpenAI API key:**
   Create a `.env` file in the project root:
   ```bash
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```

Remember to deactivate the virtual environment when done: `deactivate`

**Using Conda**

- Install [anaconda](https://www.anaconda.com/download) or [miniconda](https://docs.conda.io/en/latest/miniconda.html)
- This repo was tested with Python 3.11
- Create an environment: `conda create -n openai-agentkit python=3.11`
- Activate your environment: `conda activate openai-agentkit`
- Install requirements: `pip install -r requirements/requirements.txt`
- Setup Jupyter kernel: `python -m ipykernel install --user --name=openai-agentkit`
- Setup your OpenAI [API key](https://platform.openai.com/)

## Quick Start with Makefile

The project includes a Makefile for common tasks:

```bash
# Create virtual environment and install everything
make all

# Clean up environment
make clean

# Add new packages
make add pandas numpy

# Update requirements after manual changes
make env-update

# Show activation command
make activate
```

## Setup your .env file

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your-openai-api-key-here
```

## Notebooks

The notebooks live in `notebooks/` and run in order as a single sequence. `0.x`–`1.x` are
the core teaching path; `2.x` are production-oriented reference implementations.

1. [**0.0 — Intro to Responses API**](notebooks/0.0-intro-responses-api.ipynb) — Main teaching notebook. Covers the Responses API end-to-end: items-based I/O, server-side state, built-in tools, structured outputs, and multi-turn agents.
2. [**1.0 — Paper Data Extraction**](notebooks/1.0-paper-data-extraction.ipynb) — Applied use-case: extract structured data from academic papers using the Responses API and Pydantic schemas.
3. [**1.1 — Data Analysis (Finance)**](notebooks/1.1-data-analysis-finance.ipynb) — Data-analysis workflow with tool/function calling over the Responses API.
4. [**2.0 — Agentic Workflow with Structured Outputs**](notebooks/2.0-agentic-workflow-struct-out.ipynb) — Structured-output agentic pipeline.
5. [**2.1 — Intro to Responses API (reference)**](notebooks/2.1-intro-responses-api.ipynb) — Complete Responses API lifecycle reference (create, retrieve, cancel, token counts).
6. [**2.2 — Building with the Responses API**](notebooks/2.2-building-with-responses-api.ipynb) — Ten production patterns: streaming, retries, token budgets, function calling, caching, and more.
7. [**2.3 — Intro to Conversations API (reference)**](notebooks/2.3-intro-conversations-api.ipynb) — Complete Conversations API lifecycle reference (create, update, items CRUD, pagination).
8. [**2.4 — Building with the Conversations API**](notebooks/2.4-building-with-conversations-api.ipynb) — Production conversation patterns: sessions, templates, batch ops, branching, analytics.

Input files the notebooks read (PDFs, images, sample text) live in `notebooks/assets/` and the repo-level `assets/`.

## Demo Applications

The notebooks have been converted into runnable demo apps. Each demo is self-contained and can be run independently.

### Streamlit Apps (Module 1)

| Demo | Description | Run |
|------|-------------|-----|
| [Paper Chat App](demos/paper-chat-app/) | Upload a PDF and ask questions about it using the Responses API | `streamlit run demos/paper-chat-app/app.py` |
| [Video Script Generator](demos/video-script-app/) | Convert a research paper into a 60-second educational video script with optional DALL-E scene images | `streamlit run demos/video-script-app/app.py` |
| [Research Report App](demos/research-report-app/) | Generate a structured research report from a PDF, exported as Markdown | `streamlit run demos/research-report-app/app.py` |

### Agent Builder Workflows (Module 3) *(deprecated Nov 30, 2026 — patterns transferable to Agents SDK)*

Three Agent Builder workflows built in the OpenAI platform, each with a `README.md` and screenshots:

| Demo | Description |
|------|-------------|
| [Demo 1 — Course Assistant](demos/agent-builder/demo-1-intro-assistant/) | Minimal single-node workflow: Start → Agent → End. Good starting template. |
| [Demo 2 — Support Triage with Guardrails](demos/agent-builder/demo-2-support-triage/) | Guardrails → Classifier → 3 specialist agents (Billing / Technical / General) or Safety Refusal. PII detection, jailbreak protection. |
| [Demo 3 — File Search RAG](demos/agent-builder/demo-3-file-search-rag/) | RAG workflow over 10 SEC 10-K filings: Query Agent → File Search → Transform → Evidence Summarizer with cited sources. |

### ChatKit App (Module 4)

| Demo | Description | Docs |
|------|-------------|------|
| [ChatKit App](demos/chatkit-app/) | Next.js starter that embeds an Agent Builder workflow via ChatKit. Handles auth, streaming, and file upload. | [README](demos/chatkit-app/README.md) · [Review](demos/chatkit-app/REVIEW.md) |

## Repository Structure

```
├── notebooks/                              # Course notebooks (run in order)
│   ├── 0.0-intro-responses-api.ipynb
│   ├── 1.0-paper-data-extraction.ipynb
│   ├── 1.1-data-analysis-finance.ipynb
│   ├── 2.0-agentic-workflow-struct-out.ipynb
│   ├── 2.1-intro-responses-api.ipynb
│   ├── 2.2-building-with-responses-api.ipynb
│   ├── 2.3-intro-conversations-api.ipynb
│   ├── 2.4-building-with-conversations-api.ipynb
│   └── assets/                             # Notebook input files (PDFs, images, text)
├── demos/                                  # Runnable demo applications
│   ├── paper-chat-app/                     # Streamlit — PDF Q&A (Module 1)
│   ├── video-script-app/                   # Streamlit — video script generator (Module 1)
│   ├── research-report-app/                # Streamlit — research report generator (Module 1)
│   ├── agent-builder/                      # Agent Builder workflows (Module 3)
│   │   ├── demo-1-intro-assistant/         # Simple single-node assistant
│   │   ├── demo-2-support-triage/          # Multi-agent triage with guardrails
│   │   └── demo-3-file-search-rag/         # RAG over SEC 10-K filings
│   └── chatkit-app/                        # Next.js ChatKit starter (Module 4)
├── presentation/                           # Course slides (Remark.js HTML + PDF)
├── assets/                                 # Images, diagrams, and reference documents
├── research/                               # Background research and use-case analysis
├── requirements/                           # Python dependencies
│   ├── requirements.in                     # Direct dependencies
│   └── requirements.txt                    # Locked dependencies
├── Makefile                                # Automation scripts
└── .venv/                                  # Virtual environment (created by setup)
```

## Key Features

This course covers the full OpenAI agent stack:

- **Responses API**: The primitive — direct API calls, server-side state, built-in tools (`file_search`, `web_search`, `code_interpreter`, `mcp`)
- **Agents SDK**: The framework — multi-agent orchestration, handoffs, guardrails, tracing; works with 100+ LLMs
- **Agent Builder**: Visual drag-and-drop workflow composer — nodes, classifiers, guardrails, MCP connectors, versioning, and evals
- **ChatKit**: Embeddable React/Web Component chat UI — file upload, streaming, tool invocation display
- **Guardrails**: Open-source modular safety layer — PII detection, jailbreak protection, prompt injection defense
- **Structured Outputs**: Guaranteed JSON schemas for reliable data extraction
- **File Search & RAG**: Retrieval-augmented generation with vector stores
- **Multi-modal Agents**: Text, images, and document processing
- **Evals**: Trace grading, dataset building, and automated prompt optimization *(deprecated Nov 30, 2026 — migrate to Agents SDK tracing)*

## Troubleshooting

**Jupyter Kernel Not Found:**
```bash
python -m ipykernel install --user --name=openai-agentkit
```

**API Key Issues:**
Make sure your `.env` file is in the project root and contains:
```
OPENAI_API_KEY=sk-...
```

**Package Installation Issues:**
Try upgrading pip first:
```bash
pip install --upgrade pip
pip install -r requirements/requirements.txt
```

**Streamlit Apps:**
Run from the project root so relative paths resolve correctly:
```bash
streamlit run demos/paper-chat-app/app.py
```

**ChatKit App:**
Requires Node.js 18+. See [demos/chatkit-app/README.md](demos/chatkit-app/README.md) for full setup.

## Additional Resources

- [OpenAI Platform Documentation](https://platform.openai.com/docs)
- [OpenAI Cookbook](https://cookbook.openai.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Agent Builder Guide](https://platform.openai.com/docs/guides/agent-builder)
- [ChatKit Guide](https://platform.openai.com/docs/guides/chatkit)
- [Agents SDK (GitHub)](https://github.com/openai/openai-agents-python)

## License

Materials created for O'Reilly Live Training
