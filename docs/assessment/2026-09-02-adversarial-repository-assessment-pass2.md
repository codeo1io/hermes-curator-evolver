# Adversarial Repository Assessment — hermes-curator-evolver (pass 2)

- **Date:** 2026-09-02
- **Run (assessment):** 682bd7e431e34f7b9efc0c881cde253a / attempt b183995208f14babb5cae8751b3fb94a
- **Review run:** ce-code-review / RUN_ID 20260902-074026-de593d58 (`/tmp/compound-engineering-1000/ce-code-review/20260902-074026-de593d58`)
- **Tree reviewed:** branch `main`, HEAD 45328db **plus 11 uncommitted modified files** (auto_evolve.py, backfill.py, candidates.py, cli.py, guarded_apply.py, storage.py + 5 test files; 833 insertions — the cycle-1 remediation for prior U1–U4/F1/F2/F5 items)
- **Baseline at review time:** `python -m pytest tests` → 174 passed; `ruff check .` → 65 errors (46 fixable)
- **Mode:** full adversarial assessment, report-only. No fixes applied, nothing committed or pushed.

## Methodology disclosure

Routed to **ce-code-review** via the compound-engineering router (no ce-assess skill exists; ce-code-review is the narrowest match for an evidence-first adversarial assessment). The pi harness exposes **no subagent primitive**, so the fast pass and the persona passes (correctness, security, reliability, performance, maintainability) were executed **in-thread by the primary reviewer model with sequential persona framing — they are not independent reviewers, and no finding below claims independent corroboration**. The cross-model adversarial peer was skipped as sanctioned (host model family not discernible). All findings carry fresh file:line evidence from the current tree; the two headline defects were **reproduced empirically** (see notes).

## Verified remediation (current diff) — regression-checked, OK

The uncommitted cycle-1 changes were read in full and re-tested:

- `_strip_nul_bytes` in storage (NUL + escaped `\x00` forms) — applied consistently to `_compact` and `_json_dumps`; skill validators can no longer be poisoned by recorded NULs.
- `_is_tool_failure` structured-first rework in candidates.py (F2): `success:true` + exit 0 short-circuits to False — verified live against keyword-bearing success text.
- `_block_shell_spans` only counts standalone command lines (F5) — prose backticks no longer fake workflow evidence.
- State-DB backfill now has per-session exception boundaries + `sessions_failed` counters; restore-drill gate wiring (`record_apply_in_state` in guarded_apply.py:358 → `evaluate_restore_drill_gate`) is correctly chained.
- `_build_verify_env` passes only PATH/HOME/TMPDIR/TERM/LANG + `LC_*` + explicit `HERMES_CURATOR_*` to verify subprocesses — good secret-hygiene fix.

174/174 tests pass with these changes and no regression was found in them.

## Findings — current (introduced by or newly binding on this diff)

| # | Sev | Location | Finding |
|---|-----|----------|---------|
| C1 | P2 | `hermes_curator_evolver/cli.py:786` | `rollback` only constrains the manifest target when `--skills-dir` is passed; `rollback_guarded_patch` (guarded_apply.py:499) skips the root check entirely when `allowed_target_roots is None`. The function's own docstring (guarded_apply.py:486) promises "a tampered manifest must not turn rollback into an arbitrary-file overwrite primitive" — by CLI default it still can be. Fall back to the default skills dir, or require an explicit opt-in. |
| C2 | P2 | `hermes_curator_evolver/semantic.py:246` | Reranker reranks the already-truncated top-`limit` embedding slice, so `--rerank-candidates` can only permute those N — it can never promote a skill the embedder ranked N+1. Oversample (e.g. 5×limit) before rerank, then truncate. |
| C3 | P3 | `hermes_curator_evolver/review_queue.py:178` | `update_status` is dead surface: no CLI subcommand moves candidates pending→accepted/rejected, yet `candidates-list --status accepted|rejected` exists. The human-review loop the queue exists for requires hand-written sqlite. Owner: human (workflow decision). |

## Findings — pre-existing, confirmed still open in the current tree

