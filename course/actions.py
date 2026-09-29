"""A mock publish action with durable, content-bound approval and idempotency.

No network publication occurs: execution inserts the approved brief into SQLite.
The model never receives a capability that can call approve_and_publish.
"""

import hashlib
import sqlite3
import time
import uuid
from pathlib import Path


class Publisher:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS publications (
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, session_id TEXT NOT NULL,
                markdown TEXT NOT NULL, digest TEXT NOT NULL, created REAL NOT NULL,
                approved INTEGER NOT NULL DEFAULT 0, published INTEGER NOT NULL DEFAULT 0
            )""")

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def preview(self, owner, session_id, markdown):
        draft_id = uuid.uuid4().hex
        digest = hashlib.sha256(markdown.encode()).hexdigest()
        with self.connect() as db:
            db.execute(
                "INSERT INTO publications VALUES (?, ?, ?, ?, ?, ?, 0, 0)",
                (draft_id, owner, session_id, markdown, digest, time.time()),
            )
        return {"draft_id": draft_id, "digest": digest, "markdown": markdown, "published": False}

    def approve_and_publish(self, owner, draft_id, digest, *, approved, can_publish):
        if not approved or not can_publish:
            raise PermissionError("Explicit approval and publisher permission are both required.")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT owner, digest, created, published FROM publications WHERE id=?", (draft_id,)
            ).fetchone()
            if row is None or row[0] != owner or row[1] != digest:
                raise PermissionError("Draft ownership or content digest did not match.")
            if time.time() - row[2] > 600:
                raise PermissionError("Preview expired; preview the brief again.")
            already = bool(row[3])
            # The mock side effect and idempotency record commit in the SAME transaction.
            db.execute("UPDATE publications SET approved=1, published=1 WHERE id=?", (draft_id,))
        return {
            "draft_id": draft_id,
            "published": True,
            "already_published": already,
            "destination": "local mock publication table",
        }
