"""Prove that approval, authorization, ownership, and content all matter.

This local mock writes only to a temporary SQLite database, then removes it.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from course.actions import Publisher

if __name__ == "__main__":
    with TemporaryDirectory() as directory:
        publisher = Publisher(Path(directory) / "publications.sqlite3")
        preview = publisher.preview("teacher", "class-session", "# A brief\n\nEvidence here.")
        attempts = [
            ("missing_approval", "teacher", preview["digest"], False, True),
            ("missing_permission", "teacher", preview["digest"], True, False),
            ("wrong_owner", "another-user", preview["digest"], True, True),
            ("changed_digest", "teacher", "changed-content", True, True),
        ]
        for name, owner, digest, approved, permission in attempts:
            try:
                publisher.approve_and_publish(
                    owner, preview["draft_id"], digest, approved=approved, can_publish=permission
                )
            except PermissionError:
                print(f"{name}: denied")
            else:
                raise AssertionError(f"{name} unexpectedly published")
        first = publisher.approve_and_publish(
            "teacher", preview["draft_id"], preview["digest"], approved=True, can_publish=True
        )
        second = publisher.approve_and_publish(
            "teacher", preview["draft_id"], preview["digest"], approved=True, can_publish=True
        )
        assert first["published"] and not first["already_published"]
        assert second["already_published"]
        print("valid_request: published\nrepeated_request: already_published")
