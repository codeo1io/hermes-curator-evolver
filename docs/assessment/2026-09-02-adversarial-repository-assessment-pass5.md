---
date: 2026-09-02
topic: hermes-curator-evolver-adversarial-repository-assessment
mode: repo-grounded
run: 2cc5b112c9694bfaa4a47645f139983a
phase: assess
action: assess:assess
attempt: b7800038a84c4198bcf2d7be22cc61f3
skill: ce-code-review methodology via the compound-engineering router (no dedicated ce-assess skill installed; ce-code-review is the narrowest match for an adversarial repo assessment)
review-run: /tmp/compound-engineering-1000/ce-code-review/20260902-111048-85ee6539
---

# Adversarial repository assessment — pass 5

**Tree reviewed:** `main` @ `45328db` plus the uncommitted remediation diff (13 files,
1641 insertions / 91 deletions — the cycle-1 remediation **plus the cycle-4 batch
CU-Q..CU-V**, which landed after pass 4: lambda replacement in `_apply_managed_block`,
sqlite WAL/busy_timeout/retry, value-layer NUL sanitization, tamper-resistant +
atomic rollback, explicit-zero flag parsing, and the unified error classifier).
Cycles 2–3 were prioritization/ideation only — `docs/implementation/` holds exactly
one file (cycle-4). Source files verified changed since pass 4 via `find -newer`.

**Fresh baselines this attempt:** `python -m pytest` → **184 passed** (17 files).
`ruff check .` → **64 errors / 45 fixable** (pass-4 baseline 65/46, cycle-4 reported
63/45 — the count moved again and nothing gates it). `data/evidence.sqlite` correctly
gitignored.

**Focus of this pass.** The tree *changed* since pass 4 (cycle-4 landed), so the
adversarial weight went onto the six new change units, then every carried finding was
re-derived fresh (reproducer script:
`/home/agent/.hermes/conductor-runs/2cc5b112c9694bfaa4a47645f139983a-assess/repro-pass5.py`,
JSON results beside it). 22 probes: 21 reproduced, 1 tested-and-cleared (R8 pagination
dedupe — could not construct a duplicate-yielding fake; dropped, not reported).

## Methodology disclosure

Routed via the compound-engineering router to **ce-code-review** (narrowest match).
Pi exposes no subagent primitive, so the persona lenses (correctness, security,
reliability, performance, maintainability, testing, docs/DX) ran in-thread — **no
finding claims independent corroboration**. Cross-model adversarial peer skipped:
host harness is pi with no `CLAUDECODE`/`CODEX_*`/`CURSOR_*` markers, so
`XHOST_FAMILY=unknown` cannot satisfy same-family exclusion (same sanctioned skip as
passes 2–4); no `.compound-engineering/` config exists to override. Report-only:
nothing applied, committed, or pushed.

## Fresh empirical reproductions (this attempt)

| ID | Result |
|----|--------|
| Q1 | `looks_like_error({"stdout":"ok","stderr":""})` → **True**; `{"returncode":1,"stdout":"boom"}` → **False**; `"0 failed, 12 passed"` → **True**; `"exit code 0"` → **True**; `{"code":1}`/`{"ok":False}` → **False** |
| N2 | oldest-first fake SessionDB + `limit=2` → inspected `['s1','s0']`; the newest session (10 days) never read |
| N2b | `[old1(400d), nt1, nt2, real_new(1d)]` + `limit=3` → inspected `['nt2','nt1','old1']`; `real_new` never read |
| N3 | 5 sessions, 1 inside `days=30` → **5/5 transcripts fetched**; caller now `continue`s where it used to `break` (`backfill.py:411`); `bootstrap` passes `limit=None` (`cli.py:527`) |
| N6 | `grounding_event_count: 999` vs report with 1 event → `verify_proposal` **passes, zero failures**; whole-file-replacement payload accepted |
| P7 | `_quote_systemd_arg("daily\nExecStartPost=/tmp/pwned.sh")` → `'"daily\nExecStartPost=/tmp/pwned.sh"'` (newline survives) |
| C1 | source order in `_semantic_candidates`: `candidates[: max(1, limit)]` (semantic.py:200) precedes `_predict_rerank` (semantic.py:206) |
| Q2 | `typing.get_type_hints(cli._explicit_int)` → **`NameError: name 'Any' is not defined`** |
| Q3 | target chmod 0o640 → after apply **0o664**, after rollback **0o664** (was 0o640; `shutil.copy2` used to preserve it) |
| Q4 | README:346's rollback form → `{"reason": "unrestricted-target"}` (documented command now errors) |
| P10 | `propose --skill-file /nonexistent/nope.md` → raw `FileNotFoundError` traceback |
| P9 | stray duplicate markers → `auto_block_count=2`, validate `ok=False` |
| P5/P6 | loop body `auto_evolve.py:1069-1090`: `support_path.write_text(content` present, `try:` absent |
| P8 | `except (OSError, json.JSONDecodeError)` still at `backfill.py:435`; per-session boundary only on the state path |
| N7 | human summary (`cli.py:858-868`) prints seen/imported/skipped/files_failed — **no `sessions_failed`/`last_session_error`** |
| Fix-verify | N1 ✅ tampered `support_files:[SKILL.md]` → skipped `target-file`, target restored intact; N4 ✅ `keep=0` prunes nothing, same-pass reference survives; N5 ✅ `_compact({"a":"x\x00y"})` → `{"a": "xy"}` and literal `printf '\x00'` survives; P2-baseline ✅ `"3 passed, no errors found"` → False; P3 ✅ explicit 0 honored; C2 ✅ bare rollback refused |
| N1r | residual: attacker who can also write inside the manifest dir (fake `support/` snapshot) still gets a sibling deleted — but a `rollback-safety/` copy now exists, so it is recoverable; requires ≥ manifest-dir write privilege |
| R8 | pagination-duplicate probe: **not reproducible** with a shifting-page fake — cleared, not reported |

