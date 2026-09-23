"""Read-only candidate mining for the curator-evolver review queue.

This module classifies redacted evidence snippets into review candidates.
Nothing here writes to user memory, mutates skills, or auto-applies anything;
every produced candidate defaults to ``auto_apply_allowed=False`` and
``requires_human_review=True``.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

CANDIDATE_TYPE_MEMORY = "memory"
CANDIDATE_TYPE_SKILL_UPDATE = "skill_update"
CANDIDATE_TYPE_SKILL_NEW = "skill_new"
CANDIDATE_TYPE_REPLAY_BENCHMARK = "replay_benchmark"
CANDIDATE_TYPE_IGNORE = "ignore"

CANDIDATE_TYPES = {
    CANDIDATE_TYPE_MEMORY,
    CANDIDATE_TYPE_SKILL_UPDATE,
    CANDIDATE_TYPE_SKILL_NEW,
    CANDIDATE_TYPE_REPLAY_BENCHMARK,
    CANDIDATE_TYPE_IGNORE,
}

SKILL_MD_NEAR_CAP_BYTES = 90_000
SKILL_MD_HARD_CAP_BYTES = 100_000


def candidate_id(candidate_type: str, title: str, evidence_refs: Iterable[str]) -> str:
    """Stable sha256-derived id over type, title, and sorted evidence refs."""
    refs = ",".join(sorted(str(r) for r in evidence_refs))
    payload = f"{candidate_type}|{title}|{refs}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:32]


@dataclass
class Candidate:
    candidate_type: str
    title: str
    rationale: str
    confidence: float
    evidence_refs: list[str]
    target_skill: str | None = None
    auto_apply_allowed: bool = False
    requires_human_review: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = ""

    def __post_init__(self) -> None:
        if self.candidate_type not in CANDIDATE_TYPES:
            raise ValueError(f"unknown candidate_type: {self.candidate_type!r}")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be within [0, 1]")
        if self.auto_apply_allowed:
            raise ValueError(
                "auto_apply_allowed must remain False in the read-only candidate miner"
            )
        if not self.requires_human_review:
            raise ValueError(
                "requires_human_review must remain True in the read-only candidate miner"
            )
        if not self.id:
            self.id = candidate_id(self.candidate_type, self.title, self.evidence_refs)


_SAFETY_PREF_PATTERN = re.compile(
    r"curator[-\s]?evolver.*(auto[-\s]?apply).*(agent[-\s]?created|non[-\s]?core)",
    re.IGNORECASE | re.DOTALL,
)
_SAFETY_PROHIBIT_PATTERN = re.compile(
    r"(must not|never|do not|don't).*(modify|touch|change).*(core|official|external)",
    re.IGNORECASE | re.DOTALL,
)
_MEMORY_POLICY_PATTERN = re.compile(
    r"durable\s+memory.*(只存|不存|流程/步驟/SOP|task\s+progress|PR\s*/\s*SHA)",
    re.IGNORECASE | re.DOTALL,
)

_STEP_NUMBERED_PATTERN = re.compile(r"\b[1-9]\.\s+\S")
_STEP_KEYWORD_PATTERN = re.compile(
    r"\b(first|then|next|finally|step\s+\d+)\b|先|再|最後|流程|步驟|SOP",
    re.IGNORECASE,
)
_SHELL_COMMAND_PATTERN = re.compile(r"`[^`]{2,}`|\brun\s+`", re.IGNORECASE)
_SHELL_SPAN_PATTERN = re.compile(r"`[^`]{2,}`")
_LINE_DECORATION_PATTERN = re.compile(r"^(?:\d+[.)]|[-*+>|]|\$|#)\s*")
_ZH_WORKFLOW_PATTERN = re.compile(
    r"(流程|步驟|SOP).{0,80}(先|再|最後).{0,160}(先|再|最後)", re.DOTALL
)

_FAILURE_KEYWORD_PATTERN = re.compile(
    # Separator set ``[-\s_:=]`` (roadmap U79, cycle 9): models emit
    # ``exit_code=1``, ``exit_code: 1``, ``exit-code 1`` — snake_case,
    # hyphen, and punctuation joins the old ``\s+``-only arms could not
    # see, so a failure-shaped report with NO other keyword classified
    # as success (pass-9: "exit_code=1" alone). The set strictly widens
    # the old arms (``\s+`` → ``[-\s_:=]+``), so every previously-
    # matching shape still matches; zero stays excluded by ``[1-9]\d*``.
    r"\b(traceback|not[_\s-]?found|exit[-\s_:=]+(?:code|status)[-\s_:=]+[1-9]\d*"
    r"|exit(?:ed|ing)?(?:[-\s_:=]+with)?[-\s_:=]+(?:code|status)[-\s_:=]+[1-9]\d*"
    r"|exit[\s_]*=[\s_]*[1-9]\d*"
    r"|nonzero|failed|size\s+cap|exceeded"
    # Cycle-10 U86 (pass-7 F4 probe set): prose shapes the exit-code arms
    # could not see. ``exit(?:ed)? N`` is the bare short form with NO
    # code/status word (zero stays excluded by ``[1-9]\d*`` — and the
    # group is written ``exit(?:ed)?``, not ``exited?``, because
    # ``exited?`` regex-parses as ``exite|exited`` and missed the plain
    # shell phrasing "exit 1");
    # ``errors?:`` is the log-line prefix, colon-terminated so success
    # prose ("no errors", "error rate healthy") never matches;
    # ``timed[-\s_]*out`` is the verb phrase including joined
    # ``timed_out`` — bare ``timeout`` stays a status word only, because
    # config narratives say "30s timeout"; ``permission denied`` and
    # the ``failing`` participle join ``failed`` as unanswered-failure
    # keywords that a clause-level success claim can still answer
    # positionally (KTD35).
    r"|exit(?:ed)?[-\s_:=]+[1-9]\d*"
    r"|timed[-\s_]*out"
    r"|permission\s+denied"
    # Cycle-10 review fix (M2): the noun-plural ``failures`` joins the
    # unanswered-keyword family — the roadmap U86 packet names
    # "failing/failures plurals", and "build failures detected" carries
    # no count and no colon, so only a bare keyword sees it. Singular
    # ``failure`` deliberately stays a structured-status word only.
    # Zero/count shapes ("0 failures", "2 failures") resolve through
    # the count parses, not this arm.
    r"|failing|failures)\b"
    # ``errors?:`` lives OUTSIDE the ``\b(...)\b`` group because the arm
    # ends in a non-word character (``:``): a trailing ``\b`` between
    # ``:`` and whitespace never holds (probe "ERRORS: 4 found" exposed
    # it). Its own leading ``\b`` is all it needs.
    r"|\berrors?[-\s_]*:",
    re.IGNORECASE,
)

# Paired-count truth (roadmap U51/U67, assessments S1 + N1): ``N failed``
# is a failure for every N > 0 at ANY digit width and with ANY digit
# grouping — the cycle-5 lookbehind cleared every count ending in a zero
# ("10 failed"), and the cycle-6 ``(\d+)`` capture bound only the trailing
# group of comma-formatted counts ("1,000 failed" read as 000 → success,
# pass-7 N1). The pattern therefore accepts plain integers, comma-grouped
# thousands, and — per the format-matrix rule L15 (KTD31), which the
# independent review found governing (finding 1) — EVERY other digit-
# grouping separator: ``10.000``, ``10 000``, ``10_000`` carry the same
# magnitude as ``1,000``, and malformed groups ("10,00") are accepted
# deliberately, because for failure detection a miss on failure-shaped
# text is worse than a hit on an unusual format. The caller strips ALL
# separators before the int() so every grouping parses at true magnitude
# ("2,048 failed" stays a failure at 2048). Zero-count reports
# ("0 failed") are success phrases handled by the count parse, not
# lookbehind tricks.
#
# Cycle-10 U86: the verb family widens beyond ``failed`` — ``failing``
# ("3 tests failing", pass-7 F4) and ``errors?`` ("2 errors",
# "4 validation errors") — and an optional interposed noun
# (``(?:\w+\s+)?``) lets the count bind across "3 tests failing" /
# "1,000 checks failed" shapes. This also repairs a pre-U86 gap on the
# success side: "0 tests failed" used to miss the count parse (noun in
# the way), fall to the unanswered-keyword rule, and misclassify as
# failure; it now resolves to the zero-count success answer.
#
# Cycle-10 review fixes (M2 + L1): ``failures?`` ("2 failures",
# "3 test failures") and ``timed[-\s_]*out`` ("12 requests timed out")
# join the verb family, so their zero forms ("0 failures",
# "0 timed out, 12 passed") get the zero-count success answer for free
# from the positional resolver below.
_FAILURE_COUNT_PATTERN = re.compile(
    r"(\d+(?:[,. _]\d+)+|\d+)\s+(?:\w+\s+)?(?:failed|failing|errors?|failures?|timed[-\s_]*out)\b",
    re.IGNORECASE,
)

# Cycle-10 review fixes (M1 + M2 + L1): digit-AFTER-colon count forms.
# Lint/test-style summaries put the count on the other side of the
# colon from the noun — ``errors: 4``, ``failures: 2``, ``tests timed
# out: 3`` — and the same shapes carry the zero answers the review
# found missing: ``errors: 0`` / ``timed out: 0`` must resolve to the
# success answer (L2 symmetric-success discipline), while any nonzero
# count is failure exactly like the digit-before-noun family. Colon +
# prose (``ERROR: file not found``) stays with the ``errors?:`` keyword
# arm above; colon + none/null/zero words (``error: none``) are success
# phrases in _SUCCESS_COUNT_PATTERN.
_COLON_COUNT_PATTERN = re.compile(
    r"\b(?:errors?|failures?|timed[-\s_]*out)[-\s_]*:\s*(\d+(?:[,. _]\d+)+|\d+)",
    re.IGNORECASE,
)

# Success-phrase scoping (roadmap U51, assessments S4 + N3): a success
# phrase clears only the failure keywords that share its clause (line,
# sentence, or semicolon-separated segment) — "no errors" on a different
# line than "deploy failed: connection refused" is a different clause's
# truth and must not erase the failure. Sentence ends split even when the
# join is unspaced (pass-7 N3b: "deploy failed.no errors later" is two
# clauses, not one) — models emit concatenated output without the space.
# EXCEPT when a digit immediately follows the period: "10.000 failed"
# dot-groups its magnitude (L15 separator set is `,` `.` space `_`), so a
# period between digits is a grouping separator, not a sentence end
# (independent-review finding 1). Commas are deliberately NOT clause
# separators: they group digits ("1,000 failed") and carry list items
# ("error, line 3, not found"). Comma-joined mixed claims are resolved
# POSITIONALLY in _text_bears_failure (pass-8 F1 / KTD35): a success
# phrase answers failure evidence that PRECEDES it in the clause, while
# a failure keyword that follows the clause's last success phrase is a
# new claim that stands — "no tests failed, deploy failed: connection
# refused" fails, "exit code 1, no errors" stays a success report.
_CLAUSE_SPLIT_PATTERN = re.compile(
    r"[;\n；]|(?<=[!?。！？])\s*|(?<=\.)(?!\d)\s*"
)

# Success-bearing count phrases that must clear a keyword hit: a report
# saying zero things failed is a success report even though it contains the
# word "failed" (assessment Q1: '0 failed, 12 passed' / 'grep: 0 failed' /
# 'success: no tests failed' were classified as errors by the bare-keyword
# scan).
_SUCCESS_COUNT_PATTERN = re.compile(
    r"\b0\s+failed\b|\bno\s+errors?\b|\bnothing\s+failed\b|\bno\s+(?:\w+\s+)?failed\b"
    # Cycle-10 U86: the no-…-failed family widens with the failure
    # verbs — "no tests failing" / "no parse errors" are success claims
    # that must answer a keyword hit positionally, exactly like
    # "no tests failed" (KTD35).
    r"|\bno\s+(?:\w+\s+)?(?:failing|errors?|failures?|timed[-\s_]*out)\b"
    # Cycle-10 review fixes (M1 + L1): colon-form success answers —
    # "error: none" / "Error: null" are explicit zero claims (digit
    # zeros like "errors: 0" resolve through _COLON_COUNT_PATTERN),
    # and "no timed out tests" / "no requests timed out" answer the
    # timed-out keyword positionally like every other no-phrase.
    r"|\b(?:errors?|failures?)\s*:\s*(?:none|null|zero)\b"
    r"|\bno\s+timed[-\s_]*out\b",
    re.IGNORECASE,
)

# Structured failure/success vocabulary (assessment Q1 truth table).
_EXIT_CODE_KEYS = ("exit_code", "returncode", "code")
# In-band success statuses for the ambiguous generic ``code`` key
# (roadmap U51/U67/U73, assessments S2 + N4 + pass-8 F3): tool wrappers
# store HTTP statuses in ``code`` verbatim, so these nonzero values are NOT
# process failures. The rule is the full in-band RANGE, not an enumerated
# set: every 2xx is success, and so is the whole 3xx family, because
# these plugins run redirect-following clients (curl -L / requests
# defaults): 301/302/303/307/308 are followed transparently and land on a
# final status, and 304 is a conditional-cache success. Enumeration is
# what missed 203/206 in cycle 6 and 226 in pass 8 (IM Used is a legal
# in-band response), so the range is total by construction.
# ``exit_code``/``returncode`` keep strict nonzero-is-failure semantics.
_IN_BAND_SUCCESS_MIN = 200
_IN_BAND_SUCCESS_MAX = 400
# Cycle-10 U86 alignment: ``timed_out`` / ``permission_denied`` are
# exact-match snake_case statuses the prose vocabulary now recognizes;
# without them a structured ``status: timed_out`` carried no signal and
# the verdict depended on the payload's prose text alone.
_STATUS_FAILURE_WORDS = frozenset(
    {
        "error",
        "failed",
        "failure",
        "timeout",
        "timed_out",
        "permission_denied",
        "cancelled",
        "canceled",
        "aborted",
        "denied",
    }
)
_STATUS_SUCCESS_WORDS = frozenset(
    {"ok", "success", "succeeded", "passed", "completed", "healthy"}
)

# Status-payload truth (roadmap U73, pass-8 F4): ``status`` arrives as a
# bare integer ("status": 500) or a status LINE ("500 Internal Server
# Error"), not only a vocabulary word. The same in-band range rule
# governs both: 200-399 is an explicit success signal, any other number
# is an explicit failure signal. Word statuses keep the vocabulary check.
_STATUS_LINE_PATTERN = re.compile(r"^\s*(\d{3})\b")


def _status_signal(value: Any) -> str | None:
    """Classify a ``status`` payload as "failure", "success", or no signal."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        # NaN/Infinity carry no status truth (cycle-8 review P3, fixed
        # cycle 9): ``int(float("nan"))`` raises, which used to crash the
        # classifier and abort a whole backfill. Unrepresentable numbers
        # are no signal, not a crash — that includes ints beyond float
        # range (``float(10**400)`` raises OverflowError; cycle-9 review
        # F3: the pre-fix ``int(value)`` never crashed on ints).
        try:
            number = float(value)
        except OverflowError:
            return None
        if number != number or number in (float("inf"), float("-inf")):
            return None
        code = int(number)
        return (
            "success"
            if _IN_BAND_SUCCESS_MIN <= code < _IN_BAND_SUCCESS_MAX
            else "failure"
        )
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _STATUS_FAILURE_WORDS:
            return "failure"
        if lowered in _STATUS_SUCCESS_WORDS:
            return "success"
        match = _STATUS_LINE_PATTERN.match(value)
        if match:
            code = int(match.group(1))
            return (
                "success"
                if _IN_BAND_SUCCESS_MIN <= code < _IN_BAND_SUCCESS_MAX
                else "failure"
            )
    return None

