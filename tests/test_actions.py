import pytest

from course.actions import Publisher


@pytest.fixture
def publisher(tmp_path):
    return Publisher(tmp_path / "publication.sqlite3")


@pytest.mark.parametrize("approved, can_publish", [(False, True), (True, False), (False, False)])
def test_approval_and_permission_are_independently_required(publisher, approved, can_publish):
    draft = publisher.preview("alice", "session-1", "# Evidence-bound draft")
    with pytest.raises(PermissionError, match="both required"):
        publisher.approve_and_publish("alice", draft["draft_id"], draft["digest"],
                                      approved=approved, can_publish=can_publish)
    with publisher.connect() as db:
        assert db.execute("SELECT approved, published FROM publications").fetchone() == (0, 0)


@pytest.mark.parametrize("owner, draft_id, digest", [
    ("bob", None, None), ("alice", "unknown-draft", None),
    ("alice", None, "changed-content-digest"),
])
def test_other_owner_unknown_draft_and_tampered_digest_are_denied(publisher, owner, draft_id, digest):
    draft = publisher.preview("alice", "session-1", "# Original draft")
    with pytest.raises(PermissionError, match="did not match"):
        publisher.approve_and_publish(owner, draft_id or draft["draft_id"], digest or draft["digest"],
                                      approved=True, can_publish=True)


def test_approval_is_bound_to_the_exact_preview(publisher):
    original = publisher.preview("alice", "session-1", "# First draft")
    updated = publisher.preview("alice", "session-1", "# Revised draft")
    assert original["digest"] != updated["digest"]
    with pytest.raises(PermissionError):
        publisher.approve_and_publish("alice", updated["draft_id"], original["digest"],
                                      approved=True, can_publish=True)


def test_replay_is_idempotent_and_persists_across_instances(publisher):
    draft = publisher.preview("alice", "session-1", "# Approved draft")
    first = publisher.approve_and_publish("alice", draft["draft_id"], draft["digest"],
                                         approved=True, can_publish=True)
    restarted = Publisher(publisher.path)
    replay = restarted.approve_and_publish("alice", draft["draft_id"], draft["digest"],
                                          approved=True, can_publish=True)
    assert first["published"] and not first["already_published"]
    assert replay["published"] and replay["already_published"]
    with restarted.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM publications WHERE published=1").fetchone() == (1,)
        assert db.execute("SELECT markdown FROM publications").fetchone() == ("# Approved draft",)


def test_expired_preview_requires_a_fresh_preview(publisher, monkeypatch):
    draft = publisher.preview("alice", "session-1", "# Draft")
    with publisher.connect() as db:
        db.execute("UPDATE publications SET created=0 WHERE id=?", (draft["draft_id"],))
    monkeypatch.setattr("course.actions.time.time", lambda: 601)
    with pytest.raises(PermissionError, match="expired"):
        publisher.approve_and_publish("alice", draft["draft_id"], draft["digest"],
                                      approved=True, can_publish=True)
