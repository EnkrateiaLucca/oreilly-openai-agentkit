"""One model, explicit limits, and server-side credentials for every lesson."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)


class Settings(BaseModel):
    model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-6-luna"))
    max_steps: int = Field(default=6, ge=1, le=12)
    max_tool_calls: int = Field(default=8, ge=1, le=20)
    max_output_tokens: int = Field(default=2400, ge=128, le=8000)
    timeout_seconds: float = Field(default=120, gt=0, le=300)
    max_user_turns: int = Field(default=4, ge=1, le=10)
    max_input_chars: int = Field(default=3000, ge=100, le=10000)
    # Optional published per-million-token rates; never invent a price.
    input_rate: float | None = Field(default_factory=lambda: rate("INPUT_USD_PER_MILLION"), ge=0)
    output_rate: float | None = Field(default_factory=lambda: rate("OUTPUT_USD_PER_MILLION"), ge=0)


def rate(name: str) -> float | None:
    value = os.getenv(name)
    return float(value) if value else None


def api_client(settings: Settings):
    from openai import AsyncOpenAI

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("Set OPENAI_API_KEY in the server environment or use --runtime offline.")
    return AsyncOpenAI(timeout=settings.timeout_seconds, max_retries=0)
