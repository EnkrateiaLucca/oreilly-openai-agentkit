import base64
import json
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from course import backend, tools
from course.actions import Publisher
from course.config import Settings
from course.runtimes.offline import OfflineRuntime

USERS = {
    "alice": {"token": "alice-classroom-token", "can_publish": True},
    "bob": {"token": "bob-classroom-token", "can_publish": False},
}


def auth(name="alice"):
    return {"Authorization": f"Bearer {USERS[name]['token']}"}


@pytest.fixture
def classroom(tmp_path, monkeypatch, page_text):
    runtimes = []
    monkeypatch.setattr(tools, "paper_pages", lambda: {"paper:1": page_text})
    monkeypatch.setattr(tools, "lookup_paper", lambda query: {
        "found": False, "records": [], "source_kind": "secondary CSV summaries",
    })

    def make_runtime(name, settings, toolbox):
        runtime = OfflineRuntime(settings, toolbox)
        runtime.close = AsyncMock()
        runtimes.append(runtime)
        return runtime

    monkeypatch.setattr(backend, "make_runtime", make_runtime)
    app = backend.create_app(users=USERS, settings=Settings(
        model="test-model", max_user_turns=2, input_rate=None, output_rate=None,
    ), publisher=Publisher(tmp_path / "publication.sqlite3"))
    with TestClient(app) as client:
        yield client, runtimes


def create_session(client, name="alice", **payload):
    response = client.post("/sessions", json={"runtime": "offline", **payload}, headers=auth(name))
    assert response.status_code == 200, response.text
    return response.json()["session_id"]


def run_turn(client, session_id, name="alice", prompt="Summarize the supplied evidence."):
    return client.post(f"/sessions/{session_id}/turns", json={"prompt": prompt}, headers=auth(name))


def events(response):
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong"},
                                     {"Authorization": "Basic alice"}])
def test_authentication_is_required(classroom, headers):
    client, _ = classroom
    assert client.get("/health").json() == {"status": "ok"}
    assert client.post("/sessions", json={}, headers=headers).status_code == 401


def test_owner_isolation_hides_sessions_for_every_route(classroom):
    client, _ = classroom
    key = create_session(client)
    for method, path, payload in [
        ("post", f"/sessions/{key}/turns", {"prompt": "Read evidence"}),
        ("get", f"/sessions/{key}/brief", None),
        ("post", f"/sessions/{key}/preview", {}),
        ("delete", f"/sessions/{key}", None),
    ]:
        kwargs = {"headers": auth("bob")}
        if payload is not None:
            kwargs["json"] = payload
        assert getattr(client, method)(path, **kwargs).status_code == 404


def test_stream_returns_validated_result_then_allows_download(classroom):
    client, _ = classroom
    key = create_session(client)
    assert client.get(f"/sessions/{key}/brief", headers=auth()).status_code == 409
    assert client.post(f"/sessions/{key}/preview", headers=auth()).status_code == 409
    response = run_turn(client, key)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-store"
    received = events(response)
    assert received[0]["type"] == "progress"
    assert any(event["type"] == "tool" for event in received)
    assert received[-1]["type"] == "result"
    result = received[-1]["result"]
    assert result["runtime"] == "offline"
    assert result["citation_errors"] == []
    assert result["semantic_review"] == "required"
    assert client.get(f"/sessions/{key}/brief", headers=auth()).json()["markdown"] == result["markdown"]


def test_turn_cap_is_enforced_before_opening_another_stream(classroom):
    client, _ = classroom
    key = create_session(client)
    assert run_turn(client, key).status_code == 200
    assert run_turn(client, key).status_code == 200
    assert run_turn(client, key).status_code == 409


def test_failed_run_clears_previous_result_and_scrubs_error_details(classroom):
    client, runtimes = classroom
    key = create_session(client)
    run_turn(client, key)
    runtimes[0].run = AsyncMock(side_effect=RuntimeError("private provider error details"))
    response = run_turn(client, key)
    assert events(response)[-1]["type"] == "error"
    assert "private provider error details" not in response.text
    assert client.get(f"/sessions/{key}/brief", headers=auth()).status_code == 409
    assert client.post(f"/sessions/{key}/preview", headers=auth()).status_code == 409


