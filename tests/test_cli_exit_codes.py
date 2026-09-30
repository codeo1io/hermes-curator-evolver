"""Cycle-12 U107: the CLI exit-code contract.

``main()`` must propagate command outcomes: a FAILED verify, an apply or
rollback refusal, a failed restore drill and an unusable backfill source
all exit 1, while warning-only degradation (impact dry-run on a missing
skill or store) deliberately stays 0.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hermes_curator_evolver.__main__ import main


@pytest.fixture()
def isolated_env(tmp_path, monkeypatch):
    """Point every default path (home + db) at tmp so probes stay hermetic."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("HERMES_CURATOR_EVOLVER_DB", str(tmp_path / "evidence.sqlite"))
    return tmp_path


def test_verify_failed_exits_nonzero(isolated_env, tmp_path, capsys):
    proposal = tmp_path / "proposal.json"
    proposal.write_text(json.dumps({}), encoding="utf-8")
    rc = main(["verify", "--proposal-file", str(proposal)])
    assert rc == 1


def test_status_exits_zero(isolated_env, capsys):
    assert main(["status"]) == 0


def test_apply_refusal_exits_nonzero(isolated_env, tmp_path):
    content = tmp_path / "content.md"
    content.write_text("x", encoding="utf-8")
    rc = main(
        [
            "apply",
            "--target",
            str(tmp_path / "does-not-exist.md"),
            "--content-file",
            str(content),
            "--expected-sha256",
            "0" * 64,
            "--approve",
        ]
    )
    assert rc == 1


def test_rollback_refusal_exits_nonzero(isolated_env, tmp_path):
    rc = main(["rollback", "--manifest", str(tmp_path / "missing-manifest.json")])
    assert rc == 1


def test_restore_drill_fail_exits_nonzero(isolated_env, tmp_path):
    # A manifest without a backup path drills to status "fail"
    # (manifest-missing-backup-path) — the exit code must say so.
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "target_path": str(tmp_path / "target.md"),
                "original_sha256": "0" * 64,
            }
        ),
        encoding="utf-8",
    )
    rc = main(
        ["restore-drill", "--manifest", str(manifest), "--target-dir", str(tmp_path / "drill")]
    )
    assert rc == 1


def test_backfill_missing_source_exits_nonzero(isolated_env, tmp_path):
    rc = main(
        [
            "backfill-sessions",
            "--sessions-dir",
            str(tmp_path / "no-such-dir"),
        ]
    )
    assert rc == 1


def test_impact_missing_skill_stays_zero(isolated_env, capsys):
    # Warning-only degradation is not a failure: the impact dry-run still
    # reports evidence edges (KTD43: no store is created either).
    rc = main(["impact", "--skill", "does-not-exist"])
    assert rc == 0
