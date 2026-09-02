# Cycle-5 Maintenance Batch — Implementation Report

- **Run**: `2cc5b112c9694bfaa4a47645f139983a` · **Phase**: implement · **Attempt**: `09254dfc34094d6e9c7a71d14a2fcd20`
- **Date**: 2026-09-02 · **Skill**: ce-work (narrowest installed match for implementation + local verification; no subagent dispatch available in pi → all passes in-thread, disclosed)
- **Batch**: U43 + U45/U46 + U44 + U36 + U17 + U7-riders = change units **CU-W..CU-AB** per `docs/stewardship/2026-09-02-cycle-5-stewardship-request.md`, discharging B19 (U43), B20 (U45+U46), B21 (U44), B22 (U36), B17 (U17), B9 (U7-riders)
- **Base**: main @ `45328db`, single worktree (no conductor worktree was created); pre-existing uncommitted cycle-1 + cycle-4 batches (13 modified tracked files + untracked docs) preserved untouched and NOT folded into this batch — per KTD21 the commit gate covers all batches and was not issued in this phase. Nothing committed, pushed, or PRed (prohibited).

## Verification summary (all gates re-run fresh after the last edit)

| Gate | Baseline | Result |
|---|---|---|
| `python3 -m pytest` | 184 passed | **249 passed** (+65 new regression tests; zero pre-existing tests deleted) |
| `ruff check .` | 64 errors / 45 fixable | **64 errors / 48 fixable** (no count increase; F821 **eliminated**) |
| `ruff check --select F821 .` | 1 (`Any` @ `cli.py:466`) | **All checks passed** |
| `repro-pass5.py` corpus | 21/22 reproduced | **12 batch targets flipped to not-reproduced; 7 non-batch findings still reproduce** (N6, C1, P10, P9, P5/P6, P8, R7) |

Batch-target flips: **R1/Q1** (classifier corpus), **R2/Q3** (mode preserved apply+rollback), **R3/Q5** (atomic snapshot), **R4/Q4** (README rollback form works as documented), **R5/Q6** (hook-path stall window), **R6/Q7** (all-tables schema probe), **N2/N2b/N3** (trusted-order backfill), **N7** (failed sessions in human summary), **P7** (schedule/arg injection rejected), **R8 stays clear** (dedupe + bounded pagination). Expected-open per the prioritization doc: P5/P6, P8, P9, P10, N6, C1, R7.

## Implemented change units

### CU-W — U43: classifier truth table (Q1/R1; B19)
`hermes_curator_evolver/candidates.py`
- `_ERROR_KEYWORD_PATTERN` → `_FAILURE_KEYWORD_PATTERN`: nonzero `exit code|status N`, `exited/exiting with code|status N`, `exit=N`, `nonzero`, `(?<!0\s)failed`, `size cap|exceeded`, `traceback`, `not found`. Bare `stderr` keyword removed.
- New `_SUCCESS_COUNT_PATTERN` (`0 failed`, `no errors`, `nothing failed`, `no <word> failed`) — a success-bearing count phrase clears a keyword hit ("success: no tests failed" was the corpus miss; added a `no\s+(?:\w+\s+)?failed` arm for it).
- New `_EXIT_CODE_KEYS` (`exit_code`/`returncode`/`code`), `_STATUS_FAILURE_WORDS`, `_STATUS_SUCCESS_WORDS`.
- `_is_tool_failure` rewritten as a **structured-first truth table**: `is_error` → nonzero exit code → `error`/`exception` payload → `ok`/`success is False` → failure status word → zero-exit and success signals clear the keyword scan → keyword fallback (stringified JSON included). Zero exit with scary text is success; `ok: True` with `exit_code: 1` is failure.
- Regressions: `tests/test_candidates.py` — `test_u43_success_shapes_are_not_errors` (13 params), `test_u43_failure_shapes_are_errors` (14 params), `test_u43_zero_exit_status_is_explicit_success_even_with_scary_text`, `test_u43_stringified_structured_failure_is_caught`, `test_u43_list_of_results_is_error_iff_any_element_is`; `tests/test_storage.py` — `test_u43_keyword_bearing_success_strings_never_become_error_events`, `test_u43_structured_failure_shapes_become_error_events` (ingest agreement with the truth table — error_events is append-only, so misclassification is permanent).

