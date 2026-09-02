import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from hermes_curator_evolver.backfill import (
    backfill_sessions,
    default_sessions_dir,
    default_state_db_path,
)
from hermes_curator_evolver.storage import EvidenceStore


def _write_session(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "session_id": "session-test",
                "session_start": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "model": "gpt-5.5",
                "platform": "slack",
                "messages": [
                    {"role": "user", "content": "Use the github PR skill"},
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call-1",
                                "type": "function",
                                "function": {
                                    "name": "skill_view",
                                    "arguments": json.dumps({"name": "github-pr-workflow"}),
                                },
                            }
                        ],
                    },
                    {
                        "role": "tool",
                        "tool_call_id": "call-1",
                        "content": json.dumps({"success": True, "name": "github-pr-workflow"}),
                    },
                    {"role": "assistant", "content": "Loaded the PR workflow."},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_backfill_sessions_imports_tool_turn_and_session_events(tmp_path):
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    _write_session(sessions_dir / "session_20260501_100000_test.json")
    store = EvidenceStore(tmp_path / "evidence.sqlite")

    result = backfill_sessions(sessions_dir=sessions_dir, store=store, days=365)

    assert result["sessions_seen"] == 1
    assert result["sessions_imported"] == 1
    assert result["tool_events_imported"] == 1
    assert result["turn_events_imported"] == 1
    assert result["session_events_imported"] == 1
    summary = store.summary(days=365)
    assert summary["tool_events"] == 1
    assert summary["turn_events"] == 1
    assert summary["session_events"] == 1
    assert summary["skills"][0]["skill_name"] == "github-pr-workflow"


def test_backfill_sessions_is_idempotent_for_same_session_file(tmp_path):
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    _write_session(sessions_dir / "session_20260501_100000_test.json")
    store = EvidenceStore(tmp_path / "evidence.sqlite")

    first = backfill_sessions(sessions_dir=sessions_dir, store=store, days=365)
    second = backfill_sessions(sessions_dir=sessions_dir, store=store, days=365)

    assert first["tool_events_imported"] == 1
    assert second["tool_events_imported"] == 0
    summary = store.summary(days=365)
    assert summary["tool_events"] == 1
    assert summary["turn_events"] == 1
    assert summary["session_events"] == 1


def test_default_session_sources_follow_active_hermes_home(tmp_path, monkeypatch):
    hermes_home = tmp_path / "AppData" / "Local" / "hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    assert default_sessions_dir() == hermes_home / "sessions"
    assert default_state_db_path() == hermes_home / "state.db"


def test_backfill_sessions_reads_current_hermes_state_db_read_only(tmp_path, monkeypatch):
    state_db = tmp_path / "state.db"
    state_db.touch()
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    now = datetime.now(timezone.utc).timestamp()
    closed = []

    class FakeSessionDB:
        def __init__(self, db_path, read_only=False):
            assert Path(db_path) == state_db
            assert read_only is True

        def search_sessions(self, source=None, limit=20, offset=0):
            if offset:
                return []
            return [
                {
                    "id": "state-session-test",
                    "started_at": now - 60,
                    "ended_at": now,
                    "last_active": now,
                    "model": "gpt-5.6",
                    "source": "desktop",
                }
            ]

        def get_messages(self, session_id, *, include_compacted=False):
            assert session_id == "state-session-test"
            assert include_compacted is True
            return [
                {"role": "user", "content": "Use the github PR skill"},
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call-state-1",
                            "type": "function",
                            "function": {
                                "name": "skill_view",
                                "arguments": json.dumps({"name": "github-operations"}),
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": "call-state-1",
                    "content": json.dumps({"success": True, "name": "github-operations"}),
                },
                {"role": "assistant", "content": "Loaded the GitHub workflow."},
            ]

        def close(self):
            closed.append(True)

    monkeypatch.setitem(sys.modules, "hermes_state", SimpleNamespace(SessionDB=FakeSessionDB))

    result = backfill_sessions(state_db=state_db, store=store, days=30)
    repeated = backfill_sessions(state_db=state_db, store=store, days=30)

    assert result["source_type"] == "state_db"
    assert result["source_path"] == str(state_db)
    assert result["sessions_seen"] == 1
    assert result["sessions_imported"] == 1
    assert result["tool_events_imported"] == 1
    assert result["turn_events_imported"] == 1
    assert result["session_events_imported"] == 1
    assert repeated["tool_events_imported"] == 0
    assert repeated["turn_events_imported"] == 0
    assert repeated["session_events_imported"] == 0
    assert closed == [True, True]
    summary = store.summary(days=30)
    assert summary["skills"][0]["skill_name"] == "github-operations"


