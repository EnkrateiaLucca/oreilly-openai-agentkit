import json

import httpx2
import pytest
from openai import APIConnectionError, APIStatusError

from course.errors import explain_error

PRIVATE_MARKER = "FAKE_API_CREDENTIAL_DO_NOT_ECHO"
BILLING = "https://platform.openai.com/settings/organization/billing"
LIMITS = "https://platform.openai.com/settings/organization/limits"


def request():
    return httpx2.Request("POST", "https://api.openai.com/v1/responses", headers={
        "Authorization": f"Bearer {PRIVATE_MARKER}",
    })


def api_error(status, *, code=None, error_type=None, nested=True):
    detail = {"message": f"Provider debug message containing {PRIVATE_MARKER}"}
    if code is not None:
        detail["code"] = code
    if error_type is not None:
        detail["type"] = error_type
    return APIStatusError(
        f"Raw exception details containing {PRIVATE_MARKER}",
        response=httpx2.Response(status, request=request(), headers={"x-request-id": "req-test"}),
        body={"error": detail} if nested else detail,
    )


def test_transport_failure_takes_precedence_over_unreliable_status_metadata():
    error = APIConnectionError(message=f"DNS debug message: {PRIVATE_MARKER}", request=request())
    error.status_code = 401
    result = explain_error(error)
    assert result["category"] == "transport"
    assert "No API response" in result["message"]
    assert "http_status" not in result
    assert PRIVATE_MARKER not in json.dumps(result)


def test_authentication_error_is_not_classified_as_quota():
    result = explain_error(api_error(401, code="insufficient_quota"))
    assert result["category"] == "authentication"
    assert result["http_status"] == 401
    assert result["request_id"] == "req-test"
    assert "help_links" not in result


@pytest.mark.parametrize("code, expected_links", [
    ("insufficient_quota", {"billing": BILLING, "limits": LIMITS}),
    ("credit_balance_exhausted", {"billing": BILLING}),
    ("organization_spend_limit_exceeded", {"limits": LIMITS}),
    ("organization_usage_limit_exceeded", {"limits": LIMITS}),
    ("project_spend_limit_exceeded", {"project_settings": "https://platform.openai.com/settings/"}),
])
@pytest.mark.parametrize("nested", [True, False])
def test_known_quota_codes_select_the_relevant_help_links(code, expected_links, nested):
    result = explain_error(api_error(429, code=code, nested=nested))
    assert result["category"] == "quota"
    assert result["help_links"] == expected_links
    assert result["code"] == code
    assert result["http_status"] == 429
    assert "repeated retries will not help" in result["message"]
    assert PRIVATE_MARKER not in json.dumps(result)


@pytest.mark.parametrize("nested", [True, False])
def test_insufficient_quota_type_is_recognized_when_code_is_missing(nested):
    result = explain_error(api_error(429, error_type="insufficient_quota", nested=nested))
    assert result["category"] == "quota"
    assert result["help_links"] == {"billing": BILLING, "limits": LIMITS}


@pytest.mark.parametrize("code, error_type", [
    ("rate_limit_exceeded", None), ("slow_down", None),
    (None, "rate_limit_exceeded"), (None, "rate_limit_error"),
])
def test_explicit_rate_limits_recommend_pacing_without_billing_advice(code, error_type):
    result = explain_error(api_error(429, code=code, error_type=error_type))
    assert result["category"] == "rate_limit"
    assert "Pace requests" in result["message"]
    assert "Retry-After" in result["message"]
    assert "help_links" not in result
    assert "credits" not in result["message"]
    assert PRIVATE_MARKER not in json.dumps(result)


@pytest.mark.parametrize("code", [None, "unrecognized_429_code"])
def test_ambiguous_429_does_not_guess_between_quota_and_rate_limit(code):
    result = explain_error(api_error(429, code=code))
    assert result["category"] == "quota_or_rate_limit"
    assert "before retrying" in result["message"]
    assert "help_links" not in result


@pytest.mark.parametrize("status, code", [(403, None), (404, "model_not_found")])
def test_model_and_project_permission_failures_are_access_errors(status, code):
    result = explain_error(api_error(status, code=code))
    assert result["category"] == "access"
    assert "model availability" in result["message"]


@pytest.mark.parametrize("status, code", [
    (400, "invalid_request_error"), (401, "invalid_api_key"), (403, None),
    (404, "model_not_found"), (429, None), (500, "server_error"),
])
def test_api_failure_reports_never_echo_body_message_or_authorization(status, code):
    result = explain_error(api_error(status, code=code))
    serialized = json.dumps(result)
    assert PRIVATE_MARKER not in serialized
    assert "Provider debug message" not in serialized
    assert "Raw exception details" not in serialized
    assert "Authorization" not in serialized
    assert result["http_status"] == status
    if status in {400, 500}:
        assert result["category"] == "api_request"


def test_local_deadline_is_separate_from_api_transport_failure():
    result = explain_error(TimeoutError("operation timed out"))
    assert result["category"] == "timeout"
    assert "classroom deadline" in result["message"]