## Findings — new this pass (8), all in or triggered by the cycle-4 batch

| # | Sev | Location | Finding |
|---|-----|----------|---------|
| Q1 | **P2** | `candidates.py:97-100,210-241` | The unified classifier (U28) is both over- and under-inclusive. **False positives:** the keyword pattern contains bare `stderr`, `failed`, `exceeded` and `exit\s+code\s+\d+` — so `{"stdout":"ok","stderr":""}` (the canonical successful-subprocess shape), `"0 failed, 12 passed"`, `"exit code 0"`, `"quota not exceeded"` all classify as errors unless the payload happens to carry `success`/`exit_code`. **False negatives:** the structured branch recognizes only `exit_code`/`error`/`exception`/`success` — `{"returncode":1}`, `{"code":1}`, `{"ok":False}`, `"aborted with status 2"` classify as successes. This is the same `is_error` column that feeds `error_events` cohorts gating auto-evolve thresholds (the exact blast radius U28 was built to close), reopened through a new mechanism. Fix: drop `stderr`/`failed` from the pattern or require non-zero context (`(?<!0 )failed`, `exit code [1-9]`), and teach the structured branch `returncode`/`code`/`status`/`ok`. |
| Q2 | P3 | `cli.py:466` | `_explicit_int(values: dict[str, Any], ...)` references `Any`, which cli.py never imports (F821). `from __future__ import annotations` hides it at runtime, but `typing.get_type_hints(cli._explicit_int)` raises `NameError` — any annotation-evaluating tooling (docs generators, runtime checkers, IDE strictness) breaks, and no lint gate exists to catch it (P14; ruff's default rule set flags it today: 1 of the 64). One-line fix: `from typing import Any`. |
| Q3 | P3 | `guarded_apply.py:41-67` | The new atomic writes (`_atomic_write_bytes/_atomic_copy` behind apply, verify-failed restore, and rollback restore) create the replacement file with the process umask instead of the target's mode: chmod 0o640 → 0o664 after apply **and** after rollback (reproduced). `shutil.copy2`, which they replaced, preserved mode. On shared/group-readable skills trees (or any setup where Hermes runs as a different user than the apply), a guarded apply silently changes readability; the restore path makes it permanent. Fix: `os.chmod(temp, stat.S_IMODE(path.stat().st_mode))` before `os.replace` when the target exists. |
| Q4 | P3 | `README.md:346` + `cli.py:205-217` | Docs regression from CU-T: README's rollback example (`rollback --manifest ...`, no `--skills-dir`) now refuses with `unrestricted-target` — the documented command errors until the user supplies a flag the README never mentions. `--allow-any-target`, `rollback --skills-dir`, and `--max-reference-files` have zero hits across README + `docs/*.md`. |
| Q5 | P3 | `guarded_apply.py:458-472` | `_snapshot_for_safety` writes the rollback-safety copy with plain `dest.write_bytes(...)` while every other manifest-adjacent write in the same change unit went atomic+fsync. A torn snapshot (no exception) silently becomes the "recoverable copy" the whole U35 fail-closed design leans on. Fix: route it through `_atomic_write_bytes`. |
| Q6 | P3 | `storage.py:78,244-263` | `record_*` now waits up to **~15.75 s per event** (3 × 5 s busy_timeout + 0.25/0.5 s backoff) under sustained write contention before the hook boundary swallows the failure. The disclosed design boundary covers only the *infinite* holder; ordinary contention (backfill import vs. hooks from several Hermes sessions) now blocks the session's post-tool hook for seconds where it previously failed fast. Fix: a hook-path-specific short budget (e.g. 1 attempt × 1 s) with the long budget reserved for CLI callers. |
| Q7 | P3 | `storage.py:265-277` | `_schema_ready` probes only `tool_events`. `executescript` commits per statement, so an interrupted first init can leave `tool_events` present but `turn_events`/`session_events` missing — the new short-circuit then skips `executescript` forever and every `record_turn`/`record_session_end` fails with "no such table". Fix: probe all three tables (or wrap the script in one transaction). |
| Q8 | P3 | `cli.py:466-484` + `auto_evolve.py:846` | The silent-value-rewrite class moved rather than disappeared: `_explicit_int` swallows garbage to the default (unreachable from the CLI, where `type=int` already rejects it, but reachable through the programmatic `values` path), and `_bounded` still silently clamps out-of-range explicit flags (`--max-reference-files 200` → 100, `--max-skills -1` → 1) with no warning or result echo. |

## Findings — carried, re-derived against the current tree this attempt (15)

| # | Sev | Location | Fresh evidence |
|---|-----|----------|----------------|
| N2 | **P2** | `backfill.py:186-227` | U4's client-side sort fixed *ordering* but not *membership*: rows are still collected in storage order and capped at `limit` **before** the sort (`limit=2` → `['s1','s0']`, newest never read), while `cli.py:392` still promises "Maximum number of **newest** sessions to inspect". Timestamp-less rows sort as `datetime.now()` (newest) and displace genuinely recent sessions (N2b). Fix: filter by cutoff during collection (also fixes N3), sort, then take `limit`. |
| N3 | **P2** | `backfill.py:217-227,408-412` | Every session's transcript is fetched by the iterator before the caller applies the `days` cutoff, and the caller now `continue`s where it used to `break` — a full-history transcript read on every backfill; `_run_bootstrap` passes `limit=None` (`cli.py:527`), so the one-command bootstrap always reads the entire DB's transcripts regardless of `--days`. Fix: stop once the sorted newest-first stream passes the cutoff. |
| P7 | **P2** | `auto_evolve.py:1394,190-193` | `OnCalendar={schedule}` verbatim; `_systemd_quote` escapes only `\` and `"` — a newline-bearing `--schedule`/ExecStart arg still ends the unit line and injects further directives; bootstrap then enables + starts the unit. Reproduced verbatim this attempt. |
| C1 | **P2** | `semantic.py:200` | Truncation to the embedder's top-`limit` still precedes rerank pair construction (`:206`); `--rerank-candidates` can never promote a skill the embedder ranked beyond its first slice. Source order re-verified this attempt. |
| P5 | **P2** | `auto_evolve.py:1069-1090` | Still no per-candidate try/except around apply → support write → register → prune; one raising candidate aborts the pass after earlier applies and loses the result JSON (compounds any guarded-apply error). |
| P6 | **P2** | `auto_evolve.py:1073-1076` | Support files still written with unchecked `write_text` after apply+verify; unverified content lands in the skills tree, and a partial failure leaves SKILL.md referencing missing files. |
| P8 | **P2** | `backfill.py:435` | Legacy `session_*.json` path still `except (OSError, json.JSONDecodeError)` (misses `UnicodeDecodeError`) with no per-session boundary, unlike the state path. |
| P9 | **P2** | `auto_evolve.py:383-393` | Stray/duplicate managed-block markers still produce a two-block file; `skill_validate` then reports `auto_block_count=2` and fails every later staged verify until hand-edited (reproduced). |
| N6 | P3 | `verifier.py:24-27,35-39` | The gate still never cross-checks claimed `grounding_event_count` against the report (999 vs 1 passes); `_non_destructive` token-scans only `kind`+`description` so a whole-file replacement payload passes; `error_events` alone still satisfies grounding — and Q1 now inflates that very counter. |
| P10 | P3 | `cli.py` (propose/apply paths) | Bad `--skill-file` path still surfaces as a raw `FileNotFoundError` traceback instead of an actionable error (reproduced). |
| N7 | P3 | `cli.py:858-868` | `sessions_failed`/`last_session_error` still never printed in the human-readable backfill summary — silently dropped transcripts stay invisible without `--format json`. |
| C3 | P3 | `review_queue.py:173` | `update_status` still has no caller anywhere; `candidates-list --status accepted/rejected` still advertises filters nothing can produce. |
| P12 | P3 | `skill_sources.py:59-60` | A custom `--skills-dir` not literally named `skills` still yields `unknown`/not-writable for every skill → auto-apply silently disabled, no warning. |
| P13 | P3 | `__init__.py:11` | Version drift unchanged and now worse against the roadmap: package `0.8.0` vs plugin.yaml/pyproject `0.10.0` vs shipped SKILL.md `0.11.0`; result `schema_version` still `"0.8"` (`auto_evolve.py:1092`). |
| P14 | P3 | `.github/workflows/ci.yaml` | CI remains pytest-only; the ruff baseline moved 65 → 63 (cycle-4 report) → **64 now** with nothing noticing, and this pass's Q2 (F821) is exactly the class a lint step would have caught. |
| P15 | P3 (advisory, owner: human) | `cli.py:507-530` | `bootstrap` still grants unattended-write authority by default (`--proposal-only` is the opt-out; the scheduler command bakes `--apply-low-risk --approve-auto-apply`). Mitigations are real (provenance gate, bounded blocks, staged verify, drill gate, now containment-refusing rollback); remains an explicit human trust-boundary decision. |

## Verification of the cycle-4 batch's own goals (regression check)

- ✅ **U15 (P1 re.sub injection)** — `pattern.sub(lambda _match: block, ...)` at
  `auto_evolve.py:391`; a lambda replacement is never parsed for group references.
  Class closed.
- ✅ **U7a (sqlite locking, P4)** — WAL + busy_timeout + bounded retry + connection
  cache; the realistic-contention test passes. Gaps: hook-path worst case ~15.75 s
  (Q6) and the single-table schema probe (Q7).
- ✅ **U37 (NUL, N5)** — `_sanitize_nul` at the value layer; `{"a":"x\x00y"}` →
  `{"a": "xy"}`, literal `printf '\x00'` survives. Closed for every encoding.
- ✅ **U35 (N1/C2 rollback)** — target-identity refusal reproduced (tampered
  `support_files:[SKILL.md]` → skipped `target-file`, target restored), registration
  cross-check, fail-closed pre-removal snapshots, unrestricted rollback now explicit
  opt-in. Residuals: Q3 (mode loss), Q5 (non-atomic snapshot), and the
  manifest-dir-write residual (recovered via safety copy — acceptable).
- ✅ **U16 (N4/P3 explicit zero)** — `keep <= 0` disables pruning (same-pass
  reference survives, reproduced); `_explicit_int` honors explicit 0 end-to-end.
  Residual: Q8 silent clamping and the unreachable-from-CLI garbage branch.
- ⚠️ **U28 (P2 single classifier)** — one classifier now feeds both ingest and
  mining and the pass-4 headline string (`"3 passed, no errors found"`) classifies
  correctly — but Q1 reopens the defect through the keyword tail and the
  unrecognized structured shapes, at the same `error_events` blast radius.

## Testing gaps (fresh)

1. The new classifier tests cover only `exit_code`/`error`/`success` shapes — nothing
   asserts `{"stderr": ""}` is a success or `{"returncode": 1}` is a failure (Q1
   invisible to the suite).
2. No test asserts apply/rollback preserves the target's file mode (Q3).
3. No test calls `typing.get_type_hints` on CLI helpers, and no lint gate exists
   (Q2/P14 — ruff flags it today).
4. No test drives `--limit` with a non-newest-first or timestamp-less fake SessionDB
   (N2/N2b still invisible).
5. No test counts `get_messages` calls, so the transcript over-fetch (N3) cannot
   fail a test.
6. No test asserts `verify_proposal` rejects an inflated `grounding_event_count`
   (N6); no newline-bearing scheduler-arg rejection test (P7); no
   rerank-promotion-beyond-embedder-slice test (C1); no version-consistency test
   (P13); no hook-latency bound (Q6); no corrupt/partial-schema store test (Q7).

## Verdict

**Not phase-clean.** The cycle-4 batch landed cleanly (184/184 green, +10 tests) and
genuinely closed five of the seven corpus defects it targeted — including both
tamper/crash primitives on the write path (P1, N1, C2). But this pass found **eight
new defects in or exposed by that batch**, one of them P2: the unified error
classifier (Q1) misclassifies the most common subprocess success shape
(`{"stdout": …, "stderr": ""}`) as an error and misses `returncode`/`code`/`ok`
failures — the same `error_events` cohort corruption U28 was built to fix. Carried
P2s N2/N3 (backfill membership + full-history transcript reads), P7 (systemd newline
injection), C1 (rerank ceiling), P5/P6/P8/P9 remain open and were re-derived fresh.
**Recommended order for the next fixing phase: Q1 (classifier truth table + tests),
then N2+N3 together (cutoff during collection fixes both), then P7/C1, then the
reliability cluster (P5/P6/P8/P9), then Q2–Q8 and the P3 tail; add a lint gate
(P14/Q2) before the next batch grows the baseline again.**

*Report-only assessment: no code changed, nothing committed or pushed.*
