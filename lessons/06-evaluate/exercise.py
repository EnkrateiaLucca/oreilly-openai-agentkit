"""Create a schema-valid but semantically unsupported claim.

1. Read the small source below.
2. Write a claim that is stronger than its evidence.
3. Preserve the source ID and an exact quote.
4. Explain why a quote checker alone cannot reject the claim.
"""

SOURCE = "On the selected benchmark, the method improved accuracy by two percentage points."
CLAIM = "YOUR UNSUPPORTED CLAIM"

if __name__ == "__main__":
    print("Evidence:", SOURCE)
    print("Claim:", CLAIM)
