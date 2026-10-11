"""Item 248: compat-symlink hygiene after the plugin-data migration.

The trailing-slash patterns (`data/`, `backups/`, `logs/`) only match
directories. After the documented offline migration (docs/after-install.md
step 6 "optionally leave compatibility symlinks"), the leftovers at the repo
root are SYMLINKS (git mode 120000), which those patterns do not match — the
worktree then permanently shows `?? data` / `?? backups` untracked noise that
autonomy flows can sweep into commits. The root-anchored `/data` `/backups`
`/logs` patterns must match those symlinks.
"""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
NAMES = ("data", "backups", "logs")


def _ignored(path: Path) -> bool:
    """True when git reports `path` as ignored (works for symlinks)."""

    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "check-ignore", "--no-index", str(path)],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def _subject(name: str, tmp_path):
    """Return (path, created). Reuse the live compat symlink when present."""

    link = REPO_ROOT / name
    if link.is_symlink():
        assert not link.is_dir() or link.resolve() != REPO_ROOT, (
            f"{name} resolves inside the repo; not a canonical compat symlink"
        )
        return link, False
    if link.exists():
        pytest.fail(f"real {link} exists in the worktree; refusing to shadow it")
    target = tmp_path / f"external-{name}"
    target.mkdir()
    link.symlink_to(target, target_is_directory=True)
    return link, True


def test_compat_symlinks_are_ignored(tmp_path):
    cleanup = []
    for name in NAMES:
        link, created = _subject(name, tmp_path)
        if created:
            cleanup.append(link)
        assert _ignored(link), (
            f"compat symlink {name} is not git-ignored — it will show as "
            "untracked noise and commit bait after the plugin-data migration"
        )
    for link in cleanup:
        link.unlink()


def test_real_directories_still_ignored(tmp_path):
    made = []
    for name in NAMES:
        d = REPO_ROOT / name
        if d.is_symlink():
            continue  # live compat symlink already proves the ignored state
        if d.exists():
            pytest.fail(f"real {d} exists in the worktree; refusing to shadow it")
        d.mkdir()
        made.append(d)
    try:
        for d in made:
            assert _ignored(d), f"directory {d.name}/ lost its ignore pattern"
    finally:
        for d in made:
            d.rmdir()