_PR_REF_PATTERN = re.compile(r"\bPR\s*#?\d+\b|\bpull[-\s]request\s*#?\d+\b", re.IGNORECASE)
_ISSUE_ONLY_PATTERN = re.compile(r"^#\d+$")
_SHA_ONLY_PATTERN = re.compile(r"^[0-9a-f]{7,40}$", re.IGNORECASE)
_EPHEMERAL_KEYWORDS = re.compile(
    r"\b(merged|squashed|rebased|todo|wip)\b", re.IGNORECASE
)

_SKILL_MD_SIZE_PATTERN = re.compile(
    r"SKILL\.md.{0,40}?(\d{4,6})\s*bytes", re.IGNORECASE | re.DOTALL
)
_NEAR_CAP_WORDS = re.compile(r"near\s+100k|near\s+cap|over\s+cap", re.IGNORECASE)


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _extract_inner_text(text: str) -> str:
    """Return reviewer-readable text from common tool-result JSON wrappers."""
    stripped = (text or "").strip()
    if not stripped.startswith(("{", "[")):
        return text
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return text

    def collect(value: Any) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            out: list[str] = []
            for item in value:
                out.extend(collect(item))
            return out
        if isinstance(value, dict):
            out: list[str] = []
            for key in ("summary", "text", "output", "content", "error", "exception"):
                if key in value:
                    out.extend(collect(value[key]))
            if not out and "results" in value:
                out.extend(collect(value["results"]))
            return out
        return []

    parts = [p.strip() for p in collect(payload) if p and p.strip()]
    return "\n".join(parts) if parts else text


