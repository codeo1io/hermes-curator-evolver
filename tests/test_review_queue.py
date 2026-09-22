import sqlite3
import threading
import time
from types import SimpleNamespace
from typing import Any

import pytest

from hermes_curator_evolver.candidates import (
    CANDIDATE_TYPE_MEMORY,
    CANDIDATE_TYPE_REPLAY_BENCHMARK,
    Candidate,
)
from hermes_curator_evolver.review_queue import ReviewQueue


def _candidate(t: str, *, title: str = "t", evidence_refs=None) -> Candidate:
    return Candidate(
        candidate_type=t,
        title=title,
        rationale="r",
        confidence=0.9,
        evidence_refs=list(evidence_refs or ["s:1"]),
    )


def test_review_queue_initializes_schema(tmp_path):
    q = ReviewQueue(tmp_path / "queue.sqlite")

    assert q.db_path.exists()
    assert q.list_candidates() == []


def test_enqueue_is_idempotent_on_same_id(tmp_path):
    q = ReviewQueue(tmp_path / "queue.sqlite")
    c = _candidate(CANDIDATE_TYPE_MEMORY)

    first = q.enqueue(c)
    second = q.enqueue(c)

    assert first is True
    assert second is False
    rows = q.list_candidates()
    assert len(rows) == 1
    assert rows[0]["candidate_type"] == CANDIDATE_TYPE_MEMORY
    assert rows[0]["status"] == "pending"
    assert rows[0]["id"] == c.id


def test_enqueued_row_preserves_safety_defaults(tmp_path):
    q = ReviewQueue(tmp_path / "queue.sqlite")
    c = _candidate(CANDIDATE_TYPE_MEMORY)

    q.enqueue(c)

    row = q.list_candidates()[0]
    assert row["auto_apply_allowed"] is False
    assert row["requires_human_review"] is True


def test_queue_refuses_auto_apply_even_if_candidate_object_is_bypassed(tmp_path):
    q = ReviewQueue(tmp_path / "queue.sqlite")
    unsafe: Any = SimpleNamespace(
        id="unsafe",
        candidate_type=CANDIDATE_TYPE_MEMORY,
        title="unsafe",
        rationale="unsafe",
        confidence=0.9,
        evidence_refs=["s:unsafe"],
        target_skill=None,
        auto_apply_allowed=True,
        requires_human_review=True,
        metadata={},
    )

    with pytest.raises(ValueError, match="auto_apply_allowed"):
        q.enqueue(unsafe)

    assert q.list_candidates() == []


def test_queue_refuses_non_human_review_candidate_if_constructor_is_bypassed(tmp_path):
    q = ReviewQueue(tmp_path / "queue.sqlite")
    unsafe: Any = SimpleNamespace(
        id="unsafe-review",
        candidate_type=CANDIDATE_TYPE_MEMORY,
        title="unsafe",
        rationale="unsafe",
        confidence=0.9,
        evidence_refs=["s:unsafe"],
        target_skill=None,
        auto_apply_allowed=False,
        requires_human_review=False,
        metadata={},
    )

    with pytest.raises(ValueError, match="requires_human_review"):
        q.enqueue(unsafe)

    assert q.list_candidates() == []


def test_list_candidates_filters_by_status_and_type(tmp_path):
    q = ReviewQueue(tmp_path / "queue.sqlite")
    a = _candidate(CANDIDATE_TYPE_MEMORY, title="A", evidence_refs=["s:a"])
    b = _candidate(
        CANDIDATE_TYPE_REPLAY_BENCHMARK, title="B", evidence_refs=["s:b"]
    )

    q.enqueue(a)
    q.enqueue(b)
    q.update_status(a.id, "accepted")

    accepted = q.list_candidates(status="accepted")
    assert [row["id"] for row in accepted] == [a.id]

    pending = q.list_candidates(status="pending")
    assert [row["id"] for row in pending] == [b.id]

    by_type = q.list_candidates(candidate_type=CANDIDATE_TYPE_MEMORY)
    assert [row["id"] for row in by_type] == [a.id]


def test_update_status_validates_value(tmp_path):
    q = ReviewQueue(tmp_path / "queue.sqlite")
    c = _candidate(CANDIDATE_TYPE_MEMORY)
    q.enqueue(c)

    with pytest.raises(ValueError):
        q.update_status(c.id, "bogus")

    assert q.update_status(c.id, "rejected") is True
    rows = q.list_candidates(status="rejected")
    assert rows and rows[0]["id"] == c.id


def test_update_status_unknown_id_returns_false(tmp_path):
    q = ReviewQueue(tmp_path / "queue.sqlite")

    assert q.update_status("nope", "accepted") is False


def test_review_queue_persists_across_instances(tmp_path):
    db = tmp_path / "queue.sqlite"
    first = ReviewQueue(db)
    c = _candidate(CANDIDATE_TYPE_MEMORY)
    first.enqueue(c)

    second = ReviewQueue(db)
    rows = second.list_candidates()

    assert len(rows) == 1
    assert rows[0]["id"] == c.id


def test_u82_connection_sets_busy_timeout_and_journal_limits(tmp_path):
    """U82: every queue connection carries the U45-class hardening pragmas."""

    q = ReviewQueue(tmp_path / "queue.sqlite")
    conn = q._connect()
    try:
        timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
        assert timeout == 5000
        mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()
        if mode == "wal":
            limit = conn.execute("PRAGMA journal_size_limit").fetchone()[0]
            assert limit == 64 * 1024 * 1024
    finally:
        conn.close()


def test_u82_enqueue_lands_under_external_holder_with_wide_margin(tmp_path):
    """U82 parity reproducer: a queue write under an external EXCLUSIVE holder.

    Mirrors the evidence store's U45 bounded-write test
    (test_u45_hook_writes_are_bounded_under_one_external_holder) but with a
    WIDE margin by design (prioritize-phase mandate): the holder releases at
    ~6s, past one busy_timeout window; the hardened connection must absorb
    the hold across the bounded retry ladder and land the enqueue instead of
    raising OperationalError (the pre-U82 behaviour: default 5s timeout, no
    busy pragma, no retry).
    """

    q = ReviewQueue(tmp_path / "queue.sqlite")
    q.enqueue(_candidate(CANDIDATE_TYPE_MEMORY, title="seed"))

    held = threading.Event()
    release = threading.Event()

    def hold() -> None:
        conn = sqlite3.connect(str(q.db_path), timeout=30.0)
        try:
            conn.execute("BEGIN EXCLUSIVE")
            held.set()
            release.wait(timeout=6.0)
            conn.rollback()
        finally:
            conn.close()

    holder = threading.Thread(target=hold)
    holder.start()
    try:
        assert held.wait(timeout=5.0)
        started = time.monotonic()
        inserted = q.enqueue(
            _candidate(CANDIDATE_TYPE_REPLAY_BENCHMARK, title="contended")
        )
        elapsed = time.monotonic() - started
    finally:
        release.set()
        holder.join(timeout=10.0)

    assert inserted is True
    assert elapsed >= 5.0, elapsed
    assert elapsed < 12.0, elapsed
    rows = q.list_candidates()
    assert {row["title"] for row in rows} == {"seed", "contended"}
