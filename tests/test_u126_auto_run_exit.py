"""U126 (cycle-13, assess F1; the cycle-12 KNOWN LIMIT explicitly deferred
"to the next cycle" in commit 2de240b — this is that cycle): auto-run exits
1 when a guarded apply fails.

The run JSON always reported ``summary.apply_failed`` (U111 semantics: a
guarded apply that refused, hit hash drift, failed its verify command or
rolled back), but ``cli.py`` did a bare ``return`` — so a scheduler or
script wrapping ``auto-run`` saw success on failure. The exit code now
carries the failure. Deliberate no-ops stay 0: no candidates, dry-run
all-planned, approval-required refusal (F4's shape), restore-drill gate
skips — the planned-vs-failed distinction is exactly U111's.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hermes_curator_evolver.__main__ import main
from hermes_curator_evolver.storage import EvidenceStore

_FAILING_VERIFY = 'python3 -c "import sys; sys.exit(1)"'


@pytest.fixture()
def isolated_env(tmp_path, monkeypatch):
    """Point every default path (home + db) at tmp so probes stay hermetic."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("HERMES_CURATOR_EVOLVER_DB", str(tmp_path / "evidence.sqlite"))
    return tmp_path


def _write_skill(root: Path, name: str) -> Path:
    path = root / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        f"---\nname: {name}\ndescription: test skill\n---\n\n# {name}\n\n"
        "Use this skill for gateway troubleshooting.\n",
        encoding="utf-8",
    )
    return path


def _seed(tmp_path: Path, with_evidence: bool = True) -> Path:
    """Create a skills dir + evidence at the env-pinned store (the auto-run
    CLI path uses the default EvidenceStore, so the seed must land exactly
    where HERMES_CURATOR_EVOLVER_DB points)."""
    skills = tmp_path / "skills"
    _write_skill(skills, "store-playbook")
    if with_evidence:
        store = EvidenceStore(tmp_path / "evidence.sqlite")
        store.record_tool_call(
            tool_name="skill_view",
            args={"name": "store-playbook"},
            result={"success": True},
            session_id="s1",
        )
    return skills


def _auto_run(skills: Path, *flags: str) -> int:
    return main(
        [
            "auto-run",
            "--skills-dir",
            str(skills),
            "--backup-dir",
            str(skills.parent / "backups"),
            "--min-evidence",
            "1",
            *flags,
        ]
    )


def test_u126_apply_failure_exits_one(isolated_env, tmp_path, capsys):
    """The assess F1 live rig: apply-low-risk + approve + failing verify →
    apply_failed:1 in the summary — and now rc 1 (previously rc 0)."""
    skills = _seed(tmp_path)
    rc = _auto_run(
        skills, "--apply-low-risk", "--approve-auto-apply", "--verify-command",
        _FAILING_VERIFY,
    )
    captured = capsys.readouterr()
    assert rc == 1
    assert "Apply failed: 1" in captured.out


def test_u126_dry_run_all_planned_exits_zero(isolated_env, tmp_path, capsys):
    """Without --apply-low-risk every candidate stays planned: a deliberate
    no-op must not become a failure exit."""
    skills = _seed(tmp_path)
    rc = _auto_run(skills)
    captured = capsys.readouterr()
    assert rc == 0
    # The summary line is printed unconditionally — the contract is the
    # count (and the rc), not the line's absence.
    assert "Apply failed: 0" in captured.out


def test_u126_approval_refusal_exits_zero(isolated_env, tmp_path, capsys):
    """--apply-low-risk WITHOUT --approve-auto-apply is the F4 refusal
    shape: candidates stay planned with apply_result "auto-approval-
    required" — deliberate refusal, not failure (U111 planned-vs-failed)."""
    skills = _seed(tmp_path)
    rc = _auto_run(skills, "--apply-low-risk")
    captured = capsys.readouterr()
    assert rc == 0
    assert "Apply failed: 0" in captured.out


def test_u126_no_candidates_exits_zero(isolated_env, tmp_path):
    """No evidence → no candidates → nothing happened → rc 0."""
    skills = _seed(tmp_path, with_evidence=False)
    rc = _auto_run(skills, "--apply-low-risk", "--approve-auto-apply",
                   "--verify-command", _FAILING_VERIFY)
    assert rc == 0


def test_u126_json_output_still_printed_on_failure(isolated_env, tmp_path, capsys):
    """The rc wiring must not eat the report: JSON callers still get the
    machine-readable summary with ``apply_failed`` in it."""
    import json

    skills = _seed(tmp_path)
    rc = _auto_run(
        skills,
        "--format",
        "json",
        "--apply-low-risk",
        "--approve-auto-apply",
        "--verify-command",
        _FAILING_VERIFY,
    )
    captured = capsys.readouterr()
    assert rc == 1
    payload = json.loads(captured.out)
    assert payload["summary"]["apply_failed"] == 1