def _evidence_refs(record: dict[str, Any]) -> list[str]:
    raw = record.get("evidence_refs") or record.get("evidence_ref") or []
    if isinstance(raw, str):
        return [raw] if raw else []
    return [str(r) for r in raw if r]


def _is_safety_preference(text: str) -> bool:
    if not text:
        return False
    if _SAFETY_PREF_PATTERN.search(text):
        return True
    if _MEMORY_POLICY_PATTERN.search(text):
        return True
    if "curator" in text.lower() and _SAFETY_PROHIBIT_PATTERN.search(text):
        return True
    return False


def _block_shell_spans(text: str) -> int:
    """Count shell spans presented as standalone commands, not inline prose.

    A span counts only when its line is (almost) nothing but the command -
    optionally decorated with a list marker, step number, ``$`` or ``#`` -
    so prose like ``I ran `git status` then `git diff``` provides sequence
    evidence of zero. Procedural docs put commands on their own lines; that
    is the command-sequence signal ``_looks_workflow`` requires (roadmap U2,
    assessment finding F5).
    """

    count = 0
    for line in text.splitlines():
        stripped = _LINE_DECORATION_PATTERN.sub("", line.strip())
        if not stripped:
            continue
        for match in _SHELL_SPAN_PATTERN.finditer(stripped):
            remainder = (stripped[: match.start()] + stripped[match.end() :]).strip()
            if not remainder or set(remainder) <= {"$", "#"}:
                count += 1
    return count


