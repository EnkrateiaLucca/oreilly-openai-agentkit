"""Authenticated classroom backend: one process, in-memory conversation state.

Deployments need TLS, an identity provider, shared state, and a job queue.
The SQLite publisher demonstrates durable approval across process restarts.
"""

import asyncio
import base64
import json
import os
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from io import BytesIO

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import Field
from pypdf import PdfReader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from course.actions import Publisher
from course.config import ROOT, Settings
from course.runtimes import make_runtime
from course.schemas import StrictModel
from course.tools import ToolBox


class NewSession(StrictModel):
    runtime: str = Field(default="offline", pattern="^(offline|responses|sdk|managed)$")
    paper_base64: str | None = Field(default=None, max_length=7_000_000)


class Task(StrictModel):
    prompt: str = Field(min_length=1, max_length=3000)


class Approval(StrictModel):
    draft_id: str
    digest: str
    approved: bool


@dataclass
class Session:
    owner: str
    runtime: object
    touched: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    result: object = None


class BodyLimit(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method in {"POST", "PUT", "PATCH"}:
            data = bytearray()
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data) > 7_100_000:
                    return JSONResponse(
                        {"detail": "Upload exceeds the classroom limit."}, status_code=413
                    )
            request._body = bytes(data)
        return await call_next(request)


def create_app(*, users=None, settings=None, publisher=None):
    settings = settings or Settings()
    sessions: dict[str, Session] = {}
    slots = asyncio.Semaphore(4)
    publication = publisher or Publisher(ROOT / ".runtime/publications.sqlite3")

    def configured_users():
        if users is not None:
            return users
        raw = os.getenv("COURSE_USERS_JSON")
        if raw:
            return json.loads(raw)
        path = ROOT / ".runtime/access.json"
        if path.exists():
            return json.loads(path.read_text())
        raise HTTPException(503, "Run python -m course access to configure classroom logins.")

    async def principal(authorization: str = Header(default="")):
        if not authorization.startswith("Bearer "):
            raise HTTPException(401, "Sign in with your classroom token.")
        token = authorization[7:]
        for name, account in configured_users().items():
            if secrets.compare_digest(token, account["token"]):
                return {"name": name, "can_publish": account.get("can_publish", False)}
        raise HTTPException(401, "Invalid classroom token.")

    def owned(session_id, user):
        session = sessions.get(session_id)
        if session is None or session.owner != user["name"]:
            raise HTTPException(404, "Session not found.")
        return session

    async def expire():
        while True:
            await asyncio.sleep(30)
            for key, session in list(sessions.items()):
                if not session.lock.locked() and time.monotonic() - session.touched > 900:
                    sessions.pop(key, None)
                    try:
                        await session.runtime.close()
                    except Exception:
                        pass  # Pending managed cleanup is kept in its resource manifest.

    @asynccontextmanager
    async def lifespan(app):
        reaper = asyncio.create_task(expire())
        yield
        reaper.cancel()
        await asyncio.gather(reaper, return_exceptions=True)
        await asyncio.gather(
            *(s.runtime.close() for s in sessions.values()), return_exceptions=True
        )

    app = FastAPI(title="Building Agents with OpenAI", lifespan=lifespan)
    app.add_middleware(BodyLimit)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/sessions")
    async def create(body: NewSession, user=Depends(principal)):
        if sum(s.owner == user["name"] for s in sessions.values()) >= 2 or len(sessions) >= 20:
            raise HTTPException(429, "Close an existing session before opening another.")
        pages = None
        if body.paper_base64:
            try:
                data = base64.b64decode(body.paper_base64, validate=True)
                if len(data) > 5 * 1024 * 1024:
                    raise ValueError("File too large.")
                reader = PdfReader(BytesIO(data))
                pages = {
                    f"paper:{i + 1}": (page.extract_text() or "")[:12000]
                    for i, page in enumerate(reader.pages[:12])
                }
                if not any(pages.values()):
                    raise ValueError("No extractable text.")
            except Exception:
                raise HTTPException(
                    422, "Use a text PDF up to 5 MiB. Scanned/encrypted PDFs are unsupported."
                ) from None
        try:
            toolbox = ToolBox(pages=pages, max_calls=settings.max_tool_calls)
            runtime = make_runtime(body.runtime, settings, toolbox)
            if body.paper_base64 and body.runtime == "managed":
                runtime.paper_bytes = data
        except ValueError:
            raise HTTPException(
                503, "Runtime unavailable; configure the server API key or use offline."
            ) from None
        key = uuid.uuid4().hex
        sessions[key] = Session(owner=user["name"], runtime=runtime)
        return {"session_id": key, "runtime": body.runtime}

    @app.post("/sessions/{session_id}/turns")
    async def turn(session_id: str, body: Task, user=Depends(principal)):
        session = owned(session_id, user)
        if session.lock.locked():
            raise HTTPException(409, "A turn is already running.")
        if session.runtime.broken or session.runtime.turns >= settings.max_user_turns:
            raise HTTPException(409, "Start a new session to continue.")
        await session.lock.acquire()
        session.touched = time.monotonic()
        queue = asyncio.Queue(maxsize=2000)

        async def produce():
            try:
                async with slots:
                    session.result = None
                    result = await session.runtime.run(body.prompt, queue.put_nowait)
                    session.result = result
                    await queue.put({"type": "result", "result": result.model_dump()})
            except Exception as exc:
                await queue.put(
                    {
                        "type": "error",
                        "error": type(exc).__name__,
                        "message": "Run stopped. Check API access, evidence, and limits; start a new session.",
                    }
                )
            finally:
                await queue.put(None)

        async def stream():
            worker = asyncio.create_task(produce())
            try:
                while True:
                    event = await queue.get()
                    if event is None:
                        break
                    yield "data: " + json.dumps(event) + "\n\n"
            finally:
                worker.cancel()
                # Free space for the producer's final marker even if the client disconnected.
                while not queue.empty():
                    queue.get_nowait()
                await asyncio.gather(worker, return_exceptions=True)
                session.touched = time.monotonic()
                session.lock.release()

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    @app.get("/sessions/{session_id}/brief")
    async def brief(session_id: str, user=Depends(principal)):
        session = owned(session_id, user)
        if session.result is None:
            raise HTTPException(409, "No validated brief is available.")
        return {"markdown": session.result.markdown}

    @app.post("/sessions/{session_id}/preview")
    async def preview(session_id: str, user=Depends(principal)):
        session = owned(session_id, user)
        if session.result is None or session.lock.locked():
            raise HTTPException(409, "Finish a validated brief first.")
        return publication.preview(user["name"], session_id, session.result.markdown)

    @app.post("/publish")
    async def publish(body: Approval, user=Depends(principal)):
        try:
            return publication.approve_and_publish(
                user["name"],
                body.draft_id,
                body.digest,
                approved=body.approved,
                can_publish=user["can_publish"],
            )
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from None

    @app.delete("/sessions/{session_id}")
    async def delete(session_id: str, user=Depends(principal)):
        session = owned(session_id, user)
        if session.lock.locked():
            raise HTTPException(409, "Wait for the active turn to stop.")
        async with session.lock:
            try:
                await session.runtime.close()
            except Exception:
                raise HTTPException(
                    503, "Cleanup pending; instructor should run python -m course cleanup."
                ) from None
            del sessions[session_id]
        return {"deleted": True}

    return app


app = create_app()
