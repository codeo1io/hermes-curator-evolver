"""U127/U122 (cycle-13): one limit contract on both backfill sources, a
clean failure on a wrong-shape state db, and the ingestion-coverage rider.

U127 (assess F2; the cycle-12 KNOWN LIMIT explicitly deferred "to the next
cycle" in commit 2de240b — this is that cycle): ``backfill_sessions(
state_db=..., limit=0)`` used to treat ``limit <= 0`` as unbounded — the
legacy path raised the U109 ValueError in ``_iter_session_files`` while the
state-db path's line-level slice guard silently imported the whole window
and recorded ``result["limit"] == 0`` as if a real cap. The guard is now
hoisted to the ``backfill_sessions`` entry so CLI, bootstrap, legacy and
state-db all agree (the legacy CLI surface is already pinned in
test_backfill_limit.py::test_cli_backfill_sessions_limit_zero_exits_one;
the ``_iter_session_files`` helper keeps its defensive raise for direct
callers).

U122 (assess F9): a SQLite file without a ``sessions`` table used to crash
out of the import with a raw ``sqlite3.OperationalError`` traceback (the
CLI caught only ValueError); it is now classified as a ``source_error`` so
the documented backfill-source-error contract (clean ``Source error:`` line,
rc 1) holds for every source shape.

Ingestion-coverage rider (research addfd20c): the summary discloses
``source_tool_messages`` and ``tool_event_coverage_pct`` — what fraction of
the tool calls the import examined is represented in the evidence store
(imported this run + disclosed dedupe skips; the live corpus baseline is
~93% = 188,831 stored tool_events vs 201,913 source tool messages).
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from hermes_curator_evolver.__main__ import main
from hermes_curator_evolver.backfill import backfill_sessions
from hermes_curator_evolver.storage import EvidenceStore


@pytest.fixture()
def isolated_env(tmp_path, monkeypatch):
    """Point every default path (home + db) at tmp so probes stay hermetic."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("HERMES_CURATOR_EVOLVER_DB", str(tmp_path / "evidence.sqlite"))
    return tmp_path


# --------------------------------------------------------------------------
# U127: the hoisted entry guard
# --------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [0, -1])
def test_u127_state_db_zero_limit_raises_at_entry(isolated_env, tmp_path, bad):
    """Zero/negative raise the U109 ValueError before ANY source is opened.

    The guard fires at the ``backfill_sessions`` entry — before the evidence
    store is even constructed (previously the state-db path imported the
    whole window and reported ``result["limit"] == 0`` as if a real cap).
    """
    db = tmp_path / "evidence.sqlite"
    with pytest.raises(ValueError) as excinfo:
        backfill_sessions(
            state_db=tmp_path / "state.db",  # deliberately nonexistent
            limit=bad,
        )
    message = str(excinfo.value)
    assert "limit must be a positive integer" in message
    assert "omit it for unbounded" in message
    # Entry-level proof: the guard precedes evidence-store construction.
    assert not db.exists()


def _fake_state_module(monkeypatch, sessions: list[dict]) -> list:
    """Install an in-memory hermes_state.SessionDB fake with N sessions."""
    closed: list[bool] = []
    now = datetime.now(timezone.utc).timestamp()

    class FakeSessionDB:
        def __init__(self, db_path, read_only=False):
            assert read_only is True

        def search_sessions(self, source=None, limit=200, offset=0):
            return sessions[offset : offset + limit]

        def get_messages(self, session_id, *, include_compacted=False):
            return [
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": f"call-{session_id}",
                            "type": "function",
                            "function": {
                                "name": "skill_view",
                                "arguments": json.dumps({"name": session_id}),
                            },
                        }
                    ],
                }
            ]

        def close(self):
            closed.append(True)

    for index, session_id in enumerate(sessions):
        sessions[index] = {
            "id": session_id,
            "started_at": now - 3600 - index,
            "ended_at": now - index,
            "last_active": now - index,
            "model": "gpt-5.6",
            "source": "desktop",
        }
    monkeypatch.setitem(
        sys.modules, "hermes_state", SimpleNamespace(SessionDB=FakeSessionDB)
    )
    return closed