### CU-X — U45+U46: warm single-flight writer + errno split, all-tables schema probe (Q6/Q7; B20)
`hermes_curator_evolver/storage.py`
- **U45**: module-level `_connection_lock` / `_connections` cache / `_path_locks`; `connect()` returns one cached warm connection per resolved path (single-flight: cache entry installed under lock, rolled back if pragmas fail); `check_same_thread=False` (all writes serialize on the per-path lock); new public `close()` per store + `_close_cached_connections` installed via `atexit`. Upstream recipe #101191 (merged) = law-grade.
- `_write_with_retry` serializes on `_path_lock(path)`; **errno split** per #101202 (recipe-grade): busy/locked still retry, every other `sqlite3.OperationalError` fails fast on attempt 1 with `sqlite_errorcode` logged.
- **Hook-path stall window**: `_WRITE_ATTEMPTS` 3 → **2** (comment documents the single-flight rationale: our own writers no longer contend, so the third window only ever waited out a 10–15 s external holder — not worth +5 s of gateway hook latency). `busy_timeout` stays 5000 (cycle-4 contract `>= 5000` preserved).
- **U46**: `_SCHEMA_TABLES` constant; `_schema_ready()` probes **all** of `tool_events`/`turn_events`/`session_events`; a crash mid-`executescript` after `tool_events` heals on the next store construction; `init_db()` rewritten with explicit `commit()` under the path lock.
- `hooks.py` `_store()` docstring updated (warm-connection layering note + upstream refs).
- Regressions: `test_u45_one_cached_connection_per_path_under_cold_burst`, `test_u45_hook_writes_are_bounded_under_one_external_holder` (wall-clock bound `< 15 s` vs the old ~15.75 s worst case), `test_u45_environment_error_fails_fast_without_retry_ladder` (exactly 1 call), `test_u46_interrupted_first_init_heals_on_next_store`, `test_u46_steady_state_schema_probe_is_cheap_and_stable`; cycle-4's `test_record_retries_through_held_write_lock` still green.

