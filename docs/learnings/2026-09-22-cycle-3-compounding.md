# Cycle-3 Compounding — Durable Lessons (pre-review)

> **Integration renumber note (2026-09-24, roadmap KTD46):** merged onto main per KTD41, main's cycle-9 compounding (`docs/learnings/2026-09-22-cycle-9-compounding.md`) had already taken **L29–L34**, so this doc's items renumber: L29→L35, L30→L36, L31→L37, L32→L38, L33→L39, L34→L40, L35→L41, L36→L42. The headers below keep their original (void) numbers as written; cite them by the new identities. The batch units also renumbered: U82→U93, U83→U94 (roadmap "Integration fold 2026-09-24").

- **Run**: `3ed5d14a80a245f3bb71735d577be08a` · **Phase**: compound · **Attempt**: `ebb80ad486824051b38f4a6c1089471d`
- **Date**: 2026-09-22 · **Scope**: pre-review cycle evidence only (assessment, research, roadmap, prioritization, stewardship, implementation, targeted/full test outcomes). Review and shipping outcomes are NOT folded here — the next cycle's assessment carries them.
- **Batch compounded**: U82 + U83 ("secondary-surface hardening parity") per `docs/prioritization/2026-09-22-cycle-3-batch.md` and `docs/stewardship/2026-09-22-cycle-3-stewardship-request.md` — review-queue busy-retry parity (U45 recipe mirrored in `review_queue.py`) and restore-drill manifest-path validation (routed through `guarded_apply._resolve_within`), 6 new tests, full suite 293 passed, ruff flat at 12.
- **Rule numbering**: continues main's line (L1–L14 cycle 6, L15 KTD31, L16–L21 cycle 7, L22–L28 cycle 8 — max `L28` in `docs/learnings/2026-09-21-cycle-8-compounding.md`); this doc takes **L29–L36**. On merge, if origin/main has taken L29+ first, renumber this doc's items in a dated note rather than colliding.
- **Era note**: this cycle ran on a worktree 6 commits behind origin/main (pre-cycle-7/cycle-8 base). L29 generalizes that constraint; the rest are era-independent.

## L29 — On a stale worktree, prioritize by value-per-merge-conflict, not raw severity

The cycle-3 board's highest-scoring unit (U77, classifier NaN/Infinity hardening, 22 points) was **gated out of implementation**: origin/main's cycles 7–8 rewrote `candidates.py` (+154/−52) and already hold the same defects as open review findings — a fix here produces a diff that merges as noise or gets discarded wholesale. The selected batch (U82+U83) lived entirely in 0-main-commit files (`review_queue.py`, `restore_drill.py`) whose diffs carry forward merge-free.

**Rule**: before selecting any implementation batch on a worktree that is behind the integration tip, derive the merge-base (`git merge-base HEAD origin/main`) and count main commits per candidate file since that base. A defect in a file main has rewritten belongs to main's tree, no matter how high it scores — record it as supporting evidence for main's unit instead of duplicating it. Severity ranks the work; merge-conflict exposure decides *where* it lands.