def test_u127_state_db_positive_limit_imports_exactly_n(
    isolated_env, tmp_path, monkeypatch
):
    """A real cap binds the NEWEST in-window sessions and the truthfully
    discloses selection vs. examination (U52/U36 semantics unchanged)."""
    _fake_state_module(monkeypatch, ["s0", "s1", "s2"])
    state_db = tmp_path / "state.db"
    state_db.touch()
    store = EvidenceStore(tmp_path / "evidence.sqlite")

    result = backfill_sessions(state_db=state_db, store=store, days=30, limit=2)

    assert result["limit"] == 2
    assert result["sessions_seen"] == 3  # the scan examines all three
    assert result["sessions_selected"] == 2  # ...but only imports two
    assert result["sessions_imported"] == 2
    assert result["tool_events_imported"] == 2
    # Rider: everything the import examined is represented in the store.
    assert result["source_tool_messages"] == 2
    assert result["tool_event_coverage_pct"] == 100.0


def test_u127_state_db_omitted_limit_is_unbounded(
    isolated_env, tmp_path, monkeypatch
):
    _fake_state_module(monkeypatch, ["s0", "s1", "s2"])
    state_db = tmp_path / "state.db"
    state_db.touch()
    store = EvidenceStore(tmp_path / "evidence.sqlite")

    result = backfill_sessions(state_db=state_db, store=store, days=30)

    assert result["limit"] is None
    assert result["sessions_selected"] == 3
    assert result["sessions_imported"] == 3
    assert result["tool_events_imported"] == 3


def test_u127_cli_state_db_limit_zero_exits_one(isolated_env, tmp_path):
    """The CLI surface of the entry guard on the state-db source kind
    (the legacy-dirs kind is pinned in test_backfill_limit.py)."""
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hermes_curator_evolver",
            "backfill-sessions",
            "--state-db",
            str(tmp_path / "state.db"),
            "--limit",
            "0",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert completed.returncode == 1
    assert "positive integer" in completed.stderr
    assert "Traceback" not in completed.stderr


# --------------------------------------------------------------------------
# U122: a wrong-shape state db is a source error, not a traceback
# --------------------------------------------------------------------------


