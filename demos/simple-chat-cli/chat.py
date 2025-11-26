#!/usr/bin/env python3
"""
Simple Chat CLI - A pedagogical introduction to OpenAI's Responses and Conversations APIs

This CLI demonstrates:
1. Chat agent built on the Conversations API (persistent state)
2. File references with @ completion
3. Tool calling via the Responses API
4. Token counting and usage tracking
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, List

from openai import OpenAI
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import PathCompleter, Completer, Completion, WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from dotenv import load_dotenv
from tools import create_file, move_file, edit_file, FILE_TOOL_DEFINITIONS


# Load environment variables
load_dotenv()

# Initialize clients
console = Console()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



TOOL_HANDLERS = {
    "create_file": create_file,
    "move_file": move_file,
    "edit_file": edit_file,
}


class ChatCompleter(Completer):
    """
    Custom completer that handles both:
    1. Command completion when line starts with /
    2. File path completion when @ is typed
    """

    def __init__(self):
        self.path_completer = PathCompleter(expanduser=True)

        # Define available commands with descriptions
        self.commands = {
            'help': 'Show help message',
            'history': 'View full conversation history',
            'stats': 'Show token usage and session statistics',
            'new': 'Start a new conversation',
            'websearch': 'Toggle web search on/off',
            'tools': 'List the currently available tools',
            'clear': 'Clear the screen',
            'exit': 'Exit the application',
            'quit': 'Exit the application',
        }

        self.command_completer = WordCompleter(
            list(self.commands.keys()),
            meta_dict=self.commands,
            ignore_case=True,
        )

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Check if we're completing a command (line starts with /)
        if text.startswith('/'):
            # Remove the leading / for command completion
            command_text = text[1:]

            from prompt_toolkit.document import Document
            command_doc = Document(command_text, len(command_text))

            # Get command completions - keep the start_position as-is since it's
            # already relative to the command text (after the /)
            for completion in self.command_completer.get_completions(command_doc, complete_event):
                yield Completion(
                    completion.text,
                    start_position=completion.start_position,
                    display=completion.display,
                    display_meta=completion.display_meta,
                )

        # Check if we're completing a file reference (contains @)
        else:
            last_at_pos = text.rfind('@')

            if last_at_pos >= 0:
                # Extract the path after @
                path_text = text[last_at_pos + 1:]

                # Create a modified document for path completion
                from prompt_toolkit.document import Document
                path_doc = Document(path_text, len(path_text))

                # Get path completions - keep the start_position as-is since it's
                # already relative to the path text (after the @)
                for completion in self.path_completer.get_completions(path_doc, complete_event):
                    yield Completion(
                        completion.text,
                        start_position=completion.start_position,
                        display=completion.display,
                        display_meta=completion.display_meta,
                    )


class ChatSession:
    """Manages a chat session using OpenAI's APIs"""

    def __init__(self, model: str = "gpt-5-mini"):
        self.model = model
        self.conversation_id: Optional[str] = None
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.message_count = 0
        self.web_search_enabled = True  # Enable web search tool by default

    def _build_tool_payload(self) -> List[dict]:
        """Return the list of tool definitions to offer the model."""
        tools = list(FILE_TOOL_DEFINITIONS)
        if self.web_search_enabled:
            tools.append({"type": "web_search"})
        return tools

    def _execute_tool_call(self, call_item):
        """Invoke a local Python function for the tool call and format output for the API."""
        handler = TOOL_HANDLERS.get(call_item.name)
        if handler is None:
            message = f"Tool '{call_item.name}' is not available in this CLI."
            console.print(f"[yellow]{message}[/yellow]")
            return {
                "type": "function_call_output",
                "call_id": call_item.call_id,
                "output": json.dumps({"error": message}),
            }

        try:
            args = json.loads(call_item.arguments or "{}")
            if not isinstance(args, dict):
                raise ValueError("Tool arguments must deserialize to an object.")
        except Exception as exc:
            error_msg = f"Failed to parse arguments for {call_item.name}: {exc}"
            console.print(f"[red]{error_msg}[/red]")
            return {
                "type": "function_call_output",
                "call_id": call_item.call_id,
                "output": json.dumps({"error": error_msg}),
            }

        try:
            console.print(f"[dim]→ Executing tool {call_item.name} with args {args}[/dim]")
            result = handler(**args)
        except Exception as exc:
            result = f"Tool {call_item.name} raised an error: {exc}"
            console.print(f"[red]{result}[/red]")

        return {
            "type": "function_call_output",
            "call_id": call_item.call_id,
            "output": json.dumps({"result": result}),
        }

    def _call_model_with_tools(self, input_items: List[dict], conversation_id: Optional[str] = None):
        """
        Call the Responses API and automatically satisfy function calls by executing local tools.
        Returns the final response once the model emits a standard message.
        """
        include = ["web_search_call.action.sources"] if self.web_search_enabled else None
        tools = self._build_tool_payload()

        last_response = None
        for _ in range(5):  # Prevent infinite loops
            request_kwargs = {
                "model": self.model,
                "input": input_items,
                "tools": tools if tools else None,
                "include": include,
            }
            if conversation_id:
                request_kwargs["conversation"] = conversation_id

            last_response = client.responses.create(**request_kwargs)

            tool_calls = [
                item for item in last_response.output
                if getattr(item, "type", "") == "function_call"
            ]

            if not tool_calls:
                break

            # Keep the model's outputs in the running list before adding tool results
            input_items += last_response.output

            for call_item in tool_calls:
                tool_output = self._execute_tool_call(call_item)
                input_items.append(tool_output)
        else:
            console.print("[yellow]Stopping tool loop after 5 iterations to avoid infinite cycle.[/yellow]")

        return last_response

    def read_file_references(self, text: str) -> str:
        """
        Find @file.txt references in the text and replace with file contents
        This demonstrates how to prepare context for the model
        """
        import re

        # Find all @path references
        pattern = r'@([^\s]+)'
        matches = re.finditer(pattern, text)

        result = text
        for match in matches:
            filepath = match.group(1)
            try:
                path = Path(filepath).expanduser()
                if path.exists() and path.is_file():
                    with open(path, 'r') as f:
                        content = f.read()
                    # Replace @filepath with the file content
                    result = result.replace(
                        match.group(0),
                        f"\n--- Content from {filepath} ---\n{content}\n--- End of {filepath} ---\n"
                    )
                    console.print(f"[dim]Attached: {filepath}[/dim]")
                else:
                    console.print(f"[yellow]Warning: {filepath} not found[/yellow]")
            except Exception as e:
                console.print(f"[red]Error reading {filepath}: {e}[/red]")

        return result

    def send_message_chat_agent(self, user_input: str):
        """
        Send a message using the Conversations API (stateful chat-agent mode)
        """
        try:
            # Process file references
            processed_input = self.read_file_references(user_input)

            # Create conversation if it doesn't exist
            if not self.conversation_id:
                console.print("\n[bold cyan]Creating new conversation...[/bold cyan]")
                conversation = client.conversations.create(
                    metadata={"session": "chat-cli", "model": self.model}
                )
                self.conversation_id = conversation.id
                console.print(f"[dim]Conversation ID: {self.conversation_id}[/dim]")

            console.print("\n[bold cyan]Using Chat Agent (stateful)[/bold cyan]")
            if self.web_search_enabled:
                console.print("[dim]Web search: enabled[/dim]")

            input_payload = [{"role": "user", "content": processed_input}]
            response = self._call_model_with_tools(
                input_payload,
                conversation_id=self.conversation_id,
            )

            # Display web search sources if used
            self._display_web_search_sources(response)

            # Extract and display the response
            assistant_message = self._extract_response_text(response)
            console.print(f"\n[bold green]Assistant:[/bold green]")
            console.print(Markdown(assistant_message))

            # Update usage statistics
            if response.usage:
                self._update_stats(response.usage)

            self.message_count += 1

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    def _extract_response_text(self, response) -> str:
        """Extract text content from a response object"""
        if hasattr(response, 'output_text') and response.output_text:
            return response.output_text

        # Fallback: manually extract from output array
        for item in response.output:
            if item.type == "message":
                for content in item.content:
                    if hasattr(content, 'text'):
                        return content.text
        return ""

    def _update_stats(self, usage):
        """Update token usage statistics"""
        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens

    def _display_web_search_sources(self, response):
        """Display web search sources if the model used web search"""
        try:
            for item in response.output:
                if item.type == "web_search_call":
                    # Model decided to use web search
                    if hasattr(item, 'action') and hasattr(item.action, 'sources'):
                        console.print("\n[bold magenta]🔍 Web Sources Used:[/bold magenta]")
                        for i, source in enumerate(item.action.sources, 1):
                            title = source.get('title', 'Untitled')
                            url = source.get('url', '')
                            console.print(f"  {i}. {title}")
                            console.print(f"     [dim]{url}[/dim]")
                        console.print()
        except Exception:
            # Silently ignore if we can't extract sources
            pass

    def show_stats(self):
        """Display session statistics"""
        total_tokens = self.total_input_tokens + self.total_output_tokens

        stats_text = Text()
        stats_text.append("\nSession Statistics\n", style="bold cyan")
        stats_text.append("Mode: chat agent\n", style="yellow")
        stats_text.append(f"Messages: {self.message_count}\n")
        stats_text.append(f"Input tokens: {self.total_input_tokens:,}\n")
        stats_text.append(f"Output tokens: {self.total_output_tokens:,}\n")
        stats_text.append(f"Total tokens: {total_tokens:,}\n", style="bold")

        if self.conversation_id:
            stats_text.append(f"Conversation ID: {self.conversation_id}\n", style="dim")

        console.print(Panel(stats_text, title="📊 Stats", border_style="cyan"))

    def show_tools(self):
        """Display the currently available tools and their status."""
        lines = [
            "# Available Tools",
            "",
            "The assistant can call these helper functions when it needs to take action.",
            "",
            "## File Utilities",
        ]

        for tool in FILE_TOOL_DEFINITIONS:
            required = tool.get("parameters", {}).get("required", [])
            req_display = ", ".join(required) if required else "None"
            lines.append(f"- **{tool['name']}** — {tool.get('description', '')} (required params: {req_display})")

        lines.append("")
        lines.append("## Web Search")
        status = "enabled" if self.web_search_enabled else "disabled"
        lines.append(f"- **web_search** — OpenAI web search tool ({status}). Toggle with `/websearch`.")

        console.print(Markdown("\n".join(lines)))

    def show_conversation_history(self):
        """Display the full chat history for the active session"""
        if not self.conversation_id:
            console.print("[yellow]No conversation active yet. Send a message to start chatting.[/yellow]")
            return

        try:
            # List all items in the conversation
            items = client.conversations.items.list(
                self.conversation_id,
                limit=100,
                order="asc"
            )

            console.print(f"\n[bold cyan]Conversation History ({self.conversation_id})[/bold cyan]\n")

            for item in items.data:
                if item.type == "message":
                    role = item.role.capitalize()
                    role_color = "green" if item.role == "assistant" else "blue"

                    console.print(f"[bold {role_color}]{role}:[/bold {role_color}]")

                    for content in item.content:
                        if hasattr(content, 'text'):
                            console.print(f"  {content.text}\n")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    def new_conversation(self):
        """Start a new conversation"""
        self.conversation_id = None
        self.message_count = 0
        console.print("[green]✓ Started new chat session[/green]")

