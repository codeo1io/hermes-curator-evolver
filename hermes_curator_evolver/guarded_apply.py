"""Guarded apply and rollback helpers for reviewed skill patches."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .restore_drill import (
    DRILL_STATE_FILENAME,
    record_apply_in_state,
)


_MANAGED_BLOCK_START = "<!-- curator-evolver:auto:start -->"
_MANAGED_BLOCK_END = "<!-- curator-evolver:auto:end -->"
_BUILTIN_HARD_CAP_CHARS = 100_000


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _atomic_write_bytes(
    path: Path, data: bytes, mode: int | None = None
) -> None:
    """Write bytes via temp file + atomic rename (roadmap U35/U18/U44).

    A partial write must never be visible as the target's content: the temp
    file lives in the destination directory (same filesystem, so ``os.replace``
    is atomic) and readers either see the old bytes or the complete new ones.
    The temp file also inherits the target's existing permission bits — or an
    explicit ``mode`` — before the rename, so an apply or rollback no longer
    re-creates a carefully-chmodded file at the process umask (assessment
    Q3: 0o640 became 0o664 through both apply and rollback).
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp-{os.getpid()}-{threading.get_ident()}")
    try:
        with temp.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        dest_mode = mode
        if dest_mode is None:
            try:
                dest_mode = path.stat().st_mode & 0o7777
            except OSError:
                dest_mode = None  # new file: keep the umask default
        if dest_mode is not None:
            os.chmod(temp, dest_mode)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink(missing_ok=True)


def _atomic_write_text(path: Path, text: str, mode: int | None = None) -> None:
    _atomic_write_bytes(path, text.encode("utf-8"), mode=mode)


def _atomic_copy(source: Path, dest: Path) -> None:
    """Copy via the atomic write path, preserving the source's mode (U44)."""

    source_path = Path(source)
    try:
        source_mode = source_path.stat().st_mode & 0o7777
    except OSError:
        source_mode = None
    _atomic_write_bytes(dest, source_path.read_bytes(), mode=source_mode)


def _write_manifest(path: Path, data: dict[str, Any]) -> None:
    _atomic_write_text(
        path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    )


_VERIFY_ENV_KEYS = ("PATH", "HOME", "TMPDIR", "TERM", "LANG")