def test_backfill_sessions_prefers_default_state_db_over_legacy_dumps(tmp_path, monkeypatch):
    hermes_home = tmp_path / "hermes"
    sessions_dir = hermes_home / "sessions"
    sessions_dir.mkdir(parents=True)
    _write_session(sessions_dir / "session_legacy.json")
    state_db = hermes_home / "state.db"
    state_db.touch()
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    class EmptySessionDB:
        def __init__(self, db_path, read_only=False):
            assert Path(db_path) == state_db
            assert read_only is True

        def search_sessions(self, source=None, limit=20, offset=0):
            return []

        def get_messages(self, session_id):
            raise AssertionError("no sessions should be loaded")

        def close(self):
            return None

    monkeypatch.setitem(sys.modules, "hermes_state", SimpleNamespace(SessionDB=EmptySessionDB))

    result = backfill_sessions(store=EvidenceStore(tmp_path / "evidence.sqlite"), days=30)

    assert result["source_type"] == "state_db"
    assert result["sessions_seen"] == 0


def test_backfill_sessions_does_not_mark_live_state_session_complete(tmp_path, monkeypatch):
    state_db = tmp_path / "state.db"
    state_db.touch()
    now = datetime.now(timezone.utc).timestamp()

    class LiveSessionDB:
        def __init__(self, db_path, read_only=False):
            assert Path(db_path) == state_db
            assert read_only is True

        def search_sessions(self, source=None, limit=20, offset=0):
            if offset:
                return []
            return [
                {
                    "id": "live-session",
                    "started_at": now - 60,
                    "ended_at": None,
                    "last_active": now,
                    "model": "gpt-5.6",
                    "source": "desktop",
                }
            ]

        # Hermes versions before August 2026 do not expose include_compacted.
        # Backfill must retain this compatibility path.
        def get_messages(self, session_id):
            return [
                {"role": "user", "content": "Still running", "timestamp": now - 1},
                {"role": "assistant", "content": "Yes", "timestamp": now},
            ]

        def close(self):
            return None

    monkeypatch.setitem(sys.modules, "hermes_state", SimpleNamespace(SessionDB=LiveSessionDB))
    store = EvidenceStore(tmp_path / "evidence.sqlite")

    result = backfill_sessions(state_db=state_db, store=store, days=30)

    assert result["turn_events_imported"] == 1
    assert result["session_events_imported"] == 0
    assert store.summary(days=30)["session_events"] == 0


def test_backfill_sessions_explicit_legacy_dir_remains_supported(tmp_path):
    sessions_dir = tmp_path / "legacy-sessions"
    sessions_dir.mkdir()
    _write_session(sessions_dir / "session_legacy.json")

    result = backfill_sessions(
        sessions_dir=sessions_dir,
        store=EvidenceStore(tmp_path / "evidence.sqlite"),
        days=365,
    )

    assert result["source_type"] == "legacy_json"
    assert result["source_path"] == str(sessions_dir)
    assert result["sessions_seen"] == 1


