---
date: 2026-09-02
topic: hermes-curator-evolver-adversarial-repository-assessment
mode: repo-grounded
run: 673d15323b9c4580a0e2ed84fa8625fc
phase: assess
action: assess:assess
attempt: f44a056ccec043c0950be48743c25762
skill: ce-code-review methodology (routed via the compound-engineering router; no dedicated ce-assess skill is installed in this delegate environment)
---

# Adversarial repository assessment — pass 4

**Tree reviewed:** `main` @ `45328db` plus the 11 uncommitted cycle-1 remediation files
(833 insertions across `auto_evolve.py`, `backfill.py`, `candidates.py`, `cli.py`,
`guarded_apply.py`, `storage.py` and five test files). No source file has changed since
pass 3 reviewed the same tree; **all 12 reproducers below were executed fresh against
that tree this attempt** (script:
`/home/agent/.hermes/conductor-runs/673d15323b9c4580a0e2ed84fa8625fc-assess/repro-adversarial-findings-pass4.sh`).

**Fresh baselines:** `python -m pytest -q` → 174 passed (17 files). `ruff check .` →
65 errors / 46 fixable — **~19 of them now sit inside the six remediation files**.

**Focus of this pass.** Passes 1–3 reviewed the committed tree thoroughly. What is *new*
in the repository since the first assessment is the uncommitted cycle-1 remediation diff
itself, so this pass put its adversarial weight there (new rollback deletion loop, new
backfill collection/sort, new reference pruning, new NUL sanitizer, new classifier
rework, new verify-env allowlist) and re-derived every carried headline defect with a
live probe rather than by reading the old reports.

## Methodology disclosure

Routed to **ce-code-review** (narrowest match; no `ce-assess` skill exists). The pi
harness exposes no subagent primitive, so the persona lenses ran in-thread; **no finding
claims independent corroboration**. Report-only: nothing was applied, committed, or
pushed. Every finding carries file/line evidence from the current tree; the twelve
headline defects were reproduced empirically this attempt.

## Fresh empirical reproductions (this attempt)

| ID | Result |
|----|--------|
| N1 | Tampered manifest `support_files:[{path:"SKILL.md", sha:<pre-apply sha>}]` → rollback returns `removed:['SKILL.md']` and **the skill file is gone from disk** — even with `allowed_target_roots` supplied |
| N2 | `--limit 2` against an oldest-first `search_sessions` → inspected `['s1','s0']` (200/300 days old); the newest session (10 days) is never read; 3 timestamp-less rows displace every real session under `--limit 3` |
| N3 | `days=30` over 5 sessions (1 in window) → **5 transcripts fetched** (pre-remediation interleave: 2). `bootstrap` calls `backfill_sessions(limit=None)` |
| N4 | `prune_auto_reference_files(skill_dir, "demo", keep=0)` deletes exactly the reference path this pass generated; the applied SKILL.md keeps linking to it |
| N5 | `storage._compact({"a": "x\x00y"})` → `'{"a": "x\\u0000y"}'` (escape survives); `_compact("use printf '\\x00' to emit a NUL")` → `"use printf '' to emit a NUL"` |
| N6 | Proposal claiming `grounding_event_count: 999` against a report with 1 event → `verify_proposal` **passes with zero failures**; whole-file replacement action passes the destructive scan; `error_events`-only grounding passes |
| P1 | `_apply_managed_block` with a `\1`-bearing preview → `re.error: invalid group reference 1` |
| P2 | `_looks_like_error('3 passed, no errors found')` → `True`; the same words inside a dict payload → `False` |
| C2 | CLI-default rollback with `target_path` rewritten to `/tmp/.../victim.txt` → `rolled_back: True`, victim overwritten with backup content |
| P3 | `parse_args(['auto-run','--max-reference-files','0'])` → `int(x or 5)` → **5** (help: "0 disables pruning") |
| P4 | Concurrent hook-style write while a writer txn is open → `OperationalError: database is locked` |
| P7 | `_quote_systemd_arg("daily\nExecStartPost=/tmp/pwned.sh")` → `'"daily\nExecStartPost=/tmp/pwned.sh"'` — newline survives quoting |

