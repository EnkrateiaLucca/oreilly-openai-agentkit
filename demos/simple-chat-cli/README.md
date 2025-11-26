# Simple Chat CLI

A pedagogical command-line chat interface that introduces OpenAI's **Responses API** and **Conversations API** in an interactive, hands-on way.

## What You'll Learn

This CLI demonstrates the fundamental building blocks of OpenAI's agent platform:

1. **Responses API** - The core primitive for generating model responses (stateless)
2. **Conversations API** - Persistent conversation state management (stateful)
3. **File context injection** - How to provide documents as input to models (using @ syntax)
4. **Web search tool** - Built-in web search capability for current information
5. **Token counting** - Understanding and tracking API usage

## Prerequisites

- Python 3.8+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

## Installation

1. **Navigate to this directory:**
   ```bash
   cd demos/simple-chat-cli
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

## Usage

Run the chat application:

```bash
python chat.py
```

## Two Operating Modes

### 1. Responses API Mode (Default)

**Stateless** - Each message is independent.

```
[responses]> What is the capital of France?
```

**Use cases:**
- One-off questions
- Independent queries
- Simple request-response patterns

**Switch to this mode:** `/responses`

### 2. Conversations API Mode

**Stateful** - Full conversation history is maintained.

```
[conversation]> What is the capital of France?
[conversation]> What is its population?
```

The second question automatically has context from the first!

**Use cases:**
- Multi-turn conversations
- Context-dependent interactions
- Building chatbots with memory

**Switch to this mode:** `/conversation`

## Commands

All commands start with `/`. **Press TAB after typing `/` to see available commands with descriptions!**

| Command | Description |
|---------|-------------|
| `/help` | Show help message |
| `/responses` | Switch to Responses API mode (stateless) |
| `/conversation` | Switch to Conversations API mode (stateful) |
| `/history` | View full conversation history |
| `/stats` | Show token usage and session statistics |
| `/websearch` | Toggle web search on/off (enabled by default) |
| `/new` | Start a new conversation |
| `/clear` | Clear the screen |
| `/exit` or `/quit` | Exit the application |

## Web Search

The model can automatically search the web when it needs current information!

**How it works:**
- Enabled by default
- Model autonomously decides when to search
- Sources are displayed when used
- Perfect for current events, recent updates, or factual information

**Example:**
```
[responses]> What are the latest developments in AI this week?

🔍 Web Sources Used:
  1. Latest AI News - TechCrunch
     https://techcrunch.com/ai/...
  2. OpenAI Blog Updates
     https://openai.com/blog/...
```

## File References (@ syntax)

You can include file contents in your prompts using `@`:

```
[responses]> Summarize @README.md
[responses]> Analyze @/absolute/path/to/file.py
[conversation]> What are the main points in @docs/intro.txt?
```

**Features:**
- **Tab completion** - Press TAB after typing `@` to complete file paths
- Supports relative paths (`@file.txt`, `@../dir/file.md`)
- Supports absolute paths (`@/usr/local/config.json`)
- Home directory expansion (`@~/Documents/notes.txt`)

## Example Sessions

### Example 1: Stateless Responses

```bash
# Start in responses mode (stateless - default)
[responses]> What are the three laws of thermodynamics?
Using Responses API (stateless)