def test_backfill_import_strips_nul_bytes_from_recorded_tool_results(tmp_path):
    # Roadmap U1 end-to-end: a NUL byte in a recorded tool result must not
    # survive the import write path into the evidence preview.
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    (sessions_dir / "session_nul.json").write_text(
        json.dumps(
            {
                "session_id": "session-nul",
                "session_start": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "messages": [
                    {"role": "user", "content": "run the binary check"},
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call-nul",
                                "type": "function",
                                "function": {
                                    "name": "terminal",
                                    "arguments": json.dumps({"command": "cat binary"}),
                                },
                            }
                        ],
                    },
                    {
                        "role": "tool",
                        "tool_call_id": "call-nul",
                        "content": "ok\x00output",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    store = EvidenceStore(tmp_path / "evidence.sqlite")

    result = backfill_sessions(sessions_dir=sessions_dir, store=store, days=30)

    assert result["tool_events_imported"] == 1
    previews = [
        row["result_preview"] for row in store.recent_tool_events(days=30, limit=10)
    ]
    assert previews and all("\x00" not in preview for preview in previews)


def test_backfill_state_db_imports_regardless_of_storage_order(tmp_path, monkeypatch):
    # Roadmap U4: search_sessions pagination order is not a recency contract.
    # This store returns sessions oldest-first, which used to make the cutoff
    # loop break immediately and silently import nothing.
    state_db = tmp_path / "state.db"
    state_db.touch()
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    now = datetime.now(timezone.utc).timestamp()
    closed = []

    class OldestFirstSessionDB:
        def __init__(self, db_path, read_only=False):
            assert Path(db_path) == state_db

        def search_sessions(self, source=None, limit=20, offset=0):
            if offset:
                return []
            return [
                {
                    "id": "state-session-oldest",
                    "started_at": now - 20 * 86400,
                    "last_active": now - 20 * 86400,
                },
                {
                    "id": "state-session-newer",
                    "started_at": now - 3600,
                    "last_active": now - 3600,
                },
                {
                    "id": "state-session-newest",
                    "started_at": now - 60,
                    "last_active": now - 60,
                },
            ]

        def get_messages(self, session_id, *, include_compacted=False):
            return [
                {"role": "user", "content": f"use skill {session_id}"},
                {"role": "assistant", "content": "did the thing"},
            ]

        def close(self):
            closed.append(True)

    monkeypatch.setitem(
        sys.modules, "hermes_state", SimpleNamespace(SessionDB=OldestFirstSessionDB)
    )

    result = backfill_sessions(state_db=state_db, store=store, days=7)

    assert result["sessions_seen"] == 3
    assert result["sessions_skipped_old"] == 1
    assert result["sessions_imported"] == 2
    assert result["sessions_failed"] == 0
    assert closed == [True]


def test_backfill_state_db_counts_per_session_failures_without_aborting(
    tmp_path, monkeypatch
):
    # Roadmap U4: one corrupt session is a counted skip in the summary, never
    # a wholesale abort of the import.
    import hermes_curator_evolver.backfill as backfill_module

    state_db = tmp_path / "state.db"
    state_db.touch()
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    now = datetime.now(timezone.utc).timestamp()

    class TwoSessionDB:
        def __init__(self, db_path, read_only=False):
            pass

        def search_sessions(self, source=None, limit=20, offset=0):
            if offset:
                return []
            return [
                {"id": "state-session-bad", "started_at": now - 60, "last_active": now - 60},
                {"id": "state-session-good", "started_at": now - 120, "last_active": now - 120},
            ]

        def get_messages(self, session_id, *, include_compacted=False):
            return [
                {"role": "user", "content": f"use skill {session_id}"},
                {"role": "assistant", "content": "did the thing"},
            ]

        def close(self):
            return None

    monkeypatch.setitem(sys.modules, "hermes_state", SimpleNamespace(SessionDB=TwoSessionDB))

    original_import = backfill_module._import_session_data

    def flaky_import(data, **kwargs):
        if str(data.get("id")).endswith("-bad"):
            raise ValueError("corrupt session row")
        return original_import(data, **kwargs)

    monkeypatch.setattr(backfill_module, "_import_session_data", flaky_import)

    result = backfill_sessions(state_db=state_db, store=store, days=7)

    assert result["sessions_seen"] == 2
    assert result["sessions_failed"] == 1
    assert result["sessions_imported"] == 1
    assert "corrupt session row" in result["last_session_error"]
    assert "source_error" not in result


def test_backfill_state_db_surfaces_unreadable_transcripts_as_counted_failures(
    tmp_path, monkeypatch
):
    state_db = tmp_path / "state.db"
    state_db.touch()
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    now = datetime.now(timezone.utc).timestamp()

    class OneUnreadableSessionDB:
        def __init__(self, db_path, read_only=False):
            pass

        def search_sessions(self, source=None, limit=20, offset=0):
            if offset:
                return []
            return [
                {"id": "state-session-unreadable", "started_at": now - 60, "last_active": now - 60},
                {"id": "state-session-readable", "started_at": now - 120, "last_active": now - 120},
            ]

        def get_messages(self, session_id, *, include_compacted=False):
            if session_id.endswith("-unreadable"):
                raise RuntimeError("transcript unreadable")
            return [
                {"role": "user", "content": "use the github PR skill"},
                {"role": "assistant", "content": "loaded it"},
            ]

        def close(self):
            return None

    monkeypatch.setitem(
        sys.modules, "hermes_state", SimpleNamespace(SessionDB=OneUnreadableSessionDB)
    )

    result = backfill_sessions(state_db=state_db, store=store, days=7)

    assert result["sessions_seen"] == 2
    assert result["sessions_failed"] == 1
    assert result["sessions_imported"] == 1
    assert result["files_failed"] == 0
    assert "unreadable transcript" in result["last_session_error"]
    assert "source_error" not in result


# ---------------------------------------------------------------------------
# Roadmap U36 (assessment N2/N2b/N3): trusted-order backfill with the cutoff
# applied BEFORE any transcript fetch, and a bounded bootstrap.
# ---------------------------------------------------------------------------


class _RecordingSessionDB:
    """Fake state SessionDB with a hostile storage order and a fetch counter."""

    def __init__(self, rows):
        self.rows = rows
        self.fetched = []

    def search_sessions(self, source=None, limit=20, offset=0):
        if offset:
            return []
        return self.rows

    def get_messages(self, session_id, *, include_compacted=False):
        self.fetched.append(session_id)
        return [
            {"role": "user", "content": f"use skill {session_id}"},
            {"role": "assistant", "content": "did the thing"},
        ]

    def close(self):
        pass


def test_u36_limit_takes_the_newest_sessions_not_storage_order(tmp_path, monkeypatch):
    # Assessment N2: with --limit 2 over storage order [s1, s0, s2] where s2
    # is newest, the inspected set used to be {s1, s0}; it must be the two
    # newest by session time.
    state_db = tmp_path / "state.db"
    state_db.touch()
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    now = datetime.now(timezone.utc).timestamp()
    db = _RecordingSessionDB(
        [
            {"id": "s1", "last_active": now - 500},
            {"id": "s0", "last_active": now - 900},
            {"id": "s2", "last_active": now - 60},
        ]
    )
    monkeypatch.setitem(sys.modules, "hermes_state", SimpleNamespace(SessionDB=lambda **kw: db))

    result = backfill_sessions(state_db=state_db, store=store, days=30, limit=2)

    assert result["sessions_seen"] == 2
    assert sorted(db.fetched) == ["s1", "s2"], db.fetched
    assert result["sessions_imported"] == 2


def test_u36_cutoff_runs_before_any_transcript_fetch(tmp_path, monkeypatch):
    # Assessment N3: a one-in-window import must not fetch every transcript.
    state_db = tmp_path / "state.db"
    state_db.touch()
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    now = datetime.now(timezone.utc).timestamp()
    rows = [
        {"id": f"old-{index}", "last_active": now - (index + 1) * 20 * 86400}
        for index in range(5)
    ] + [{"id": "fresh", "last_active": now - 60}]
    db = _RecordingSessionDB(rows)
    monkeypatch.setitem(sys.modules, "hermes_state", SimpleNamespace(SessionDB=lambda **kw: db))

    result = backfill_sessions(state_db=state_db, store=store, days=7)

    assert db.fetched == ["fresh"], db.fetched
    assert result["sessions_skipped_old"] == 5
    # All six rows were examined in metadata (counted as seen); only the one
    # in-window session had its transcript fetched.
    assert result["sessions_seen"] == 6
    assert result["sessions_imported"] == 1


def test_u36_newest_first_order_is_monotonic(tmp_path, monkeypatch):
    state_db = tmp_path / "state.db"
    state_db.touch()
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    now = datetime.now(timezone.utc).timestamp()
    db = _RecordingSessionDB(
        [
            {"id": "mid", "last_active": now - 3600},
            {"id": "old", "last_active": now - 86400},
            {"id": "new", "last_active": now - 10},
        ]
    )
    monkeypatch.setitem(sys.modules, "hermes_state", SimpleNamespace(SessionDB=lambda **kw: db))

    result = backfill_sessions(state_db=state_db, store=store, days=30)

    assert db.fetched == ["new", "mid", "old"], db.fetched
    assert result["sessions_imported"] == 3


def test_u36_bootstrap_limit_helper_bounds_bootstrap_backfill():
    from hermes_curator_evolver.cli import _backfill_limit

    assert _backfill_limit(None, default=500) == 500
    assert _backfill_limit(0, default=500) == 500  # 0 keeps the default (N3)
    assert _backfill_limit(-3, default=500) == 500
    assert _backfill_limit(7, default=500) == 7
    assert _backfill_limit(10_000, default=500) == 10_000


def test_u36_cli_human_summary_names_failed_sessions():
    # Assessment N7: sessions_failed was invisible in the bootstrap text
    # summary (json only); the human-readable form must name the failure
    # count and the last reason.
    result = {
        "source_type": "state_db",
        "source_path": "/tmp/state.db",
        "db_path": "/tmp/evidence.sqlite",
        "sessions_seen": 3,
        "sessions_imported": 1,
        "sessions_skipped_old": 0,
        "sessions_failed": 2,
        "last_session_error": "UnicodeDecodeError: bad bytes",
        "files_failed": 0,
        "tool_events_imported": 1,
        "turn_events_imported": 1,
        "session_events_imported": 0,
    }
    from hermes_curator_evolver.cli import _format_bootstrap_result

    bootstrap_result = {
        "mode": "bootstrap",
        "backfill": result,
        "auto_timer": {
            "installed": True,
            "enabled": False,
            "schedule": "daily",
            "command": "python -m hermes_curator_evolver auto-run",
            "auto_apply_policy": "local-agent-created-skills-only",
            "verify_command": None,
            "verify_cwd": None,
        },
        "next_steps": ["Restart Hermes gateway"],
    }
    summary = _format_bootstrap_result(bootstrap_result)
    assert "2 session(s) failed" in summary
    assert "UnicodeDecodeError" in summary


def test_u36_backfill_text_output_names_failed_sessions(capsys, monkeypatch, tmp_path):
    # The `backfill-sessions` text path (assessment N7): the printed block
    # must gain 'Failed sessions' / 'Last session error' lines.
    from hermes_curator_evolver import cli

    fake = {
        "source_type": "state_db",
        "source_path": str(tmp_path / "state.db"),
        "db_path": str(tmp_path / "evidence.sqlite"),
        "sessions_seen": 2,
        "sessions_imported": 1,
        "sessions_skipped_old": 0,
        "sessions_failed": 1,
        "last_session_error": "boom",
        "files_failed": 0,
        "tool_events_imported": 3,
        "turn_events_imported": 1,
        "session_events_imported": 1,
    }
    monkeypatch.setattr(cli, "backfill_sessions", lambda **kwargs: fake)
    from hermes_curator_evolver.__main__ import build_parser

    parser = build_parser()
    args = parser.parse_args(
        ["backfill-sessions", "--sessions-dir", str(tmp_path), "--format", "text"]
    )
    cli.handle_cli(args)
    out = capsys.readouterr().out
    assert "Failed sessions: 1" in out
    assert "Last session error: boom" in out


def test_u36_hostile_infinite_pagination_is_bounded_and_deduped(monkeypatch):
    """Assessment R8's hostile fake: pages never end, newest row shifts pages.

    The metadata collection must terminate (bounded) and never yield the
    same session twice when a storage shifts rows across pages.
    """
    from datetime import timedelta

    now_dt = datetime.now(timezone.utc)

    class ShiftingDB:
        def __init__(self):
            self.n = 0

        def search_sessions(self, limit=None, offset=0):
            self.n += 1
            base = [{"id": "s-new", "last_active": now_dt.isoformat()}] if self.n % 2 else []
            tail = [
                {"id": f"s{o}", "last_active": (now_dt - timedelta(days=o + 1)).isoformat()}
                for o in range(offset, offset + (limit or 200))
            ]
            return (base + tail)[: limit or 200]

        def get_messages(self, sid, **kw):
            return []

        def close(self):
            pass

    from hermes_curator_evolver.backfill import _iter_state_sessions

    db = ShiftingDB()
    seen = [d["id"] for d in _iter_state_sessions(db, 6)]
    assert len(seen) == len(set(seen)), seen
    assert "s-new" in seen
    assert db.n < 200  # bounded: did not walk every page forever
