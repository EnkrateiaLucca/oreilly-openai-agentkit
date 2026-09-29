"""A valid quote can accompany an invalid conclusion. No model call is made."""

from course.schemas import ResearchBrief, check_citations

if __name__ == "__main__":
    # This is a deliberately synthetic teaching passage, not a claim about the course paper.
    source = "On the selected benchmark, the method improved accuracy by two percentage points."
    bad = ResearchBrief.model_validate(
        {
            "title": "Deliberately bad candidate",
            "claims": [
                {
                    "text": "The method is guaranteed to improve every possible task.",
                    "evidence": {"source_id": "teaching:1", "quote": source},
                }
            ],
            "not_found": [],
            "limitations": [],
            "action": "none",
        }
    )
    errors = check_citations(bad, {"teaching:1": source})
    assert errors == []
    print("Schema: valid. Quote substring check: passes.")
    print("Human semantic review: FAIL. One benchmark does not establish a universal guarantee.")
    print("Repair: narrow the claim to the selected benchmark and state the generalization limit.")
