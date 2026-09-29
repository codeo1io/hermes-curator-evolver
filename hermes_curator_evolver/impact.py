"""Dependency-aware skill impact analysis (roadmap U87, upstream issue #12).

Answers "what else should I look at if this skill changes?" by inferring
dependency edges from three independent sources, each carrying its own
truth level:

``explicit_related_skill``
    The skill's own ``related_skills`` frontmatter — an author-declared
    dependency. Always actionable (``review``): the author said the skills
    are related, so a change to this skill warrants review of each one.

``co_usage``
    Session evidence: two skills used in the same session have an observed
    interaction. Two or more shared sessions (``CO_USAGE_REVIEW_MIN``) is
    ``review`` — repeated co-usage is behavioral coupling worth checking —
    while a single shared session is ``no-op`` (one coincidence carries no
    recommendation; the edge is still reported so operators see it).

``shared_tool``
    Two skills that drive the same tool. Weakest signal (most tools are
    shared by unrelated skills), so the recommended action is
    ``proposal-only``: surface it in a proposal for human review, never as
    a review requirement.

DRY-RUN ONLY (KTD43): this module performs no writes of any kind — no
evidence-store writes, no file writes, no state changes. All evidence
reads run on the store's read-only connection (U53 discipline), and the
frontmatter read never falls back to writing. The report is returned to
the caller (CLI prints it); nothing is persisted. A MISSING store stays
missing (cycle-11 review fix, finding 2): ``EvidenceStore.__init__"
creates its database (mkdir + schema init), so the missing-db path is
guarded — a store that does not exist yields zero evidence edges and a
``db_found: false`` report field instead of materializing the file the
dry-run promised not to write.

One disclosed read artifact (SQLite, not us): opening a WAL-mode
``mode=ro`` connection on a *quiescent* store materializes the
``-shm``/``-wal`` companions, and a read-only closer cannot checkpoint
them away — they linger until the next writer closes (verified: the
database file's bytes are never modified, and the first subsequent
write-mode close removes both files). On the production path (a live
store held open by Hermes) the companions already exist, so this is
only observable in drill/fixture contexts. Recorded here so it is
never mistaken for a KTD43 write.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .auto_evolve import _default_skills_dir, discover_skill_files
from .storage import EvidenceStore, default_db_path
from .skill_validate import _frontmatter

SOURCE_EXPLICIT = "explicit_related_skill"
SOURCE_CO_USAGE = "co_usage"
SOURCE_SHARED_TOOL = "shared_tool"

ACTION_REVIEW = "review"
ACTION_NO_OP = "no-op"
ACTION_PROPOSAL_ONLY = "proposal-only"

# Co-usage observed in at least this many distinct sessions is behavioral
# coupling worth a review; a single session is reported but not actionable.
CO_USAGE_REVIEW_MIN = 2


def _parse_related_skills(value: Any) -> list[str]:
    """Normalize ``related_skills`` frontmatter to a name list."""
    if value is None:
        return []
    if isinstance(value, str):
        names = [part.strip() for part in value.replace(",", ";").split(";")]
    elif isinstance(value, list):
        names = [str(part).strip() for part in value]
    else:
        return []
    return [name for name in names if name]


def _explicit_edges(skill: str, skill_path: Path | None) -> list[dict[str, Any]]:
    """Edges from the skill's own ``related_skills`` frontmatter."""
    if skill_path is None or not skill_path.exists():
        return []
    try:
        meta, _err = _frontmatter(skill_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return []
    if not isinstance(meta, dict):
        return []
    return [
        {
            "skill": name,
            "source": SOURCE_EXPLICIT,
            "action": ACTION_REVIEW,
            "evidence": {"declared_in": str(skill_path), "related_skills": name},
        }
        for name in _parse_related_skills(meta.get("related_skills"))
    ]


def _co_usage_edges(signals: dict[str, Any]) -> list[dict[str, Any]]:
    """Edges from observed same-session usage (session evidence)."""
    edges: list[dict[str, Any]] = []
    for row in signals.get("co_usage", []):
        shared_sessions = int(row.get("shared_sessions") or 0)
        edges.append(
            {
                "skill": row["skill"],
                "source": SOURCE_CO_USAGE,
                "action": (
                    ACTION_REVIEW
                    if shared_sessions >= CO_USAGE_REVIEW_MIN
                    else ACTION_NO_OP
                ),
                "evidence": {
                    "shared_sessions": shared_sessions,
                    "error_events": int(row.get("error_events") or 0),
                },
            }
        )
    return edges


def _shared_tool_edges(signals: dict[str, Any]) -> list[dict[str, Any]]:
    """Edges from shared tool usage — proposal-only by construction."""
    per_skill: dict[str, dict[str, Any]] = {}
    for row in signals.get("shared_tools", []):
        entry = per_skill.setdefault(
            row["skill"], {"skill": row["skill"], "tools": [], "uses": 0}
        )
        entry["tools"].append(row["tool"])
        entry["uses"] += int(row.get("uses") or 0)
    return [
        {
            "skill": entry["skill"],
            "source": SOURCE_SHARED_TOOL,
            "action": ACTION_PROPOSAL_ONLY,
            "evidence": {
                "shared_tools": sorted(entry["tools"]),
                "shared_tool_uses": entry["uses"],
            },
        }
        for entry in sorted(per_skill.values(), key=lambda item: (-item["uses"], item["skill"]))
    ]


def build_impact_report(
    skill: str,
    *,
    days: int = 30,
    skills_dir: str | Path | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build the dependency impact report for one skill (read-only, dry-run)."""
    root = Path(skills_dir) if skills_dir is not None else _default_skills_dir()
    discovered = discover_skill_files(root)
    skill_path = discovered.get(skill)

    edges: list[dict[str, Any]] = []
    edges.extend(_explicit_edges(skill, skill_path))

    # KTD43 / cycle-11 review fix (finding 2): constructing
    # ``EvidenceStore`` on a missing path would CREATE the database
    # (mkdir + init_db). Resolve the same path it would use, and when
    # the store does not exist, answer with zero evidence edges — the
    # honest answer for an absent store — without touching the disk.
    store_path = Path(db_path) if db_path is not None else default_db_path()
    db_found = store_path.exists()
    if db_found:
        store = EvidenceStore(db_path)
        try:
            signals = store.impact_signals(skill=skill, days=days)
        finally:
            store.close()
        db_used = str(store.db_path)
    else:
        signals = {"co_usage": [], "shared_tools": []}
        db_used = str(store_path)
    edges.extend(_co_usage_edges(signals))
    edges.extend(_shared_tool_edges(signals))

    edges.sort(key=lambda edge: (edge["skill"], edge["source"]))
    totals: dict[str, int] = {}
    for edge in edges:
        totals[edge["action"]] = totals.get(edge["action"], 0) + 1

    return {
        "skill": skill,
        "days": days,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "skills_dir": str(root),
        "skill_path": str(skill_path) if skill_path else None,
        "skill_found": skill_path is not None,
        "db_found": db_found,
        "db_path": db_used,
        "edges": edges,
        "totals_by_action": totals,
        "dry_run": True,
    }


def _md_cell(value: Any) -> str:
    """Escape a value for a markdown table cell (review fix, finding 8).

    Skill names and tool lists are frontmatter-authorable; a raw ``|``
    would split the cell (injecting a phantom column) and a newline
    would break the row (injecting a phantom row). Both are flattened;
    the report is read-only output, so escaping is the whole defense.
    """
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def format_impact_markdown(report: dict[str, Any]) -> str:
    """Render the impact report as the ``--format markdown`` document."""
    store_line = (
        f"- Evidence store: {report['db_path']} (read-only)"
        if report.get("db_found", True)
        else (
            f"- Evidence store: {report['db_path']} — NOT FOUND; session"
            " evidence skipped, store not created (dry-run, KTD43)"
        )
    )
    lines = [
        f"# Impact analysis: {_md_cell(report['skill'])}",
        "",
        f"- Window: last {report['days']} days",
        f"- Skills dir: {report['skills_dir']}",
        store_line,
        f"- Skill file: {report['skill_path'] or 'not found by name'}",
        "- Mode: dry-run — no writes, no cascading actions (KTD43)",
        "",
    ]
    edges = report["edges"]
    if not edges:
        lines.append("No dependency edges found for this skill in the window.")
        lines.append("")
        return "\n".join(lines)
    lines.append("| Skill | Source | Recommended action | Evidence |")
    lines.append("| --- | --- | --- | --- |")
    for edge in edges:
        evidence = edge["evidence"]
        if edge["source"] == SOURCE_EXPLICIT:
            detail = "declared in frontmatter `related_skills`"
        elif edge["source"] == SOURCE_CO_USAGE:
            detail = (
                f"{evidence['shared_sessions']} shared session(s), "
                f"{evidence['error_events']} error event(s)"
            )
        else:
            detail = (
                f"tools: {', '.join(evidence['shared_tools'])} "
                f"({evidence['shared_tool_uses']} shared uses)"
            )
        lines.append(
            f"| {_md_cell(edge['skill'])} | {_md_cell(edge['source'])} "
            f"| {_md_cell(edge['action'])} | {_md_cell(detail)} |"
        )
    totals = report["totals_by_action"]
    lines.append("")
    lines.append(
        "Totals: "
        + ", ".join(f"{count} {action}" for action, count in sorted(totals.items()))
    )
    lines.append("")
    return "\n".join(lines)


def format_impact_json(report: dict[str, Any]) -> str:
    """Render the impact report as JSON (machine consumption)."""
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
