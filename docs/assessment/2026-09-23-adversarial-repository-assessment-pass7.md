---
date: 2026-09-23
topic: hermes-curator-evolver-adversarial-repository-assessment
mode: repo-grounded
run: cf968161814b
phase: assess
action: assess:assess
attempt: 31660eaded184817a35110f39e71bd92
skill: direct assessment in repo docs/assessment pass format (no ce-assess skill exists in the fleet's ce-* roster; ce-code-review is diff-scoped subagent machinery unusable here — routing precedent, pass 7)
review-run: /home/agent/.hermes/conductor-runs/cf968161814b-assess
---

# Adversarial repository assessment — pass 7

**Tree reviewed:** conductor worktree `run-cf968161814b-cf968161` @ `a76962c`
(post-cycle-6: U43 truth-table classifier, U45/U46/U53/U54 storage topology,
backfill N7, restore-drill gate N4 all present). Branch clean, no local changes.

**Dominant context finding (F1):** this worktree's base — and the canonical
checkout at `/work/projects/hermes-curator-evolver` — are **10 commits behind
live `origin/main` (`27487cd`, cycle-9 merge of PR #8, 2026-09-22)**. Cycles
7–9 landed upstream fixes this tree lacks (U69–U82: ingest identity, crash
containment, credential scrubbing, classifier truth-table repair, review-queue
lock margins, pinned-ruff CI lint job). Several defects below are therefore
*already fixed upstream* — remediation is a rebase, not a re-fix, and any
change made on this stale base risks conflict/redundancy with main. Every
"fixed upstream" cross-ref below was verified read-only via
`git show origin/main:...`.

**Fresh baselines this attempt:** `pytest` (repo venv, 3.12 wheel env) →
**287/287 passed** (17 files, all green; summary line suppressed by the
doubled `-q`, per known addopts quirk). `grep -rn scrub|redact|credential`
over the package → no scrubbing anywhere (F2). CI at this base
(`.github/workflows/ci.yaml`) has a test job only (self-hosted, 3.11+3.12
matrix) — **no lint job** (added upstream in cycle-8/9 with a pinned ruff
ceiling).

## Findings

### F2 (HIGH, security/privacy) — unscrubbed tool-result previews flow into publishable SKILL.md

Hooks and backfill store raw `result_preview` text (first 220+ chars of tool
output, which routinely contains tokens, keys, internal paths). Evidence rows
are embedded **verbatim** into the managed evidence block of SKILL.md files at
`auto_evolve.py:418-424` (`_format_evidence_rows`), and again at lines 568 and
830. Skills are the project's *publishing* surface (skills-index/hub). No
scrub/redact/credential handling exists anywhere in the package (grep-verified;
the "redacted evidence" wording in `candidates.py`/`cli.py` refers only to the
operator-supplied JSONL packets). A DB row whose preview reads
`export API_TOKEN=sk-live-...` becomes a permanent line in a managed skill
block that auto-evolve later rewrites/republishes. **Upstream fixed this in
cycle-9 (U77)**: `hermes_curator_evolver/hygiene.py` `scrub_text` applied at
exactly these embed points plus a `credentials_scrubbed` counter in backfill
stats (verified via `git show origin/main:hermes_curator_evolver/backfill.py`).
Here: live.

### F3 (MEDIUM, correctness/concurrency) — backfill dedupe probes read on the warm writer connection

`backfill.py:100`, `:121`, `:141` (`_tool_event_exists`, `_turn_event_exists`,
`_session_event_exists`) run `with store.connect() as conn:` — the **shared
warm writer connection**, outside the per-path lock. `storage.py:306-325`
forbids exactly this in its own docstring: *"Only the write helpers … may run
statements on it … READERS MUST NOT TOUCH IT — a bare `with conn:` block would
COMMIT or ROLL BACK whatever transaction a writer thread has open."* A probe
exiting its `with` block calls `commit()` on a connection a hook-thread writer
may hold mid-transaction, breaking the writer's atomicity contract (benign
today only because each `_insert` is single-statement). **Upstream fixed**:
origin/main `backfill.py:115-163` routes all three through
`store._read_connection()` with an explicit "do not touch the warm writer
handle" comment. Remediation: rebase (or port the same one-line-per-probe fix
if this base must ship).

### F4 (MEDIUM-LOW, correctness) — free-text failure vocabulary misses common prose failure phrasings

Probe-evidenced against `looks_like_error` at this base (probe transcript in
review-run dir):

| text | classified |
|---|---|
| `ERROR: connection refused while fetching index` | success (miss) |
| `command exited 1 after retries` | success (miss) |
| `3 tests failing in suite` | success (miss) |
| `build finished: 3 errors, 0 warnings` | success (miss) |
| `request timed out after 30s` | success (miss) |
| `permission denied: cannot write /etc/hosts` | success (miss) |
| `deploy exited with exit status 1` | error ✓ |
| `0 failed, exit code 0` / `1 failed, exit code 1` | ✓ / ✓ |