def show_welcome():
    """Display welcome message"""
    welcome = """
# Welcome to the Simple Chat Agent! 🤖

This CLI keeps a single chat experience built on OpenAI's Conversations API. Every turn shares context automatically, and the agent can call local tools (create/move/edit files) plus optional web search when needed.

## Commands:
- `/help` - Show this help
- `/history` - Show chat history
- `/stats` - Show session statistics
- `/websearch` - Toggle web search on/off (enabled by default)
- `/tools` - Display available tools and their status
- `/new` - Start a fresh chat session
- `/clear` - Clear screen
- `/exit` - Exit the chat

## Attach Files with @
Reference files inline (e.g., "Summarize @README.md"). The CLI will inline their contents before sending the request.

## Tips:
- Press TAB after typing `/` to see available commands
- Press TAB after typing `@` to complete file paths
- Use `/tools` anytime to review which tools the agent can call

---
Type your first message below to spin up the chat agent!
"""
    console.print(Markdown(welcome))


def show_help():
    """Display help message"""
    help_text = """
# Chat CLI Help

## Commands:
- `/help` - Show this help message
- `/history` - Show full conversation history
- `/stats` - Show token usage and session stats
- `/websearch` - Toggle web search on/off
- `/tools` - List available tools and current web search status
- `/new` - Start a new conversation
- `/clear` - Clear the screen
- `/exit` or `/quit` - Exit the application

## Web Search:

The model can search the web automatically when it needs current information!
- Enabled by default
- Toggle with `/websearch` command
- Sources are displayed when used
- Great for questions about current events, recent updates, or factual lookups

**Example:** "What are the latest features in Python 3.13?"

## Tools & Automations:

Use `/tools` to see which helper functions the assistant can call.
- Includes file utilities (`create_file`, `move_file`, `edit_file`)
- Shows whether the built-in `web_search` tool is enabled
- Toggle web search with `/websearch`

## File References (@ syntax):

You can include file contents in your prompts using `@`:
- `@file.txt` - Include file.txt in your message
- `@../data/doc.md` - Relative paths work
- `@~/Documents/notes.txt` - Home directory expansion
- `@/absolute/path/to/file.txt` - Absolute paths work

**Example:** "Analyze the code in @chat.py and suggest improvements"

## Chat Agent Mode:
- Built on Conversations API for automatic context
- All messages stay in a single ongoing chat unless you run `/new`
- Tool outputs are automatically fed back to the model

## Tips:
- Tab completion works for commands (type / and press TAB)
- Tab completion works for file paths after @
- Token usage is tracked and displayed with /stats
- Conversation IDs are displayed whenever a chat session is active
"""
    console.print(Markdown(help_text))


