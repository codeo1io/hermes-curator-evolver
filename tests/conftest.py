"""Never let plugin tests discover or mutate the operator's Hermes state."""

import pytest


@pytest.fixture(autouse=True)
def isolated_hermes_home(tmp_path, monkeypatch):
    # The fake user home must NOT live inside tmp_path: tests assert exact
    # tmp_path contents (e.g. test_u44_no_stray_temp_files_after_writes,
    # test_evidence_probe_leaves_quiescent_wal_database_untouched), and a
    # "user" directory created by this fixture is exactly the kind of stray
    # entry those guards exist to catch. As a numbered-sibling of tmp_path
    # under the pytest basetemp it stays isolated per test, gets the same
    # automatic cleanup, and never leaks into the operator's real home.
    user_home = tmp_path.parent / f"{tmp_path.name}-user-home"
    user_home.mkdir()
    monkeypatch.setenv("HOME", str(user_home))
    monkeypatch.setenv("USERPROFILE", str(user_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(user_home / ".config"))
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes-home"))
    monkeypatch.delenv("HERMES_CURATOR_EVOLVER_DB", raising=False)