**Prevention hook**: every prioritization doc on a non-tip worktree opens with the per-file main-commit table (this cycle's: `docs/prioritization/2026-09-22-cycle-3-batch.md`) and states the exclusion rule explicitly so a severity-maximizer can't "rescue" a conflicted unit back into the batch.

## L30 — SQLite connection pragmas split by persistence: file-property vs per-connection

`journal_mode` is a **database-file property** — set once, persists in the file, safe to cache per path. `busy_timeout` and `journal_size_limit` are **per-connection** — a new connection starts without them. The U82 port initially applied `journal_size_limit` only in the once-per-path WAL setup; the first connection looked hardened while every later one silently ran unbounded. The bug was caught only because the batch's own test asserted the pragma on a *second* connection.

**Rule**: when porting a connection-hardening recipe, classify every pragma by persistence before writing `_connect`. File-property pragmas: once per path, guarded by a lock and cache. Per-connection pragmas: applied in the connection constructor, unconditionally, every time.

**Prevention hook**: any connection-layer hardening unit ships a test that opens a **second** connection to the same file and asserts each pragma there (this cycle: `test_u82_connection_sets_busy_timeout_and_journal_limits`). First-connection-only assertions enshrine the bug (cf. L17).

## L31 — `except (OSError, json.JSONDecodeError)` is never enough around `read_text()` + `json.loads()`

`UnicodeDecodeError` subclasses **neither** — it is a `ValueError` sibling of `JSONDecodeError`. This is now the repo's third recurrence of the same trap: the legacy backfill gate (pre-U76 era, `backfill.py:525`), the restore-drill manifest/state readers (fixed this cycle), and `guarded_apply`'s own rollback readers (still open, registered as follow-up). Undecodable bytes crash a "guarded" reader with a raw traceback every time.

**Rule**: around `Path.read_text()`/`open(...).read()` feeding `json.loads()`, catch `ValueError` (covers both decode and JSON errors) or name `UnicodeDecodeError` explicitly — never the two-name tuple alone. OSError covers the rest.

**Prevention hook**: (a) every JSON-read site ships an undecodable-bytes fixture (this cycle: `test_run_restore_drill_reports_undecodable_manifest_cleanly`, `test_evaluate_restore_drill_gate_blocks_undecodable_state_when_required`); (b) each assessment greps the tree for `OSError, json.JSONDecodeError` and treats every hit as a finding until shown safe.

## L32 — Manifest fields that name filesystem paths are untrusted input; readers inherit the writer's trust discipline

Rollback validated its manifest-named paths (cycle-1 U3/N1); the restore drill read the *same manifest format* without any validation — a tampered manifest could point the "non-destructive" drill's readers at arbitrary files. The asymmetry, not the missing check in isolation, was the defect. U83 closed it by routing the drill's `backup_path` fields through the same `_resolve_within` containment, refusing with the **same verbatim string** (`unsafe-backup-path`) rollback uses.

**Rule**: wherever a serialization format carries paths, every consumer — read-only ones included — validates those paths against the same containment root with the same refusal vocabulary. Shared refusal strings make the class greppable and auditable; divergent ones (or warn-vs-fail drift) recreate the asymmetry one refactor later.

**Prevention hook**: when a format gains a path-bearing field, the change unit lists **all** readers of that format (grep the format's magic strings), and each reader's test suite gains one tampered-path fixture. A reader that cannot show the fixture doesn't ship.

## L33 — Contention tests must be wide-margin by design; prove both directions

The U45 lock-bounded test is marginal-by-design (holder releases at 10s, busy window 5s, assert bound 15.0s vs 15.11s observed worst case) and is the repo's standing flake source (#5350). This cycle's U82 holder test was built to the opposite spec: a holder that auto-releases ~1s past **one** busy window, an acceptance band spanning several windows (5.0s ≤ elapsed < 12.0s), and the pre-fix behavior proven first (the raw code raises `OperationalError` at the ~5s default timeout — the test discriminates fixed from broken).

**Rule**: concurrency/lock tests state their window arithmetic (holder duration vs busy timeout vs retry ladder) in the test docstring, hold margins of at least one full window on each side of the expected landing, and include or cite a both-directions proof (fails on pre-fix code, passes on fixed — L18 applied to concurrency). A contention test whose bound sits within normal scheduler jitter is a future CI leg's flake, not a guard.

**Prevention hook**: reviewing a lock test = checking three numbers (holder release point, busy window, bound) before reading the assertions. U56's queued widening of the U45 bound remains the cleanup path for the legacy instance.

## L34 — Check import direction before routing a fix through another module's helper

`guarded_apply` imports `restore_drill` at module top (it records drill state after applies). A top-level `from .guarded_apply import _resolve_within` inside `restore_drill` therefore breaks package init — discovered as 16 collection errors. The fix is a call-time import at the two validation sites, with a comment naming the direction of the top-level dependency.

**Rule**: before adding a cross-module import in a hardening change, draw the existing import edges. If the target already imports you top-level, import it lazily at call time (with a comment stating why) or invert the dependency by extracting a leaf module. The stewardship contract should carry the constraint: "surface X may depend on surface Y only lazily."

**Prevention hook**: `python -c "import <package>"` after every multi-hunk edit batch — a cycle-edge breaks at import, not at test time, so the cheapest detection is the cheapest command. (This cycle's break surfaced at collection; the next one shouldn't have to.)

## L35 — Multi-hunk edits demand an immediate compile gate; a silent syntax error costs a full suite run to find

One edit in the U82 batch embedded a literal `\n` (two characters) into `review_queue.py` — a valid file write, invisible in the edit tool's success message, and detected only when the full suite died at collection. The two-stage diagnosis (16 → 10 errors) burned a full pytest cycle.

**Rule**: after each edit batch touching executable code, run `python -m py_compile <files>` (or import the package) *before* any test run. The compile gate costs ~0.1s; the suite costs ~40s.

**Prevention hook**: the implement-phase checklist gets an explicit step between "apply edits" and "run suite": compile gate, then targeted import, then suite.

## L36 — Baseline claims must name the binary and environment they were measured on

"Ruff flat at 12" was measured on 0.15.10 — the **only** ruff binary that exists in the conductor run-worktree environment (the project venv has none; the 0.16.7 PATH binary from earlier sessions lives in a different environment context, #5442). The claim is true and verifiable *here* and unreproducible *there*. Same class: "293 passed" depends on the interpreter (both 3.11/pytest 9.1.1 and the project venv/pytest 8.x happened to agree this cycle — that agreement is evidence, not a guarantee).

**Rule**: every lint/test baseline cited in a phase result or doc carries (binary, version, environment) — e.g. "ruff 0.15.10 (PATH, run-worktree env), full tree, 12 errors". Two environments with different binaries never compare counts directly; the comparison happens binary-to-binary within one environment.

**Prevention hook**: validation evidence records include the `command` verbatim (interpreter path included) precisely so the fold gate and reviewers can see which arm produced the number. CI pins its tool versions (U56) for the same reason.

---

### Craft rules for the next implement batch (this worktree line)

- Targeted + full validation both run on two interpreters when available (PATH python and project venv) — agreement is cheap regression insurance; disagreement is a finding.
- Wide-margin holder tests replace marginal ones as they're touched; do not port marginal bounds into new tests (L33).
- Undecodable fixtures accompany every JSON reader (L31) and tampered-path fixtures every path-bearing manifest reader (L32).
- Second-connection pragma assertions accompany any connection-layer change (L30).
- Compile gate between edits and suite (L35).

### Follow-ups registered (not unitized here)

- `guarded_apply` rollback readers' `UnicodeDecodeError` gap (L31's remaining instance) — belongs on main's tree, where `guarded_apply` was reuse-only by contract this cycle.
- `_check_evidence_refs` opens the manifest-named evidence DB path without containment (read-only surface; same L32 class, lower stakes).
- Pre-existing `F401` unused `pytest` import in `tests/test_restore_drill.py:5` — carried deliberately to keep the batch diff surgical; fold into the next lint-hygiene unit (U56 line).
