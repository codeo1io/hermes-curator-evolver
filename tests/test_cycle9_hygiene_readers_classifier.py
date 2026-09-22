"""Cycle-9 (maintenance) tests: U77 credential hygiene, U78 backfill readers
and containment, U79 classifier residual edges.

Every test pins a behavior that was live-verified as broken on main@709fbeb
during the cycle-9 adversarial assessment (delegate spool 24f53e69…).
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from hermes_curator_evolver import backfill
from hermes_curator_evolver.auto_evolve import (
    _build_semantic_query,
    _format_evidence_reference,
    _format_evidence_rows,
)
from hermes_curator_evolver.candidates import looks_like_error
from hermes_curator_evolver.__main__ import build_parser
from hermes_curator_evolver.cli import handle_cli
from hermes_curator_evolver.hygiene import (
    count_credentials,
    scrub_text,
    stats_reset,
    stats_snapshot,
)
from hermes_curator_evolver.skill_validate import validate_skill_file
from hermes_curator_evolver.storage import EvidenceStore

# Synthetic credential shapes (roadmap KTD39: presumptively synthetic, never
# issued). The ghp_ string is the exact shape committed in
# docs/ideation/2026-09-02-cycle-2-extension-research.md.
GHP = "ghp_16C7e42F292c6912E7710c838347Ae178B4a"


# --------------------------------------------------------------------------
# U77 — credential hygiene at ingest, embed, and validate
# --------------------------------------------------------------------------


def test_u77_scrub_text_replaces_every_credential_family() -> None:
    cases = [
        (f"TOKEN={GHP}", "[REDACTED:github-token]"),
        ("github_pat_" + "A" * 82, "[REDACTED:github-fine-grained-pat]"),
        ("AKIAIOSFODNN7EXAMPLE", "[REDACTED:aws-access-key]"),
        ("sk-ant-api03-" + "B" * 30, "[REDACTED:openai-or-anthropic-key]"),
        ("xoxb-123456789012-abcdef", "[REDACTED:slack-token]"),
        ("token: simplevalue123", "[REDACTED:generic-token-assignment]"),
    ]
    for raw, expected_marker in cases:
        text, hits = scrub_text(raw)
        assert hits == 1, raw
        assert expected_marker in text
        assert raw not in text
    clean, hits = scrub_text("perfectly ordinary prose, no credentials")
    assert (clean, hits) == ("perfectly ordinary prose, no credentials", 0)
    # Idempotence: scrubbing scrubbed text is a no-op (markers do not
    # re-match the generic arm — the ``[`` lookahead blocks it).
    once = scrub_text(f"TOKEN={GHP}")[0]
    assert scrub_text(once) == (once, 0)


def test_u77_storage_scrubs_previews_and_args_before_write(tmp_path) -> None:
    store = EvidenceStore(tmp_path / "ev.sqlite")
    store.record_tool_call(
        tool_name="skill_manage",
        args={"auth": f"Bearer {GHP}"},
        result=f"TOKEN={GHP} applied",
        task_id="backfill:s1:c1",
        session_id="s1",
    )
    with store._read_connection() as conn:
        row = conn.execute(
            "SELECT args_json, result_preview FROM tool_events"
        ).fetchone()
    assert GHP not in row["args_json"]
    assert GHP not in row["result_preview"]
    assert "[REDACTED:github-token]" in row["args_json"]
    assert "[REDACTED:github-token]" in row["result_preview"]


def test_u77_scrub_runs_before_the_length_cut(tmp_path) -> None:
    # preview_chars=40 truncates inside the credential: without the
    # scrub-before-cut order the stored preview would keep the token head.
    store = EvidenceStore(tmp_path / "ev.sqlite", preview_chars=40)
    payload = "x" * 35 + " " + f"TOKEN={GHP}"
    store.record_tool_call(
        tool_name="bash",
        args={},
        result=payload,
        task_id="backfill:s1:c1",
        session_id="s1",
    )
    with store._read_connection() as conn:
        preview = conn.execute(
            "SELECT result_preview FROM tool_events"
        ).fetchone()["result_preview"]
    assert "ghp_" not in preview
    assert "16C7e" not in preview  # the cut lands before the marker; the body is gone
    assert preview.endswith("…")


def test_u77_embed_points_scrub_pre_fix_rows_from_old_stores() -> None:
    # Simulates a row ingested before U77 (raw preview already stored).
    lines = _format_evidence_rows(
        [
            {
                "created_at": "2026-09-22T00:00:00Z",
                "tool_name": "skill_manage",
                "is_error": 0,
                "result_preview": f"TOKEN={GHP} verbatim",
            }
        ]
    )
    joined = "\n".join(lines)
    assert GHP not in joined
    assert "[REDACTED:github-token]" in joined


def test_u77_reference_spill_embed_point_scrubs(tmp_path) -> None:
    # Review F4: every U77 embed point is pinned, not just _format_evidence_rows.
    spill = tmp_path / "evidence.md"
    spill.write_text(
        _format_evidence_reference(
            skill_name="demo",
            generated_at="2026-09-22T00:00:00Z",
            days=7,
            summary={"tool_events": 1, "skill_events": 1, "error_events": 0},
            evidence_rows=[
                {
                    "created_at": "2026-09-22T00:00:00Z",
                    "tool_name": "skill_manage",
                    "is_error": 0,
                    "result_preview": f"TOKEN={GHP} verbatim",
                }
            ],
        ),
        encoding="utf-8",
    )
    text = spill.read_text(encoding="utf-8")
    assert GHP not in text
    assert "[REDACTED:github-token]" in text


def test_u77_semantic_query_embed_point_scrubs() -> None:
    # Review F4: the query that leaves the process is a published surface.
    report = {
        "summary": {"skills": [{"skill_name": "demo", "event_count": 1, "errors": 0}]},
        "skill_evidence": [
            {
                "skill_name": "demo",
                "tool_name": "skill_manage",
                "result_preview": f"TOKEN={GHP} verbatim",
            }
        ],
    }
    query = _build_semantic_query(report, eligible_names={"demo"})
    assert GHP not in query
    assert "[REDACTED:github-token]" in query


def test_u77_validation_detection_does_not_inflate_scrub_counter(tmp_path) -> None:
    # Review F5: skill_validate DETECTS without scrubbing — the disclosed
    # `scrubbed` counter counts operations, and a validate-only run must
    # not report scrubbed=1 when nothing was scrubbed.
    stats_reset()
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "SKILL.md").write_text(
        "---\nname: leaky\ndescription: A leaky skill.\n---\n\n# Leaky\n\n"
        f"Result was TOKEN={GHP}\n",
        encoding="utf-8",
    )
    result = validate_skill_file(bad / "SKILL.md")
    assert result["ok"] is False
    assert any("credential-shaped" in e for e in result["errors"])
    # Both the github-token value pattern and the generic token= assignment
    # pattern see the original string (2 detections); scrubbing replaces
    # once (the first marker hides the value from the second pattern).
    assert count_credentials(f"TOKEN={GHP}") == 2
    assert stats_snapshot()["scrubbed"] == 0  # detected, not scrubbed
    # A real scrub still counts, so the counter stays meaningful.
    scrub_text(f"TOKEN={GHP}")
    assert stats_snapshot()["scrubbed"] == 1


def test_u77_skill_validate_rejects_credential_content(tmp_path) -> None:
    good = tmp_path / "good"
    good.mkdir()
    (good / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Demo skill\n---\n\n# Demo\n",
        encoding="utf-8",
    )
    assert validate_skill_file(good / "SKILL.md")["ok"] is True

    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "SKILL.md").write_text(
        "---\nname: leaky\ndescription: A leaky skill.\n---\n\n# Leaky\n\n"
        f"Result was TOKEN={GHP}\n",
        encoding="utf-8",
    )
    result = validate_skill_file(bad / "SKILL.md")
    assert result["ok"] is False
    assert any("credential-shaped" in e for e in result["errors"])


def _write_token_session(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "session_id": "session-token",
                "session_start": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "model": "gpt-5.5",
                "platform": "slack",
                "messages": [
                    {"role": "user", "content": "manage the skill"},
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call-1",
                                "type": "function",
                                "function": {
                                    "name": "skill_manage",
                                    "arguments": json.dumps({"name": "demo"}),
                                },
                            }
                        ],
                    },
                    {
                        "role": "tool",
                        "tool_call_id": "call-1",
                        "content": f"TOKEN={GHP} applied",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_u77_backfill_discloses_scrub_count_and_scrubs_rows(tmp_path) -> None:
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    _write_token_session(sessions_dir / "session_20260922_100000_token.json")
    store = EvidenceStore(tmp_path / "ev.sqlite")

    result = backfill.backfill_sessions(
        sessions_dir=sessions_dir, store=store, days=365
    )

    assert result["tool_events_imported"] == 1
    assert result["credentials_scrubbed"] >= 1
    with store._read_connection() as conn:
        preview = conn.execute(
            "SELECT result_preview FROM tool_events"
        ).fetchone()["result_preview"]
    assert GHP not in preview
    assert "[REDACTED:github-token]" in preview


# --------------------------------------------------------------------------
# U78 — backfill readers, containment, and the dedupe race
# --------------------------------------------------------------------------


def test_u78_backfill_readers_never_touch_the_warm_writer(tmp_path, monkeypatch) -> None:
    store = EvidenceStore(tmp_path / "ev.sqlite")
    # After init, ANY use of the writer connection is a contract failure.
    def _explode(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("reader ran on the warm writer connection")

    monkeypatch.setattr(store, "connect", _explode)
    assert backfill._tool_event_exists(
        store, session_id="s", task_id="t", tool_name="x"
    ) is False
    assert backfill._turn_event_exists(
        store,
        session_id="s",
        model="m",
        platform="p",
        user_message="u",
        assistant_response="a",
    ) is False
    assert backfill._session_event_exists(store, session_id="s") is False


def test_u78_dedupe_race_returns_false_and_is_counted(tmp_path) -> None:
    store = EvidenceStore(tmp_path / "ev.sqlite")
    assert store.dedupe_index_active is True
    first = store.record_tool_call(
        tool_name="skill_view",
        args={"name": "demo"},
        result="ok",
        task_id="backfill:s1:c1",
        session_id="s1",
    )
    loser = store.record_tool_call(
        tool_name="skill_view",
        args={"name": "demo"},
        result="ok",
        task_id="backfill:s1:c1",
        session_id="s1",
    )
    assert first is True
    assert loser is False  # index arbitrated the duplicate insert
    # Live-path semantics preserved: an empty task_id may repeat freely.
    assert (
        store.record_tool_call(tool_name="bash", args={}, result="", session_id="s1")
        is True
    )
    assert (
        store.record_tool_call(tool_name="bash", args={}, result="", session_id="s1")
        is True
    )


def test_u78_legacy_duplicate_rows_keep_data_and_disclose(tmp_path, caplog) -> None:
    path = tmp_path / "legacy.sqlite"
    EvidenceStore(path)  # schema exists; index active on a fresh store
    conn = sqlite3.connect(path)
    # Simulate a legacy database: drop the index, then plant the duplicate
    # identities the pre-U74 ids could produce — index creation must fail
    # non-destructively on reopen.
    conn.execute("DROP INDEX IF EXISTS ux_tool_events_backfill_identity")
    for created in ("2026-09-20T00:00:00Z", "2026-09-21T00:00:00Z"):
        conn.execute(
            "INSERT INTO tool_events (created_at, session_id, task_id, tool_name,"
            " duration_ms, is_error, skill_name, args_json, result_preview)"
            " VALUES (?, ?, ?, ?, NULL, 0, '', '{}', 'x')",
            (created, "s1", "backfill:s1:c1", "skill_view"),
        )
    conn.commit()
    conn.close()

    with caplog.at_level(logging.WARNING, logger="hermes_curator_evolver.storage"):
        reopened = EvidenceStore(path)

    assert reopened.dedupe_index_active is False
    assert "dedupe index not created" in caplog.text
    with reopened._read_connection() as conn:
        rows = conn.execute("SELECT COUNT(*) FROM tool_events").fetchone()
    assert rows[0] == 2  # legacy data intact, no destructive migration


def test_u78_poison_legacy_session_is_contained_per_session(tmp_path, monkeypatch) -> None:
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()

    def write_session(name: str, session_id: str) -> None:
        (sessions_dir / name).write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "session_start": datetime.now(timezone.utc).isoformat(),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "model": "gpt-5.5",
                    "platform": "slack",
                    "messages": [
                        {"role": "user", "content": "go"},
                        {"role": "assistant", "content": "done"},
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    write_session("session_20260922_100000_good.json", "session-good")
    write_session("session_20260922_110000_bad.json", "session-bad")
    write_session("session_20260922_120000_after.json", "session-after")

    original = backfill._import_session_data

    def poisoned(data, **kwargs):
        if data.get("session_id") == "session-bad":
            raise ValueError("poison record (pass-9 stand-in for the P8 NaN abort)")
        return original(data, **kwargs)

    monkeypatch.setattr(backfill, "_import_session_data", poisoned)

    result = backfill.backfill_sessions(
        sessions_dir=sessions_dir, store=EvidenceStore(tmp_path / "ev.sqlite"), days=365
    )

    assert result["sessions_failed"] == 1
    assert result["sessions_imported"] == 2  # both neighbors still imported
    assert result["session_events_imported"] == 2
    assert "session_20260922_110000_bad.json" in result["last_session_error"]


def test_u78_mtime_guard_survives_vanished_files() -> None:
    assert backfill._mtime(Path("/definitely/not/here.json")) == 0.0


def test_u78_human_output_carries_truthful_counters(tmp_path, monkeypatch, capsys) -> None:
    hermes_home = tmp_path / "hermes-home"
    hermes_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    _write_token_session(sessions_dir / "session_20260922_100000_token.json")

    parser = build_parser()
    args = parser.parse_args(
        ["backfill-sessions", "--sessions-dir", str(sessions_dir), "--days", "365"]
    )
    handle_cli(args)

    out = capsys.readouterr().out
    assert "Credential-shaped strings scrubbed:" in out
    assert "Tool events imported: 1" in out


# --------------------------------------------------------------------------
# U79 — classifier residual edges
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        # Sibling exit-status keys outrank a zero primary exit (the key-pick
        # loop used to stop at exit_code and never read ``code``).
        ({"exit_code": 0, "code": 500}, True),
        ({"exit_code": 0, "code": 404}, True),
        ({"exit_code": 0, "code": 200}, False),  # in-band HTTP success stays success
        ({"exit_code": 0, "code": 201}, False),
        ({"exit_code": 0, "code": 226}, False),
        ({"exit_code": 0, "returncode": 1}, True),
        ({"exit_code": 0, "returncode": 0, "code": 201}, False),
        ({"code": 500}, True),  # mirror: without the zero sibling, unchanged
        ({"exit_code": 0}, False),
    ],
)
def test_u79_sibling_exit_key_outranks_zero_primary_exit(payload, expected) -> None:
    assert looks_like_error(payload) is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("exit_code=1", True),
        ("exit_code: 1", True),
        ("exit-code 2", True),
        ("exit_code_1", True),  # underscore-joined count is failure-shaped; lean failure (cheap signal)
        ("exited_with_code 4", True),
        ("exit=2", True),
        ("exit code 1", True),  # legacy arm still covered (widening is strict)
        ("exit_code=0", False),
        ("exit code 0", False),
        ("all good", False),
        # KTD35 positional pin: a later success claim answers the report.
        ("exit_code=1, no errors", False),
    ],
)
def test_u79_snake_case_exit_code_prose_is_failure(text, expected) -> None:
    assert looks_like_error(text) is expected


def test_u79_nan_and_infinity_never_crash_the_classifier() -> None:
    nan = float("nan")
    inf = float("inf")
    for payload in (
        {"status": nan},
        {"exit_code": nan},
        {"code": nan},
        {"exit_code": 0, "code": nan},
        {"status": inf},
        {"exit_code": inf},
    ):
        assert looks_like_error(payload) is False  # no signal, no crash
    # Explicit failure signals still classify under odd neighbors.
    assert looks_like_error({"status": nan, "error": "boom"}) is True


def test_u79_huge_ints_are_no_signal_not_a_crash() -> None:
    # Review F3: ints beyond float range (float(10**400) raises
    # OverflowError) must degrade to no signal — the pre-fix int(value)
    # never crashed on ints, so the NaN guard may not introduce a new
    # crash class. Mirror pair per L24: sibling orderings both pinned.
    huge = 10**400
    assert looks_like_error({"status": huge}) is False
    assert looks_like_error({"exit_code": huge}) is False
    assert looks_like_error({"exit_code": 0, "code": huge}) is False
    assert looks_like_error({"exit_code": huge, "code": 500}) is True
    assert looks_like_error({"status": huge, "error": "boom"}) is True