def _looks_workflow(text: str) -> bool:
    if not text:
        return False
    numbered = len(_STEP_NUMBERED_PATTERN.findall(text)) >= 2
    keyword_hits = len(_STEP_KEYWORD_PATTERN.findall(text))
    shell_hits = len(_SHELL_COMMAND_PATTERN.findall(text))
    block_shell_hits = _block_shell_spans(text)
    if _ZH_WORKFLOW_PATTERN.search(text):
        return True
    return numbered or (keyword_hits >= 2 and shell_hits >= 1) or (block_shell_hits >= 2)


def _is_tool_failure(record: dict[str, Any], text: str) -> bool:
    """Classify failure from the U43 truth table: structured-first, never a bare keyword.

    Structured payload fields are authoritative, in this order: an explicit
    ``is_error`` record flag; a nonzero numeric exit status under any of
    ``exit_code``/``returncode``/``code``; a truthy ``error``/``exception``;
    ``ok``/``success`` ``False``; a ``status`` failure signal (vocabulary
    word, 4xx/5xx number, or "NNN …" status line). A zero exit status is an explicit success (it returns before
    the text scan), as are ``ok``/``success`` ``True`` and success-status
    strings when the exit status agrees. Only when no structured signal
    decides does the keyword scan run — and it never matches a success
    report: the failure pattern requires a nonzero ``exit code``/``status``,
    the bare ``stderr`` key name is gone (assessment Q1:
    ``{"stdout": "ok", "stderr": ""}`` was classified as an error by the
    key name alone), and success count phrases (``0 failed``, ``no errors``)
    clear a stray ``failed`` hit (``"0 failed, 12 passed"`` is a success).
    """

    if bool(record.get("is_error")):
        return True
    try:
        payload = json.loads(text) if isinstance(text, str) and text.strip().startswith("{") else None
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        # Truth table (roadmap U43/U51, assessments Q1+S1/S2/S4/S5): every
        # structured failure signal is honored first; explicit success
        # signals clear the text scan only when the exit status agrees; a
        # bare ``exit code 0``-style numeric success never matches the
        # keyword fallback because the failure pattern requires a nonzero
        # status word. The generic ``code`` key is ambiguous — tool wrappers
        # store HTTP statuses in it verbatim — so a nonzero value there is
        # NOT a process failure when it is a recognized in-band success
        # status and no explicit failure field exists (S2);
        # ``exit_code``/``returncode`` keep strict exit semantics. The
        # generic ``code`` in-band test is the RANGE 200-399 (pass-8 F3:
        # the enumerated set missed 226), and ``status`` carries numeric
        # and status-line signals under the same range (pass-8 F4).
        # Key-pick precedence (U43/U51) with a NaN/Infinity guard (cycle-8
        # review P3, fixed cycle 9 — twin of the ``_status_signal`` guard):
        # ``exit_code`` outranks ``returncode`` outranks ``code``, and an
        # unrepresentable float is ignored rather than crashing the
        # classifier. Sibling keys the pick skipped are re-examined below
        # under a zero primary exit (U79).
        exit_values: dict[str, int] = {}
        for key in _EXIT_CODE_KEYS:
            value = payload.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            try:
                number = float(value)
            except OverflowError:
                continue  # ints beyond float range: no representable exit
            if number != number or number in (float("inf"), float("-inf")):
                continue
            exit_values[key] = int(number)
        exit_code_key = next(iter(exit_values), None)
        exit_code = exit_values.get(exit_code_key) if exit_code_key else None
        status_signal = _status_signal(payload.get("status"))
        explicit_failure = bool(
            payload.get("error")
            or payload.get("exception")
            or payload.get("ok") is False
            or payload.get("success") is False
            or status_signal == "failure"
        )
        if exit_code is not None and exit_code != 0 and not (
            exit_code_key == "code"
            and _IN_BAND_SUCCESS_MIN <= exit_code < _IN_BAND_SUCCESS_MAX
            and not explicit_failure
        ):
            return True
        if payload.get("error") or payload.get("exception"):
            return True
        if payload.get("ok") is False or payload.get("success") is False:
            return True
        if status_signal == "failure":
            return True
        if exit_code == 0:
            # Sibling exit-status keys under a zero primary exit (roadmap
            # U79, cycle 9, KTD35 explicit-failure precedence): the key
            # pick stops at the FIRST present key, so {"exit_code": 0,
            # "code": 500} used to return success without ever reading
            # ``code``. A sibling reporting failure now outranks the zero
            # exit; a sibling whose value is itself an in-band HTTP
            # success ({"exit_code": 0, "code": 200}) keeps the success.
            for key, value in exit_values.items():
                if key == exit_code_key or value == 0:
                    continue
                if (
                    key == "code"
                    and _IN_BAND_SUCCESS_MIN <= value < _IN_BAND_SUCCESS_MAX
                    and not explicit_failure
                ):
                    continue
                return True
            return False
        if payload.get("ok") is True or payload.get("success") is True:
            return False
        if status_signal == "success":
            return False
    return _text_bears_failure(text)


