"""SQLite-backed review queue for curator-evolver candidates.

Persistence-only. This module stores candidate JSON and lifecycle status; it
never writes to user memory or skill files.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .candidates import CANDIDATE_TYPES, Candidate
from .storage import _is_busy_error

logger = logging.getLogger(__name__)

STATUS_PENDING = "pending"
STATUS_ACCEPTED = "accepted"
STATUS_REJECTED = "rejected"

VALID_STATUSES = {STATUS_PENDING, STATUS_ACCEPTED, STATUS_REJECTED}

# ---------------------------------------------------------------------------
# Concurrency hardening (roadmap U93 — parity port of the evidence store's
# U7a/U45 WAL layer from storage.py, mirrored locally so this stays a
# queue-only diff; storage.py itself is untouched):
#   * busy_timeout so a short overlapping external write waits instead of
#     erroring the enqueue/status update away
#   * WAL (with DELETE fallback on WAL-incompatible filesystems, logged
#     once per path) so queue writers and readers stop blocking each other
#   * journal_size_limit so the WAL cannot strand the high-water mark
#   * bounded retry with backoff so realistic external contention lands
#     instead of dropping the write (the exact discipline U45 gave the
#     evidence store; constants mirror storage.py's single-flight recipe)
# An infinite lock holder is not survivable by any bounded design; retries
# exhaust and the OperationalError propagates to the caller.
# ---------------------------------------------------------------------------
_BUSY_TIMEOUT_MS = 5_000
_WRITE_ATTEMPTS = 2
_RETRY_BACKOFF_S = 0.25
_WAL_SIZE_LIMIT_BYTES = 64 * 1024 * 1024
_WAL_INCOMPAT_MARKERS = (
    "locking protocol",  # SQLITE_PROTOCOL on NFS/SMB/FUSE
    "not authorized",  # some FUSE mounts refuse the WAL pragma outright
    "disk i/o error",  # ZFS SHM corruption under concurrent connections
)
_journal_mode_lock = threading.Lock()
_journal_mode_cache: dict[str, str] = {}
_journal_mode_warned: set[str] = set()


def _apply_journal_mode(conn: sqlite3.Connection, db_path: Path) -> None:
    """Enable WAL once per path, falling back to DELETE (parity port).

    Same recipe as the evidence store's journal-mode handling: the pragma
    is a query-that-sets, WAL-incompatible filesystems fall back to DELETE
    (logged once per path), a database already in WAL is never downgraded,
    and the per-path cache skips the pragma on later connections entirely.
    """

    try:
        key = str(db_path.resolve())
    except OSError:
        key = str(db_path)
    with _journal_mode_lock:
        cached = _journal_mode_cache.get(key)
    if cached:
        return
    mode = ""
    try:
        row = conn.execute("PRAGMA journal_mode=WAL").fetchone()
        mode = str(row[0]).strip().lower() if row and row[0] is not None else ""
    except sqlite3.OperationalError as exc:
        message = str(exc).lower()
        if not any(marker in message for marker in _WAL_INCOMPAT_MARKERS):
            raise
    if mode != "wal":
        with _journal_mode_lock:
            if key not in _journal_mode_warned:
                _journal_mode_warned.add(key)
                logger.warning(
                    "curator-evolver review queue fell back to DELETE journal mode "
                    "for %s (WAL unavailable); concurrent writers may block each other",
                    key,
                )
    with _journal_mode_lock:
        _journal_mode_cache[key] = mode or "delete"


_SCHEMA = """
CREATE TABLE IF NOT EXISTS review_candidates (
    id TEXT PRIMARY KEY,
    candidate_type TEXT NOT NULL,
    title TEXT NOT NULL,
    rationale TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence_refs_json TEXT NOT NULL,
    target_skill TEXT,
    auto_apply_allowed INTEGER NOT NULL DEFAULT 0,
    requires_human_review INTEGER NOT NULL DEFAULT 1,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_review_candidates_status
    ON review_candidates(status);
CREATE INDEX IF NOT EXISTS idx_review_candidates_type
    ON review_candidates(candidate_type);
"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "candidate_type": row["candidate_type"],
        "title": row["title"],
        "rationale": row["rationale"],
        "confidence": float(row["confidence"]),
        "evidence_refs": json.loads(row["evidence_refs_json"] or "[]"),
        "target_skill": row["target_skill"],
        "auto_apply_allowed": bool(row["auto_apply_allowed"]),
        "requires_human_review": bool(row["requires_human_review"]),
        "metadata": json.loads(row["metadata_json"] or "{}"),
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


class ReviewQueue:
    """Tiny SQLite review queue for candidate triage.

    Stores already-classified Candidate objects only. The queue is
    write-once-per-id: enqueueing the same id twice is a no-op so that mining
    can be re-run safely.
    """

    def __init__(self, db_path: Path | str, *, create: bool = True) -> None:
        self.db_path = Path(db_path)
        self._create = create
        if create:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            def _init_schema(conn: sqlite3.Connection) -> None:
                conn.executescript(_SCHEMA)
                conn.commit()

            self._write_with_retry(_init_schema)
        elif not self.db_path.exists():
            raise FileNotFoundError(f"review queue DB does not exist: {self.db_path}")

    def _connect(self) -> sqlite3.Connection:
        if self._create:
            conn = sqlite3.connect(self.db_path, timeout=_BUSY_TIMEOUT_MS / 1000)
        else:
            conn = sqlite3.connect(
                f"file:{self.db_path.resolve().as_posix()}?mode=rw",
                uri=True,
                timeout=_BUSY_TIMEOUT_MS / 1000,
            )
        conn.row_factory = sqlite3.Row
        try:
            conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
            try:
                conn.execute(f"PRAGMA journal_size_limit={_WAL_SIZE_LIMIT_BYTES}")
            except sqlite3.OperationalError:  # pragma: no cover - best effort
                logger.debug("review queue journal_size_limit not applied")
            _apply_journal_mode(conn, self.db_path)
        except sqlite3.Error:
            conn.close()
            raise
        return conn

    def _write_with_retry(self, action) -> Any:
        """Run a write with bounded retry under external contention (U93).

        A busy/locked error means an *external* process holds the write lock
        (auto-run in a separate shell, a manual ``sqlite3`` session): that is
        retried with linear backoff so realistic overlap lands instead of
        dropping the enqueue. Any other database error is an environment
        failure and fails fast — no timeout burn, no retry.
        """

        last_exc: sqlite3.OperationalError | None = None
        for attempt in range(_WRITE_ATTEMPTS):
            conn: sqlite3.Connection | None = None
            try:
                conn = self._connect()
                with conn:
                    result = action(conn)
                return result
            except sqlite3.OperationalError as exc:
                if not _is_busy_error(exc):
                    raise
                last_exc = exc
                if attempt + 1 < _WRITE_ATTEMPTS:
                    time.sleep(_RETRY_BACKOFF_S * (attempt + 1))
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except sqlite3.Error:  # pragma: no cover - teardown best effort
                        pass
        raise last_exc  # type: ignore[misc]

    def enqueue(self, candidate: Candidate) -> bool:
        """Insert a candidate; return True if newly inserted, False if duplicate."""
        if candidate.candidate_type not in CANDIDATE_TYPES:
            raise ValueError(
                f"refusing to enqueue unknown candidate_type "
                f"{candidate.candidate_type!r}"
            )
        if candidate.auto_apply_allowed:
            raise ValueError("refusing to enqueue auto_apply_allowed=True candidate")
        if not candidate.requires_human_review:
            raise ValueError("refusing to enqueue requires_human_review=False candidate")
        now = _utc_now()

        def _insert(conn: sqlite3.Connection) -> bool:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO review_candidates (
                    id,
                    candidate_type,
                    title,
                    rationale,
                    confidence,
                    evidence_refs_json,
                    target_skill,
                    auto_apply_allowed,
                    requires_human_review,
                    metadata_json,
                    status,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate.id,
                    candidate.candidate_type,
                    candidate.title,
                    candidate.rationale,
                    float(candidate.confidence),
                    json.dumps(list(candidate.evidence_refs), ensure_ascii=False),
                    candidate.target_skill,
                    int(bool(candidate.auto_apply_allowed)),
                    int(bool(candidate.requires_human_review)),
                    json.dumps(candidate.metadata or {}, ensure_ascii=False, sort_keys=True),
                    STATUS_PENDING,
                    now,
                    now,
                ),
            )
            conn.commit()
            return cur.rowcount == 1

        return self._write_with_retry(_insert)

    def list_candidates(
        self,
        *,
        status: str | None = None,
        candidate_type: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if status is not None:
            if status not in VALID_STATUSES:
                raise ValueError(f"invalid status filter {status!r}")
            clauses.append("status = ?")
            params.append(status)
        if candidate_type is not None:
            if candidate_type not in CANDIDATE_TYPES:
                raise ValueError(
                    f"invalid candidate_type filter {candidate_type!r}"
                )
            clauses.append("candidate_type = ?")
            params.append(candidate_type)
        sql = "SELECT * FROM review_candidates"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at ASC, id ASC"
        conn = self._connect()
        try:
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
        return [_row_to_dict(r) for r in rows]

    def update_status(self, candidate_id: str, new_status: str) -> bool:
        if new_status not in VALID_STATUSES:
            raise ValueError(
                f"new_status must be one of {sorted(VALID_STATUSES)!r}"
            )
        now = _utc_now()

        def _update(conn: sqlite3.Connection) -> bool:
            cur = conn.execute(
                """
                UPDATE review_candidates
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_status, now, candidate_id),
            )
            conn.commit()
            return cur.rowcount > 0

        return self._write_with_retry(_update)
