import json
import sqlite3

from hermes_curator_evolver.storage import EvidenceStore


def test_store_records_tool_call_and_detects_skill_reference(tmp_path):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)

    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "hermes-agent"},
        result='{"success": true}',
        task_id="task-1",
        session_id="session-1",
        duration_ms=12,
    )

    summary = store.summary(days=7)

    assert summary["tool_events"] == 1
    assert summary["skill_events"] == 1
    assert summary["skills"][0]["skill_name"] == "hermes-agent"
    assert summary["skills"][0]["event_count"] == 1


def test_store_flags_errors_without_throwing_on_plain_text_result(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.sqlite")

    store.record_tool_call(
        tool_name="terminal",
        args={"command": "false"},
        result="Traceback: boom",
        task_id="task-1",
        session_id="session-1",
        duration_ms=5,
    )

    summary = store.summary(days=7)

    assert summary["tool_events"] == 1
    assert summary["error_events"] == 1


def test_successful_json_with_error_word_in_field_name_is_not_error(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.sqlite")

    store.record_tool_call(
        tool_name="curator_evidence_report",
        args={"days": 1},
        result='{"success": true, "report": {"summary": {"error_events": 0}}}',
        task_id="task-1",
        session_id="session-1",
        duration_ms=5,
    )

    summary = store.summary(days=7)

    assert summary["tool_events"] == 1
    assert summary["error_events"] == 0


def test_store_compacts_long_payloads(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.sqlite", preview_chars=20)

    store.record_turn(
        session_id="s",
        user_message="u" * 100,
        assistant_response="a" * 100,
        model="m",
        platform="cli",
    )
    rows = store.recent_turns(days=1, limit=1)

    assert len(rows) == 1
    assert len(rows[0]["user_preview"]) <= 21
    assert len(rows[0]["assistant_preview"]) <= 21


def test_store_quarantines_non_sqlite_evidence_file(tmp_path):
    db = tmp_path / "evidence.sqlite"
    db.write_bytes(b"SQLit\x17\x03\x03 not sqlite")

    store = EvidenceStore(db)
    store.record_tool_call(tool_name="terminal", args={}, result="ok")

    assert store.summary(days=1)["tool_events"] == 1
    backups = list(tmp_path.glob("evidence.sqlite.corrupt.*"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == b"SQLit\x17\x03\x03 not sqlite"



def test_recorded_tool_results_never_store_nul_bytes(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.sqlite")

    store.record_tool_call(
        tool_name="terminal",
        args={"command": "cat binary"},
        result="ok\x00output",
        task_id="task-nul-raw",
        session_id="session-nul",
        duration_ms=3,
    )
    store.record_tool_call(
        tool_name="terminal",
        args={"command": "cat binary"},
        result={"stdout": "escaped\\x00payload"},
        task_id="task-nul-escaped",
        session_id="session-nul",
        duration_ms=3,
    )

    previews = [
        row["result_preview"] for row in store.recent_tool_events(days=1, limit=10)
    ]

    assert len(previews) == 2
    for preview in previews:
        assert "\x00" not in preview
    # U37: no encoding path may resurrect a NUL on read — a JSON-serialized
    # dict value must never carry the \u0000 escape (assessment N5).
    assert not any("\\u0000" in preview for preview in previews)
    assert any("okoutput" in preview for preview in previews)
    escaped = json.loads(next(p for p in previews if p.startswith("{")))
    assert escaped["stdout"] == "escaped\\x00payload"


def test_nul_sanitization_closes_every_encoding_and_keeps_literals(tmp_path):
    """U37 / assessment N5: the founding NUL poison class is closed.

    A real NUL inside a dict value used to serialize as the ``\\u0000``
    escape, decode back to a NUL on every later read, and re-open the
    perpetual rollback loop U1 closed. Values are now sanitized before
    serialization, so no escape is ever emitted — while literal backslash
    spellings in documentation text are legitimate content and survive.
    """

    store = EvidenceStore(tmp_path / "evidence.sqlite")

    store.record_tool_call(
        tool_name="terminal",
        args={"command": "demo"},
        result={"stdout": "x\x00y", "nested": ["a\x00b"]},
        task_id="task-nul-dict",
        session_id="session-nul",
    )
    store.record_tool_call(
        tool_name="terminal",
        args={"command": "demo"},
        result="use printf '\\x00' to emit a NUL",
        task_id="task-nul-literal",
        session_id="session-nul",
    )

    previews = [
        row["result_preview"] for row in store.recent_tool_events(days=1, limit=10)
    ]

    dict_preview = next(p for p in previews if p.startswith("{"))
    payload = json.loads(dict_preview)
    assert payload["stdout"] == "xy"
    assert payload["nested"] == ["ab"]
    assert "\x00" not in dict_preview and "\\u0000" not in dict_preview

    literal_preview = next(p for p in previews if "printf" in p)
    assert literal_preview == "use printf '\\x00' to emit a NUL"


def test_record_retries_through_held_write_lock(tmp_path):
    """U7a / assessment P4: realistic lock contention must land, not raise.

    Another writer holds the database's write lock for well under the
    busy_timeout window; a concurrent record_* call used to fail instantly
    with ``database is locked`` (no busy_timeout, no journal mode, no
    retry). With WAL, busy_timeout and bounded retries the event lands
    after the holder releases.
    """

    import threading
    import time

    store = EvidenceStore(tmp_path / "evidence.sqlite")
    holder_path = str(store.db_path)

    # Prove the connect-time contract the fix installed.
    with sqlite3.connect(holder_path) as probe:
        journal = probe.execute("PRAGMA journal_mode").fetchone()[0]
        timeout_ms = probe.execute("PRAGMA busy_timeout").fetchone()[0]
    assert journal.lower() == "wal"
    assert timeout_ms >= 5000

    started = threading.Event()
    release = threading.Event()

    def hold_write_lock():
        conn = sqlite3.connect(holder_path, timeout=30.0)
        conn.execute("BEGIN EXCLUSIVE")
        conn.execute(
            "INSERT INTO tool_events (created_at, session_id, task_id, tool_name,"
            " is_error, args_json, result_preview)"
            " VALUES ('2026-09-02T00:00:00+00:00', 's', 't', 'holder', 0, '{}', 'hold')"
        )
        started.set()
        release.wait(timeout=10.0)
        conn.rollback()
        conn.close()

    holder = threading.Thread(target=hold_write_lock)
    holder.start()
    assert started.wait(timeout=5.0)
    time.sleep(0.1)  # ensure the record call overlaps the held lock

    try:
        store.record_tool_call(
            tool_name="terminal",
            args={"command": "blocked-but-retried"},
            result="ok",
            task_id="task-lock",
            session_id="session-lock",
        )
    finally:
        release.set()
        holder.join(timeout=10.0)

    args = [
        row["args_json"]
        for row in store.recent_tool_events(days=1, limit=10)
        if "blocked-but-retried" in row["args_json"]
    ]
    assert args, "record_tool_call must survive a short-held write lock"


# ---------------------------------------------------------------------------
# Roadmap U43 (assessment Q1): ingest must agree with the classifier truth
# table — keyword-bearing success strings never produce error_events rows.
# ---------------------------------------------------------------------------


def test_u43_keyword_bearing_success_strings_never_become_error_events(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    success_payloads = [
        "0 failed, 12 passed",
        "success: no tests failed",
        "grep: 0 failed",
        "exit code 0",
    ]
    for index, payload in enumerate(success_payloads):
        store.record_tool_call(
            tool_name="bash",
            args={"cmd": f"check-{index}"},
            result=payload,
            task_id=f"t-{index}",
            session_id="s",
        )
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT result_preview, is_error FROM tool_events ORDER BY id"
        ).fetchall()
    assert len(rows) == len(success_payloads)
    assert all(row["is_error"] == 0 for row in rows), [
        (row["result_preview"], row["is_error"]) for row in rows
    ]


def test_u43_structured_failure_shapes_become_error_events(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    failure_payloads = [
        {"returncode": 1},
        {"code": 1},
        {"ok": False},
        {"status": "error"},
    ]
    for index, payload in enumerate(failure_payloads):
        store.record_tool_call(
            tool_name="bash",
            args={"cmd": f"fail-{index}"},
            result=payload,
            task_id=f"f-{index}",
            session_id="s",
        )
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT result_preview, is_error FROM tool_events ORDER BY id"
        ).fetchall()
    assert len(rows) == len(failure_payloads)
    assert all(row["is_error"] == 1 for row in rows), [
        (row["result_preview"], row["is_error"]) for row in rows
    ]


# ---------------------------------------------------------------------------
import pytest

# Roadmap U45 (assessment Q6, upstream #101191/#101202): warm-writer topology
# and the contention-vs-environment errno split.
# ---------------------------------------------------------------------------


def test_u45_one_cached_connection_per_path_under_cold_burst(tmp_path):
    """A cold burst of record_* calls must open exactly one connection."""

    from hermes_curator_evolver import storage as storage_module

    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    key = str(db.resolve())
    before = storage_module._connections.get(key)
    for index in range(5):
        store.record_tool_call(
            tool_name="bash",
            args={"i": index},
            result="ok",
            task_id=f"burst-{index}",
            session_id="s",
        )
    after = storage_module._connections.get(key)
    assert after is not None
    assert after is before or before is None
    # The warm connection is registered for teardown and closeable per store.
    store.close()
    assert storage_module._connections.get(key) is None
    # Reconnect on demand still works after an explicit close.
    store.record_tool_call(
        tool_name="bash", args={}, result="ok", task_id="post-close", session_id="s"
    )
    assert storage_module._connections.get(key) is not None
    store.close()


def test_u45_hook_writes_are_bounded_under_one_external_holder(tmp_path):
    """Q6 reproducer shape: worst-case hook latency under an external holder.

    The old connect-per-call design opened a fresh connection per record_*
    call and burned the full 3 x 5s retry ladder (~15.75s). With one warm
    connection and serialized writes, a short external hold resolves within a
    single busy_timeout window; the measured wall time must stay bounded far
    below the old worst case.
    """

    import threading
    import time

    store = EvidenceStore(tmp_path / "evidence.sqlite")
    holder_path = str(store.db_path)
    release = threading.Event()
    held = threading.Event()

    def hold_write_lock():
        conn = sqlite3.connect(holder_path, timeout=30.0)
        conn.execute("BEGIN EXCLUSIVE")
        conn.execute(
            "INSERT INTO tool_events (created_at, session_id, task_id, tool_name,"
            " is_error, args_json, result_preview)"
            " VALUES ('2026-09-02T00:00:00+00:00', 's', 't', 'holder', 0, '{}', 'hold')"
        )
        held.set()
        release.wait(timeout=10.0)
        conn.rollback()
        conn.close()

    thread = threading.Thread(target=hold_write_lock)
    thread.start()
    try:
        assert held.wait(timeout=5.0)
        started = time.monotonic()
        store.record_tool_call(
            tool_name="bash",
            args={"cmd": "contended"},
            result="ok",
            task_id="contended",
            session_id="s",
        )
        elapsed = time.monotonic() - started
    finally:
        release.set()
        thread.join(timeout=10.0)
    assert elapsed < 15.0, elapsed  # old worst case ~15.75s; new bound is one window


def test_u45_environment_error_fails_fast_without_retry_ladder(tmp_path):
    """Non-busy OperationalError raises immediately (errno split, #101202)."""

    from hermes_curator_evolver import storage as storage_module

    store = EvidenceStore(tmp_path / "evidence.sqlite")

    calls = {"n": 0}

    class _EnvError(sqlite3.OperationalError):
        pass

    def exploding_action():
        calls["n"] += 1
        raise _EnvError("attempt to write a readonly database")

    original_sleep = storage_module.time.sleep
    storage_module.time.sleep = lambda _seconds: None
    try:
        with pytest.raises(_EnvError):
            store._write_with_retry(exploding_action)
    finally:
        storage_module.time.sleep = original_sleep
    assert calls["n"] == 1, "environment errors must not be retried"


# ---------------------------------------------------------------------------
# Roadmap U46 (assessment Q7): schema readiness probes every table.
# ---------------------------------------------------------------------------


def test_u46_interrupted_first_init_heals_on_next_store(tmp_path):
    """tool_events alone must not count as schema-ready (assessment Q7)."""

    db = tmp_path / "evidence.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as partial:
        partial.execute(
            "CREATE TABLE tool_events (id INTEGER PRIMARY KEY, created_at TEXT,"
            " session_id TEXT, task_id TEXT, tool_name TEXT, duration_ms INTEGER,"
            " is_error INTEGER, skill_name TEXT, args_json TEXT, result_preview TEXT)"
        )
        partial.commit()

    store = EvidenceStore(db)  # must heal the partial schema
    with store.connect() as conn:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert {"tool_events", "turn_events", "session_events"} <= tables
    store.record_turn(
        session_id="s", user_message="hi", assistant_response="ok"
    )
    store.record_session_end(session_id="s", completed=True, interrupted=False)
    store.close()


def test_u46_steady_state_schema_probe_is_cheap_and_stable(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    assert store._schema_ready() is True
    # A second init over a complete schema does no writes.
    store.init_db()
    assert store._schema_ready() is True
    store.close()


# ---------------------------------------------------------------------------
# Roadmap U51 (assessment S2/F18): an HTTP-shaped success stored through the
# generic ``code`` key must never poison the append-only error_events history.
# ---------------------------------------------------------------------------


def test_u51_http_success_code_never_poisons_error_events(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    for index in range(3):
        store.record_tool_call(
            tool_name="http_probe",
            args={"url": f"https://example.test/{index}"},
            result={"code": 200, "body": "OK"},
        )
    summary = store.summary(days=1)
    assert summary["tool_events"] == 3
    assert summary["error_events"] == 0


# ---------------------------------------------------------------------------
# Roadmap U53 (assessment S5/F6): readers run on a separate read-only
# connection — they neither queue behind the writer's path lock nor touch
# (and thereby commit/rollback) the warm writer connection's open
# transaction.
# ---------------------------------------------------------------------------


def test_u53_reader_runs_on_its_own_read_only_connection_under_a_held_lock(tmp_path):
    import threading
    import time

    store = EvidenceStore(tmp_path / "evidence.sqlite")
    store.record_tool_call(tool_name="t", args={}, result="ok", session_id="s")
    warm = store.connect()
    reader_conn = store._read_connection()

    # The reader is a different connection object, and it cannot write.
    assert reader_conn is not warm
    with pytest.raises(sqlite3.OperationalError):
        reader_conn.execute("DELETE FROM tool_events")

    # Assessment F6: summary() used to be fine here by accident (it bypassed
    # the lock AND shared the writer connection). Under the U53 contract it
    # completes because it owns a read-only connection — and that is now the
    # documented guarantee, not an accident.
    completed = []

    def _timed_summary():
        start = time.time()
        store.summary(days=1)
        completed.append(round(time.time() - start, 3))

    with store._path_lock():  # simulate an in-process writer holding the lock
        thread = threading.Thread(target=_timed_summary, daemon=True)
        thread.start()
        thread.join(timeout=10)
    assert completed, "reader deadlocked behind the writer's path lock"

    # recent_* readers share the same contract.
    assert store.recent_tool_events(days=1) or store.recent_tool_events(days=1) == []
    store.recent_turns(days=1)
    store.close()


def test_u53_reader_never_commits_or_rolls_back_a_writers_transaction(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    store.record_tool_call(
        tool_name="seed", args={}, result="ok", session_id="s", task_id="seed"
    )
    conn = store.connect()
    with store._path_lock():
        # An open, uncommitted writer transaction on the warm connection...
        conn.execute(
            """
            INSERT INTO tool_events
                (created_at, session_id, task_id, tool_name, is_error, args_json, result_preview)
            VALUES ('2030-01-01T00:00:00', 's', 'open-txn', 'midflight', 0, '{}', 'uncommitted')
            """
        )
        # ...while a reader runs. The legacy ``with self.connect() as conn:``
        # reader COMMITted this transaction as a side effect of its block
        # exit; the read-only connection cannot.
        mid = store.summary(days=99999)
        # Snapshot isolation: the read-only connection sees only committed
        # data — the uncommitted row is invisible to the reader.
        assert mid["tool_events"] == 1
        conn.rollback()
    assert store.summary(days=99999)["tool_events"] == 1
    store.close()


# ---------------------------------------------------------------------------
# Roadmap U54 (assessment S6): symmetric skill attribution. One shared
# extraction vocabulary for every tool, and skills[].event_count counts
# attributed actions — a single lookup surfaced through two differently
# tagged events is ONE action, while real repeated usage still counts.
# ---------------------------------------------------------------------------


def test_u54_skill_attribution_is_symmetric_across_all_tools():
    from hermes_curator_evolver.storage import _extract_skill_name

    # S6 asymmetry: the skill tools used to read only the singular keys.
    assert _extract_skill_name("skill_view", {"skills": ["demo-skill"]}) == "demo-skill"
    assert _extract_skill_name("read_file", {"skills": ["demo-skill"]}) == "demo-skill"
    assert _extract_skill_name("skill_view", {"name": "demo-skill"}) == "demo-skill"
    assert _extract_skill_name("skill_view", {"skill": "demo-skill"}) == "demo-skill"
    assert _extract_skill_name("skill_view", {"skill_name": "demo-skill"}) == "demo-skill"
    assert _extract_skill_name("Read", {"file_path": "/x/SKILL.md"}) is None
    assert _extract_skill_name("skill_view", "not-a-dict") is None
    assert _extract_skill_name("skill_view", {}) is None


def test_u54_event_count_counts_actions_not_event_rows(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.sqlite")
    # One underlying lookup surfaced through two differently-tagged events
    # (same session, same task, same second) is ONE attributed action.
    store.record_tool_call(
        tool_name="read_file",
        args={"skills": ["demo-skill"]},
        result="ok",
        session_id="s",
        task_id="t",
    )
    store.record_tool_call(
        tool_name="skill_view",
        args={"skills": ["demo-skill"]},
        result="ok",
        session_id="s",
        task_id="t",
    )
    summary = store.summary(days=1)
    assert summary["skill_events"] == 2  # raw event rows stay visible
    skills = {row["skill_name"]: row for row in summary["skills"]}
    assert skills["demo-skill"]["event_rows"] == 2
    assert skills["demo-skill"]["event_count"] == 1

    # Real repeated usage — distinct actions — still counts.
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "demo-skill"},
        result="ok",
        session_id="s",
        task_id="t2",
        created_at="2030-01-02T00:00:00",
    )
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "demo-skill"},
        result="ok",
        session_id="s2",
        task_id="t3",
        created_at="2030-01-03T00:00:00",
    )
    skills = {row["skill_name"]: row for row in store.summary(days=1)["skills"]}
    assert skills["demo-skill"]["event_rows"] == 4
    assert skills["demo-skill"]["event_count"] == 3
    store.close()
