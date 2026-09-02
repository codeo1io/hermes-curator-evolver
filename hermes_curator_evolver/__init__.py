"""Hermes Curator Evolver plugin registration."""

from __future__ import annotations

import re
from pathlib import Path

from .cli import handle_cli, setup_cli
from .hooks import on_post_llm_call, on_post_tool_call, on_session_end
from .tools import CURATOR_EVIDENCE_REPORT_SCHEMA, curator_evidence_report


def _plugin_version() -> str:
    """Single-source the version from plugin.yaml (roadmap U7b).

    Hermes loads ``plugin.yaml`` as the plugin's version surface, so it is
    the source of truth; this module used to carry an independent
    ``0.8.0`` that drifted (assessment Q-class finding: the two disagreed
    since cycle 1). The manifest lives next to the package root; if it is
    missing (unusual layouts) the last-known literal below is used so imports
    never fail. A test pins the two surfaces together.
    """

    manifest = Path(__file__).resolve().parent.parent / "plugin.yaml"
    try:
        text = manifest.read_text(encoding="utf-8")
    except OSError:
        return "0.10.0"
    match = re.search(r"^version:\s*[\"']?([^\"'\n]+)[\"']?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else "0.10.0"


__version__ = _plugin_version()


def _handle_slash_command(raw_args: str) -> str:
    """Handle `/curator-evolver` inside Hermes sessions."""
    from .reports import build_default_report, format_markdown_report

    tokens = (raw_args or "").split()
    days = 7
    if "--days" in tokens:
        idx = tokens.index("--days")
        if idx + 1 < len(tokens):
            try:
                days = int(tokens[idx + 1])
            except ValueError:
                return "Usage: /curator-evolver [--days N]"
    if tokens and tokens[0] == "status":
        report = build_default_report(days=days)
        summary = report["summary"]
        return (
            "Curator Evolver status:\n"
            f"- DB: `{report['db_path']}`\n"
            f"- tool events: {summary['tool_events']}\n"
            f"- skill events: {summary['skill_events']}\n"
            f"- error events: {summary['error_events']}"
        )
    report = build_default_report(days=days)
    return format_markdown_report(report)


def register(ctx) -> None:
    """Register tools, observer hooks, CLI command, slash command, and skill."""
    ctx.register_tool(
        name="curator_evidence_report",
        toolset="curator-evolver",
        schema=CURATOR_EVIDENCE_REPORT_SCHEMA,
        handler=curator_evidence_report,
        description="Read-only evidence reports for Hermes skill curator decisions.",
        emoji="🧭",
    )
    ctx.register_hook("post_tool_call", on_post_tool_call)
    ctx.register_hook("post_llm_call", on_post_llm_call)
    ctx.register_hook("on_session_end", on_session_end)
    ctx.register_cli_command(
        name="curator-evolver",
        help="Evidence reports and guarded skill evolution workflows",
        setup_fn=setup_cli,
        handler_fn=handle_cli,
        description="Analyze evidence, draft proposals, find candidates, and apply reviewed changes with guardrails.",
    )
    ctx.register_command(
        "curator-evolver",
        handler=_handle_slash_command,
        description="Show read-only curator evidence reports",
        args_hint="[status|--days N]",
    )

    skill_path = Path(__file__).parent / "skills" / "curator-evolution" / "SKILL.md"
    if skill_path.exists():
        ctx.register_skill("curator-evolution", skill_path)