| # | Sev | Location | Finding (evidence) |
|---|-----|----------|--------------------|
| P1 | **P1** | `auto_evolve.py:386` | **re.sub replacement injection (reproduced).** `_apply_managed_block` builds the replacement string from evidence previews (attacker/web-influenced tool results). A block containing `\1` or `\g<name>` makes `re.sub` raise (`IndexError: unknown group name` — reproduced in a sandbox). With no per-candidate try/except (P5) the entire auto-run pass crashes. Fix: `pattern.sub(lambda _: block, ...)` or escape backslashes. |
| P2 | **P2** | `storage.py:127` | **Error classifier false-positives (reproduced).** `_looks_like_error('3 passed, no errors found')` → `True` (substring marker `"error"`), while the fixed `candidates._is_tool_failure` returns `False` for the same text and for `{"success": true, ...}`. `is_error` feeds `error_events`, which gate auto-evolve thresholds and replay-benchmark mining — clean test logs inflate the core decision metric. Consolidate on one structured-first classifier. |
| P3 | **P2** | `cli.py:803` | `--max-reference-files 0` coerced to 5 by `int(x or 5)`, contradicting the help text "(0 disables pruning)". Via the API path (`_bounded(..., minimum=0)`, auto_evolve.py:838) keep=0 reaches `prune_auto_reference_files` and deletes **all** auto references — including the file the same pass just wrote and linked (auto_evolve.py:1052-1066). |
| P4 | **P2** | `storage.py:154` | `sqlite3.connect(path)` with no `timeout`, WAL, or `busy_timeout`; hooks open a fresh store per event (hooks.py:14/31/52) while the systemd timer runs concurrently → `database is locked` after the default 5 s. Also every `with self.connect() as conn:` is a transaction context, **not** a close — connections are GC-reclaimed (same in review_queue.py:66, one per enqueued candidate). |
| P5 | **P2** | `auto_evolve.py:1040` | No per-candidate try/except in `run_auto_evolve` (only 3 `try:` in the whole file, none in the loop): one raising candidate aborts the pass **after earlier candidates were already applied**, losing the result JSON. Compounds P1. |
| P6 | **P2** | `auto_evolve.py:1052` | Support files are written **after** `apply_guarded_patch` verified only the SKILL.md; `write_text` results unchecked; manifest registration is post-hoc. A partial failure leaves an applied SKILL.md referencing missing files. |
| P7 | **P2** | `auto_evolve.py:1386` | `OnCalendar={on_calendar}` written verbatim from user `--schedule`, and `_quote_systemd_arg` (auto_evolve.py:190) doesn't reject newlines — a newline inside any ExecStart arg ends the unit line and injects additional directives (e.g. `ExecStartPost=`) into the service. Local self-config footgun (values are operator CLI args), but bootstrap/install-auto then enable+start the units silently. |
| P8 | **P2** | `backfill.py:435` | Legacy `session_*.json` path did **not** receive the per-session boundary the state path just got: `except (OSError, json.JSONDecodeError)` misses `UnicodeDecodeError`, and any exception inside `_import_session_data` (e.g. P4's lock error) aborts the whole backfill. |
| P9 | **P2** | `auto_evolve.py:383` | Marker handling: a stray `<!-- curator-evolver:auto:start -->` (or a pasted duplicate pair) makes `_apply_managed_block` append a second block; `skill_validate` then fails every later staged verify ("multiple/unbalanced auto blocks") — the skill is locked out of auto-evolution until hand-edited. |
| P10 | P3 | `cli.py:701` | Missing/invalid `--proposal-file`, `--skill-file`, `--input-jsonl`, `--source/--target` surface as raw tracebacks. |
| P11 | P3 | `storage.py:280` | `summary()` computes `cutoff_iso(days)` 3× (lines 280/299/303) and issues 4 queries per call; marker scan is per-event uncompiled-substring work. |
| P12 | P3 | `skill_sources.py:67` | A custom `--skills-dir` not literally named `skills` falls back to the real Hermes home, so every skill classifies `unknown`/not-writable → auto-apply silently disabled with no warning. |
| P13 | P3 | `__init__.py:16` | Version drift: `__version__="0.8.0"` vs plugin.yaml/pyproject `"0.10.0"`. |
| P14 | P3 | `pyproject.toml` | 65 ruff errors (46 auto-fixable) with no lint gate in CI/pre-commit. |

**Prior assessment cross-check:** H1→P1 ✓ still open · H2→P3 ✓ · H3→P7 ✓ · H4→P4 ✓ · M6→P9 ✓ · M7→P6 ✓ · M9→P11 ✓ · M12→P5 ✓. M8 (frontmatter-name vs dir-name skill identity) persists structurally (`_skill_name_from_text` vs semantic/audit dir-name use) but has bounded effect under provenance checks — tracked as residual risk.

## Residual risks (accepted-for-now, from reviewer returns)

1. Backfill fetches messages for every state session before the caller applies the date cutoff (large histories over-scan).
2. Timestamp-less session rows sort as "now" and can displace recent sessions under `--limit` (new code).
3. Two error classifiers (`storage._looks_like_error` vs `candidates._is_tool_failure`) will drift again if not consolidated.
4. `restore-drill-state.json` read-modify-write is unlocked / non-atomic; failure mode degrades safe (gate blocks under `require`).
5. `hermes_chat_backend` uses argv-list subprocess (shell-safe); model-drafted text flows only into dry-run proposals today.
6. `_run_verify` uses `shell=True` with operator-supplied verify commands (operator primitive; scheduler inherits installer's choice).
7. `skill_audit` stat() TOCTOU on support files can abort `audit-skills`.
8. Hooks create a new EvidenceStore per tool call (fine at human rates).
9. Prune ordering relies on filename lexical == recency (same-second ties undefined).

## Testing gaps (top items)

1. No test feeds backslash-group evidence text (`\1`, `\g<x>`) through `_apply_managed_block`/`run_auto_evolve`.
2. No storage-side test asserting `is_error=False` for keyword-bearing success strings (candidates.py has one; storage.py doesn't).
3. No `--max-reference-files 0` end-to-end test (CLI **and** config paths).
4. No concurrency test (hooks + timer writing the evidence DB).
5. No test for a corrupt legacy session mid-directory; no test for one candidate raising mid-loop; no support-file write-failure test.
6. No test that rerank can promote beyond the initial top-limit slice.
7. No newline-bearing `--schedule`/verify-arg rejection test; no CLI-default rollback escape test.
8. No lint gate (ruff baseline 65 can grow unnoticed); no version-consistency test.

## Verdict

The cycle-1 remediation in the working tree is real and regression-free (174/174), and the security posture of the new code is good (verify-env hygiene, source provenance, restore-drill chaining). But **all eight previously reported high/medium defects remain open**, and two of them are now empirically confirmed crash/decision-corruption primitives (re.sub injection; error-classifier false positives). Recommendation: land the current diff, then prioritize P1 → P2 → P3 in one focused cycle; P1 and P2(storage) are small, test-covered-able fixes with outsized reliability impact on the scheduler path.

*Report-only assessment. No code changed, nothing committed or pushed.*