def test_authorized_publication_still_requires_explicit_approval(classroom):
    client, _ = classroom
    key = create_session(client)
    run_turn(client, key, prompt="Prepare and publish the evidence brief.")
    draft = client.post(f"/sessions/{key}/preview", headers=auth()).json()
    payload = {key: draft[key] for key in ("draft_id", "digest")}
    denied = client.post("/publish", json={**payload, "approved": False}, headers=auth())
    assert denied.status_code == 403
    first = client.post("/publish", json={**payload, "approved": True}, headers=auth())
    second = client.post("/publish", json={**payload, "approved": True}, headers=auth())
    assert first.json()["published"] is True
    assert first.json()["already_published"] is False
    assert second.json()["already_published"] is True


def test_user_without_publish_permission_cannot_approve_own_draft(classroom):
    client, _ = classroom
    key = create_session(client, "bob")
    run_turn(client, key, "bob")
    draft = client.post(f"/sessions/{key}/preview", headers=auth("bob")).json()
    response = client.post("/publish", headers=auth("bob"), json={
        "draft_id": draft["draft_id"], "digest": draft["digest"], "approved": True,
    })
    assert response.status_code == 403


def test_other_users_draft_cannot_be_published_even_with_permission(classroom):
    client, _ = classroom
    key = create_session(client, "bob")
    run_turn(client, key, "bob")
    draft = client.post(f"/sessions/{key}/preview", headers=auth("bob")).json()
    response = client.post("/publish", headers=auth("alice"), json={
        "draft_id": draft["draft_id"], "digest": draft["digest"], "approved": True,
    })
    assert response.status_code == 403


def test_session_limit_and_explicit_cleanup(classroom):
    client, runtimes = classroom
    first = create_session(client)
    create_session(client)
    assert client.post("/sessions", json={}, headers=auth()).status_code == 429
    assert client.delete(f"/sessions/{first}", headers=auth()).json() == {"deleted": True}
    runtimes[0].close.assert_awaited_once()
    assert client.get(f"/sessions/{first}/brief", headers=auth()).status_code == 404
    create_session(client)


def test_cleanup_failure_keeps_session_available_for_retry(classroom):
    client, runtimes = classroom
    key = create_session(client)
    runtimes[0].close.side_effect = RuntimeError("cleanup pending")
    assert client.delete(f"/sessions/{key}", headers=auth()).status_code == 503
    runtimes[0].close.side_effect = None
    assert client.delete(f"/sessions/{key}", headers=auth()).status_code == 200
    assert runtimes[0].close.await_count == 2


@pytest.mark.parametrize("payload", [
    {"runtime": "unknown"}, {"runtime": "offline", "secret_option": True},
    {"paper_base64": "not valid base64!?"},
    {"paper_base64": base64.b64encode(b"not a PDF").decode()},
])
def test_invalid_runtime_or_upload_is_rejected(classroom, payload):
    client, runtimes = classroom
    response = client.post("/sessions", json=payload, headers=auth())
    assert response.status_code == 422
    assert runtimes == []


def test_raw_body_limit_is_enforced_before_parsing(classroom):
    client, _ = classroom
    response = client.post("/sessions", content=b"x" * 7_100_001,
                           headers={**auth(), "Content-Type": "application/json"})
    assert response.status_code == 413


def test_decoded_pdf_limit_is_enforced(classroom):
    client, runtimes = classroom
    payload = base64.b64encode(b"x" * (5 * 1024 * 1024 + 1)).decode()
    response = client.post("/sessions", json={"paper_base64": payload}, headers=auth())
    assert response.status_code == 422
    assert runtimes == []


def test_empty_pdf_is_rejected_and_uploaded_text_is_session_local(classroom, monkeypatch):
    client, runtimes = classroom

    class Page:
        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

    class Reader:
        pages = (Page(""),)

    monkeypatch.setattr(backend, "PdfReader", lambda _: Reader())
    payload = {"paper_base64": base64.b64encode(b"pdf fixture bytes").decode()}
    assert client.post("/sessions", json=payload, headers=auth()).status_code == 422
    Reader.pages = (Page("Uploaded private evidence for this specific session."),)
    uploaded = create_session(client, **payload)
    regular = create_session(client)
    assert uploaded != regular
    assert runtimes[0].tools.pages["paper:1"].startswith("Uploaded private")
    assert not runtimes[1].tools.pages["paper:1"].startswith("Uploaded private")


@pytest.mark.parametrize("prompt", ["", "x" * 3001])
def test_invalid_prompt_is_rejected_before_runtime(classroom, prompt):
    client, runtimes = classroom
    key = create_session(client)
    assert run_turn(client, key, prompt=prompt).status_code == 422
    assert runtimes[0].turns == 0
