"""U120 (cycle-13, assess F4): the co_usage impact join ignores empty-string
session ids.

The hook path defaults ``session_id=""`` (hooks.on_post_tool_call), and the
U87 join's ``other.session_id IS NOT NULL`` does not exclude empty strings —
so two skills that never truly co-occurred fabricated a co_usage edge off
their session-less events (probe: skill-a@s1, skill-b@s2 disjoint, plus one
session_id="" event each → edge skill-b shared_sessions=1 error_events=1).
Both sides of the join now refuse empty-string session ids, which also
means such rows can never inflate a REAL edge's shared_sessions count (the
review-escalation threshold is >= CO_USAGE_REVIEW_MIN shared sessions).
"""

from __future__ import annotations

from pathlib import Path

from hermes_curator_evolver.impact import SOURCE_CO_USAGE, build_impact_report
from hermes_curator_evolver.storage import EvidenceStore


def _write_skill(root: Path, name: str) -> Path:
    path = root / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        f"---\nname: {name}\ndescription: test skill\n---\nBody.\n",
        encoding="utf-8",
    )
    return path


def _probe_store(db_path: Path) -> None:
    """skill-a and skill-b NEVER truly co-occur: one disjoint real session
    each, plus one session-less ('' default) event each — exactly the
    assess F4 probe shape. The session-less skill-b event is error-shaped
    so a fabricated edge would also carry error_events=1."""
    store = EvidenceStore(db_path)
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "skill-a"},
        result="ok",
        session_id="s1",
    )
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "skill-b"},
        result="ok",
        session_id="s2",
    )
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "skill-a"},
        result="ok",
        session_id="",  # hook-path default (hooks.py:31)
    )
    store.record_tool_call(
        tool_name="terminal",
        args={"name": "skill-b"},
        result={"error": "upstream timeout (connection refused)"},
        session_id="",  # hook-path default (hooks.py:31)
    )
    store.close()


def test_u120_disjoint_session_less_events_fabricate_no_edge(tmp_path):
    db = tmp_path / "e.sqlite"
    _probe_store(db)

    signals = EvidenceStore(db).impact_signals(skill="skill-a", days=30)

    assert signals["co_usage"] == []


def test_u120_empty_session_rows_never_inflate_shared_sessions(tmp_path):
    """A REAL co-used pair keeps its truthful count: the two session-less
    events must not add a phantom second shared session."""
    db = tmp_path / "e.sqlite"
    _probe_store(db)
    store = EvidenceStore(db)
    # The real pair: skill-a and skill-b genuinely co-used in s1.
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "skill-b"},
        result="ok",
        session_id="s1",
    )
    store.close()

    signals = EvidenceStore(db).impact_signals(skill="skill-a", days=30)

    assert [row["skill"] for row in signals["co_usage"]] == ["skill-b"]
    assert signals["co_usage"][0]["shared_sessions"] == 1
    assert signals["co_usage"][0]["error_events"] == 0


def test_u120_true_co_usage_still_detected(tmp_path):
    """Positive control (U87 semantics unchanged): same-session use still
    yields the edge with a truthful shared_sessions count."""
    db = tmp_path / "e.sqlite"
    store = EvidenceStore(db)
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "skill-a"}, result="ok", session_id="s1"
    )
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "skill-b"}, result="ok", session_id="s1"
    )
    store.close()

    signals = EvidenceStore(db).impact_signals(skill="skill-a", days=30)

    assert [row["skill"] for row in signals["co_usage"]] == ["skill-b"]
    assert signals["co_usage"][0]["shared_sessions"] == 1


def test_u120_report_level_no_edge_from_session_less_rows(tmp_path):
    """The report consumer (``impact`` CLI) sees no fabricated edge either —
    before the fix this shape surfaced a no-op co_usage edge for skill-b."""
    db = tmp_path / "e.sqlite"
    _probe_store(db)
    root = tmp_path / "skills"
    root.mkdir()
    _write_skill(root, "skill-a")
    _write_skill(root, "skill-b")

    report = build_impact_report("skill-a", days=30, skills_dir=root, db_path=db)

    co_usage_edges = [
        edge for edge in report["edges"] if edge["source"] == SOURCE_CO_USAGE
    ]
    assert co_usage_edges == []
