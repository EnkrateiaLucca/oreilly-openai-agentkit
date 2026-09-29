"""Safe failure classification using the OpenAI API Troubleshooting skill's routing."""

from openai import APIConnectionError, APIStatusError


def explain_error(error: Exception) -> dict:
    if isinstance(error, APIConnectionError):
        return {
            "category": "transport",
            "message": "No API response. Check outbound network/DNS/proxy access to api.openai.com.",
        }
    code = getattr(error, "code", None)
    error_type = getattr(error, "type", None)
    status = getattr(error, "status_code", None)
    body = getattr(error, "body", None)
    if isinstance(body, dict):
        detail = body.get("error", body)
        if isinstance(detail, dict):
            code = detail.get("code") or code
            error_type = detail.get("type") or error_type
    if status == 401:
        category, message = (
            "authentication",
            "The request was not authenticated. Check the server API key and project.",
        )
    elif (
        code
        in {
            "insufficient_quota",
            "credit_balance_exhausted",
            "organization_spend_limit_exceeded",
            "project_spend_limit_exceeded",
            "organization_usage_limit_exceeded",
        }
        or error_type == "insufficient_quota"
    ):
        category, message = (
            "quota",
            "API credits are exhausted or a spend/usage limit was reached. "
            "Check billing and the relevant limits; repeated retries will not help.",
        )
    elif code in {"rate_limit_exceeded", "slow_down"} or error_type in {
        "rate_limit_exceeded",
        "rate_limit_error",
    }:
        category, message = (
            "rate_limit",
            "Pace requests and wait before retrying. Inspect Retry-After and project rate limits.",
        )
    elif status == 429:
        category, message = (
            "quota_or_rate_limit",
            "HTTP 429 without a specific code: inspect API billing, spend limits, and rate limits before retrying.",
        )
    elif status == 403 or code == "model_not_found":
        category, message = (
            "access",
            "Check model availability, project/organization, and key scopes.",
        )
    elif isinstance(error, APIStatusError):
        category, message = (
            "api_request",
            "The API rejected or failed the request. Inspect its status/code and the current API schema.",
        )
    elif isinstance(error, TimeoutError):
        category, message = "timeout", "The classroom deadline was reached; the run was cancelled."
    else:
        category, message = (
            "local",
            str(error)
            if isinstance(error, (ValueError, RuntimeError))
            else "A local operation failed.",
        )
    result = {"category": category, "message": message}
    if category == "quota":
        billing = "https://platform.openai.com/settings/organization/billing"
        limits = "https://platform.openai.com/settings/organization/limits"
        if code == "credit_balance_exhausted":
            result["help_links"] = {"billing": billing}
        elif code == "project_spend_limit_exceeded":
            result["help_links"] = {"project_settings": "https://platform.openai.com/settings/"}
        elif code in {"organization_spend_limit_exceeded", "organization_usage_limit_exceeded"}:
            result["help_links"] = {"limits": limits}
        else:
            result["help_links"] = {"billing": billing, "limits": limits}
    if status:
        result["http_status"] = status
    if code:
        result["code"] = code
    if getattr(error, "request_id", None):
        result["request_id"] = error.request_id
    return result
