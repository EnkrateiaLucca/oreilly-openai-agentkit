"""Local replacement for the historical Builder support-triage branching exercise.

This is a deterministic baseline, not model-generated classification.
"""

import argparse
import json
from typing import Literal

from pydantic import BaseModel


class Triage(BaseModel):
    category: Literal["account", "billing", "technical", "human_review"]
    next_action: str
    performs_action: bool = False


def route(message: str) -> Triage:
    text = message.casefold()
    matches = []
    for category, words in {
        "account": ("sign in", "login", "password", "locked out"),
        "billing": ("invoice", "charged", "refund", "payment"),
        "technical": ("error", "crash", "broken", "timeout"),
    }.items():
        if any(word in text for word in words):
            matches.append(category)
    category = matches[0] if len(matches) == 1 else "human_review"
    actions = {
        "account": "Offer account recovery guidance; never request the user's password.",
        "billing": "Collect the issue for billing review; do not issue a refund automatically.",
        "technical": "Ask for the error and reproduction steps without secrets.",
        "human_review": "Ask a clarifying question or send the ambiguous issue for human review.",
    }
    return Triage(category=category, next_action=actions[category])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", default="I cannot sign in")
    args = parser.parse_args()
    print(json.dumps(route(args.message).model_dump(), indent=2))