class _RealSqliteSessionDB:
    """A SessionDB stand-in that runs REAL sqlite against the given file.

    The reader contract is the one hermes_state.SessionDB exposes; running
    real sqlite makes the wrong-shape pins raise the very same exception
    class and message the live host store does.
    """

    def __init__(self, db_path, read_only=False):
        self._conn = sqlite3.connect(f"file:{Path(db_path)}?mode=ro", uri=True)

    def search_sessions(self, source=None, limit=200, offset=0):
        return [
            dict(row)
            for row in self._conn.execute(
                "SELECT id, started_at, ended_at, last_active, model, source"
                " FROM sessions ORDER BY started_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        ]

    def get_messages(self, session_id, *, include_compacted=False):
        return []

    def close(self):
        self._conn.close()


def _install_real_sqlite_state(monkeypatch):
    monkeypatch.setitem(
        sys.modules, "hermes_state", SimpleNamespace(SessionDB=_RealSqliteSessionDB)
    )


def test_u122_wrong_shape_state_db_is_source_error_not_crash(
    isolated_env, tmp_path, monkeypatch
):
    """A SQLite file without a ``sessions`` table (previously a raw
    ``sqlite3.OperationalError`` traceback out of the CLI) is now the
    documented backfill-source-error classification."""
    _install_real_sqlite_state(monkeypatch)
    state_db = tmp_path / "state.db"
    conn = sqlite3.connect(state_db)
    conn.execute("CREATE TABLE unrelated(x)")
    conn.commit()
    conn.close()

    result = backfill_sessions(
        state_db=state_db, store=EvidenceStore(tmp_path / "evidence.sqlite"), days=30
    )

    assert result["source_type"] == "state_db"
    assert result["source_error"] == "OperationalError: no such table: sessions"
    assert result["files_failed"] == 1
    assert result["sessions_imported"] == 0
    assert result["tool_events_imported"] == 0


def test_u122_garbage_state_db_is_source_error(isolated_env, tmp_path, monkeypatch):
    """A non-database file that passed the exists() check fails the same
    classified way (sqlite3.DatabaseError, not a traceback)."""
    _install_real_sqlite_state(monkeypatch)
    state_db = tmp_path / "state.db"
    state_db.write_text("this is not a database at all", encoding="utf-8")

    result = backfill_sessions(
        state_db=state_db, store=EvidenceStore(tmp_path / "evidence.sqlite"), days=30
    )

    assert "file is not a database" in result["source_error"]
    assert result["files_failed"] == 1


def test_u122_cli_wrong_shape_state_db_exits_one_cleanly(
    isolated_env, tmp_path, monkeypatch, capsys
):
    """The documented CLI contract: clean ``Source error:`` line, rc 1,
    no traceback (mirrors the assess F9 live probe)."""
    _install_real_sqlite_state(monkeypatch)
    state_db = tmp_path / "state.db"
    conn = sqlite3.connect(state_db)
    conn.execute("CREATE TABLE unrelated(x)")
    conn.commit()
    conn.close()

    rc = main(["backfill-sessions", "--state-db", str(state_db)])

    captured = capsys.readouterr()
    assert rc == 1
    assert "Source error: OperationalError: no such table: sessions" in captured.out
    assert "Traceback" not in captured.out + captured.err


# --------------------------------------------------------------------------
# Ingestion-coverage rider (research addfd20c)
# --------------------------------------------------------------------------


def _write_session_with_tool_call(path: Path, session_id: str, skill: str) -> None:
    path.write_text(
        json.dumps(
            {
                "session_id": session_id,
                "session_start": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "model": "gpt-5.5",
                "platform": "slack",
                "messages": [
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": f"call-{session_id}",
                                "type": "function",
                                "function": {
                                    "name": "skill_view",
                                    "arguments": json.dumps({"name": skill}),
                                },
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _sessions_dir(tmp_path: Path) -> Path:
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    _write_session_with_tool_call(
        sessions_dir / "session_20260501_100000_a.json", "session-a", "skill-a"
    )
    _write_session_with_tool_call(
        sessions_dir / "session_20260502_100000_b.json", "session-b", "skill-b"
    )
    return sessions_dir


def test_rider_fresh_import_discloses_full_coverage(isolated_env, tmp_path):
    store = EvidenceStore(tmp_path / "evidence.sqlite")

    result = backfill_sessions(
        sessions_dir=_sessions_dir(tmp_path), store=store, days=30
    )

    assert result["source_tool_messages"] == 2
    assert result["tool_events_imported"] == 2
    assert result["tool_events_skipped_duplicate"] == 0
    assert result["tool_event_coverage_pct"] == 100.0


def test_rider_reimport_counts_dedupe_skips_as_covered(isolated_env, tmp_path):
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    sessions_dir = _sessions_dir(tmp_path)

    first = backfill_sessions(sessions_dir=sessions_dir, store=store, days=30)
    second = backfill_sessions(sessions_dir=sessions_dir, store=store, days=30)

    assert first["tool_events_imported"] == 2
    assert second["tool_events_imported"] == 0
    assert second["tool_events_skipped_duplicate"] == 2
    assert second["source_tool_messages"] == 2
    # A dedupe skip means an earlier run already stored it: still coverage.
    assert second["tool_event_coverage_pct"] == 100.0


def test_rider_missing_source_makes_no_coverage_claim(isolated_env, tmp_path):
    result = backfill_sessions(
        sessions_dir=tmp_path / "no-such-dir", days=30
    )

    assert result["missing"] is True
    assert result["source_tool_messages"] == 0
    assert "tool_event_coverage_pct" not in result


def test_rider_human_summary_prints_coverage(isolated_env, tmp_path, capsys):
    rc = main(["backfill-sessions", "--sessions-dir", str(_sessions_dir(tmp_path))])

    captured = capsys.readouterr()
    assert rc == 0
    assert "Tool-event ingestion coverage: 100.0%" in captured.out
    assert "(2/2 source tool messages)" in captured.out