def _parse_count(raw_count: str) -> int:
    """Parse a failure-count capture at true magnitude (cycle-10 review M3).

    Guards the py3.11+ integer-string conversion limit: a count wider
    than ~4300 digits is failure-shaped absurd text, and the pre-fix
    bare ``int()`` raised ValueError out of ``looks_like_error`` — a
    predicate-contract breach reachable from ingest
    (storage.py ``record_tool_call``). hooks.py catches ValueError at the
    live boundary, but a classifier predicate must not raise; an
    unparseable width is a nonzero count, not a crash.
    """
    stripped = re.sub(r"[,. _]", "", raw_count)
    # A giant all-zero width ("0"*5000 + " failed") is still zero —
    # int() raises on ANY string past the 4300-digit limit, zeros
    # included, so the zero check must precede the guarded conversion.
    if len(stripped) > 4300 and not stripped.strip("0"):
        return 0
    try:
        return int(stripped)
    except ValueError:
        return 1


def _text_bears_failure(text: str) -> bool:
    """Clause-scoped keyword scan of a free-text payload (roadmap U51/U67).

    The payload is split into clauses (lines, sentences — spaced or
    unspaced joins — and semicolon segments); a clause is failure-bearing
    when it carries a failure keyword that is not answered in clause
    order. A clause with explicit ``N failed`` counts is a failure exactly
    when any N > 0 — every digit width and grouping (`,` `.` space `_`),
    with or without a paired
    passing count (assessments S1 + N1). Digit-after-colon forms
    (``errors: 4``, ``timed out: 0`` — cycle-10 review M1/M2/L1) follow
    the same rule through _COLON_COUNT_PATTERN, and overlong counts
    (beyond the py3.11+ int-str limit) parse as nonzero instead of
    raising (review M3). Positional success-phrase truth
    (pass-8 F1 / KTD35): the clause's LAST success phrase (a zero-count
    claim or a ``no-…-failed``/``no errors`` phrase) is its final answer —
    it clears the failure evidence that PRECEDES it in the clause, while
    a failure keyword AFTER it is a new claim that stands: ``"no tests
    failed, deploy failed: connection refused"`` fails, and ``"0 failed,
    deploy failed: connection refused"`` still fails (pass-7 N3), while
    ``"0 failed, exit code 1, no errors"`` stays a success report
    (independent-review finding 2) and ``"0 failed, 12 passed"`` stays a
    success (pass-7 N1). A success phrase in a DIFFERENT clause never
    clears a failing clause (assessment S4: "no errors" on another line
    must not erase "deploy failed").
    """

    for clause in _CLAUSE_SPLIT_PATTERN.split(text):
        # Cycle-10 U86: a clause may bear failure ONLY as a count
        # (``2 errors``, ``4 validation errors`` — no keyword, no colon):
        # nonzero counts are self-evidencing, so the count pattern is an
        # entry gate in its own right. Zero-only counts still resolve to
        # the success answer below ("0 errors" never fails).
        if not (
            _FAILURE_KEYWORD_PATTERN.search(clause)
            or _FAILURE_COUNT_PATTERN.search(clause)
        ):
            continue
        counts = [
            _parse_count(count)
            for count in _FAILURE_COUNT_PATTERN.findall(clause)
        ] + [
            _parse_count(count)
            for count in _COLON_COUNT_PATTERN.findall(clause)
        ]
        if any(count > 0 for count in counts):
            return True
        # Positional resolution (pass-8 F1 / KTD35): the clause's LAST
        # success claim — a zero-count phrase (any digit grouping: "0
        # failed", "0,000 failed" are matched by the count pattern, whose
        # counts reaching here are all zero) or a ``no-…-failed``/``no
        # errors`` phrase — is its final answer: it clears the failure
        # evidence that PRECEDES it in the clause, while a failure keyword
        # AFTER it is a new claim that stands. A keyword with neither a
        # count nor a success claim is an unanswered failure.
        last_success_end = 0
        for match in _SUCCESS_COUNT_PATTERN.finditer(clause):
            last_success_end = match.end()
        for match in _FAILURE_COUNT_PATTERN.finditer(clause):
            last_success_end = max(last_success_end, match.end())
        # Colon-form zero counts ("errors: 0", "tests timed out: 0")
        # are success answers exactly like digit-before-noun zeros
        # (cycle-10 review M1/L1); nonzero colon counts never reach
        # here — they returned True in the counts pass above.
        for match in _COLON_COUNT_PATTERN.finditer(clause):
            if _parse_count(match.group(1)) == 0:
                last_success_end = max(last_success_end, match.end())
        if not last_success_end:
            return True
        if _FAILURE_KEYWORD_PATTERN.search(clause[last_success_end:]):
            return True
        continue
    return False


