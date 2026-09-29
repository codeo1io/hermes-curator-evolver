"""Cycle-11 U87 — dependency-aware skill impact analysis (dry-run only).

Upstream issue pingchesu/hermes-curator-evolver#12. Three edge sources
(``explicit_related_skill`` frontmatter, ``co_usage`` session evidence,
``shared_tool`` usage overlap), each carrying a recommended action
(``review`` / ``no-op`` / ``proposal-only``), exposed as the
``hermes-curator-evolver impact`` CLI. KTD43: the analysis writes
nothing, anywhere, ever — the dry-run test pins that by hash.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from hermes_curator_evolver.__main__ import build_parser
from hermes_curator_evolver.cli import handle_cli
from hermes_curator_evolver.impact import (
    ACTION_NO_OP,
    ACTION_PROPOSAL_ONLY,
    ACTION_REVIEW,
    SOURCE_CO_USAGE,
    SOURCE_EXPLICIT,
    SOURCE_SHARED_TOOL,
    build_impact_report,
    format_impact_json,
    format_impact_markdown,
)
from hermes_curator_evolver.proposals import (
    build_skill_proposal,
    format_proposal_markdown,
)
from hermes_curator_evolver.storage import EvidenceStore


def _write_skill(root: Path, name: str, frontmatter_extra: str = "") -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    path = skill_dir / "SKILL.md"
    path.write_text(
        "---\n"
        f"name: {name}\n"
        "description: test skill\n"
        f"{frontmatter_extra}"
        "---\n"
        "Body text.\n",
        encoding="utf-8",
    )
    return path


def _seed_store(db_path: Path) -> None:
    store = EvidenceStore(db_path)
    # skill-a and skill-b co-used in TWO sessions (>= CO_USAGE_REVIEW_MIN
    # → review).
    for session in ("session-1", "session-2"):
        store.record_tool_call(
            tool_name="Bash",
            args={"name": "skill-a", "command": "ls"},
            result="ok",
            session_id=session,
        )
        store.record_tool_call(
            tool_name="Bash",
            args={"name": "skill-b", "command": "ls"},
            result="ok",
            session_id=session,
        )
    # skill-a and skill-e co-used in ONE session (single observation →
    # no-op).
    store.record_tool_call(
        tool_name="Read",
        args={"name": "skill-a", "path": "/tmp/x"},
        result="ok",
        session_id="session-3",
    )
    store.record_tool_call(
        tool_name="Read",
        args={"name": "skill-e", "path": "/tmp/x"},
        result="ok",
        session_id="session-3",
    )
    # skill-a and skill-c share the WebSearch tool but never co-occur in
    # a session (shared_tool → proposal-only).
    store.record_tool_call(
        tool_name="WebSearch",
        args={"name": "skill-a", "query": "tests"},
        result="ok",
        session_id="session-4",
    )
    store.record_tool_call(
        tool_name="WebSearch",
        args={"name": "skill-c", "query": "other"},
        result="ok",
        session_id="session-5",
    )
    # Unrelated skill: its own tool, never shared with or near skill-a —
    # no edge of any source.
    store.record_tool_call(
        tool_name="TodoWrite",
        args={"name": "skill-unrelated", "todos": []},
        result="ok",
        session_id="session-6",
    )
    store.close()


@pytest.fixture()
def skills_dir(tmp_path: Path) -> Path:
    root = tmp_path / "skills"
    root.mkdir()
    _write_skill(root, "skill-a", "related_skills: [skill-c]\n")
    _write_skill(root, "skill-b")
    _write_skill(root, "skill-c")
    _write_skill(root, "skill-unrelated")
    return root


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "evidence" / "ev.sqlite"


def _edges(report: dict, skill: str, source: str) -> list[dict]:
    return [
        edge
        for edge in report["edges"]
        if edge["skill"] == skill and edge["source"] == source
    ]


def test_explicit_related_skill_edge_is_review(skills_dir: Path, tmp_path: Path):
    db = tmp_path / "e-explicit.sqlite"
    _seed_store(db)
    report = build_impact_report(
        "skill-a", days=30, skills_dir=skills_dir, db_path=db
    )
    assert report["skill_found"] is True
    edges = _edges(report, "skill-c", SOURCE_EXPLICIT)
    assert len(edges) == 1
    assert edges[0]["action"] == ACTION_REVIEW
    assert edges[0]["evidence"]["declared_in"].endswith("skill-a/SKILL.md")


def test_co_usage_edge_review_at_threshold(skills_dir: Path, db_path: Path):
    _seed_store(db_path)
    report = build_impact_report(
        "skill-a", days=30, skills_dir=skills_dir, db_path=db_path
    )
    edges = _edges(report, "skill-b", SOURCE_CO_USAGE)
    assert len(edges) == 1
    assert edges[0]["action"] == ACTION_REVIEW
    assert edges[0]["evidence"]["shared_sessions"] == 2


def test_co_usage_edge_no_op_single_session(skills_dir: Path, db_path: Path):
    _seed_store(db_path)
    report = build_impact_report(
        "skill-a", days=30, skills_dir=skills_dir, db_path=db_path
    )
    edges = _edges(report, "skill-e", SOURCE_CO_USAGE)
    assert len(edges) == 1
    assert edges[0]["action"] == ACTION_NO_OP
    assert edges[0]["evidence"]["shared_sessions"] == 1


def test_shared_tool_edge_is_proposal_only(skills_dir: Path, db_path: Path):
    _seed_store(db_path)
    report = build_impact_report(
        "skill-a", days=30, skills_dir=skills_dir, db_path=db_path
    )
    edges = _edges(report, "skill-c", SOURCE_SHARED_TOOL)
    assert len(edges) == 1
    assert edges[0]["action"] == ACTION_PROPOSAL_ONLY
    assert edges[0]["evidence"]["shared_tools"] == ["WebSearch"]


def test_unrelated_skill_has_no_edges(skills_dir: Path, db_path: Path):
    _seed_store(db_path)
    report = build_impact_report(
        "skill-a", days=30, skills_dir=skills_dir, db_path=db_path
    )
    assert _edges(report, "skill-unrelated", SOURCE_CO_USAGE) == []
    assert _edges(report, "skill-unrelated", SOURCE_SHARED_TOOL) == []


def test_dry_run_leaves_store_bytes_and_skill_files_unchanged(
    skills_dir: Path, db_path: Path, tmp_path: Path
):
    """KTD43 pin: the db's BYTES never change and no file outside the db's
    own SQLite companions is created. The ``-shm``/``-wal`` companions a
    read-only WAL open materializes on a quiescent store are disclosed in
    the module docstring: they carry no committed frames (hash proves it)
    and the next write-mode close removes them — pinned below."""
    _seed_store(db_path)
    before_files = sorted(p.name for p in tmp_path.rglob("*") if p.is_file())
    before_hash = hashlib.sha256(db_path.read_bytes()).hexdigest()
    build_impact_report("skill-a", days=30, skills_dir=skills_dir, db_path=db_path)
    after_hash = hashlib.sha256(db_path.read_bytes()).hexdigest()
    assert before_hash == after_hash
    assert not (db_path.parent / (db_path.name + "-journal")).exists()
    for skill_file in sorted(skills_dir.rglob("*")):
        if skill_file.is_file():
            assert skill_file.read_text(encoding="utf-8")
    # No file outside the db's companion pair was created.
    allowed = {db_path.name, db_path.name + "-shm", db_path.name + "-wal"}
    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert path.name in allowed | set(before_files)
    # The companions are transient: the next write-mode close cleans them.
    store = EvidenceStore(db_path)
    store.record_tool_call(
        tool_name="Bash", args={"name": "skill-a"}, result="ok", session_id="heal"
    )
    store.close()
    assert not (db_path.parent / (db_path.name + "-wal")).exists()
    assert not (db_path.parent / (db_path.name + "-shm")).exists()


def test_impact_cli_markdown_and_json(skills_dir: Path, db_path: Path, monkeypatch, capsys):
    _seed_store(db_path)
    monkeypatch.setenv("HERMES_CURATOR_EVOLVER_DB", str(db_path))
    parser = build_parser()
    args = parser.parse_args(
        [
            "impact",
            "--skill",
            "skill-a",
            "--days",
            "30",
            "--skills-dir",
            str(skills_dir),
        ]
    )
    handle_cli(args)
    markdown = capsys.readouterr().out
    assert "# Impact analysis: skill-a" in markdown
    assert "| skill-b | co_usage | review | 2 shared session(s)" in markdown
    assert "| skill-c | explicit_related_skill | review |" in markdown
    assert "| skill-c | shared_tool | proposal-only |" in markdown
    assert "| skill-e | co_usage | no-op | 1 shared session(s)" in markdown
    assert "dry-run" in markdown

    args = parser.parse_args(
        [
            "impact",
            "--skill",
            "skill-a",
            "--skills-dir",
            str(skills_dir),
            "--format",
            "json",
        ]
    )
    handle_cli(args)
    report = json.loads(capsys.readouterr().out)
    assert report["skill"] == "skill-a"
    assert report["dry_run"] is True
    assert report["totals_by_action"]["review"] == 2
    assert report["totals_by_action"]["no-op"] == 1
    assert report["totals_by_action"]["proposal-only"] == 3


def test_impact_cli_unknown_skill_warns_but_reports_evidence(
    db_path: Path, monkeypatch, capsys
):
    _seed_store(db_path)
    monkeypatch.setenv("HERMES_CURATOR_EVOLVER_DB", str(db_path))
    parser = build_parser()
    args = parser.parse_args(
        ["impact", "--skill", "skill-a", "--skills-dir", "/tmp/definitely-missing"]
    )
    handle_cli(args)
    out = capsys.readouterr().out
    assert "warning: skill 'skill-a' not found" in out
    assert "co_usage" in out


def test_end_to_end_pending_proposal_lists_co_used_skill(
    skills_dir: Path, db_path: Path
):
    """U87 acceptance: skill A's pending proposal (built from real
    evidence via ``build_skill_proposal``) is accompanied by an impact
    listing that names skill B through co-usage evidence — the
    dependency is invisible to the proposal's own evidence summary and
    only the impact report surfaces it."""
    _seed_store(db_path)
    store = EvidenceStore(db_path)
    report = store.summary(days=30, skill="skill-a")
    rows = store.recent_tool_events(days=30, skill="skill-a", limit=50)
    store.close()

    proposal = build_skill_proposal(
        {**report, "skill_evidence": rows}, skill_name="skill-a"
    )
    assert proposal["dry_run"] is True
    assert proposal["skill_name"] == "skill-a"
    # The proposal itself never mentions skill-b — the dependency edge
    # is exactly what the impact command exists to surface.
    assert "skill-b" not in format_proposal_markdown(proposal)

    impact = build_impact_report(
        "skill-a", days=30, skills_dir=skills_dir, db_path=db_path
    )
    markdown = format_impact_markdown(impact)
    assert "skill-b" in markdown
    assert _edges(impact, "skill-b", SOURCE_CO_USAGE)[0]["action"] == ACTION_REVIEW
    assert "skill-b" in format_impact_json(impact)
