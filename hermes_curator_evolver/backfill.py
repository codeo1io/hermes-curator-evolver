"""Import historical Hermes sessions into the curator evidence store."""

from __future__ import annotations

import importlib
import inspect
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from .paths import hermes_home
from .storage import EvidenceStore, _compact


def default_sessions_dir() -> Path:
    """Return the legacy JSON transcript directory under the active Hermes home."""

    return hermes_home() / "sessions"


def default_state_db_path() -> Path:
    """Return the current Hermes session database under the active Hermes home."""

    return hermes_home() / "state.db"


def _parse_dt(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _iso(dt: datetime | None) -> str:
    return (dt or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec="seconds")


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _content_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return repr(value)


def _tool_call_id(call: dict[str, Any], index: int) -> str:
    return str(call.get("id") or call.get("call_id") or call.get("tool_call_id") or f"tool-{index}")


def _tool_call_name_and_args(call: dict[str, Any]) -> tuple[str, Any]:
    function = call.get("function") if isinstance(call.get("function"), dict) else {}
    name = str(function.get("name") or call.get("name") or "")
    raw_args = function.get("arguments", call.get("arguments", {}))
    if isinstance(raw_args, str):
        try:
            args = json.loads(raw_args) if raw_args.strip() else {}
        except json.JSONDecodeError:
            args = {"raw_arguments": raw_args}
    else:
        args = raw_args or {}
    return name, args


def _tool_results_by_call_id(messages: list[dict[str, Any]]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for message in messages:
        if message.get("role") != "tool":
            continue
        call_id = message.get("tool_call_id") or message.get("id")
        if call_id:
            results[str(call_id)] = message.get("content")
    return results


def _tool_event_exists(store: EvidenceStore, *, session_id: str, task_id: str, tool_name: str) -> bool:
    with store.connect() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM tool_events
            WHERE session_id = ? AND task_id = ? AND tool_name = ?
            LIMIT 1
            """,
            (session_id, task_id, tool_name),
        ).fetchone()
    return row is not None


def _turn_event_exists(
    store: EvidenceStore,
    *,
    session_id: str,
    model: str,
    platform: str,
    user_message: str,
    assistant_response: str,
) -> bool:
    with store.connect() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM turn_events
            WHERE session_id = ? AND model = ? AND platform = ?
              AND user_preview = ? AND assistant_preview = ?
            LIMIT 1
            """,
            (
                session_id,
                model,
                platform,
                _compact(user_message, store.preview_chars),
                _compact(assistant_response, store.preview_chars),
            ),
        ).fetchone()
    return row is not None


def _session_event_exists(store: EvidenceStore, *, session_id: str) -> bool:
    with store.connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM session_events WHERE session_id = ? LIMIT 1",
            (session_id,),
        ).fetchone()
    return row is not None