def looks_like_error(result: Any) -> bool:
    """Single error classifier for tool results (roadmap U28, truth table U43/U51).

    Ingest (:mod:`hermes_curator_evolver.storage`) and candidate mining
    (:func:`classify_record`) must agree on what counts as an error, so both
    call this one structured-first classifier. The U43/U51 truth table:
    ``exit_code``/``returncode``/``code`` nonzero → error, zero → success —
    but explicit failure fields (``error``, ``exception``, ``ok``/``success``
    false, ``status`` failure signal) outrank a zero exit (assessment S5: the
    code checks them before the zero-exit return and tests pin that order;
    the old docstring claimed "zero → success" and was the defect); a
    nonzero ``code`` value that is an in-band HTTP success status
    with no failure field is not
    an error (assessment S2 + pass-7 N4 + pass-8 F3: the in-band test is
    the full 200-399 RANGE — enumeration kept missing legal codes like
    226); a numeric or status-line ``status`` carries the same range rule
    and failure/success vocabulary (pass-8 F4); the keyword scan runs only when
    no structured verdict exists, is scoped per clause, and binds
    ``N failed`` counts at every digit width and grouping (`,` `.` space
    `_`: ``"1,000"``, ``"10.000"``, ``"10 000"``, ``"10_000"``, malformed
    groups) — so
    ``"0 failed, 12 passed"``, ``"success: no tests
    failed"``, ``{"stdout": "ok", "stderr": ""}``, ``"exit code 0"``, and
    ``{"code": 200}`` classify as success while ``"10 failed, 2 passed"``,
    ``{"returncode": 1}``, ``{"code": 1}``, and ``{"ok": false}`` classify
    as failure (assessments Q1/S1/S2, which reopened U43's table twice).
    """

    if isinstance(result, str):
        return _is_tool_failure({}, result)
    if isinstance(result, list):
        # A list result is a batch of results: it is a failure exactly when
        # any element is (an empty batch is not).
        return any(looks_like_error(item) for item in result)
    if isinstance(result, dict):
        try:
            text = json.dumps(result, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):
            text = str(result)
        return _is_tool_failure({}, text)
    if result is None:
        return False
    return _is_tool_failure({}, str(result))


