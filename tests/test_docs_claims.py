"""Structural documentation pins (run 1f928624bd59 — README/ROADMAP reconciliation).

These pins lock documentation claims that had drifted from shipped behavior,
so the drift cannot silently return. They assert structural strings only —
parser defaults, subcommand sets, path spellings, and the plugin tool id —
never prose (reconciliation plan assumption A5).

Truths locked at introduction:

- ``cli.py`` apply ``--backup-dir`` defaults to the CWD-relative
  ``.curator-evolver-backups``; only ``auto-run`` applies default to the
  plugin-data backup root (``paths.default_backup_dir()``).
- ``build_parser()`` subcommands and README document exactly the same set,
  both directions.
- State never lives in the ``~/.hermes/plugins/curator-evolver/`` install
  tree (logs/backups moved to ``~/.hermes/plugin-data/curator-evolver/``).
- ``plugin.yaml`` provides exactly the tool the README names.
"""

import argparse
import re
from pathlib import Path

import yaml

from hermes_curator_evolver.__main__ import build_parser

REPO_ROOT = Path(__file__).resolve().parent.parent
STALE_STATE_PATH = re.compile(r"~/?\.hermes/plugins/curator-evolver/(?:logs|backups)")
DOC_FILES = [REPO_ROOT / "README.md", *sorted((REPO_ROOT / "docs").glob("*.md"))]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _subcommands() -> set:
    parser = build_parser()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return set(action.choices)
    raise AssertionError("build_parser exposed no subparsers")


def test_pin1_apply_backup_default_documented_truthfully():
    parser = build_parser()
    args = parser.parse_args(
        [
            "apply",
            "--target",
            "SKILL.md",
            "--content-file",
            "new-SKILL.md",
            "--expected-sha256",
            "0" * 64,
        ]
    )
    # The parser default is the CWD-relative backup root ...
    assert args.backup_dir == ".curator-evolver-backups"
    readme = _read(REPO_ROOT / "README.md")
    # ... so README must document that spelling ...
    assert ".curator-evolver-backups" in readme
    # ... and must not claim guarded-apply backups universally default to
    # the plugin-data root (that default holds for auto-run applies only).
    assert (
        "Guarded-apply backups default to "
        "`~/.hermes/plugin-data/curator-evolver/backups/`." not in readme
    )


def test_pin2_readme_documents_exactly_the_cli_subcommands():
    readme = _read(REPO_ROOT / "README.md")
    documented = set(re.findall(r"hermes-curator-evolver ([a-z][a-z-]*)", readme))
    assert documented == _subcommands()


def test_pin3_no_stale_install_tree_state_paths_in_docs():
    offenders = [
        f"{path}: {match.group(0)}"
        for path in DOC_FILES
        if (match := STALE_STATE_PATH.search(_read(path)))
    ]
    assert offenders == []


def test_pin4_plugin_provided_tool_named_in_readme():
    plugin = yaml.safe_load(_read(REPO_ROOT / "plugin.yaml"))
    tools = plugin["provides_tools"]
    assert tools == ["curator_evidence_report"]
    readme = _read(REPO_ROOT / "README.md")
    for tool in tools:
        assert tool in readme
