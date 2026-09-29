# Extension: ChatKit with your own backend

The completed course UI is Streamlit. This optional exercise uses ChatKit as another interface to the same application-owned execution and permissions. It replaces the historical `archive/chatkit-workflow-app` workflow-ID dependency.

Read the [ChatKit guide](https://developers.openai.com/api/docs/guides/chatkit) and [advanced integration guide](https://developers.openai.com/api/docs/guides/custom-chatkit) before implementing the adapter. Verify the current server SDK/protocol; a ChatKit client cannot consume the course's custom SSE stream simply by changing its URL.

## Target architecture

```text
Authenticated browser + ChatKit
          ↓ ChatKit protocol / backend adapter
Current user's course session
          ↓
selected managed / Responses / SDK runtime
          ↓
shared tools + typed brief + application approval policy
```

The adapter owns the conversion between ChatKit thread items and the course backend's progress/result events. It must preserve the current user's identity, course session ownership, error states, and completed brief downloads. Store OpenAI credentials only on the server.

## Exercise

1. Create a ChatKit server endpoint using the current server integration API. Authenticate each request before loading a thread.
2. Map each ChatKit thread to a course session owned by that user. Persist that association; never accept a client-provided owner as authorization.
3. Translate the course progress stream into supported ChatKit events. Translate the final brief into assistant content and a downloadable artifact.
4. Route follow-up messages to the same mapped session. Close or expire the course session when its work is complete.
5. Implement preview and approval as explicit UI controls. Submit the exact server-created draft ID and digest. Model text and client-supplied roles cannot authorize publication.
6. Run the same evidence/failure tests plus cross-user thread access, expired sessions, duplicate approvals, and disconnect tests.

## Acceptance criteria

- No Agent Builder workflow ID or prompt-object ID is required.
- No OpenAI API key or classroom credential appears in client JavaScript or rendered messages.
- A user cannot read or mutate another user's thread/session.
- Stream disconnects produce an explicit incomplete state; they do not silently duplicate publication.
- The same fixed evaluation cases remain usable below the UI layer.

A correct solution adds an authenticated protocol adapter and reuses `course/` rather than creating a second implementation of the agent's permissions. The adapter itself is intentionally left as the optional exercise.
