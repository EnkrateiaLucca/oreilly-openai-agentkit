#!/usr/bin/env python3
"""Simple terminal chat app using the OpenAI Responses API.

Setup:
  1) pip install --upgrade openai
  2) export OPENAI_API_KEY="..."
  3) python chat_agent.py

This uses the Responses API (POST /v1/responses) via the official OpenAI Python SDK.
Docs references:
  - Responses API reference (incl. output_text convenience property)
  - Streaming Responses guide
"""

from __future__ import annotations

import os
import sys
from typing import List, Dict, Any

from openai import OpenAI


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")


def _ensure_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY is not set.")
        print("Set it, e.g.:")
        print('  export OPENAI_API_KEY="sk-..."')
        sys.exit(1)


def chat_loop(model: str = DEFAULT_MODEL, stream: bool = True) -> None:
    """Run an interactive chat loop.

    Conversation state is maintained client-side as a list of messages and sent each turn.
    """

    _ensure_api_key()

    client = OpenAI()

    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Keep answers concise unless asked.",
        }
    ]

    print(f"OpenAI Responses API chat. Model: {model}. Stream: {stream}")
    print("Type your message and press Enter.")
    print("Commands: /exit, /quit, /reset, /model <name>, /stream on|off")

    while True:
        try:
            user_text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return

        if not user_text:
            continue

        if user_text in {"/exit", "/quit"}:
            print("Exiting.")
            return

        if user_text == "/reset":
            messages = messages[:1]
            print("Conversation reset.")
            continue

        if user_text.startswith("/model "):
            model = user_text.split(" ", 1)[1].strip() or model
            print(f"Model set to: {model}")
            continue

        if user_text.startswith("/stream "):
            val = user_text.split(" ", 1)[1].strip().lower()
            if val in {"on", "true", "1", "yes"}:
                stream = True
            elif val in {"off", "false", "0", "no"}:
                stream = False
            else:
                print("Usage: /stream on|off")
                continue
            print(f"Streaming: {stream}")
            continue

        messages.append({"role": "user", "content": user_text})

        try:
            if stream:
                # Streaming mode: iterate server-sent events.
                stream_iter = client.responses.create(
                    model=model,
                    input=messages,
                    stream=True,
                )

                assistant_text_parts: List[str] = []
                print("Assistant: ", end="", flush=True)
                for event in stream_iter:
                    # The streaming guide documents `response.output_text.delta` events for text.
                    if getattr(event, "type", None) == "response.output_text.delta":
                        delta = event.delta or ""
                        assistant_text_parts.append(delta)
                        print(delta, end="", flush=True)

                    # You can also watch for `response.completed` and other lifecycle events if desired.

                print()  # newline after the streamed response
                assistant_text = "".join(assistant_text_parts).strip()

            else:
                response = client.responses.create(
                    model=model,
                    input=messages,
                )
                assistant_text = (response.output_text or "").strip()
                print(f"Assistant: {assistant_text}")

            # Store assistant message for multi-turn chat.
            if assistant_text:
                messages.append({"role": "assistant", "content": assistant_text})

        except Exception as e:
            print(f"\nERROR calling OpenAI API: {e}")
            # Roll back last user message so retries don't duplicate it.
            if messages and messages[-1].get("role") == "user":
                messages.pop()


if __name__ == "__main__":
    # Optional CLI: python chat_agent.py [model]
    m = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    chat_loop(model=m, stream=True)