The structured-path vocabulary (`_STATUS_FAILURE_WORDS`: error, failed,
failure, timeout, denied, …) is far richer than the free-text keyword pattern
(traceback / not-found / exit code N / nonzero / failed / size cap /
exceeded). Transcripts whose tool output is prose ("ERROR:", "timed out",
"permission denied") silently classify as success → `error_events`
undercounted → weaker failure-evidence signal for the whole curation
pipeline. Conservative-by-design is fine; this is the *opposite* direction
(false negatives for failures). Upstream cycle-8 U73 repaired the structured
truth table and success-phrase position; whether the free-text vocabulary gap
persists on live main was not re-verified this pass (research item).

### F5 (LOW, reliability) — legacy backfill lacks per-session crash containment

The state-db branch wraps each `_import_session_data` in a per-session
try/except boundary (backfill.py:468-478); the **legacy** branch
(backfill.py:519-530) does not — one malformed `session_*.json` aborts the
entire legacy import mid-stream. Additionally `_load_json`'s gate at
backfill.py:525 catches only `(OSError, json.JSONDecodeError)`;
`UnicodeDecodeError` subclasses neither (known P8/U76 upstream). Main now has
a `legacy_skipped_undecodable` counter — fixed upstream, live here.

### F6 (LOW) — identical-turn dedupe drops legitimate repeats

`_turn_event_exists` dedupes on preview equality (same user + assistant
preview text in one session): a user legitimately re-issuing an identical
message with an identical response (retry after gateway blip) is silently
dropped as a duplicate. Undercounts turn evidence.

### F7 (LOW) — duplicate skill names shadow silently

`discover_skill_files` (auto_evolve.py ~399-409) keys on frontmatter `name:`;
two skills with the same name in different subdirs → last-sorted silently
wins as the auto-evolve target; the other is never considered. No warning.

### F8 (LOW) — support-file writes bypass atomic-write discipline

SKILL.md writes go through `_atomic_write_text` (temp + os.replace, U44), but
`auto_evolve.py:1163` writes reference/support files with plain
`support_path.write_text`. A crash mid-write leaves a torn reference file that
`register_support_file_in_manifest` then records as canonical prior-state
truth — the restore drill would faithfully restore the *torn* content.

### F9 (LOW) — review queue connection hygiene

`ReviewQueue._connect` opens a fresh connection per operation and every call
uses `with conn:` which commits but **never closes** (the exact pattern
storage.py's U45 rewrote; relies on CPython refcount finalization). No WAL
and no busy-retry hardening on `review_queue.db`; upstream added an
enqueue-under-external-holder margin test (U82) in a later cycle — real-world
lock contention was evidently observed.

### F10 (LOW, DX) — CLI/tool exception boundaries

`handle_cli` has no top-level error boundary: malformed JSONL
(`candidates-mine`), corrupt manifest (`rollback`, `restore-drill`),
malformed proposal JSON (`verify`), negative `--seconds` (`teach`),
missing `--content-file` (`apply`) all dump raw tracebacks. Plugin tool
`curator_evidence_report` (tools.py:43) does `int(payload.get("days") or 7)`:
a non-numeric `"days": "week"` raises ValueError into the host tool call.

### F11 (LOW, hardening asymmetry) — apply has no target-root containment; rollback does

`rollback_guarded_patch` refuses unrestricted targets without
`allowed_target_roots`/explicit opt-in (guarded_apply.py:634-645, U35), but
`apply_guarded_patch` (guarded_apply.py:311) accepts any absolute
`target_path` given hash-match + `--approve` (cli.py `apply` passes operator
paths unchecked). Operator-trust tool, but the guardrail story is one-sided:
one typo'd `--target` writes outside the skills tree with full ceremony.

## Cleared / positive

- storage.py topology is genuinely hardened at this base: per-path locks,
  single-flight warm writer, read-only reader connections, WAL-fallback with
  cross-VM refusal, quarantine-on-corruption, atexit close.
- guarded_apply: atomic writes, mode preservation, symlink refusal,
  scrubbed-env verify subprocess, staged pre-verify, manifest validation N1.
- systemd installer (U17) rejects control chars, quotes args, unit hardened.
- restore-drill gate is fail-closed (unreadable state blocks applies when
  required).
- `prune_auto_reference_files` deletes only its own prefixed pattern; `keep=0`
  disables.
- 287/287 tests green at this base; docs/assessment trail (passes 1-6) is
  unusually rigorous and reproducible.

## Recommended order of operations

1. **Rebase the worktree/canonical checkout to `27487cd`** before any code
   change (F1). Re-derive F4/F6/F7/F8/F9/F10/F11 against the new base; F2/F3/
   F5 are expected to fall away as already-fixed.
2. F4 (classifier text vocabulary) is the most promising *net-new* unit if
   still present post-rebase — probe first against the rebased tree.
3. Do not "fix" F2/F3/F5 on this base — duplicate/conflicting work vs main.
