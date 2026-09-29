"""Streamlit UI: API key stays in the authenticated research backend."""

import base64
import json
import os

import httpx
import streamlit as st

st.set_page_config(page_title="Building Agents with OpenAI", page_icon="📚", layout="wide")
st.title("Research brief studio")
st.caption("Read a paper, inspect the evidence, and revise a cited brief.")
API = os.getenv("COURSE_BACKEND_URL", "http://127.0.0.1:8000")


def request(method, path, **kwargs):
    try:
        response = httpx.request(
            method,
            API + path,
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            timeout=150,
            **kwargs,
        )
        if response.is_error:
            st.error(response.json().get("detail", "The backend could not complete the request."))
            st.stop()
        return response.json()
    except httpx.HTTPError:
        st.error("Backend connection failed. Start the backend and check its address.")
        st.stop()


with st.sidebar:
    st.header("Classroom sign-in")
    token = st.text_input("Classroom token", type="password", key="token")
    st.caption("Use the instructor's classroom token. API keys belong on the backend.")
    runtime = st.selectbox(
        "Runtime",
        ["offline", "managed", "responses", "sdk"],
        disabled=bool(st.session_state.get("session_id")),
    )
    if runtime == "offline":
        st.info("Offline rehearsal: deterministic output, no model call.")
    uploaded = st.file_uploader(
        "Paper PDF (optional, up to 5 MiB)",
        type=["pdf"],
        disabled=bool(st.session_state.get("session_id")),
    )
    st.caption("Leave empty to use the course paper. Tools can read text from up to 12 pages.")
    if st.button("Start session", disabled=not token or bool(st.session_state.get("session_id"))):
        body = {"runtime": runtime}
        if uploaded:
            if uploaded.size > 5 * 1024 * 1024:
                st.error("Choose a PDF up to 5 MiB.")
                st.stop()
            body["paper_base64"] = base64.b64encode(uploaded.getvalue()).decode()
        st.session_state.session_id = request("POST", "/sessions", json=body)["session_id"]
        st.session_state.messages = []
        st.session_state.session_token = token
        st.rerun()
    if st.button("Close session", disabled=not st.session_state.get("session_id")):
        request("DELETE", f"/sessions/{st.session_state.session_id}")
        for key in ["session_id", "messages", "result", "preview", "session_token"]:
            st.session_state.pop(key, None)
        st.rerun()

if not st.session_state.get("session_id"):
    st.info("Sign in and start a session. The offline option works without an OpenAI key.")
    st.stop()
if token != st.session_state.get("session_token"):
    # Do not show a previous principal's session after the login changes.
    for key in ["session_id", "messages", "result", "preview", "session_token"]:
        st.session_state.pop(key, None)
    st.rerun()

for message in st.session_state.get("messages", []):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Read page 1, look up Context Engineering, and write two cited claims.")
if prompt:
    st.session_state.pop("preview", None)
    st.session_state.pop("result", None)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.status("Researching…", expanded=True) as status:
        try:
            received = False
            with httpx.stream(
                "POST",
                API + f"/sessions/{st.session_state.session_id}/turns",
                headers={"Authorization": f"Bearer {token}"},
                json={"prompt": prompt},
                timeout=150,
            ) as response:
                if response.is_error:
                    st.error(json.loads(response.read()).get("detail", "Request failed."))
                    st.stop()
                for line in response.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    event = json.loads(line[6:])
                    if event["type"] in {"progress", "tool"}:
                        st.write(event.get("message", event.get("name")))
                    elif event["type"] == "error":
                        st.error(event["message"])
                        status.update(label="Run stopped", state="error")
                        st.stop()
                    elif event["type"] == "result":
                        received = True
                        st.session_state.result = event["result"]
                        st.session_state.messages.append(
                            {"role": "assistant", "content": event["result"]["markdown"]}
                        )
            if not received:
                st.error("The stream ended without a brief. Close this session and start again.")
                st.stop()
            status.update(label="Brief ready", state="complete")
        except httpx.HTTPError:
            st.error("Backend connection failed. Start the backend and check its address.")
            st.stop()
    st.rerun()

if result := st.session_state.get("result"):
    st.download_button("Download brief", result["markdown"], "research-brief.md", "text/markdown")
    with st.expander("Inspect run and evidence"):
        st.json(
            {
                key: result[key]
                for key in [
                    "runtime",
                    "model",
                    "usage",
                    "latency_seconds",
                    "tool_calls",
                    "semantic_review",
                ]
            }
        )
    st.caption("Quote checks passed. Review whether each claim follows from its evidence.")
    if st.button("Preview mock publication"):
        st.session_state.preview = request(
            "POST", f"/sessions/{st.session_state.session_id}/preview"
        )
    if preview := st.session_state.get("preview"):
        st.markdown(preview["markdown"])
        approved = st.checkbox(
            "I reviewed this exact brief and approve mock publication", key=preview["draft_id"]
        )
        if st.button("Publish once", disabled=not approved):
            outcome = request(
                "POST",
                "/publish",
                json={
                    "draft_id": preview["draft_id"],
                    "digest": preview["digest"],
                    "approved": approved,
                },
            )
            st.success(
                "Already published."
                if outcome["already_published"]
                else "Saved to the local mock publication table."
            )
