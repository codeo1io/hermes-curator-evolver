"""U109: ``--limit 0`` has one semantic everywhere.

Before U109 the file path treated ``0`` as unbounded (a full import) while
the bootstrap renderers silently substituted the default 500. Both paths now
reject zero with a clear error; ``None``/omitted keeps its meaning
(unbounded for the backfill path, default 500 for bootstrap).
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from hermes_curator_evolver.backfill import _iter_session_files, backfill_sessions
from hermes_curator_evolver.cli import _backfill_limit


def _write_session(path: Path, session_id: str = "session-test") -> None:
    path.write_text(
        json.dumps(
            {
                "session_id": session_id,
                "session_start": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "model": "gpt-5.5",
                "platform": "slack",
                "messages": [
                    {"role": "user", "content": "Use the github PR skill"},
                    {"role": "assistant", "content": "Loaded the PR workflow."},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _sessions_dir(tmp_path: Path, count: int = 3) -> Path:
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    for index in range(count):
        _write_session(
            sessions_dir / f"session_2026050{index + 1}_100000_{index}.json",
            session_id=f"session-{index}",
        )
    return sessions_dir


def test_backfill_limit_none_keeps_default():
    assert _backfill_limit(None, default=500) == 500


def test_backfill_limit_positive_passes_through():
    assert _backfill_limit(7, default=500) == 7


@pytest.mark.parametrize("zero", [0, -3])
def test_backfill_limit_zero_is_rejected(zero):
    with pytest.raises(ValueError, match="positive integer"):
        _backfill_limit(zero, default=500)


def test_iter_session_files_zero_is_rejected(tmp_path):
    sessions_dir = _sessions_dir(tmp_path)
    with pytest.raises(ValueError, match="positive integer"):
        _iter_session_files(sessions_dir, 0)


def test_iter_session_files_none_is_unbounded(tmp_path):
    sessions_dir = _sessions_dir(tmp_path, count=3)
    assert len(_iter_session_files(sessions_dir, None)) == 3


def test_iter_session_files_positive_bounds(tmp_path):
    sessions_dir = _sessions_dir(tmp_path, count=3)
    assert len(_iter_session_files(sessions_dir, 2)) == 2


def test_backfill_sessions_zero_is_rejected(tmp_path):
    sessions_dir = _sessions_dir(tmp_path, count=1)
    with pytest.raises(ValueError, match="positive integer"):
        backfill_sessions(sessions_dir=sessions_dir, days=30, limit=0)


def test_backfill_sessions_none_still_imports_all(tmp_path):
    sessions_dir = _sessions_dir(tmp_path, count=3)
    result = backfill_sessions(
        sessions_dir=sessions_dir,
        days=30,
        limit=None,
    )
    assert result["sessions_seen"] == 3


def test_cli_backfill_sessions_limit_zero_exits_one(tmp_path):
    sessions_dir = _sessions_dir(tmp_path, count=1)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hermes_curator_evolver",
            "backfill-sessions",
            "--sessions-dir",
            str(sessions_dir),
            "--limit",
            "0",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert completed.returncode == 1
    assert "positive integer" in completed.stderr


def test_cli_backfill_sessions_positive_still_succeeds(tmp_path):
    sessions_dir = _sessions_dir(tmp_path, count=1)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hermes_curator_evolver",
            "backfill-sessions",
            "--sessions-dir",
            str(sessions_dir),
            "--limit",
            "1",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert completed.returncode == 0
