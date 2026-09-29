# Agent Builder Demos

This directory contains the three Agent Builder dashboard demos for Module 3.

## Demos

1. `demo-1-intro-assistant/` - a simple teaching assistant workflow.
2. `demo-2-support-triage/` - support request triage with guardrails and classification.
3. `demo-3-file-search-rag/` - simple File Search/RAG over uploaded 10-K filing extracts.

Each demo folder includes a README with the workflow context, node setup, prompts, and test inputs.

Quick File Search note: when a workflow sends File Search results into an agent, add a Transform node between them. File Search returns a structured object, and the Transform node reshapes that output into a prompt-friendly list or text value the agent can use.