def main():
    """Main chat loop"""
    # Verify API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[bold red]Error:[/bold red] OPENAI_API_KEY not found in environment")
        console.print("Please set your API key in .env file or environment variables")
        sys.exit(1)

    # Show welcome message
    show_welcome()

    # Create chat session
    session = ChatSession()

    # Setup prompt toolkit with custom style and completer
    style = Style.from_dict({
        'prompt': '#00aa00 bold',
    })

    prompt_session = PromptSession(
        completer=ChatCompleter(),
        style=style,
    )

    # Main chat loop
    while True:
        try:
            # Get user input with nice prompt
            user_input = prompt_session.prompt(
                HTML('<prompt>[chat-agent]> </prompt>')
            ).strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith('/'):
                command = user_input[1:].split(maxsplit=1)[0].lower()

                if command in ['exit', 'quit']:
                    console.print("\n[cyan]Goodbye! 👋[/cyan]")
                    break

                elif command == 'help':
                    show_help()

                elif command == 'history':
                    session.show_conversation_history()

                elif command == 'stats':
                    session.show_stats()

                elif command == 'new':
                    session.new_conversation()

                elif command == 'websearch':
                    session.web_search_enabled = not session.web_search_enabled
                    status = "enabled" if session.web_search_enabled else "disabled"
                    console.print(f"[green]✓ Web search {status}[/green]")

                elif command == 'tools':
                    session.show_tools()

                elif command == 'clear':
                    console.clear()
                    show_welcome()

                else:
                    console.print(f"[red]Unknown command: {command}[/red]")
                    console.print("[dim]Type /help for available commands[/dim]")

                continue

            # Send message using the chat agent
            session.send_message_chat_agent(user_input)

        except KeyboardInterrupt:
            console.print("\n[yellow]Use /exit to quit[/yellow]")
            continue

        except EOFError:
            console.print("\n[cyan]Goodbye! 👋[/cyan]")
            break

        except Exception as e:
            console.print(f"[bold red]Unexpected error:[/bold red] {e}")


if __name__ == "__main__":
    main()
