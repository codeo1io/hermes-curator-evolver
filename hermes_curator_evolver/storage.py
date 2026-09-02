"""SQLite evidence storage for Hermes Curator Evolver."""

from __future__ import annotations

import atexit
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .candidates import looks_like_error
from .paths import default_db_path

logger = logging.getLogger(__name__)

_SQLITE_HEADER = b"SQLite format 3\x00"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tool_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    session_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    duration_ms INTEGER,
    is_error INTEGER NOT NULL,
    skill_name TEXT,
    args_json TEXT NOT NULL,
    result_preview TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tool_events_created ON tool_events(created_at);
CREATE INDEX IF NOT EXISTS idx_tool_events_skill ON tool_events(skill_name);
CREATE INDEX IF NOT EXISTS idx_tool_events_backfill_key ON tool_events(session_id, task_id, tool_name);

CREATE TABLE IF NOT EXISTS turn_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    session_id TEXT NOT NULL,
    model TEXT NOT NULL,
    platform TEXT NOT NULL,
    user_preview TEXT NOT NULL,
    assistant_preview TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_turn_events_created ON turn_events(created_at);
CREATE INDEX IF NOT EXISTS idx_turn_events_session ON turn_events(session_id);

CREATE TABLE IF NOT EXISTS session_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    session_id TEXT NOT NULL,
    completed INTEGER NOT NULL,
    interrupted INTEGER NOT NULL,
    model TEXT NOT NULL,
    platform TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_session_events_created ON session_events(created_at);