def _build_verify_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Construct a minimal environment for verify commands (roadmap U3).

    The full parent environment is deliberately NOT forwarded: a verify
    command runs attacker-adjacent tooling against a freshly written skill
    file, and leaking every ``os.environ`` entry (API keys, proxy settings,
    job secrets) into it widens the blast radius of a tampered
    ``verify_command``. Only the variables shell commands need to start -
    ``PATH``/``HOME`` plus locale - are passed, then the caller's explicit
    per-apply context (``HERMES_CURATOR_*``) on top.
    """

    env = {key: os.environ[key] for key in _VERIFY_ENV_KEYS if os.environ.get(key)}
    env.update(
        {key: value for key, value in os.environ.items() if key.startswith("LC_") and value}
    )
    env.update({key: value for key, value in (extra or {}).items() if value is not None})
    return env


def _resolve_within(path: Path, root: Path) -> Path | None:
    """Resolve ``path`` and return it only if it stays inside ``root``."""

    try:
        resolved = path.resolve()
        root_resolved = root.resolve()
    except OSError:
        return None
    if resolved == root_resolved or root_resolved in resolved.parents:
        return resolved
    return None


def _run_verify(command: str | None, cwd: Path | None, env: dict[str, str] | None = None) -> dict[str, Any]:
    if not command:
        return {"enabled": False, "passed": True, "exit_code": 0, "output": ""}
    try:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=300,
            check=False,
            env=_build_verify_env(env),
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "enabled": True,
            "passed": False,
            "exit_code": 124,
            "output": f"verification timed out after {exc.timeout} seconds",
        }
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return {
            "enabled": True,
            "passed": False,
            "exit_code": 125,
            "output": f"verification failed to start: {exc}",
        }
    return {
        "enabled": True,
        "passed": completed.returncode == 0,
        "exit_code": completed.returncode,
        "output": completed.stdout[-4000:],
    }


def _run_builtin_cheap_check(target: Path) -> dict[str, Any]:
    """In-process structural check for the post-write SKILL.md.

    This is the cheap stage of the staged verifier gate. It enforces invariants
    the plugin already promises (size cap and managed-block boundedness) so an
    expensive `verify_command` only runs when the file at least looks sane.
    """

    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {
            "name": "builtin-structural",
            "enabled": True,
            "passed": False,
            "reason": f"read-failed: {exc}",
        }
    failures: list[str] = []
    if len(text) > _BUILTIN_HARD_CAP_CHARS:
        failures.append(f"over-hard-cap:{len(text)}>{_BUILTIN_HARD_CAP_CHARS}")
    start_count = text.count(_MANAGED_BLOCK_START)
    end_count = text.count(_MANAGED_BLOCK_END)
    if start_count != end_count:
        failures.append(f"unbalanced-managed-block-markers:{start_count}!={end_count}")
    if start_count > 1:
        failures.append(f"duplicate-managed-block:{start_count}")
    if start_count == 1:
        if text.find(_MANAGED_BLOCK_END) <= text.find(_MANAGED_BLOCK_START):
            failures.append("managed-block-end-before-start")
    if text.startswith("---"):
        match = re.match(r"^---\s*\n(?P<body>.*?)\n---\s*\n", text, re.DOTALL)
        if not match:
            failures.append("frontmatter-not-parseable")
        else:
            try:
                parsed = yaml.safe_load(match.group("body")) or {}
            except yaml.YAMLError as exc:
                failures.append(f"frontmatter-not-parseable:{exc.__class__.__name__}")
            else:
                if not isinstance(parsed, dict):
                    failures.append("frontmatter-not-mapping")
    return {
        "name": "builtin-structural",
        "enabled": True,
        "passed": not failures,
        "reason": "ok" if not failures else ",".join(failures),
        "content_chars": len(text),
    }


def _run_staged_verify(
    *,
    target: Path,
    pre_verify_command: str | None,
    verify_command: str | None,
    verify_cwd: Path | None,
    env: dict[str, str],
) -> dict[str, Any]:
    """Run the cheap-then-expensive verifier chain.

    The aggregate result is returned in a backward-compatible shape:
    ``passed`` / ``exit_code`` / ``output`` reflect the first failing stage,
    or the final stage if all passed. A ``stages`` list exposes each stage's
    individual result. ``enabled`` is True if any stage actually ran.
    """

    stages: list[dict[str, Any]] = []

    cheap = _run_builtin_cheap_check(target)
    stages.append(cheap)
    if not cheap["passed"]:
        return {
            "enabled": True,
            "staged": True,
            "passed": False,
            "exit_code": 1,
            "output": f"builtin-structural check failed: {cheap.get('reason')}",
            "failed_stage": cheap["name"],
            "stages": stages,
        }

    if pre_verify_command:
        pre = _run_verify(pre_verify_command, verify_cwd, env=env)
        pre_stage = {"name": "pre-verify-command", **pre}
        stages.append(pre_stage)
        if not pre["passed"]:
            return {
                "enabled": True,
                "staged": True,
                "passed": False,
                "exit_code": pre["exit_code"],
                "output": pre["output"],
                "failed_stage": pre_stage["name"],
                "stages": stages,
            }

    if verify_command:
        expensive = _run_verify(verify_command, verify_cwd, env=env)
        expensive_stage = {"name": "verify-command", **expensive}
        stages.append(expensive_stage)
        if not expensive["passed"]:
            return {
                "enabled": True,
                "staged": True,
                "passed": False,
                "exit_code": expensive["exit_code"],
                "output": expensive["output"],
                "failed_stage": expensive_stage["name"],
                "stages": stages,
            }
        return {
            "enabled": True,
            "staged": True,
            "passed": True,
            "exit_code": expensive["exit_code"],
            "output": expensive["output"],
            "stages": stages,
        }

    return {
        "enabled": True,
        "staged": True,
        "passed": True,
        "exit_code": 0,
        "output": "",
        "stages": stages,
    }


def apply_guarded_patch(
    *,
    target_path: str | Path,
    new_content: str,
    expected_sha256: str,
    approved: bool,
    backup_root: str | Path,
    verify_command: str | None = None,
    verify_cwd: str | Path | None = None,
    pre_verify_command: str | None = None,
    staged_verify: bool = False,
    skill_name: str | None = None,
    provenance: dict[str, Any] | None = None,
    evidence_refs: dict[str, Any] | None = None,
    scheduler_refs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply a reviewed patch with approval/hash/backup/verify gates.

    When ``staged_verify`` is set (or a ``pre_verify_command`` is provided), a
    cheap in-process structural check runs first, then an optional cheap
    ``pre_verify_command``, then the existing ``verify_command``. The expensive
    stage is skipped entirely if any earlier stage fails, and any failure after
    the write triggers the same rollback path callers already rely on. The
    returned ``verify`` dict keeps ``passed`` / ``exit_code`` / ``output`` for
    backward compatibility and adds a ``stages`` list when staged verification
    is in use.
    """

    target = Path(target_path)
    if not approved:
        return {"applied": False, "reason": "approval-required"}
    if not target.exists() or not target.is_file():
        return {"applied": False, "reason": "target-not-found", "target_path": str(target)}
    current_hash = sha256_file(target)
    if current_hash != expected_sha256:
        return {
            "applied": False,
            "reason": "hash-mismatch",
            "target_path": str(target),
            "current_sha256": current_hash,
            "expected_sha256": expected_sha256,
        }

    backup_dir = Path(backup_root) / _timestamp()
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup_path = backup_dir / target.name
    shutil.copy2(target, backup_path)
    manifest_path = backup_dir / "manifest.json"
    manifest: dict[str, Any] = {
        "schema_version": "0.6",
        "target_path": str(target),
        "backup_path": str(backup_path),
        "original_sha256": current_hash,
        "new_sha256": None,
        "applied_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rolled_back": False,
        "verify": None,
        "skill_name": skill_name,
        "provenance": (
            {**dict(provenance), "skill_name": provenance.get("skill_name") or skill_name}
            if provenance
            else ({"skill_name": skill_name} if skill_name else None)
        ),
        "evidence": dict(evidence_refs) if evidence_refs else None,
        "scheduler": dict(scheduler_refs) if scheduler_refs else None,
        "support_files": [],
    }
    _write_manifest(manifest_path, manifest)

    _atomic_write_text(target, new_content)
    manifest["new_sha256"] = sha256_file(target)
    verify_env = {
        "HERMES_CURATOR_TARGET_PATH": str(target),
        "HERMES_CURATOR_BACKUP_PATH": str(backup_path),
        "HERMES_CURATOR_MANIFEST_PATH": str(manifest_path),
        "HERMES_CURATOR_ORIGINAL_SHA256": current_hash,
        "HERMES_CURATOR_NEW_SHA256": str(manifest["new_sha256"]),
    }
    use_staged = bool(staged_verify or pre_verify_command)
    if use_staged:
        verify = _run_staged_verify(
            target=target,
            pre_verify_command=pre_verify_command,
            verify_command=verify_command,
            verify_cwd=Path(verify_cwd) if verify_cwd else target.parent,
            env=verify_env,
        )
    else:
        verify = _run_verify(
            verify_command,
            Path(verify_cwd) if verify_cwd else target.parent,
            env=verify_env,
        )
    manifest["verify"] = verify
    if not verify["passed"]:
        _atomic_copy(backup_path, target)
        manifest["rolled_back"] = True
        manifest["rollback_reason"] = "verify-failed"
        if verify.get("failed_stage"):
            manifest["rollback_failed_stage"] = verify["failed_stage"]
        _write_manifest(manifest_path, manifest)
        return {
            "applied": False,
            "reason": "verify-failed",
            "target_path": str(target),
            "backup_path": str(backup_path),
            "manifest_path": str(manifest_path),
            "verify": verify,
        }

    _write_manifest(manifest_path, manifest)
    drill_state_path = Path(backup_root) / DRILL_STATE_FILENAME
    record_apply_in_state(
        drill_state_path,
        manifest_path=manifest_path,
        applied_at=manifest["applied_at"],
        target_path=str(target),
        skill_name=skill_name,
    )
    return {
        "applied": True,
        "reason": "applied",
        "target_path": str(target),
        "backup_path": str(backup_path),
        "manifest_path": str(manifest_path),
        "new_sha256": manifest["new_sha256"],
        "verify": verify,
        "drill_state_path": str(drill_state_path),
    }


