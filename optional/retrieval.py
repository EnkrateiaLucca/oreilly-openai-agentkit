"""Literal local search of historical SEC fixture extracts; no API or vector store.

Exercise: replace this baseline with a retrieval service while keeping source IDs,
exact evidence, not-found behavior, and the separation between data and instructions.
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def search(query: str, limit: int = 3) -> dict:
    query = query.strip().casefold()
    if not query or not 1 <= limit <= 10:
        raise ValueError("Use a nonblank query and a limit from 1 to 10.")
    passages = []
    for path in sorted((ROOT / "fixtures/sec").glob("*.md")):
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            if query in line.casefold():
                passages.append(
                    {
                        "source_id": f"{path.name}:{line_number}",
                        "quote": line,
                        "source_kind": "historical SEC fixture extract",
                    }
                )
                if len(passages) >= limit:
                    return {"found": True, "passages": passages}
    return {
        "found": bool(passages),
        "passages": passages,
        "missing": [] if passages else [f"No literal match for {query!r} in the fixtures."],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="revenue")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(search(args.query, args.limit), indent=2))