CREATE INDEX IF NOT EXISTS idx_session_events_session ON session_events(session_id);
"""

# ---------------------------------------------------------------------------
# Concurrency hardening (roadmap U7a; recipe ported from the host state
# store's WAL layer — hermes_state.py journal-mode handling):
#   * WAL so hook/backfill/auto-run writers stop blocking each other's reads
#   * busy_timeout so a short overlapping write waits instead of erroring
#   * journal_size_limit so the WAL cannot strand the high-water mark forever
#   * WAL-incompatible filesystems (NFS/SMB markers) fall back to DELETE mode,
#     logged once per path — never downgrading a database already in WAL
#   * bounded retry with backoff so realistic contention lands instead of
#     dropping the event (assessment P4: one concurrent writer dropped hook
#     events wholesale)
# An infinite lock holder is not survivable by any bounded design; retries
# exhaust, and the hook boundary logs the event identity rather than
# swallowing it silently.
# ---------------------------------------------------------------------------
_BUSY_TIMEOUT_MS = 5_000
# Single-flight warm writer (roadmap U45, upstream #101191): our own writers
# serialize on the per-path lock and share one cached connection, so retries
# only ever wait out an EXTERNAL holder. Two windows (~10.5s worst case)
# bound the hook-path stall; beyond that the event is dropped and surfaced
# by the hooks boundary instead of growing the gateway request's latency —
# the 3-attempt ladder's third window bought durability only for holders
# lasting 10–15s, which is not worth an extra 5s of hook stall.
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

# ---------------------------------------------------------------------------
# Warm-writer topology (roadmap U45; recipe from upstream PR #101191's
# single-flight writer registry, errno split per #101202):
#   * ONE cached connection per resolved database path per process — the
#     old connect-per-record_* pattern leaked an open connection per call
#     (the sqlite3 transaction context commits but never closes), and every
#     garbage-collected connection fires a close-time WAL checkpoint against
#     the live writer — the corruption-incident precursor #101191 closed
#     upstream.
#   * All use of a path's connection is serialized through that path's lock,
#     so in-process writers (hooks vs. backfill vs. auto-run threads) queue
#     instead of contending; busy_timeout still covers external processes.
#   * Connections are registered for close-at-exit; an explicit ``close()``
#     per store is available for callers that want deterministic teardown.
# ---------------------------------------------------------------------------
_connection_lock = threading.Lock()
_connections: dict[str, sqlite3.Connection] = {}
_path_locks: dict[str, threading.RLock] = {}
_atexit_hook_installed = False


def _close_cached_connections() -> None:
    """Close every warm connection at interpreter exit (best effort)."""

    with _connection_lock:
        connections = list(_connections.values())
        _connections.clear()
    for connection in connections:
        try:
            connection.close()
        except sqlite3.Error:  # pragma: no cover - teardown best effort
            pass


def _install_atexit_hook() -> None:
    global _atexit_hook_installed
    if not _atexit_hook_installed:
        atexit.register(_close_cached_connections)
        _atexit_hook_installed = True


def _is_busy_error(exc: sqlite3.OperationalError) -> bool:
    message = str(exc).lower()
    return "locked" in message or "busy" in message


def _sanitize_nul(value: Any) -> Any:
    """Strip real NUL characters from a value before serialization.

    NUL bytes are the founding perpetual-rollback poison (roadmap U1): once a
    NUL reaches ``json.dumps`` it is serialized as the ``\\u0000`` escape,
    which decodes back to a real NUL on every later read and kills skill
    validation forever. Stripping the character from string values *before*
    serialization closes every encoding at once — no ``\\u0000`` escape is
    ever emitted — while literal text such as ``"use printf '\\x00'"`` in
    documentation survives untouched (assessment N5: the old post-hoc text
    replacement both missed the escape and mangled legitimate literals).
    """

    if isinstance(value, str):
        return value.replace("\x00", "")
    if isinstance(value, dict):
        return {key: _sanitize_nul(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize_nul(item) for item in value]
    return value


def _strip_nul_bytes(text: str) -> str:
    """Remove real NUL characters from serialized text.

    Final safety net for already-serialized previews (roadmap U1/U37): only
    the actual control character is removed. Literal backslash spellings
    (``\\x00``, ``\\u0000`` typed as documentation text) are legitimate
    content, round-trip harmlessly through JSON, and are preserved.
    """
    return text.replace("\x00", "")


MANAGE_TOOL_NAME = "skill" + "_" + "manage"
SKILL_TOOL_NAMES = {"skill_view", MANAGE_TOOL_NAME}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def cutoff_iso(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=max(days, 0))).isoformat(
        timespec="seconds"
    )


def _compact(value: Any, limit: int) -> str:
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(_sanitize_nul(value), ensure_ascii=False, sort_keys=True)
        except TypeError:
            text = repr(value)
    text = _strip_nul_bytes(text)
    if len(text) <= limit:
        return text
    return text[: max(limit - 1, 0)] + "…"


def _json_dumps(value: Any, limit: int) -> str:
    try:
        text = json.dumps(_sanitize_nul(value or {}), ensure_ascii=False, sort_keys=True)
    except TypeError:
        text = json.dumps({"repr": repr(value)}, ensure_ascii=False, sort_keys=True)
    text = _strip_nul_bytes(text)
    if len(text) <= limit:
        return text
    return json.dumps({"preview": text[: max(limit - 1, 0)] + "…"}, ensure_ascii=False)


def _extract_skill_name(tool_name: str, args: Any) -> str | None:
    if not isinstance(args, dict):
        return None
    if tool_name in SKILL_TOOL_NAMES:
        name = args.get("name") or args.get("skill") or args.get("skill_name")
        return str(name) if name else None
    skills = args.get("skills")
    if isinstance(skills, list) and skills:
        first = skills[0]
        return str(first) if first else None
    return None


class EvidenceStore:
    """Small SQLite repository for local curator evidence."""

    def __init__(self, db_path: str | Path | None = None, preview_chars: int = 500):
        self.db_path = Path(db_path) if db_path is not None else default_db_path()
        self.preview_chars = preview_chars
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _apply_journal_mode(self, conn: sqlite3.Connection) -> None:
        """Enable WAL once per path, falling back to DELETE (recipe port).

        ``PRAGMA journal_mode=WAL`` is a query-that-sets: the returned row is
        the resulting mode. Filesystems that refuse WAL may either raise
        (SQLITE_PROTOCOL markers) or silently keep the old mode — both are
        handled, the fallback is logged once per path, and a database already
        in WAL is never downgraded. WAL persists in the file header, so a
        cached success skips the pragma on later connections entirely.
        """

        try:
            key = str(self.db_path.resolve())
        except OSError:
            key = str(self.db_path)
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
        if mode == "wal":
            try:
                conn.execute(f"PRAGMA journal_size_limit={_WAL_SIZE_LIMIT_BYTES}")
            except sqlite3.OperationalError:  # pragma: no cover - best effort
                logger.debug("journal_size_limit not applied")
        else:
            with _journal_mode_lock:
                if key not in _journal_mode_warned:
                    _journal_mode_warned.add(key)
                    logger.warning(
                        "curator-evolver evidence store fell back to DELETE journal mode "
                        "for %s (WAL unavailable); concurrent writers may block each other",
                        key,
                    )
        with _journal_mode_lock:
            _journal_mode_cache[key] = mode or "delete"

    def _path_key(self) -> str:
        try:
            return str(self.db_path.resolve())
        except OSError:
            return str(self.db_path)

    def connect(self) -> sqlite3.Connection:
        """Return this path's warm connection, opening it single-flight (U45).

        The connection is cached per resolved path for the life of the
        process, registered for close-at-exit, and shared by every store
        instance over the same file. It is opened with
        ``check_same_thread=False`` because hooks, backfill, and auto-run may
        live on different threads; all use is serialized by the path lock the
        write/read helpers below acquire, so no two threads ever interleave
        transactions on the one connection.
        """

        key = self._path_key()
        with _connection_lock:
            connection = _connections.get(key)
            if connection is None:
                connection = sqlite3.connect(
                    self.db_path,
                    timeout=_BUSY_TIMEOUT_MS / 1000,
                    check_same_thread=False,
                )
                connection.row_factory = sqlite3.Row
                _connections[key] = connection
                _install_atexit_hook()
                try:
                    connection.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
                    self._apply_journal_mode(connection)
                except sqlite3.Error:
                    # A pragma failure must not strand a half-initialized
                    # cached connection for the whole process.
                    _connections.pop(key, None)
                    connection.close()
                    raise
            return connection

    def close(self) -> None:
        """Close this path's warm connection (deterministic teardown)."""

        key = self._path_key()
        with _connection_lock:
            connection = _connections.pop(key, None)
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error:  # pragma: no cover - teardown best effort
                pass

    def _path_lock(self) -> threading.RLock:
        key = self._path_key()
        with _connection_lock:
            lock = _path_locks.get(key)
            if lock is None:
                lock = threading.RLock()
                _path_locks[key] = lock
            return lock

    def _write_with_retry(self, action) -> Any:
        """Run a serialized write with bounded retry under external contention.

        In-process writers queue on the path lock, so a busy/locked error can
        only mean an *external* process holds the write lock (auto-run in a
        separate shell, a manual ``sqlite3`` session): that is retried with
        linear backoff so realistic overlap lands instead of dropping the
        event. Any other database error is an environment failure (disk
        full, read-only mount, corruption): it fails fast — no timeout burn,
        no retry — with sqlite's error code recorded in the log, and the
        exception propagates for the hook boundary to report (errno split
        per #101202's recipe).
        """

        last_exc: sqlite3.OperationalError | None = None
        with self._path_lock():
            for attempt in range(_WRITE_ATTEMPTS):
                try:
                    return action()
                except sqlite3.OperationalError as exc:
                    if not _is_busy_error(exc):
                        code = getattr(exc, "sqlite_errorcode", None)
                        logger.warning(
                            "curator-evolver evidence store write failed fast: "
                            "%s (sqlite error code: %s)",
                            exc,
                            code,
                        )
                        raise
                    last_exc = exc
                    if attempt + 1 < _WRITE_ATTEMPTS:
                        time.sleep(_RETRY_BACKOFF_S * (attempt + 1))
        raise last_exc  # type: ignore[misc]

    _SCHEMA_TABLES = ("tool_events", "turn_events", "session_events")

    def _schema_ready(self) -> bool:
        """Cheap read probe: EVERY table must exist (roadmap U46).

        Probing only ``tool_events`` let an interrupted first init (crash
        between the first and third ``CREATE TABLE``) freeze the schema
        forever — ``init_db`` skipped ``executescript`` steady-state while
        ``turn_events``/``session_events`` stayed missing (assessment Q7).
        The table list is a single constant shared with ``init_db``'s
        completeness check, so a future table lands in exactly one place.
        """

        try:
            with self._path_lock():
                conn = self.connect()
                rows = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
        except sqlite3.DatabaseError:
            return False
        present = {str(row[0]) for row in rows}
        return all(table in present for table in self._SCHEMA_TABLES)

    def init_db(self) -> None:
        if self._schema_ready():
            return
        try:
            with self._path_lock():
                conn = self.connect()
                conn.executescript(_SCHEMA)
                conn.commit()
        except sqlite3.DatabaseError:
            if not self._quarantine_corrupt_db():
                raise
            with self._path_lock():
                conn = self.connect()
                conn.executescript(_SCHEMA)
                conn.commit()

    def _quarantine_corrupt_db(self) -> bool:
        """Move a non-SQLite evidence file aside so collection can resume."""
        if not self.db_path.exists() or not self.db_path.is_file():
            return False
        try:
            header = self.db_path.read_bytes()[: len(_SQLITE_HEADER)]
        except OSError:
            return False
        if header == _SQLITE_HEADER:
            return False
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = self.db_path.with_name(f"{self.db_path.name}.corrupt.{stamp}")
        suffix = 1
        while backup.exists():
            backup = self.db_path.with_name(
                f"{self.db_path.name}.corrupt.{stamp}.{suffix}"
            )
            suffix += 1
        self.db_path.replace(backup)
        return True

    def record_tool_call(
        self,
        *,
        tool_name: str,
        args: Any,
        result: Any,
        task_id: str = "",
        session_id: str = "",
        duration_ms: int | None = None,
        created_at: str | None = None,
    ) -> None:
        skill_name = _extract_skill_name(tool_name, args)

        def _insert() -> None:
            with self.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO tool_events (
                    created_at, session_id, task_id, tool_name, duration_ms,
                    is_error, skill_name, args_json, result_preview
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at or utc_now(),
                    session_id or "",
                    task_id or "",
                    tool_name or "",
                    duration_ms,
                    1 if looks_like_error(result) else 0,
                    skill_name,
                    _json_dumps(args, self.preview_chars * 2),
                    _compact(result, self.preview_chars),
                ),
            )

        self._write_with_retry(_insert)

    def record_turn(
        self,
        *,
        session_id: str,
        user_message: str,
        assistant_response: str,
        model: str = "",
        platform: str = "",
        created_at: str | None = None,
    ) -> None:
        def _insert() -> None:
            with self.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO turn_events (
                    created_at, session_id, model, platform,
                    user_preview, assistant_preview
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at or utc_now(),
                    session_id or "",
                    model or "",
                    platform or "",
                    _compact(user_message, self.preview_chars),
                    _compact(assistant_response, self.preview_chars),
                ),
            )

        self._write_with_retry(_insert)

    def record_session_end(
        self,
        *,
        session_id: str,
        completed: bool,
        interrupted: bool,
        model: str = "",
        platform: str = "",
        created_at: str | None = None,
    ) -> None:
        def _insert() -> None:
            with self.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO session_events (
                    created_at, session_id, completed, interrupted, model, platform
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at or utc_now(),
                    session_id or "",
                    1 if completed else 0,
                    1 if interrupted else 0,
                    model or "",
                    platform or "",
                ),
            )

        self._write_with_retry(_insert)

    def summary(self, *, days: int, skill: str | None = None) -> dict[str, Any]:
        where = "created_at >= ?"
        params: list[Any] = [cutoff_iso(days)]
        if skill:
            where += " AND skill_name = ?"
            params.append(skill)
        with self.connect() as conn:
            tool_counts = conn.execute(
                f"""
                SELECT
                    COUNT(*) AS tool_events,
                    COALESCE(SUM(is_error), 0) AS error_events,
                    COALESCE(SUM(CASE WHEN skill_name IS NOT NULL THEN 1 ELSE 0 END), 0)
                        AS skill_events
                FROM tool_events
                WHERE {where}
                """,
                params,
            ).fetchone()
            turn_events = conn.execute(
                "SELECT COUNT(*) AS count FROM turn_events WHERE created_at >= ?",
                [cutoff_iso(days)],
            ).fetchone()["count"]
            session_events = conn.execute(
                "SELECT COUNT(*) AS count FROM session_events WHERE created_at >= ?",
                [cutoff_iso(days)],
            ).fetchone()["count"]
            skills = conn.execute(
                f"""
                SELECT skill_name, COUNT(*) AS event_count, COALESCE(SUM(is_error), 0) AS errors
                FROM tool_events
                WHERE {where} AND skill_name IS NOT NULL
                GROUP BY skill_name
                ORDER BY event_count DESC, skill_name ASC
                LIMIT 20
                """,
                params,
            ).fetchall()
            tools = conn.execute(
                f"""
                SELECT tool_name, COUNT(*) AS event_count, COALESCE(SUM(is_error), 0) AS errors
                FROM tool_events
                WHERE {where}
                GROUP BY tool_name
                ORDER BY event_count DESC, tool_name ASC
                LIMIT 20
                """,
                params,
            ).fetchall()
        return {
            "tool_events": int(tool_counts["tool_events"]),
            "error_events": int(tool_counts["error_events"]),
            "skill_events": int(tool_counts["skill_events"]),
            "turn_events": int(turn_events),
            "session_events": int(session_events),
            "skills": [dict(row) for row in skills],
            "tools": [dict(row) for row in tools],
        }

    def recent_tool_events(
        self, *, days: int, skill: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        where = "created_at >= ?"
        params: list[Any] = [cutoff_iso(days)]
        if skill:
            where += " AND skill_name = ?"
            params.append(skill)
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT created_at, session_id, task_id, tool_name, duration_ms,
                       is_error, skill_name, args_json, result_preview
                FROM tool_events
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def recent_turns(self, *, days: int, limit: int = 10) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT created_at, session_id, model, platform, user_preview, assistant_preview
                FROM turn_events
                WHERE created_at >= ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [cutoff_iso(days), limit],
            ).fetchall()
        return [dict(row) for row in rows]
