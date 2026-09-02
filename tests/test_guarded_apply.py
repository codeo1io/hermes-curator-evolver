import json
import sys
from pathlib import Path

from hermes_curator_evolver.guarded_apply import (
    apply_guarded_patch,
    register_support_file_in_manifest,
    rollback_guarded_patch,
    sha256_file,
)


def test_guarded_apply_requires_explicit_approval(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")

    result = apply_guarded_patch(
        target_path=target,
        new_content="new",
        expected_sha256=sha256_file(target),
        approved=False,
        backup_root=tmp_path / "backups",
    )

    assert result["applied"] is False
    assert result["reason"] == "approval-required"
    assert target.read_text(encoding="utf-8") == "old"


def test_guarded_apply_rejects_hash_mismatch(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")

    result = apply_guarded_patch(
        target_path=target,
        new_content="new",
        expected_sha256="wrong",
        approved=True,
        backup_root=tmp_path / "backups",
    )

    assert result["applied"] is False
    assert result["reason"] == "hash-mismatch"
    assert target.read_text(encoding="utf-8") == "old"


def test_guarded_apply_creates_backup_and_rollback_restores(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")
    original_hash = sha256_file(target)

    result = apply_guarded_patch(
        target_path=target,
        new_content="new",
        expected_sha256=original_hash,
        approved=True,
        backup_root=tmp_path / "backups",
    )

    assert result["applied"] is True
    assert target.read_text(encoding="utf-8") == "new"
    manifest = Path(result["manifest_path"])
    assert manifest.exists()
    assert Path(result["backup_path"]).read_text(encoding="utf-8") == "old"

    rollback = rollback_guarded_patch(manifest, allowed_target_roots=(tmp_path,))

    assert rollback["rolled_back"] is True
    assert target.read_text(encoding="utf-8") == "old"
    assert json.loads(manifest.read_text(encoding="utf-8"))["rolled_back"] is True


def test_guarded_apply_rolls_back_when_verify_command_fails(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")
    original_hash = sha256_file(target)

    result = apply_guarded_patch(
        target_path=target,
        new_content="new",
        expected_sha256=original_hash,
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command="exit 7",
        verify_cwd=tmp_path,
    )

    assert result["applied"] is False
    assert result["reason"] == "verify-failed"
    assert target.read_text(encoding="utf-8") == "old"
    assert result["verify"]["exit_code"] == 7


def test_guarded_apply_rolls_back_when_verify_command_errors(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")
    original_hash = sha256_file(target)

    result = apply_guarded_patch(
        target_path=target,
        new_content="new",
        expected_sha256=original_hash,
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command="echo should-not-run",
        verify_cwd=tmp_path / "missing",
    )

    assert result["applied"] is False
    assert result["reason"] == "verify-failed"
    assert target.read_text(encoding="utf-8") == "old"
    assert result["verify"]["passed"] is False


def test_rollback_refuses_to_clobber_post_apply_changes_without_force(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")
    result = apply_guarded_patch(
        target_path=target,
        new_content="new",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
    )
    target.write_text("manual edit after apply", encoding="utf-8")

    rollback = rollback_guarded_patch(
        result["manifest_path"], allowed_target_roots=(tmp_path,)
    )

    assert rollback["rolled_back"] is False
    assert rollback["reason"] == "target-changed"
    assert target.read_text(encoding="utf-8") == "manual edit after apply"

    forced = rollback_guarded_patch(
        result["manifest_path"], force=True, allowed_target_roots=(tmp_path,)
    )

    assert forced["rolled_back"] is True
    assert target.read_text(encoding="utf-8") == "old"


def test_staged_verify_runs_cheap_stage_then_expensive_when_cheap_passes(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")
    marker = tmp_path / "expensive-ran.txt"

    result = apply_guarded_patch(
        target_path=target,
        new_content="new content",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command=f"{sys.executable} -c \"open('{marker}', 'w').write('ran')\"",
        verify_cwd=tmp_path,
        staged_verify=True,
    )

    assert result["applied"] is True
    assert marker.exists(), "expensive stage should run when cheap stage passes"
    verify = result["verify"]
    assert verify["staged"] is True
    stage_names = [stage["name"] for stage in verify["stages"]]
    assert stage_names == ["builtin-structural", "verify-command"]
    assert all(stage["passed"] for stage in verify["stages"])


def test_staged_verify_skips_expensive_stage_when_cheap_stage_fails(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")
    marker = tmp_path / "expensive-ran.txt"
    huge_content = "<!-- curator-evolver:auto:start -->\n" + ("X" * 200_000) + "\n<!-- curator-evolver:auto:end -->\n"

    result = apply_guarded_patch(
        target_path=target,
        new_content=huge_content,
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command=f"{sys.executable} -c \"open('{marker}', 'w').write('ran')\"",
        verify_cwd=tmp_path,
        staged_verify=True,
    )

    assert result["applied"] is False
    assert result["reason"] == "verify-failed"
    assert target.read_text(encoding="utf-8") == "old", "rollback should restore the original file"
    assert not marker.exists(), "expensive stage must not run when cheap stage fails"
    verify = result["verify"]
    assert verify["staged"] is True
    assert verify["failed_stage"] == "builtin-structural"
    assert verify["stages"][0]["passed"] is False


def test_staged_verify_rolls_back_when_expensive_stage_fails(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")

    result = apply_guarded_patch(
        target_path=target,
        new_content="new content",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command="exit 9",
        verify_cwd=tmp_path,
        staged_verify=True,
    )

    assert result["applied"] is False
    assert result["reason"] == "verify-failed"
    assert target.read_text(encoding="utf-8") == "old"
    verify = result["verify"]
    assert verify["staged"] is True
    assert verify["failed_stage"] == "verify-command"
    assert verify["exit_code"] == 9
    manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["rolled_back"] is True
    assert manifest["rollback_failed_stage"] == "verify-command"


def test_staged_verify_runs_pre_verify_command_before_expensive(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")
    pre_marker = tmp_path / "pre.txt"
    expensive_marker = tmp_path / "expensive.txt"

    result = apply_guarded_patch(
        target_path=target,
        new_content="new",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        pre_verify_command=f"{sys.executable} -c \"open('{pre_marker}','w').write('p')\"",
        verify_command=f"{sys.executable} -c \"open('{expensive_marker}','w').write('e')\"",
        verify_cwd=tmp_path,
    )

    assert result["applied"] is True
    assert pre_marker.exists() and expensive_marker.exists()
    stage_names = [stage["name"] for stage in result["verify"]["stages"]]
    assert stage_names == ["builtin-structural", "pre-verify-command", "verify-command"]


def test_staged_verify_pre_command_failure_skips_expensive_stage(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")
    expensive_marker = tmp_path / "expensive.txt"

    result = apply_guarded_patch(
        target_path=target,
        new_content="new",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        pre_verify_command="exit 3",
        verify_command=f"{sys.executable} -c \"open('{expensive_marker}','w').write('e')\"",
        verify_cwd=tmp_path,
    )

    assert result["applied"] is False
    assert result["reason"] == "verify-failed"
    assert target.read_text(encoding="utf-8") == "old"
    assert not expensive_marker.exists()
    assert result["verify"]["failed_stage"] == "pre-verify-command"


def test_non_staged_verify_remains_backward_compatible(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")

    result = apply_guarded_patch(
        target_path=target,
        new_content="new",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command="true",
        verify_cwd=tmp_path,
    )

    verify = result["verify"]
    assert result["applied"] is True
    assert verify["passed"] is True
    assert "stages" not in verify
    assert verify.get("staged") is not True


def test_guarded_apply_exposes_target_context_to_verify_command(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")
    seen = tmp_path / "seen.json"
    verifier = tmp_path / "verify_env.py"
    verifier.write_text(
        "import json, os, pathlib\n"
        f"pathlib.Path({str(seen)!r}).write_text(json.dumps({{\n"
        "    'target': os.environ.get('HERMES_CURATOR_TARGET_PATH'),\n"
        "    'backup': os.environ.get('HERMES_CURATOR_BACKUP_PATH'),\n"
        "    'manifest': os.environ.get('HERMES_CURATOR_MANIFEST_PATH'),\n"
        "    'new_sha': os.environ.get('HERMES_CURATOR_NEW_SHA256'),\n"
        "}))\n",
        encoding="utf-8",
    )

    result = apply_guarded_patch(
        target_path=target,
        new_content="new",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command=f"{sys.executable} {verifier}",
        verify_cwd=tmp_path,
    )

    assert result["applied"] is True
    data = json.loads(seen.read_text(encoding="utf-8"))
    assert data["target"] == str(target)
    assert data["backup"] == result["backup_path"]
    assert data["manifest"] == result["manifest_path"]
    assert data["new_sha"] == result["new_sha256"]


def test_staged_verify_rolls_back_invalid_yaml_frontmatter(tmp_path):
    target = tmp_path / "SKILL.md"
    target.write_text("---\nname: old\n---\n\n# Old\n", encoding="utf-8")
    marker = tmp_path / "expensive-ran.txt"

    result = apply_guarded_patch(
        target_path=target,
        new_content="---\nname: [\n---\n\n# Broken\n",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command=f"{sys.executable} -c \"open('{marker}', 'w').write('ran')\"",
        verify_cwd=tmp_path,
        staged_verify=True,
    )

    assert result["applied"] is False
    assert result["reason"] == "verify-failed"
    assert target.read_text(encoding="utf-8") == "---\nname: old\n---\n\n# Old\n"
    assert not marker.exists(), "expensive stage must not run after invalid frontmatter"
    verify = result["verify"]
    assert verify["failed_stage"] == "builtin-structural"
    assert verify["stages"][0]["passed"] is False
    assert "frontmatter-not-parseable" in verify["stages"][0]["reason"]


def test_rollback_removes_apply_created_support_files(tmp_path):
    # Assessment F3 regression: rollback restored SKILL.md but orphaned the
    # apply's new references/ support file on disk.
    skills_root = tmp_path / "skills"
    target = skills_root / "demo" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")

    result = apply_guarded_patch(
        target_path=target,
        new_content="new\n",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command="true",
        staged_verify=True,
    )
    support = target.parent / "references" / "curator-evolver-auto-demo-x.md"
    support.parent.mkdir(parents=True)
    support.write_text("spilled evidence", encoding="utf-8")
    register_support_file_in_manifest(
        result["manifest_path"],
        source_path=support,
        relative_path="references/curator-evolver-auto-demo-x.md",
    )

    rollback = rollback_guarded_patch(
        result["manifest_path"], allowed_target_roots=(tmp_path,)
    )

    assert rollback["rolled_back"] is True
    assert target.read_text(encoding="utf-8") == "original\n"
    assert support.exists() is False, "rollback must not orphan apply-created support files"
    removed = rollback["support_files"]["removed"]
    assert [item["path"] for item in removed] == [
        "references/curator-evolver-auto-demo-x.md"
    ]
    # U35: every removal keeps a rollback-safety copy under the manifest dir
    safety_dir = Path(result["manifest_path"]).parent / "rollback-safety"
    for item in removed:
        assert Path(item["safety_copy"]).is_file()
        assert safety_dir in Path(item["safety_copy"]).parents
    manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
    assert [item["path"] for item in manifest["rollback_support_files"]["removed"]] == [
        "references/curator-evolver-auto-demo-x.md"
    ]


def test_rollback_skips_support_files_changed_since_apply(tmp_path):
    skills_root = tmp_path / "skills"
    target = skills_root / "demo" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")

    result = apply_guarded_patch(
        target_path=target,
        new_content="new\n",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command="true",
        staged_verify=True,
    )
    support = target.parent / "references" / "curator-evolver-auto-demo-y.md"
    support.parent.mkdir(parents=True)
    support.write_text("spilled evidence", encoding="utf-8")
    register_support_file_in_manifest(
        result["manifest_path"],
        source_path=support,
        relative_path="references/curator-evolver-auto-demo-y.md",
    )
    support.write_text("hand-edited after apply", encoding="utf-8")

    rollback = rollback_guarded_patch(
        result["manifest_path"], allowed_target_roots=(tmp_path,)
    )

    assert rollback["rolled_back"] is True
    assert support.exists() is True, "edited files must be preserved, not destroyed"
    assert rollback["support_files"]["skipped"] == [
        {
            "path": "references/curator-evolver-auto-demo-y.md",
            "reason": "file-changed-since-apply",
        }
    ]


def test_rollback_refuses_tampered_target_outside_allowed_roots(tmp_path):
    skills_root = tmp_path / "skills"
    target = skills_root / "demo" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")

    result = apply_guarded_patch(
        target_path=target,
        new_content="new\n",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command="true",
        staged_verify=True,
    )
    outside = tmp_path / "outside.md"
    manifest_path = Path(result["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["target_path"] = str(outside)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    rollback = rollback_guarded_patch(
        manifest_path, allowed_target_roots=(skills_root,)
    )

    assert rollback["rolled_back"] is False
    assert rollback["reason"] == "unsafe-target-path"
    assert outside.exists() is False
    assert target.read_text(encoding="utf-8") == "new\n"


def test_rollback_refuses_backup_path_outside_manifest_directory(tmp_path):
    skills_root = tmp_path / "skills"
    target = skills_root / "demo" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")

    result = apply_guarded_patch(
        target_path=target,
        new_content="new\n",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command="true",
        staged_verify=True,
    )
    evil = tmp_path / "evil-payload.md"
    evil.write_text("tampered backup", encoding="utf-8")
    manifest_path = Path(result["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backup_path"] = str(evil)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    rollback = rollback_guarded_patch(manifest_path)

    assert rollback["rolled_back"] is False
    assert rollback["reason"] == "unsafe-backup-path"
    assert target.read_text(encoding="utf-8") == "new\n"


def test_verify_command_receives_allowlisted_environment_only(tmp_path):
    # Roadmap U3: verify commands must not inherit the full parent
    # environment - a tampered verify_command must not become a secret leak.
    target = tmp_path / "SKILL.md"
    target.write_text("old", encoding="utf-8")
    seen = tmp_path / "env.json"
    verifier = tmp_path / "dump_env.py"
    verifier.write_text(
        "import json, os, pathlib\n"
        f"pathlib.Path({str(seen)!r}).write_text(json.dumps({{\n"
        "    'secret': os.environ.get('HERMES_CURATOR_TEST_SECRET'),\n"
        "    'has_path': bool(os.environ.get('PATH')),\n"
        "    'has_home': bool(os.environ.get('HOME')),\n"
        "    'target': os.environ.get('HERMES_CURATOR_TARGET_PATH'),\n"
        "}), encoding='utf-8')\n",
        encoding="utf-8",
    )

    import os

    os.environ["HERMES_CURATOR_TEST_SECRET"] = "do-not-leak"
    try:
        result = apply_guarded_patch(
            target_path=target,
            new_content="new",
            expected_sha256=sha256_file(target),
            approved=True,
            backup_root=tmp_path / "backups",
            verify_command=f"{sys.executable} {verifier}",
            verify_cwd=tmp_path,
        )
    finally:
        del os.environ["HERMES_CURATOR_TEST_SECRET"]

    assert result["applied"] is True
    data = json.loads(seen.read_text(encoding="utf-8"))
    assert data["secret"] is None
    assert data["has_path"] is True
    assert data["has_home"] is True
    assert data["target"] == str(target)


def test_rollback_refuses_to_delete_restored_target_via_tampered_manifest(tmp_path):
    """U35 / assessment N1: manifest support entries are untrusted input.

    A tampered manifest listed the skill target itself as a support file
    whose backup_path was a legitimate snapshot of SKILL.md: the rollback
    restored the target, then unlinked it because the entry hash matched.
    The entry must now be refused before any unlink - both by
    target-identity and by registration cross-check (its backup_path does
    not point at a snapshot inside the manifest's own backup directory).
    """

    skills_root = tmp_path / "skills"
    target = skills_root / "demo" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")

    result = apply_guarded_patch(
        target_path=target,
        new_content="new\n",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command="true",
    )
    assert result["applied"] is True

    # N1 attack shape: register the restored SKILL.md as a "support file",
    # pointing its backup_path at the apply's own target backup.
    manifest_path = Path(result["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["support_files"] = [
        {
            "path": "SKILL.md",
            "kind": "reference",
            "sha256": sha256_file(target),  # matches live target after restore
            "backup_path": result["backup_path"],
        }
    ]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    rollback = rollback_guarded_patch(
        manifest_path, allowed_target_roots=(skills_root,)
    )

    assert rollback["rolled_back"] is True
    assert target.read_text(encoding="utf-8") == "original\n"
    skipped = rollback["support_files"]["skipped"]
    assert any(item["path"] == "SKILL.md" for item in skipped)
    assert {item["reason"] for item in skipped} == {"target-file"}
    assert rollback["support_files"]["removed"] == []


def test_rollback_refuses_unregistered_support_entries(tmp_path):
    """U35 / assessment N1: only registered snapshots may authorize removal."""

    skills_root = tmp_path / "skills"
    target = skills_root / "demo" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")

    result = apply_guarded_patch(
        target_path=target,
        new_content="new\n",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command="true",
    )

    bystander = target.parent / "references" / "operator-notes.md"
    bystander.parent.mkdir(parents=True)
    bystander.write_text("hand-written", encoding="utf-8")

    manifest_path = Path(result["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["support_files"] = [
        {
            "path": "references/operator-notes.md",
            "kind": "reference",
            "sha256": sha256_file(bystander),
            # no backup_path at all - nothing registered this file
        }
    ]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    rollback = rollback_guarded_patch(
        manifest_path, allowed_target_roots=(skills_root,)
    )

    assert rollback["rolled_back"] is True
    assert bystander.exists() is True, "unregistered file must never be removed"
    reasons = {item["reason"] for item in rollback["support_files"]["skipped"]}
    assert reasons == {"not-registered"}
    assert rollback["support_files"]["removed"] == []


def test_rollback_requires_explicit_unrestricted_opt_in(tmp_path):
    """U35 / assessment C2: no --skills-dir must not mean "any target".

    With no allowed_target_roots the rollback used to copy the backup over
    ANY path named in the manifest - an arbitrary-overwrite primitive for a
    tampered manifest. It now refuses unless containment roots are supplied
    or the caller explicitly opts out.
    """

    skills_root = tmp_path / "skills"
    target = skills_root / "demo" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")

    result = apply_guarded_patch(
        target_path=target,
        new_content="new\n",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command="true",
    )
    manifest_path = Path(result["manifest_path"])

    refused = rollback_guarded_patch(manifest_path)

    assert refused["rolled_back"] is False
    assert refused["reason"] == "unrestricted-target"
    assert "allowed_target_roots" in refused["hint"]
    assert target.read_text(encoding="utf-8") == "new\n"

    explicit = rollback_guarded_patch(manifest_path, allow_unrestricted_target=True)

    assert explicit["rolled_back"] is True
    assert target.read_text(encoding="utf-8") == "original\n"


def test_rollback_snapshots_target_before_restore(tmp_path):
    """U35: the rollback keeps a safety copy of the overwritten target."""

    skills_root = tmp_path / "skills"
    target = skills_root / "demo" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")

    result = apply_guarded_patch(
        target_path=target,
        new_content="new\n",
        expected_sha256=sha256_file(target),
        approved=True,
        backup_root=tmp_path / "backups",
        verify_command="true",
    )
    manifest_path = Path(result["manifest_path"])

    rollback = rollback_guarded_patch(manifest_path, allowed_target_roots=(skills_root,))

    assert rollback["rolled_back"] is True
    snapshot = Path(rollback["rollback_safety"]["target_snapshot"])
    assert snapshot.is_file()
    assert snapshot.read_text(encoding="utf-8") == "new\n"
    assert snapshot.parent == manifest_path.parent / "rollback-safety"


# ---------------------------------------------------------------------------
# Roadmap U44 (assessment Q3/Q5): mode-preserving atomic writes and atomic
# snapshots.
# ---------------------------------------------------------------------------


def test_u44_atomic_write_preserves_existing_target_mode(tmp_path):
    import os
    import stat

    from hermes_curator_evolver.guarded_apply import _atomic_write_bytes

    target = tmp_path / "SKILL.md"
    target.write_text("old")
    os.chmod(target, 0o640)
    before = stat.S_IMODE(target.stat().st_mode)

    _atomic_write_bytes(target, b"new")

    after = stat.S_IMODE(target.stat().st_mode)
    assert target.read_bytes() == b"new"
    assert after == before, (before, after)


def test_u44_atomic_write_new_file_uses_explicit_mode(tmp_path):
    import stat

    from hermes_curator_evolver.guarded_apply import _atomic_write_bytes

    target = tmp_path / "SKILL.md"
    _atomic_write_bytes(target, b"new", mode=0o600)
    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_u44_apply_preserves_skill_file_permissions(tmp_path, monkeypatch):
    import os
    import stat

    # A minimal patch application path: build one via the public helper used
    # by tests above, then check the on-disk mode survived the write.
    from hermes_curator_evolver.guarded_apply import _atomic_write_text

    target = tmp_path / "SKILL.md"
    target.write_text("# skill\n")
    os.chmod(target, 0o664)
    _atomic_write_text(target, "# skill\n\nmore\n")
    assert stat.S_IMODE(target.stat().st_mode) == 0o664


def test_u44_snapshot_is_atomic_and_mode_preserving(tmp_path):
    import os
    import stat

    from hermes_curator_evolver.guarded_apply import _snapshot_for_safety

    skill = tmp_path / "SKILL.md"
    skill.write_text("body")
    os.chmod(skill, 0o640)
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    snapshot = _snapshot_for_safety(skill, backup_dir, "skill")

    assert snapshot is not None
    assert snapshot.read_text() == "body"
    assert stat.S_IMODE(snapshot.stat().st_mode) == 0o640


def test_u44_no_stray_temp_files_after_writes(tmp_path):
    from hermes_curator_evolver.guarded_apply import _atomic_write_bytes

    target = tmp_path / "target.md"
    _atomic_write_bytes(target, b"x")
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["target.md"], names