def register_support_file_in_manifest(
    manifest_path: str | Path,
    *,
    source_path: str | Path,
    relative_path: str,
    kind: str = "support",
) -> dict[str, Any]:
    """Snapshot a post-apply support file into the backup and record it.

    Auto-run writes managed support files (e.g. ``references/...``) after
    a successful apply. Recording their content here means a later restore
    drill can recreate the exact prior-apply skill state into a clean
    directory, not just the main ``SKILL.md``.
    """

    manifest_file = Path(manifest_path)
    source = Path(source_path)
    if not source.exists() or not source.is_file():
        return {"recorded": False, "reason": "source-not-found", "source_path": str(source)}
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    backup_dir = manifest_file.parent
    support_root = backup_dir / "support"
    safe_relative = Path(relative_path)
    if safe_relative.is_absolute() or any(part == ".." for part in safe_relative.parts):
        return {
            "recorded": False,
            "reason": "unsafe-relative-path",
            "relative_path": str(safe_relative),
        }
    snapshot_path = support_root / safe_relative
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, snapshot_path)
    entry = {
        "path": str(safe_relative).replace("\\", "/"),
        "kind": kind,
        "sha256": sha256_file(snapshot_path),
        "backup_path": str(snapshot_path),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    existing = manifest.get("support_files")
    if not isinstance(existing, list):
        existing = []
    existing = [item for item in existing if not (isinstance(item, dict) and item.get("path") == entry["path"])]
    existing.append(entry)
    manifest["support_files"] = existing
    _write_manifest(manifest_file, manifest)
    return {"recorded": True, "entry": entry}


def _snapshot_for_safety(source: Path, safety_dir: Path, label: str) -> Path | None:
    """Copy a file into the rollback safety directory before touching it.

    Fail-closed (roadmap U35): every destructive rollback step keeps a
    recoverable copy under the manifest's own directory, so even a validated
    removal can be undone. ``None`` means the snapshot failed and the caller
    must skip the destructive step. The copy goes through the atomic write
    primitive with fsync and mode preservation (roadmap U44, assessment Q5):
    an interrupted snapshot must leave either the complete recoverable copy
    or nothing — never a torn half-file that *looks* like the safety net.
    """

    try:
        safe_name = label.replace("/", "__").replace("\\", "__")
        dest = safety_dir / f"{_timestamp()}-{safe_name}"
        _atomic_copy(Path(source), dest)
        return dest
    except OSError:
        return None


def _rollback_support_files(
    manifest: dict[str, Any], target: Path, manifest_dir: Path | None = None
) -> dict[str, list[Any]]:
    """Remove support files this apply created, leaving edited ones alone.

    ``register_support_file_in_manifest`` snapshots post-apply support files
    (e.g. ``references/...`` spill) so restore drills can recreate them. A
    rollback must undo the apply's *writes*: a live file whose hash still
    matches the snapshot was created by this apply and is removed; one that
    no longer matches was touched afterwards and is skipped rather than
    destroyed. Snapshots under the backup stay on disk for the drill.

    Manifest entries are untrusted input (assessment N1): a tampered entry
    naming the restored target itself used to delete it after restore. Every
    entry is now validated before any unlink —

    * it must not resolve to the rollback target itself (target-identity
      refusal),
    * it must be registered, i.e. carry a snapshot path that stays inside the
      manifest's own directory and actually exists (registration
      cross-check),
    * and the live file is snapshotted into the rollback-safety directory
      first, fail-closed.
    """

    results: dict[str, list[Any]] = {"removed": [], "skipped": [], "missing": []}
    safety_dir = (Path(manifest_dir) / "rollback-safety") if manifest_dir else None
    try:
        target_resolved = target.resolve()
    except OSError:
        target_resolved = Path(target).absolute()
    for entry in manifest.get("support_files") or []:
        if not isinstance(entry, dict):
            continue
        relative = entry.get("path")
        if not isinstance(relative, str) or not relative:
            continue
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            results["skipped"].append({"path": relative, "reason": "unsafe-relative-path"})
            continue
        live = _resolve_within(target.parent / relative_path, target.parent)
        if live is None:
            results["skipped"].append({"path": relative, "reason": "unsafe-relative-path"})
            continue
        if live == target_resolved:
            # N1: the target of the rollback is never a support file; a
            # manifest claiming otherwise is tampered, not descriptive.
            results["skipped"].append({"path": relative, "reason": "target-file"})
            continue
        entry_snapshot = entry.get("backup_path")
        if manifest_dir is not None:
            registered = isinstance(entry_snapshot, str) and _resolve_within(
                Path(entry_snapshot), Path(manifest_dir)
            ) is not None and Path(entry_snapshot).is_file()
            if not registered:
                results["skipped"].append({"path": relative, "reason": "not-registered"})
                continue
        if not live.exists() or not live.is_file():
            results["missing"].append(relative)
            continue
        recorded_sha = entry.get("sha256")
        if recorded_sha and sha256_file(live) != recorded_sha:
            results["skipped"].append({"path": relative, "reason": "file-changed-since-apply"})
            continue
        safety_copy = None
        if safety_dir is not None:
            safety_copy = _snapshot_for_safety(live, safety_dir, relative)
            if safety_copy is None:
                results["skipped"].append({"path": relative, "reason": "safety-snapshot-failed"})
                continue
        try:
            live.unlink()
            removed: dict[str, Any] = {"path": relative}
            if safety_copy is not None:
                removed["safety_copy"] = str(safety_copy)
            results["removed"].append(removed)
        except OSError as exc:
            results["skipped"].append(
                {"path": relative, "reason": f"unlink-failed:{exc.__class__.__name__}"}
            )
    return results


def rollback_guarded_patch(
    manifest_path: str | Path,
    *,
    force: bool = False,
    allowed_target_roots: tuple[str | Path, ...] | list[str | Path] | None = None,
    allow_unrestricted_target: bool = False,
) -> dict[str, Any]:
    """Restore the pre-apply target and undo the apply's support-file writes.

    Paths from the manifest are treated as untrusted input: the backup must
    resolve inside the manifest's own backup directory, and - when callers
    supply ``allowed_target_roots`` (the skills roots they operate on) - the
    target must resolve inside one of them before anything is copied
    (roadmap U3; a tampered manifest must not turn rollback into an
    arbitrary-file overwrite primitive).

    U35 closes the remaining escape: without ``allowed_target_roots`` the
    rollback used to accept ANY target path (assessment C2 — the CLI's
    default when ``--skills-dir`` was omitted). An unrestricted rollback is
    now an explicit, per-call opt-in (``allow_unrestricted_target=True``);
    the refusal tells the caller how to fix it. Before the restore, the
    current target bytes are snapshotted into the manifest's
    ``rollback-safety/`` directory, fail-closed: if that snapshot cannot be
    written the rollback aborts rather than overwrite the only copy.
    """

    manifest_file = Path(manifest_path)
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    target = Path(manifest["target_path"])
    backup = Path(manifest["backup_path"])
    if _resolve_within(backup, manifest_file.parent) is None:
        return {
            "rolled_back": False,
            "reason": "unsafe-backup-path",
            "target_path": str(target),
            "backup_path": str(backup),
            "manifest_path": str(manifest_file),
        }
    if not allowed_target_roots and not allow_unrestricted_target:
        return {
            "rolled_back": False,
            "reason": "unrestricted-target",
            "target_path": str(target),
            "backup_path": str(backup),
            "manifest_path": str(manifest_file),
            "hint": "pass allowed_target_roots (the skills root), or set "
            "allow_unrestricted_target=True to override containment explicitly",
        }
    if allowed_target_roots and not any(
        _resolve_within(target, Path(root)) is not None for root in allowed_target_roots
    ):
        return {
            "rolled_back": False,
            "reason": "unsafe-target-path",
            "target_path": str(target),
            "backup_path": str(backup),
            "manifest_path": str(manifest_file),
        }
    if not backup.exists():
        return {"rolled_back": False, "reason": "backup-not-found"}
    expected_current = manifest.get("new_sha256")
    if target.exists() and expected_current and sha256_file(target) != expected_current and not force:
        return {
            "rolled_back": False,
            "reason": "target-changed",
            "target_path": str(target),
            "expected_sha256": expected_current,
            "current_sha256": sha256_file(target),
        }
    safety_dir = manifest_file.parent / "rollback-safety"
    target_safety_copy: str | None = None
    if target.exists():
        snapshot = _snapshot_for_safety(target, safety_dir, target.name)
        if snapshot is None:
            return {
                "rolled_back": False,
                "reason": "safety-snapshot-failed",
                "target_path": str(target),
                "backup_path": str(backup),
                "manifest_path": str(manifest_file),
            }
        target_safety_copy = str(snapshot)
    _atomic_copy(backup, target)
    support_results = _rollback_support_files(manifest, target, manifest_dir=manifest_file.parent)
    manifest["rolled_back"] = True
    manifest["rolled_back_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest["rollback_support_files"] = support_results
    manifest["rollback_safety"] = {
        "dir": str(safety_dir),
        "target_snapshot": target_safety_copy,
    }
    _write_manifest(manifest_file, manifest)
    return {
        "rolled_back": True,
        "reason": "rolled-back",
        "target_path": str(target),
        "backup_path": str(backup),
        "manifest_path": str(manifest_file),
        "support_files": support_results,
        "rollback_safety": manifest["rollback_safety"],
    }