def _is_ephemeral(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True
    if _ISSUE_ONLY_PATTERN.match(stripped):
        return True
    if _SHA_ONLY_PATTERN.match(stripped):
        return True
    if _PR_REF_PATTERN.search(stripped) and _EPHEMERAL_KEYWORDS.search(stripped):
        return True
    return False


def _detect_skill_md_size(record: dict[str, Any], text: str) -> int | None:
    explicit = record.get("skill_md_size")
    if isinstance(explicit, (int, float)) and explicit > 0:
        return int(explicit)
    match = _SKILL_MD_SIZE_PATTERN.search(text or "")
    if match:
        try:
            return int(match.group(1))
        except (TypeError, ValueError):
            return None
    return None


def _is_near_cap(record: dict[str, Any], text: str) -> bool:
    size = _detect_skill_md_size(record, text)
    if size is not None and size >= SKILL_MD_NEAR_CAP_BYTES:
        return True
    if _NEAR_CAP_WORDS.search(text or ""):
        return True
    return False


def _looks_line_numbered_dump(text: str) -> bool:
    """Detect raw read_file-style source/doc dumps such as ``1|...`` lines."""
    return len(re.findall(r"(?:^|\n|\s)\d+\|", text or "")) >= 2


def _truncate(text: str, limit: int = 140) -> str:
    text = (text or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def classify_record(record: dict[str, Any]) -> Candidate:
    """Classify a single redacted evidence record into one Candidate.

    Always returns a Candidate; unknown or low-confidence cases default to
    ``CANDIDATE_TYPE_IGNORE`` with ``requires_human_review=True``. The function
    never returns ``auto_apply_allowed=True``.
    """

    raw_text = _normalize_text(record.get("text"))
    text = _extract_inner_text(raw_text)
    refs = _evidence_refs(record)
    target_skill = record.get("target_skill") or None

    if _looks_line_numbered_dump(text) and not record.get("skill_md_size") and not record.get("is_error"):
        return Candidate(
            candidate_type=CANDIDATE_TYPE_IGNORE,
            title="line-numbered source dump",
            rationale="raw source/document dump is not a durable candidate signal",
            confidence=0.2,
            evidence_refs=refs,
            metadata={"category": "source_dump"},
        )

    if _is_near_cap(record, text):
        size = _detect_skill_md_size(record, text)
        rationale_bits = ["SKILL.md is at or near the 100k cap"]
        if size:
            rationale_bits.append(f"observed size ~{size} bytes")
        rationale = "; ".join(rationale_bits)
        return Candidate(
            candidate_type=CANDIDATE_TYPE_SKILL_UPDATE,
            title=f"near-cap SKILL.md for {target_skill or 'unknown skill'}",
            rationale=rationale,
            confidence=0.7,
            evidence_refs=refs,
            target_skill=target_skill,
            metadata={
                "direct_append_allowed": False,
                "reason": "skill_md_near_cap",
                "observed_size_bytes": size,
            },
        )

    if _is_safety_preference(text):
        return Candidate(
            candidate_type=CANDIDATE_TYPE_MEMORY,
            title="curator-evolver safety preference",
            rationale=_truncate(text),
            confidence=0.9,
            evidence_refs=refs,
            metadata={"category": "user_safety_preference"},
        )

    if _is_tool_failure(record, raw_text) or _is_tool_failure(record, text):
        tool = (record.get("tool_name") or "").lower() or "unknown"
        return Candidate(
            candidate_type=CANDIDATE_TYPE_REPLAY_BENCHMARK,
            title=f"replay benchmark for {tool} failure",
            rationale=_truncate(text),
            confidence=0.75,
            evidence_refs=refs,
            target_skill=target_skill,
            metadata={"tool_name": tool, "is_error": True},
        )

    if _looks_workflow(text):
        kind = CANDIDATE_TYPE_SKILL_UPDATE if target_skill else CANDIDATE_TYPE_SKILL_NEW
        return Candidate(
            candidate_type=kind,
            title=(
                f"workflow update for {target_skill}"
                if target_skill
                else "new workflow skill candidate"
            ),
            rationale=_truncate(text),
            confidence=0.65,
            evidence_refs=refs,
            target_skill=target_skill,
            metadata={"category": "workflow"},
        )

    if _is_ephemeral(text):
        return Candidate(
            candidate_type=CANDIDATE_TYPE_IGNORE,
            title="ephemeral progress note",
            rationale=_truncate(text) or "empty or short-term state",
            confidence=0.2,
            evidence_refs=refs,
            metadata={"category": "ephemeral"},
        )

    return Candidate(
        candidate_type=CANDIDATE_TYPE_IGNORE,
        title="unclassified evidence",
        rationale=_truncate(text) or "no recognizable signal",
        confidence=0.1,
        evidence_refs=refs,
        metadata={"category": "low_confidence"},
    )


def mine_candidates(records: Iterable[dict[str, Any]]) -> list[Candidate]:
    """Classify each redacted record into a Candidate, preserving input order."""
    return [classify_record(dict(r)) for r in records]