def _iter_session_files(sessions_dir: Path, limit: int | None) -> list[Path]:
    files = sorted(sessions_dir.glob("session_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if limit is not None and limit > 0:
        return files[:limit]
    return files


def _supports_compacted_history(get_messages: Any) -> bool:
    """Return whether a Hermes ``get_messages`` callable exposes compacted rows.

    Hermes added ``include_compacted`` in August 2026 so display-history rows
    archived by in-place compaction remain available to transcript consumers.
    Detect that capability before passing the keyword so older Hermes releases
    keep working without masking a ``TypeError`` raised inside ``get_messages``.
    """

    try:
        parameters = inspect.signature(get_messages).parameters
    except (TypeError, ValueError):
        return False
    return "include_compacted" in parameters or any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )


def _iter_state_sessions(
    session_db: Any,
    limit: int | None,
    cutoff: datetime | None = None,
    stats: dict[str, int] | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield current Hermes sessions newest-first, cutoff applied before transcripts.

    ``search_sessions`` pagination order is an implementation detail of the
    host SessionDB and must not be trusted as recency order (roadmap
    U4/U36): a storage that returns oldest-first would silently truncate
    every import the moment the caller's cutoff loop sees one old session.
    Rows are therefore collected as *metadata only*, sorted by session time
    on the client, and only then are transcripts fetched — at most ``limit``
    of the newest sessions inside ``cutoff`` (assessment N2/N2b/N3: the cap
    used to bind the storage-order collection window — so ``--limit 2``
    could inspect ``s1, s0`` while the newest session ``s2`` was never
    read — and every transcript was fetched before the days cutoff ran, so
    a one-in-window import read full history).

    Roadmap U52 (assessment S3/F7): the cap now bounds the *result*, never
    the *scan*. The metadata scan runs until the storage stops returning
    pages that add new sessions — an empty page, a short page, or a page of
    already-seen ids (assessment R8's shifting/hostile fake) — or until a
    generous last-resort runaway bound on distinct sessions is reached
    (three times the legacy cap; when that binds it is recorded in
    ``stats['metadata_scan_truncated']``, never silently). This is what
    makes ``--limit 2`` on a 10,040-session store fetch the two NEWEST
    sessions instead of two near-oldest ones. Bootstrap paths share this
    iterator, so they share the same ordering guarantee.

    Truthful counters (roadmap U52, assessment F24) are written to ``stats``
    when provided: ``sessions_pages_scanned``, ``sessions_metadata_seen``
    (distinct sessions examined), ``sessions_in_window``,
    ``sessions_skipped_old`` (sessions actually older than the cutoff —
    counted once, here, not pages walked), and ``sessions_selected``.
    Sessions older than ``cutoff`` are counted in ``sessions_skipped_old``
    and never fetched.
    """

    get_messages = session_db.get_messages
    include_compacted = _supports_compacted_history(get_messages)
    collected: list[tuple[datetime, dict[str, Any]]] = []
    seen_ids: set[str] = set()
    pages_scanned = 0
    offset = 0
    scan_truncated = False
    while True:
        rows = list(session_db.search_sessions(limit=200, offset=offset) or [])
        if not rows:
            break
        pages_scanned += 1
        new_sessions = 0
        for row in rows:
            data = dict(row)
            session_id = str(data.get("id") or data.get("session_id") or "")
            if session_id and session_id not in seen_ids:
                # Dedupe across shifting pages (roadmap R8): a session that
                # reappears on a later page is the same import, not a new one.
                seen_ids.add(session_id)
                collected.append((_session_time(data), data))
                new_sessions += 1
        if new_sessions == 0:
            # A page that added nothing new means every row was already
            # seen: shifting pages or an infinite repeat tail (assessment
            # R8). No forward progress is possible, so the scan is done.
            break
        if len(rows) < 200:
            break
        # Last-resort runaway bound (roadmap U52): a storage that never
        # returns an empty/short/repeat page and keeps minting new ids
        # forever cannot be walked to the end. Three times the legacy
        # 10,000-session cap, so it only binds where the old cap did AND
        # the store kept growing past it; binding is disclosed in stats.
        if len(seen_ids) >= max(int(limit or 0), 10_000) * 3:
            scan_truncated = True
            break
        offset += len(rows)
    # Trusted order: sort by the session's own time, newest first, and only
    # then apply the cutoff and the limit (roadmap U36).
    collected.sort(key=lambda item: item[0], reverse=True)
    in_window: list[tuple[datetime, dict[str, Any]]] = []
    remaining_old = 0
    for index, (session_dt, data) in enumerate(collected):
        if cutoff is not None and session_dt < cutoff:
            # Sorted newest-first: every later row is at least as old, so the
            # whole tail is skipped in one count instead of one-by-one. They
            # were examined (and counted as seen), but no transcript is
            # fetched for them (assessment N3).
            remaining_old = len(collected) - index
            break
        in_window.append((session_dt, data))
    # The cap now binds the newest in-window sessions, not the storage-order
    # collection window (assessment N2/N2b/S3): the RESULT is capped, never
    # the scan above.
    selected = in_window if limit is None or limit <= 0 else in_window[:limit]
    if stats is not None:
        # Truthful accounting (roadmap U52, assessment F24): these count
        # what actually happened during THIS scan — pages walked, distinct
        # metadata rows examined, sessions inside the cutoff, sessions
        # actually older than it, and how many were selected for import.
        # The old code folded only the old tail into ``sessions_seen`` and
        # let in-window-but-unselected sessions vanish from every counter.
        stats["sessions_pages_scanned"] = stats.get("sessions_pages_scanned", 0) + pages_scanned
        stats["sessions_metadata_seen"] = stats.get("sessions_metadata_seen", 0) + len(collected)
        stats["sessions_seen"] = stats.get("sessions_seen", 0) + len(collected)
        stats["sessions_in_window"] = stats.get("sessions_in_window", 0) + len(in_window)
        stats["sessions_skipped_old"] = stats.get("sessions_skipped_old", 0) + remaining_old
        stats["sessions_selected"] = stats.get("sessions_selected", 0) + len(selected)
        if scan_truncated:
            stats["metadata_scan_truncated"] = 1
    last_dt: datetime | None = None
    for _session_dt, data in selected:
        # Monotonicity assertion (roadmap U52): the trusted order handed to
        # callers must be strictly newest-first — every yielded session is
        # at least as old as the one yielded before it.
        if last_dt is not None and _session_dt > last_dt:
            raise AssertionError(
                "_iter_state_sessions order invariant broken: "
                f"{data.get('id')!r}({_session_dt}) is newer than the "
                f"previously yielded session ({last_dt})"
            )
        last_dt = _session_dt
        session_id = str(data.get("id") or data.get("session_id") or "")
        try:
            if include_compacted:
                data["messages"] = get_messages(session_id, include_compacted=True)
            else:
                data["messages"] = get_messages(session_id)
        except Exception as exc:  # noqa: BLE001 - any driver/IO error on one
        # transcript must not abort the import (roadmap U4); the drop is
        # surfaced to the caller via ``transcript_error`` instead of logging
        # from inside a read-only iterator.
            data["messages"] = []
            data["transcript_error"] = f"{type(exc).__name__}: {exc}"
        yield data


def _session_time(data: dict[str, Any], fallback: datetime | None = None) -> datetime:
    return (
        _parse_dt(data.get("last_active"))
        or _parse_dt(data.get("ended_at"))
        or _parse_dt(data.get("last_updated"))
        or _parse_dt(data.get("started_at"))
        or _parse_dt(data.get("session_start"))
        or fallback
        or datetime.now(timezone.utc)
    )


def _import_session_data(
    data: dict[str, Any],
    *,
    evidence: EvidenceStore,
    result: dict[str, Any],
    session_dt: datetime,
    fallback_session_id: str,
    current_state_session: bool,
) -> None:
    session_id = str(data.get("session_id") or data.get("id") or fallback_session_id)
    model = str(data.get("model") or "")
    platform = str(data.get("platform") or data.get("source") or "")
    raw_messages = data.get("messages")
    messages = [message for message in raw_messages if isinstance(message, dict)] if isinstance(raw_messages, list) else []
    before = (
        result["tool_events_imported"],
        result["turn_events_imported"],
        result["session_events_imported"],
    )

    tool_results = _tool_results_by_call_id(messages)
    for message in messages:
        raw_calls = message.get("tool_calls")
        calls = raw_calls if isinstance(raw_calls, list) else []
        for call_index, call in enumerate(calls):
            if not isinstance(call, dict):
                continue
            tool_name, args = _tool_call_name_and_args(call)
            if not tool_name:
                continue
            call_id = _tool_call_id(call, call_index)
            task_id = f"backfill:{session_id}:{call_id}"
            if _tool_event_exists(evidence, session_id=session_id, task_id=task_id, tool_name=tool_name):
                continue
            evidence.record_tool_call(
                tool_name=tool_name,
                args=args,
                result=tool_results.get(call_id, ""),
                task_id=task_id,
                session_id=session_id,
                created_at=_iso(_parse_dt(message.get("timestamp")) or session_dt),
            )
            result["tool_events_imported"] += 1

    pending_user: str | None = None
    for message in messages:
        role = message.get("role")
        content = _content_text(message.get("content"))
        if role == "user" and content.strip():
            pending_user = content
        elif role == "assistant" and pending_user and content.strip():
            if not _turn_event_exists(
                evidence,
                session_id=session_id,
                model=model,
                platform=platform,
                user_message=pending_user,
                assistant_response=content,
            ):
                evidence.record_turn(
                    session_id=session_id,
                    user_message=pending_user,
                    assistant_response=content,
                    model=model,
                    platform=platform,
                    created_at=_iso(_parse_dt(message.get("timestamp")) or session_dt),
                )
                result["turn_events_imported"] += 1
            pending_user = None

    session_has_ended = not current_state_session or data.get("ended_at") is not None
    if session_has_ended and not _session_event_exists(evidence, session_id=session_id):
        interrupted = str(data.get("end_reason") or "").casefold() in {
            "cancelled",
            "error",
            "interrupted",
            "timeout",
        }
        evidence.record_session_end(
            session_id=session_id,
            completed=not interrupted,
            interrupted=interrupted,
            model=model,
            platform=platform,
            created_at=_iso(
                _parse_dt(data.get("ended_at"))
                or _parse_dt(data.get("last_updated"))
                or session_dt
            ),
        )
        result["session_events_imported"] += 1

    after = (
        result["tool_events_imported"],
        result["turn_events_imported"],
        result["session_events_imported"],
    )
    if after != before:
        result["sessions_imported"] += 1


def backfill_sessions(
    *,
    sessions_dir: str | Path | None = None,
    state_db: str | Path | None = None,
    store: EvidenceStore | None = None,
    days: int = 30,
    limit: int | None = None,
) -> dict[str, Any]:
    """Backfill evidence from current Hermes ``state.db`` or legacy JSON dumps.

    With no source override, the importer prefers the active Hermes profile's
    read-only ``state.db`` and falls back to legacy ``session_*.json`` files only
    when that database does not exist. ``request_dump_*.json`` files are debug
    request snapshots, not the durable session transcript contract, and are
    intentionally ignored.
    """

    if sessions_dir is not None and state_db is not None:
        raise ValueError("sessions_dir and state_db are mutually exclusive")

    evidence = store or EvidenceStore()
    bounded_days = max(int(days or 1), 1)
    cutoff = datetime.now(timezone.utc) - timedelta(days=bounded_days)
    legacy_dir = Path(sessions_dir).expanduser() if sessions_dir is not None else default_sessions_dir()
    state_path = Path(state_db).expanduser() if state_db is not None else default_state_db_path()
    use_state_db = sessions_dir is None and (state_db is not None or state_path.exists())
    source_type = "state_db" if use_state_db else "legacy_json"
    source_path = state_path if use_state_db else legacy_dir
    result: dict[str, Any] = {
        "source_type": source_type,
        "source_path": str(source_path),
        "state_db_path": str(state_path),
        "sessions_dir": str(legacy_dir),
        "db_path": str(evidence.db_path),
        "days": bounded_days,
        "limit": limit,
        "sessions_seen": 0,
        "sessions_metadata_seen": 0,
        "sessions_pages_scanned": 0,
        "sessions_in_window": 0,
        "sessions_selected": 0,
        "sessions_imported": 0,
        "sessions_skipped_old": 0,
        "sessions_failed": 0,
        "files_failed": 0,
        "tool_events_imported": 0,
        "turn_events_imported": 0,
        "session_events_imported": 0,
    }
    if not source_path.exists():
        result["missing"] = True
        return result

    if use_state_db:
        try:
            SessionDB = getattr(importlib.import_module("hermes_state"), "SessionDB")
            session_db = SessionDB(db_path=state_path, read_only=True)
        except Exception as exc:
            result["files_failed"] += 1
            result["source_error"] = f"{type(exc).__name__}: {exc}"
            return result
        try:
            for data in _iter_state_sessions(session_db, limit, cutoff, result):
                # ``sessions_seen`` is owned by the iterator for state-db
                # imports (roadmap U52/F24): it counts every distinct
                # session examined during the metadata scan, so the summary
                # cannot under-report on stores larger than the import
                # limit. The legacy-dump branch below keeps its per-file
                # counting, which is already "everything examined".
                if data.get("transcript_error"):
                    result["sessions_failed"] += 1
                    result["last_session_error"] = (
                        f"unreadable transcript: {data['transcript_error']}"
                    )
                    continue
                try:
                    session_dt = _session_time(data)
                    _import_session_data(
                        data,
                        evidence=evidence,
                        result=result,
                        session_dt=session_dt,
                        fallback_session_id="",
                        current_state_session=True,
                    )
                except Exception as exc:  # noqa: BLE001 - per-session boundary
                # (roadmap U4): breadth is deliberate so one corrupt or
                # half-written session becomes a counted skip, never a
                # wholesale abort of the import; the summary surfaces it.
                    result["sessions_failed"] += 1
                    result["last_session_error"] = f"{type(exc).__name__}: {exc}"
        finally:
            session_db.close()
        return result

    for path in _iter_session_files(legacy_dir, limit):
        result["sessions_seen"] += 1
        try:
            data = _load_json(path)
        except (OSError, json.JSONDecodeError):
            result["files_failed"] += 1
            continue

        session_dt = _session_time(data, datetime.fromtimestamp(path.stat().st_mtime, timezone.utc))
        if session_dt < cutoff:
            result["sessions_skipped_old"] += 1
            continue
        _import_session_data(
            data,
            evidence=evidence,
            result=result,
            session_dt=session_dt,
            fallback_session_id=path.stem.replace("session_", ""),
            current_state_session=False,
        )

    return result
