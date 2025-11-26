# O'Reilly Live Training - OpenAI AgentKit

Welcome to the O'Reilly Live Training on OpenAI AgentKit! This course will guide you through building AI agents using OpenAI's latest APIs, including structured outputs, file search, and multi-modal capabilities.

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

### Core Learning Path

The main notebooks are organized in a progressive learning path:

1. [**Intro to Agents with Responses API**](notebooks/1.0-intro-agents-responses-api.ipynb) - Fundamentals of building agents with OpenAI
   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/EnkrateiaLucca/oreilly-openai-agentkit/blob/main/notebooks/1.0-intro-agents-responses-api.ipynb)

2. [**Simple Chat with Responses API**](notebooks/2.0-simple-chat-responses-api.ipynb) - Building conversational interfaces
   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/EnkrateiaLucca/oreilly-openai-agentkit/blob/main/notebooks/2.0-simple-chat-responses-api.ipynb)

3. [**Structured Outputs for Data Extraction**](notebooks/3.0-structured-outputs-data-extraction.ipynb) - Extracting structured data with guaranteed schemas
   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/EnkrateiaLucca/oreilly-openai-agentkit/blob/main/notebooks/3.0-structured-outputs-data-extraction.ipynb)

4. [**Agentic Workflows with Structured Outputs**](notebooks/4.0-agentic-workflow-with-struct-out-responses.ipynb) - Building complex agent workflows
   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/EnkrateiaLucca/oreilly-openai-agentkit/blob/main/notebooks/4.0-agentic-workflow-with-struct-out-responses.ipynb)

5. [**File Search & RAG with Agentic Retrieval**](notebooks/5.0-file-search-rag-agentic-retrieval.ipynb) - Implementing retrieval-augmented generation
   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/EnkrateiaLucca/oreilly-openai-agentkit/blob/main/notebooks/5.0-file-search-rag-agentic-retrieval.ipynb)

6. [**Video Script Generation with Images**](notebooks/6.0-video-script-generation-with-images.ipynb) - Multi-modal agents with vision capabilities
   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/EnkrateiaLucca/oreilly-openai-agentkit/blob/main/notebooks/6.0-video-script-generation-with-images.ipynb)

7. [**Chat with Paper Agent**](notebooks/7.0-chat-with-paper-agent.ipynb) - Building document Q&A agents
   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/EnkrateiaLucca/oreilly-openai-agentkit/blob/main/notebooks/7.0-chat-with-paper-agent.ipynb)

8. [**Research Report Generation**](notebooks/8.0-research-report-generation.ipynb) - End-to-end research agent system
   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/EnkrateiaLucca/oreilly-openai-agentkit/blob/main/notebooks/8.0-research-report-generation.ipynb)

### Additional Resources

- [**OpenAI API Overview**](notebooks/openai-api-overview.ipynb) - Comprehensive overview of OpenAI's APIs
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/EnkrateiaLucca/oreilly-openai-agentkit/blob/main/notebooks/openai-api-overview.ipynb)

- **Reference Implementations**: Check `notebooks/reference-implementations-for-production/` for production-ready examples

## Repository Structure

```
├── notebooks/                              # Main learning notebooks
│   ├── 1.0-intro-agents-responses-api.ipynb
│   ├── 2.0-simple-chat-responses-api.ipynb
│   ├── 3.0-structured-outputs-data-extraction.ipynb
│   ├── 4.0-agentic-workflow-with-struct-out-responses.ipynb
│   ├── 5.0-file-search-rag-agentic-retrieval.ipynb
│   ├── 6.0-video-script-generation-with-images.ipynb
│   ├── 7.0-chat-with-paper-agent.ipynb
│   ├── 8.0-research-report-generation.ipynb
│   ├── openai-api-overview.ipynb
│   └── reference-implementations-for-production/
├── presentation/                           # Course presentation materials
├── assets/                                 # Images, diagrams, and resources
├── demos/                                  # Demo applications
├── requirements/                           # Python dependencies
│   ├── requirements.in                     # Direct dependencies
│   └── requirements.txt                    # Locked dependencies
├── Makefile                                # Automation scripts
└── .venv/                                  # Virtual environment (created by setup)
```

## Key Features

This course covers:

- **OpenAI Responses API**: Building agentic workflows with the latest OpenAI APIs
- **Structured Outputs**: Guaranteed JSON schemas for reliable data extraction
- **File Search & RAG**: Implementing retrieval-augmented generation patterns
- **Multi-modal Agents**: Working with text, images, and documents
- **Production Patterns**: Best practices for deploying AI agents

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

## Additional Resources

- [OpenAI Platform Documentation](https://platform.openai.com/docs)
- [OpenAI Cookbook](https://cookbook.openai.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

## License

Materials created for O'Reilly Live Training