## Findings — new this pass (9), all in or triggered by the cycle-1 remediation diff

| # | Sev | Location | Finding |
|---|-----|----------|---------|
| N1 | **P2** | `guarded_apply.py:431` | `_rollback_support_files` deletes any live file under the target's directory whose sha256 matches a manifest-recorded value — including **the restored `SKILL.md` itself** (`path:"SKILL.md"`) and hand-written siblings. The sha is attacker-controlled in a tampered manifest, so the new loop widens the tampered-manifest primitive from arbitrary *overwrite* to arbitrary *delete-inside-skill-dir*, and it fires even when `allowed_target_roots` is passed. Fix: exclude the target path explicitly and require a `created_by_apply` marker recorded at registration time. |
| N2 | **P2** | `backfill.py:186` | The U4 fix removed the ordering assumption only for the unlimited case. Rows are still *collected* in storage order and capped at `limit` **before** the client-side sort, so `--limit` plus any non-newest-first `search_sessions` inspects the **oldest** sessions while the CLI help promises "Maximum number of newest sessions to inspect" (`cli.py:386`). Rows with no parseable timestamp sort as `datetime.now()` (newest), so stale timestamp-less rows displace genuinely recent sessions under any `--limit`. Fix: page without capping (or filter by cutoff during collection), sort, then take `limit`. |
| N3 | **P2** | `backfill.py:186` | Performance regression: every session row is collected and **every session's transcript is fetched before the caller applies the `days` cutoff** (caller now `continue`s where it used to `break`). `backfill-sessions --days 30` on a DB with months of history now reads the entire transcript set; `_run_bootstrap` (`cli.py:497`) passes `limit=None`, so the one-command bootstrap always does a full-history transcript read. Fix: apply the cutoff inside the iterator before `get_messages`, and stop once the sorted stream passes the cutoff. |
| N4 | P3 | `auto_evolve.py:1061` | `prune_auto_reference_files` runs immediately after this pass's own reference file is written and registered (`:1054-1060`). With `max_reference_files=0` (allowed by `_bounded(..., minimum=0)` at `:838`; help says "0 disables pruning"), the file the same pass just wrote is deleted while the already-applied, already-verified SKILL.md links to it, and the manifest keeps a snapshot of a file that no longer exists. Fix: exclude the current pass's reference from pruning, or treat `keep<=0` as "no pruning". |
| N5 | P3 | `storage.py:71` | `_strip_nul_bytes` runs *after* `json.dumps`, which has already escaped a real NUL to `\u0000` — so container-valued results still persist the escape (any consumer that JSON-decodes the preview re-materializes a real NUL byte in memory), while the literal-text branch silently rewrites legitimate evidence (`printf '\x00'` → `printf ''`). U1's contract holds only for plain-string results. |
| N6 | P3 | `verifier.py:19` | The gate that authorizes proposals toward apply never cross-checks the claimed `grounding_event_count` against the report (999 vs 1 passes); `_non_destructive` token-scans only `kind`+`description`, so an action whose payload replaces the whole file passes; grounding can be satisfied by `error_events` alone — the same counter the P2 classifier inflates with successful outputs. This is roadmap U7's promised cross-check, still unimplemented. |
| N7 | P3 | `cli.py:834` | The new `sessions_failed` / `last_session_error` accounting is never printed in the human-readable backfill summary (only `files_failed`), so silently dropped transcripts are invisible without `--format json`. |
| N8 | P3 | `cli.py:238` | Neither new flag is documented anywhere (`--max-reference-files`, `rollback --skills-dir`; grep: 0 hits across README and docs/*.md), and README:346 still teaches the rollback form whose default C2 shows is unsafe. |
| N9 | P3 | `hermes_curator_evolver/backfill.py` | The remediation itself grew the lint baseline: ~19 of the 65 ruff diagnostics are now in the six modified files (backfill 11, guarded_apply 6, candidates 6, storage 4, auto_evolve 4, cli 2), and CI still has no lint step to notice. |

## Findings — carried, re-derived against the current tree this attempt (18)

| # | Sev | Location | Fresh evidence |
|---|-----|----------|----------------|
| P1 | **P1** | `auto_evolve.py:386` | `pattern.sub(block, ...)` with evidence-derived block → `re.error: invalid group reference 1`; with no per-candidate guard (P5) the whole auto-run dies. Fix: `pattern.sub(lambda _: block, ...)`. |
| P2 | **P2** | `storage.py:113` | `is_error('3 passed, no errors found')` → 1, feeding `error_events` (`:289/:307/:318`) which gate auto-evolve thresholds. New this pass: the fallback is *also* internally inconsistent — dict payloads bypass the keyword scan while plain strings do not. |
| P3 | **P2** | `cli.py:803` | `int(values.get("max_reference_files") or 5)` rewrites an explicit 0 to 5; API path `keep=0` reaches the pruner (see N4). |
| P4 | **P2** | `storage.py:154` | `database is locked` reproduced under a concurrent writer; no timeout/WAL/busy_timeout, hooks open a store per event (`hooks.py:14`), `with conn:` never closes. |
| P5 | **P2** | `auto_evolve.py:1022` | Candidate loop body (apply → support write → register → prune) has no try/except; one raising candidate aborts the pass after earlier applies and loses the result JSON. |
| P6 | **P2** | `auto_evolve.py:1054` | Support files written after guarded apply+verify with unchecked `write_text`; unverified content lands in the skills tree; partial failure leaves SKILL.md referencing missing files. |
| P7 | **P2** | `auto_evolve.py:1386` | `OnCalendar={schedule}` verbatim; `_quote_systemd_arg` (`:196-202`) does not reject newlines, so a newline-bearing arg ends the unit line and injects further directives; bootstrap then enables+starts the unit. |
| P8 | **P2** | `backfill.py:435` | Legacy path still `except (OSError, json.JSONDecodeError)` — misses `UnicodeDecodeError` — and has no per-session boundary, unlike the state path. |
| P9 | **P2** | `auto_evolve.py:383` | Stray/duplicate managed-block markers → append → `skill_validate` "multiple/unbalanced auto blocks" (`skill_validate.py:78-82`) fails every later staged verify. |
| C1 | **P2** | `semantic.py:200` | Truncation to top-`limit` still precedes rerank pair construction (`:204-206`); the reranker can never promote beyond the embedder's first slice. |
| C2 | **P2** | `cli.py:771` | Reproduced end-to-end: without `--skills-dir`, `rollback_guarded_patch(..., allowed_target_roots=None)` overwrites an out-of-skills target; README:346 teaches this exact form (see also N1). |
| P10 | P3 | `cli.py` | `propose --skill demo --skill-file /nonexistent/nope.md` → raw `FileNotFoundError` traceback. |
| P11 | P3 | `storage.py:280` | `cutoff_iso(days)` recomputed at `:280/:299/:303` (also `:341/:370`); per-event uncompiled substring error scan. |
| P12 | P3 | `skill_sources.py:60` | Custom `--skills-dir` not literally named `skills` → every skill classifies unknown/not-writable → auto-apply silently disabled. |
| P13 | P3 | `__init__.py:11` | Version drift unchanged: package `0.8.0` vs plugin.yaml/pyproject `0.10.0` vs shipped SKILL.md `0.11.0` vs README roadmap `v0.14`. |
| P14 | P3 | `.github/workflows/ci.yaml` | CI is still pytest-only (3.11/3.12); 65 ruff errors grow unnoticed (N9). |
| C3 | P3 | `review_queue.py:173` | `update_status` still has no CLI caller; `candidates-list --status accepted/rejected` advertises filters nothing can produce. |
| P15 | P3 (advisory) | `cli.py:507` | `bootstrap` still grants unattended-write authority by default (`--proposal-only` is the opt-out; scheduler bakes `--apply-low-risk --approve-auto-apply`). Owner: human trust-boundary decision. |

## Verification of the remediation's own goals (regression check)

- ✅ **U1 (NUL)** — plain-string NUL bytes are stripped at both write paths; end-to-end
  test (`tests/test_backfill_sessions.py:267`) and storage test pass. Gap: container
  payloads keep the `\u0000` escape, and literal `\x00` text is mangled (N5).
- ✅ **U2 (classification)** — the `"cap"` substring rule is gone; structured-first
  classification covers `success`/`exit_code`; workflow detection now requires
  command-sequence lines. Gap: the keyword fallback still fires for plain strings and
  for JSON payloads without a `success` key (P2), and storage/candidates still use two
  different classifiers.
- ✅ **U3 (rollback)** — apply-created support files are now removed on rollback,
  edited ones are preserved, tampered backup paths and out-of-root targets are refused
  when roots are supplied. Gaps: the CLI default still passes no roots (C2), and the
  deletion loop is itself a new delete primitive (N1).
- ✅ **U4 (backfill ordering/failure isolation)** — per-session error boundary,
  counted failures, client-side sort, and ordering test all present. Gaps: `--limit`
  membership is still storage-order-dependent and timestamp-less rows sort newest (N2);
  transcripts are now over-fetched (N3).
- ✅ **U5 (byte caps)** — guarded_apply now measures bytes (verified in the diff).
- ✅ **U6 (bootstrap defaults)** — `bootstrap --enable` is now opt-in (help + code
  verified); the apply authority default (P15) remains the open product decision.
- ⚠️ **U7 (hygiene batch)** — verifier cross-check, version single-sourcing, WAL,
  lint/type/coverage gates: not in this diff (N6, P4, P13, P14).

## Testing gaps (fresh)

1. No test drives `--limit` with a non-newest-first fake SessionDB (the U4 test uses 3
   sessions in one page, uncapped) — N2 is invisible to the suite.
2. No test asserts the number of `get_messages` calls, so the transcript over-fetch
   (N3) cannot fail a test.
3. No test puts a `support_files` entry pointing at `SKILL.md` or a hand-written
   sibling through rollback (N1).
4. No test runs `prune_auto_reference_files` with the same pass's reference present
   under `keep=0` through the auto-run path (N4).
5. No test asserts `verify_proposal` rejects an inflated `grounding_event_count` (N6).
6. Carried gaps from pass 3 remain: no backslash-group evidence test, no
   storage-side success-string `is_error` test, no rerank-promotion test, no
   CLI-default rollback test, no concurrency test, no version-consistency test, no lint
   gate.

## Verdict

**Not phase-clean.** The cycle-1 remediation achieved its declared goals and the suite
is green (174/174), but this pass found **nine new defects introduced by or exposed by
that remediation** — two of them P2 (a new arbitrary-delete primitive inside rollback;
`--limit` inspecting the wrong sessions) and one P2 performance regression (full-history
transcript reads on every backfill, including bootstrap). The four P1/P2 headline
defects from earlier passes (re.sub injection, error-classifier false positives,
rollback-default escape, sqlite locking) remain open and were re-reproduced this
attempt. Recommended order for the next fixing phase: **P1 + N1 (both tamper/crash
primitives on the write path), then N2+N3 (backfill correctness/perf), then the P2
reliability cluster (P5/P6/P7/P8/P9), then N4–N9 and the P3 tail.**

*Report-only assessment: no code changed, nothing committed or pushed.*
