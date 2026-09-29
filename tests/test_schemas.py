import pytest
from pydantic import ValidationError

from course.schemas import ResearchBrief, Usage, check_citations, render_markdown


def test_supported_quote_accepts_whitespace_normalization(valid_brief, page_text):
    assert check_citations(valid_brief, {"paper:1": page_text.replace(" ", "\n  ")}) == []


@pytest.mark.parametrize("source_id, quote", [
    ("invented:1", "The study compares retrieval methods."),
    ("paper:1", "The results prove a conclusion absent from the source."),
    ("paper:1", "The study"),
])
def test_source_id_and_exact_quote_are_checked(valid_brief, page_text, source_id, quote):
    valid_brief.claims[0].evidence.source_id = source_id
    valid_brief.claims[0].evidence.quote = quote
    assert check_citations(valid_brief, {"paper:1": page_text}) == [
        f"Unsupported quotation: {source_id}",
    ]


def test_schema_validity_alone_does_not_establish_evidence(valid_brief):
    reconstructed = ResearchBrief.model_validate_json(valid_brief.model_dump_json())
    assert check_citations(reconstructed, {})


def test_quote_match_is_not_a_semantic_entailment_check(valid_brief, page_text):
    valid_brief.claims[0].text = "A conclusion the quoted sentence does not establish."
    assert check_citations(valid_brief, {"paper:1": page_text}) == []


def test_missing_evidence_must_be_explicit(valid_brief):
    valid_brief.claims = []
    assert check_citations(valid_brief, {}) == ["No claims and no explicit missing evidence."]
    valid_brief.not_found = ["No evidence was returned by the reader."]
    assert check_citations(valid_brief, {}) == []


def test_brief_rejects_unknown_fields_and_unknown_action(valid_brief):
    payload = valid_brief.model_dump()
    with pytest.raises(ValidationError):
        ResearchBrief.model_validate({**payload, "approved": True})
    with pytest.raises(ValidationError):
        ResearchBrief.model_validate({**payload, "action": "published"})


def test_render_keeps_model_html_and_markdown_as_text(valid_brief):
    valid_brief.title = '<script>alert("x")</script>'
    valid_brief.claims[0].text = "[click](https://example.org) ![track](https://example.org/x)"
    rendered = render_markdown(valid_brief)
    assert "<script>" not in rendered
    assert "&lt;script" in rendered
    assert "[click](" not in rendered
    assert "![track](" not in rendered
    assert "## Evidence" in rendered


def test_usage_accumulates_known_counts_without_inventing_missing_values():
    usage = Usage()
    usage.add(None)
    assert usage.input_tokens is None
    usage.add({"input_tokens": 20, "output_tokens": 4,
               "input_tokens_details": {"cached_tokens": 5}})
    usage.add({"input_tokens": 10, "output_tokens": 3})
    assert usage.model_dump() == {"input_tokens": 30, "output_tokens": 7, "cached_tokens": 5}