### CU-Y — U44: mode-preserving atomic writes + atomic snapshots (Q3/Q5; B21)
`hermes_curator_evolver/guarded_apply.py`
- New `_atomic_write_bytes(path, data, mode=None)`: temp file in the target's directory, `fsync`, **chmod to the existing target's permission bits (or explicit mode) before `os.replace`** — the apply write (`:368`) and rollback restore (`:394`) now preserve e.g. `0o640` instead of landing as `0o664`.
- `_atomic_write_text` / `_atomic_copy` take and propagate mode (copies default to the source's mode); `_snapshot_for_safety` routes through `_atomic_copy` → fsync + atomic + mode-preserving safety net (an interrupted snapshot leaves the complete copy or nothing, never a torn half-file).
- Regressions: `tests/test_guarded_apply.py` — `test_u44_atomic_write_preserves_existing_target_mode`, `test_u44_atomic_write_new_file_uses_explicit_mode`, `test_u44_apply_preserves_skill_file_permissions`, `test_u44_snapshot_is_atomic_and_mode_preserving`, `test_u44_no_stray_temp_files_after_writes`.

### CU-Z — U36: trusted-order backfill + cutoff-before-fetch + bounded bootstrap (N2/N2b/N3/N7; B22)
`hermes_curator_evolver/backfill.py`, `hermes_curator_evolver/cli.py`
- `_iter_state_sessions(session_db, limit, cutoff=None, stats=None)` rewritten: collects **metadata-only** pages (200/page), sorts **newest-first client-side by session time** (storage order is never trusted), applies the **cutoff before any transcript fetch** (the whole old tail is counted into `sessions_skipped_old` + `sessions_seen` in one step, `stats.get`-tolerant), then fetches transcripts for at most `limit` newest in-window rows. `--limit 2` now inspects the two genuinely newest sessions; a 1-in-window `--days 7` import fetches one transcript, not all history.
- **Bounded + idempotent against hostile pagination** (found live by the corpus): metadata collection capped at `max(limit, 10_000)` rows and deduped by session id across shifting pages — R8's infinite-tail fake previously spun forever; now terminates with zero duplicates.
- `cli.py`: bootstrap gains `--limit` (default **500**, `_backfill_limit()` helper; `0`/negative keeps the default — `limit=None` unbounded import is gone); `--schedule` help notes the rejected characters.
- **N7**: `_format_bootstrap_result` appends `⚠ N session(s) failed — last: <reason>`; the `backfill-sessions` text path prints `Failed sessions:` / `Last session error:` lines (JSON already carried them; the human summary did not).
- Regressions: `test_u36_limit_takes_the_newest_sessions_not_storage_order`, `test_u36_cutoff_runs_before_any_transcript_fetch`, `test_u36_newest_first_order_is_monotonic`, `test_u36_bootstrap_limit_helper_bounds_bootstrap_backfill`, `test_u36_cli_human_summary_names_failed_sessions`, `test_u36_backfill_text_output_names_failed_sessions`, `test_u36_hostile_infinite_pagination_is_bounded_and_deduped`; cycle-4's `test_backfill_state_db_imports_regardless_of_storage_order` still green (`sessions_seen` semantics preserved: examined-but-skipped rows count as seen).

### CU-AA — U17: systemd schedule grammar validation + unit escaping (P7; B17)
`hermes_curator_evolver/auto_evolve.py`
- New `_validated_on_calendar(schedule)`: `hourly`/`daily`/`weekly` (case-insensitive) pass canonically; anything else must match a strict OnCalendar subset — letters, digits, `* : , . / + -`, space. **Control characters anywhere in the raw input are rejected even when stripping would normalize them away**; quotes, `;`, `#`, `=`, `%` rejected with an error naming the offending characters.
- `install_auto_timer` validates the schedule **before any unit file is written** (nothing lands on rejection) and validates embedded paths (`--skills-dir`, `--verify-cwd`) for control characters.
- `_quote_systemd_arg` **raises** on `\n \r \t \0` (systemd has no newline escape — quoting can never make one survivable; writing it verbatim starts a fresh directive) and doubles literal `%` (specifier expansion: `%h` in a path would silently rewrite the command). Fixed a latent no-op while here: the inner-quote escape was `'\"'`, which parses as plain `"` — the backslash was missing, so embedded quotes were never actually escaped (exposed by the new unit test).
- Regressions: `test_u17_schedule_validation_accepts_canonical_and_oncalendar`, `test_u17_schedule_validation_rejects_directive_injection` (7 params incl. `daily\nExecStartPost=/tmp/pwned.sh`), `test_u17_install_auto_timer_refuses_injected_schedule` (unit dir stays empty), `test_u17_quote_systemd_arg_rejects_control_characters`, `test_u17_install_rejects_control_characters_in_embedded_paths`, `test_u17_quote_systemd_arg_doubles_percent_specifiers`.

### CU-AB — U7-riders: F821, version single-source, README rollback form, clamp warnings (Q2/Q4/Q8/U7b; B9)
- `cli.py`: `from typing import Any` added — **F821 eliminated** (`_explicit_int`'s `dict[str, Any]`).
- `__init__.py`: `__version__` is now read from `plugin.yaml` (`_plugin_version()`, regex parse with `0.10.0` fallback if the manifest is unreadable) — the two surfaces can no longer drift (they disagreed since cycle 1: `0.8.0` vs `0.10.0`).
- `README.md`: the rollback section now documents the **working** forms (`--skills-dir …` or `--allow-any-target`, plus `--force` semantics) instead of the bare form that refuses with `unrestricted-target`; also documents `--max-reference-files` and the new clamp warnings.
- `auto_evolve.py`: `_bounded(value, minimum, maximum, label="")` **warns on every clamp** naming old → new value, the label, and which bound fired; the four config call sites (`days`, `max_skills`, `min_evidence`, `max_reference_files`) pass labels. Module `logger` added (`logging.getLogger(__name__)`).
- Regressions: `test_u7b_version_agrees_with_plugin_yaml`, `test_u7b_version_is_not_the_drifted_literal`, `test_q8_clamp_warns_naming_old_and_new_value`, `test_q8_in_range_value_does_not_warn`.

## Behavior changes visible to users (disclosed in stewardship request)

1. **Backfill imports newest-first** (matches the existing help text's promise) and `sessions_seen` includes examined-but-skipped-old sessions.
2. **Bootstrap defaults to 500 sessions**; unbounded (`limit=None`) bootstrap import no longer possible via the CLI.
3. **Garbage schedules are rejected** with an actionable `ValueError` instead of being written into a systemd unit verbatim.
4. **Out-of-range numeric options warn** when clamped (values still clamp — unattended runs stay bounded).
5. `pip show`-style version surfaces now agree (`0.10.0` everywhere).

## Reproducer amendments (disclosed)

`/home/agent/.hermes/conductor-runs/2cc5b112c9694bfaa4a47645f139983a-assess/repro-pass5.py` was amended in four places, each marked inline with `[amended 2026-09-02 implement phase]`:
- **P7**: graded the quoter in isolation; the fixed contract is *rejection* — now asserts `ValueError` instead of a quoted newline.
- **N7**: targeted `def format_backfill*`, a function name that never existed (probe could never flip); now calls the real `_format_bootstrap_result`.
- **N3**: keyed on the literal word `continue` in `backfill.py` (still present in unrelated code); now tests the behavioral contract (cutoff inside the iterator → no `get_messages` for out-of-window sessions). This amendment exposed a real bug: `stats` was assumed pre-seeded → `KeyError` on a bare dict; fixed (`stats.get(..., 0)`).
- **R1-baseline**: authoring polarity bug — "still clean" printed `REPRODUCED`; inverted.
- **P5/P6** re-anchored by search instead of hardcoded line numbers (cycle-5 edits shifted the loop; the finding still reproduces, correctly).

## Files changed in this phase (working tree only — nothing committed)

```
M  README.md
M  hermes_curator_evolver/__init__.py      (CU-AB version single-source)
M  hermes_curator_evolver/auto_evolve.py   (CU-AA validation/escaping, CU-AB clamps+logger)
M  hermes_curator_evolver/backfill.py      (CU-Z trusted-order iterator)
M  hermes_curator_evolver/candidates.py    (CU-W truth table)
M  hermes_curator_evolver/cli.py           (CU-Z bootstrap limit + N7 summaries, CU-AB import)
M  hermes_curator_evolver/guarded_apply.py (CU-Y mode-preserving atomic writes)
M  hermes_curator_evolver/hooks.py         (CU-X docstring layering note)
M  hermes_curator_evolver/storage.py       (CU-X warm writer/errno/schema)
M  tests/test_auto_evolve.py               (CU-AA + CU-AB regressions)
M  tests/test_backfill_sessions.py         (CU-Z regressions)
M  tests/test_candidates.py                (CU-W corpus)
M  tests/test_cli.py                       (bounded-bootstrap expectation update)
M  tests/test_guarded_apply.py             (CU-Y regressions)
M  tests/test_storage.py                   (CU-W ingest + CU-X regressions)
+  docs/implementation/2026-09-02-cycle-5-batch-implementation.md (this file)
```

## How to verify

```bash
cd /work/projects/hermes-curator-evolver
python3 -m pytest                      # 249 passed (baseline 184)
ruff check .                           # 64 errors (baseline 64), F821 gone
ruff check --select F821 .             # All checks passed
python3 /home/agent/.hermes/conductor-runs/2cc5b112c9694bfaa4a47645f139983a-assess/repro-pass5.py
# → N2/N2b/N3/N7/P7/R1/R2/R3/R4/R5/R6/R8 not reproduced; N6/C1/P10/P9/P5-P6/P8/R7 still reproduced
git status --porcelain                 # 21 paths dirty, nothing staged/committed
```

## Provisional future work

- **final_validation + commit gates** (conductor-owned): KTD21 sequencing — commit BOTH pre-existing uncommitted batches (cycle-1 + cycle-4) first, then this batch; push target `fork` (codeo1io) only.
- Next batch pre-shaped: U18 (guarded_apply support-write boundary), U19 (legacy backfill UnicodeDecodeError → P8), U20 + N6 (verifier grounding cross-check), U26 (R7 `_explicit_int`), U6 (P9 stray markers), U16 (P10 raw traceback), C1 (rerank-after-truncation).
- Extensions U47–U50 unlock after remediation + commits clear KTD21.
