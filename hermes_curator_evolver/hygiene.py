"""Credential hygiene for the evidence pipeline (roadmap U77, cycle 9).

The curator ingests verbatim tool transcripts and embeds compact previews
into stored evidence rows, auto-generated ``SKILL.md`` blocks, spill files,
and semantic queries. This repository is PUBLIC, and the cycle-2 experiment
(``docs/ideation/2026-09-02-cycle-2-extension-research.md:60``) proved the
pipeline writes credential-shaped strings verbatim end to end — a
``ghp_…`` PAT-shaped token reached a committed document, and GitHub secret
scanning raised ZERO alerts for it (verified 2026-09-22), so there is no
external backstop. The scrub therefore lives in the pipeline itself:

* :func:`storage._compact` scrubs every stored result/turn preview;
* :func:`storage._json_dumps` scrubs serialized tool arguments;
* the three ``auto_evolve`` embed points re-scrub before formatting
  (defense in depth — a preview stored before this fix could still hold a
  credential);
* ``skill_validate`` fails a SKILL.md that still carries a hit.

The marker set is stable per credential class (``[REDACTED:github-token]``)
so a human can see WHAT was removed without seeing the value. Scrub counts
are disclosed through :func:`stats_snapshot` per the KTD36 visible-counter
pattern; the assignment backstop pattern requires a digit in the value to
avoid mangling ordinary prose like ``api-key: see-below``.
"""

from __future__ import annotations

import re
import threading
from typing import Final

# Specific credential families first, generic assignment backstop last —
# order matters: the specific patterns consume the credential body so the
# generic ``token=…`` arm never re-matches an already-inserted marker (its
# lookahead refuses a value beginning with ``[``).
_CREDENTIAL_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    ("github-fine-grained-pat", re.compile(r"github_pat_[A-Za-z0-9_]{82}")),
    ("github-token", re.compile(r"\bghp_[A-Za-z0-9]{36}\b")),
    ("github-oauth", re.compile(r"\bgho_[A-Za-z0-9]{36}\b")),
    ("github-user-token", re.compile(r"\bghu_[A-Za-z0-9]{36}\b")),
    ("github-server-token", re.compile(r"\bghs_[A-Za-z0-9]{36}\b")),
    ("github-refresh-token", re.compile(r"\bghr_[A-Za-z0-9]{76}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("openai-or-anthropic-key", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    (
        "generic-token-assignment",
        # ``token=``/``secret:``/``password=``/``api_key:`` followed by an
        # opaque value: at least 8 non-space chars containing a digit, not
        # already a redaction marker. The digit requirement keeps prose
        # like "api-key: see-below" intact while catching opaque secrets.
        re.compile(
            r"\b(?i:token|secret|password|api[_-]?key)\s*[=:]\s*(?!\[)(?=\S*\d)\S{8,}"
        ),
    ),
)

_stats_lock = threading.Lock()
_stats: dict[str, int] = {"scrubbed": 0}


def scrub_text(text: str | None) -> tuple[str, int]:
    """Replace credential-shaped substrings with stable class markers.

    Returns ``(scrubbed_text, hit_count)``. ``hit_count`` counts replaced
    occurrences (not classes) so callers can disclose a truthful number.
    A ``None`` input passes through unchanged with zero hits.

    Counter semantics (cycle-9 review F5): each call REPLACES and
    increments the process-wide ``scrubbed`` counter — ``scrubbed`` is an
    OPERATION count, not a distinct-credential count, so re-formatting a
    pre-fix row re-increments per read. Detection-only paths must use
    :func:`count_credentials`, which never touches the counters.
    """

    if text is None:
        return text, 0  # type: ignore[return-value]
    if not isinstance(text, str):
        text = str(text)
    hits = 0
    for name, pattern in _CREDENTIAL_PATTERNS:
        text, count = pattern.subn(f"[REDACTED:{name}]", text)
        hits += count
    if hits:
        with _stats_lock:
            _stats["scrubbed"] += hits
    return text, hits


def count_credentials(text: str | None) -> int:
    """Count credential-shaped substrings WITHOUT scrubbing or statting.

    Detection-only companion to :func:`scrub_text` for validation paths
    (skill_validate): reporting a credential-shaped string there is a
    named error, but it must not inflate the disclosed ``scrubbed``
    operations counter — nothing was scrubbed (cycle-9 review F5).
    """

    if text is None:
        return 0
    if not isinstance(text, str):
        text = str(text)
    hits = 0
    for _name, pattern in _CREDENTIAL_PATTERNS:
        hits += len(pattern.findall(text))
    return hits


def scrub(text: str | None) -> str | None:
    """Convenience wrapper returning only the scrubbed text."""

    return scrub_text(text)[0]


def stats_snapshot() -> dict[str, int]:
    """Return a copy of the process-wide scrub counters (KTD36 pattern).

    ``scrubbed`` counts scrub OPERATIONS (per replaced occurrence, per
    call), not distinct credentials — see :func:`scrub_text`.
    """

    with _stats_lock:
        return dict(_stats)


def stats_reset() -> None:
    """Zero the counters (test isolation)."""

    with _stats_lock:
        _stats["scrubbed"] = 0
