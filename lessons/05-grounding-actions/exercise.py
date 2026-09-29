"""Fill in this publication decision table, then inspect solution.py.

Each value should be denied, published, or already_published.
"""

EXPECTED = {
    "missing_approval": None,
    "missing_permission": None,
    "wrong_owner": None,
    "changed_digest": None,
    "valid_request": None,
    "repeated_request": None,
}

if __name__ == "__main__":
    for name, decision in EXPECTED.items():
        print(f"{name}: {decision or 'YOUR ANSWER'}")
