# Research brief application

The course app serves the same paper research task through a Streamlit interface and a separate authenticated FastAPI backend. Begin in **offline** mode; select a live runtime only after its access check succeeds.

## Start

From the repository root:

```bash
uv sync --extra class --extra app --extra dev
uv run python -m course access
make backend
```

In another terminal:

```bash
make app
```

Open the local address printed by Streamlit. Use a generated classroom bearer token to sign in. Keep token files private and off the projector. The OpenAI key belongs to the backend environment, never to a browser field.

## Demonstrate

1. Choose offline, managed, Responses, or SDK and start a session.
2. Use the fixture paper, or upload a text PDF within the 5 MiB classroom limit. The demo reads at most 12 pages; scanned/encrypted PDFs are unsupported.
3. Ask for a short brief with evidence and related records. Watch progress and inspect the citations.
4. Follow up in the same session; download the completed Markdown brief.
5. Preview the exact brief, explicitly approve as a user with publisher permission, and publish to the **local mock table**. Repeat approval to inspect execute-once behavior.
6. Close the session. Run `uv run python -m course cleanup` for any pending managed resources after an interruption.

## Application boundaries

- Each bearer token maps to a server-configured user and publisher permission. Knowing another session's ID does not grant access.
- The server accepts at most two open sessions per user and twenty overall, serializes a session's turns, caps active work, and expires idle sessions after fifteen minutes.
- The shared runtime enforces per-task deadlines, input/turn/tool limits, and cancellation. Managed API bounds differ from local-loop bounds; read [lesson 02](../../lessons/02-managed/README.md).
- The backend emits progress/result/error events. It offers only completed, validated briefs for download or preview.
- Preview binds exact Markdown to an owner and digest. Approval, server permission, ownership, expiry, and digest must all pass before the mock side effect.
- Conversation state is in memory; restarting the backend ends those conversations. Mock publications persist in local SQLite.

This is a classroom application, not a public hosting recipe. Add TLS, a production identity provider, durable shared conversation state, a job queue, operational logging, and reviewed retention before public deployment. The optional [ChatKit integration exercise](../../optional/chatkit/README.md) uses the same backend boundaries.

## Expected errors

- Invalid/missing classroom token: sign in using a valid locally generated token.
- No API key or denied model/runtime access: configure the backend project or choose offline.
- No extractable text: choose a supported text PDF.
- Limit reached or incomplete run: create a new session after inspecting the error; do not claim a partial answer is a completed brief.
- Publication denied: inspect explicit approval, publisher permission, preview owner, digest, and expiry.

For actual release test results, see [verification.md](../../docs/verification.md).
