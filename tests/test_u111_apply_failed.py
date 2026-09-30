"""Cycle-12 U111 pin: a failed guarded apply leaves an honest status.

Assess finding F8 (probe-verified at base aa93a57): the auto-run loop
stores ``apply_result`` but only ever transitions ``status`` from
``planned`` to ``applied`` — a guarded apply that refused, hit hash
drift, failed verification, or rolled back left the candidate reported
as ``planned``, so the human summary showed an attempted-and-failed
apply as merely not-yet-attempted.

Pinned behavior: a failing post-write verify makes the guarded apply roll
back, and the candidate then carries ``status == "apply_failed"`` — in
the run JSON, the ``summary`` counts, and the markdown report — while
the skill file on disk is restored. A plain dry-run still reports
``planned`` (the new status is scoped to attempted applies only).
"""

from pathlib import Path

from hermes_curator_evolver.auto_evolve import (
    AutoEvolveConfig,
    format_auto_evolve_result,
    run_auto_evolve,
)
from hermes_curator_evolver.storage import EvidenceStore

_FAILING_VERIFY = 'python3 -c "import sys; sys.exit(1)"'


def _write_skill(root: Path, name: str) -> Path:
    path = root / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        f"---\nname: {name}\ndescription: test skill\n---\n\n# {name}\n\n"
        "Use this skill for gateway troubleshooting.\n",
        encoding="utf-8",
    )
    return path


def _run(tmp_path, **config_overrides):
    db = tmp_path / "evidence.sqlite"
    store = EvidenceStore(db)
    skills = tmp_path / "skills"
    backups = tmp_path / "backups"
    skill_file = _write_skill(skills, "store-playbook")
    store.record_tool_call(
        tool_name="skill_view",
        args={"name": "store-playbook"},
        result={"success": True},
        session_id="s1",
    )
    defaults = dict(
        db_path=db,
        skills_dir=skills,
        backup_dir=backups,
        days=30,
        min_evidence=1,
        apply_low_risk=True,
        approve_auto_apply=True,
    )
    defaults.update(config_overrides)
    return run_auto_evolve(AutoEvolveConfig(**defaults)), skill_file


def test_u111_failed_verify_marks_candidate_apply_failed(tmp_path):
    result, skill_file = _run(tmp_path, verify_command=_FAILING_VERIFY)
    candidate = result["candidates"][0]

    assert candidate["status"] == "apply_failed", (
        "a rolled-back apply must not be reported as 'planned'"
    )
    assert candidate["apply_result"]["applied"] is False
    assert candidate["apply_result"]["reason"] == "verify-failed"
    assert candidate["apply_result"]["verify"]["passed"] is False
    assert candidate["apply_result"].get("backup_path")


def test_u111_failed_apply_counters_and_report(tmp_path):
    result, _ = _run(tmp_path, verify_command=_FAILING_VERIFY)

    assert result["summary"]["applied"] == 0
    assert result["summary"]["apply_failed"] == 1
    report = format_auto_evolve_result(result, output_format="markdown")
    assert "- Apply failed: 1" in report
    assert "apply_failed" in report


def test_u111_rollback_restores_the_skill_file(tmp_path):
    _, skill_file = _run(tmp_path, verify_command=_FAILING_VERIFY)
    assert "gateway troubleshooting" in skill_file.read_text(encoding="utf-8")
    assert "Auto-curated evidence notes" not in skill_file.read_text(encoding="utf-8")


def test_u111_dry_run_still_reports_planned(tmp_path):
    result, skill_file = _run(tmp_path, apply_low_risk=False)

    assert result["candidates"][0]["status"] == "planned"
    assert result["summary"]["apply_failed"] == 0
