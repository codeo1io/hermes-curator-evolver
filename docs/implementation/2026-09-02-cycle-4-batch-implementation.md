# Cycle-4 Maintenance Batch — Implementation Report

- **Run**: `673d15323b9c4580a0e2ed84fa8625fc` · **Phase**: implement · **Attempts**: `4ea3d3fce4424e38adda5752543fd1c6` (implementation) · `a6f89625a35c4db39c7ff0ae7082681b` (re-issued attempt; full re-verification, no code changes needed — all gates re-run fresh, see `conductor-runs/...-implement/repro-attempt-a6f89625.txt` + `pytest-attempt-a6f89625.txt`)
- **Date**: 2026-09-02 · **Skill**: ce-work (narrowest installed match for implementation + local verification; no subagent dispatch available in pi → all passes in-thread, disclosed)
- **Batch**: U15 + U7a + U37 + U35 + U16 + U28 = change units CU-Q..CU-V per `docs/stewardship/2026-09-02-cycle-4-stewardship-request.md`
- **Base**: main @ `45328db`, single worktree, uncommitted cycle-1 remediation (11 files) preserved untouched and NOT folded into this batch (KTD16: it commits via its own gate first)

## Implemented change units

### CU-Q — U15: managed-block rewrite is data, not a regex template (P1)
`hermes_curator_evolver/auto_evolve.py` `_apply_managed_block`
- `pattern.sub(block, skill_text, count=1)` → `pattern.sub(lambda _match: block, skill_text, count=1)`. A lambda replacement is never parsed for group references, so evidence previews containing `\1`, `\g<name>` etc. can neither raise `re.error: invalid group reference` nor inject captured groups. Closes the whole class in one expression; no per-preview neutralization.
- Regression: `tests/test_auto_evolve.py::test_apply_managed_block_replacement_is_literal_on_second_run` (second-run rewrite of an already-managed skill with backreference-laden block).

### CU-R — U7a: sqlite connect/write hardening (P4)
`hermes_curator_evolver/storage.py`
- `connect()`: `timeout=5.0`; `PRAGMA busy_timeout=5000`; `PRAGMA journal_mode=WAL` as query-that-sets with DELETE fallback on unsupported/marker errors ("locking protocol", "not authorized", "disk i/o error"); log-once per path; never downgrade on-disk WAL; best-effort `journal_size_limit=64MiB`; module-level connection-path cache + `threading.Lock`.
- `_write_with_retry()`: 3 attempts, 0.25s linear backoff, retries only busy/locked errors, exhaustion propagates. All three `record_*` writers wrapped.
- `_schema_ready()` cheap `sqlite_master` probe; `init_db` skips `executescript` steady-state.
- `hermes_curator_evolver/hooks.py`: docstring layering note (boundary catch stays; retries happen beneath it).
- Regression: `tests/test_storage.py::test_record_retries_through_held_write_lock` (asserts `journal_mode=wal` + `busy_timeout>=5000`; a 0.6s-class held `BEGIN EXCLUSIVE` lands after release).
- **Design boundary (disclosed)**: an *infinite* lock holder still errors after ~16s (3×5s timeout + backoff) — bounded by design; a durable spill-queue is provisional future work (U7b scope).

### CU-S — U37: NUL poisoning closed at the value layer (N5)
`hermes_curator_evolver/storage.py`
- New `_sanitize_nul(value)` recursively strips **real** `\x00` from str/dict/list/tuple before `json.dumps` (used in `_compact` and `_json_dumps`).
- `_strip_nul_bytes` now removes only the real control character — the old literal-form stripping (which mangled legitimate documentation text like ``use printf '\x00'``) is deleted.
- Effect: no `\u0000` escape can ever be emitted, so a stored NUL can never decode back on read; literal spellings survive as content.
- Regressions: `test_nul_sanitization_closes_every_encoding_and_keeps_literals` (new); `test_recorded_tool_results_never_store_nul_bytes` (updated to the new contract — it previously codified the over-stripping).

### CU-T — U35: tamper-resistant rollback (N1 + C2)
`hermes_curator_evolver/guarded_apply.py`
- Atomic writes: `_atomic_write_bytes/_atomic_write_text/_atomic_copy` (temp-in-dir + fsync + `os.replace`) now back `_write_manifest`, apply's target write, the verify-failed restore, and the rollback restore.
- `_rollback_support_files(manifest, target, manifest_dir=None)`: every entry validated **before** any unlink — (1) target-identity refusal (entry resolving to the rollback target → skip `target-file`); (2) registration cross-check (entry `backup_path` must resolve inside the manifest's own directory and exist → else skip `not-registered`); (3) pre-removal safety snapshot into `<manifest>/rollback-safety/`, fail-closed (`safety-snapshot-failed` skip); removals now record `{"path", "safety_copy"}`.
- `rollback_guarded_patch(...)`: pre-restore safety snapshot of the current target (fail-closed abort `safety-snapshot-failed`), atomic restore, manifest gains `rollback_safety` + `rolled_back_at`; **C2**: `allowed_target_roots=None` no longer means "any path" — unrestricted rollback requires explicit `allow_unrestricted_target=True`, otherwise refusal `unrestricted-target` with an actionable hint.
- `hermes_curator_evolver/cli.py`: rollback gains `--allow-any-target` opt-in; `--skills-dir` (when given) remains the containment root.
- Regressions: `test_rollback_refuses_to_delete_restored_target_via_tampered_manifest` (the N1 attack verbatim → skipped `target-file`, target intact), `test_rollback_refuses_unregistered_support_entries`, `test_rollback_requires_explicit_unrestricted_opt_in` (C2), `test_rollback_snapshots_target_before_restore`; existing rollback tests updated to model safe usage (`allowed_target_roots=`).

### CU-U — U16: explicit zero honored end-to-end (N4 + P3)
- `hermes_curator_evolver/auto_evolve.py` `prune_auto_reference_files`: `if keep < 0` → `if keep <= 0` (keep=0 disables pruning; only a positive bound prunes).
- `hermes_curator_evolver/cli.py`: new `_explicit_int(values, key, default)` replaces all four `int(values.get(k) or d)` collapses (`max_skills`, `min_evidence`, `variants`, `max_reference_files`); missing/empty → default, explicit `0` → 0.
- Regressions: `tests/test_auto_evolve.py::test_prune_auto_reference_files_disable_and_handwritten_protection` (**replaces** the old `test_prune_auto_reference_files_handles_missing_directory_and_zero_keep`, which codified the same-pass deletion bug); `tests/test_cli.py::test_auto_run_flags_honor_explicit_zero` (monkeypatched `run_auto_evolve` captures the config: `--max-reference-files 0` → 0).

### CU-V — U28: single error classifier (P2)
- `hermes_curator_evolver/storage.py`: private `_looks_like_error` **deleted**; import + call the public classifier.
- `hermes_curator_evolver/candidates.py`: new public `looks_like_error(result)` — str → structured-first scan; dict → JSON-marshaled structured check (`exit_code`/`error`/`exception`/`success` authoritative); list → failure iff any element fails; None → False. Keyword pattern already excludes bare "error", so `"3 passed, no errors found"` classifies as success in every shape.
- Regressions: `tests/test_candidates.py::test_looks_like_error_marshals_every_result_shape`, `test_successful_test_run_summary_is_not_classified_as_error`; storage ingest covered by the updated NUL/error tests.

## Verification evidence

| Gate | Result |
|---|---|
| Full pytest | **184 passed** (baseline 174; +10 net new, 0 failures) — `conductor-runs/...-implement/pytest.txt` |
| Ruff | **63 errors / 45 fixable** vs baseline 65/46 — no new errors; none in touched lines |
| Adversarial corpus (12 reproducers) | **7 full flips**: N1, N4, N5, P1, P2, P3, C2 now reproduce-safe; **P4 partial**: infinite holder errors by design (~16s), realistic 0.6s holder **lands**; N2, N3, N6, P7, P10 remain open (out of batch, as selected) — `conductor-runs/...-implement/repro-after-implement.txt` |
| Dirty-state preservation | All 11 pre-phase uncommitted files intact; batch changes purely additive (13 modified + 5 untracked paths) — `conductor-runs/...-implement/full-diff-including-cycle1.txt` |

Corpus probe adaptations (disclosed): the pass-4 corpus script predates two renames — (a) P2 probed the deleted private `storage._looks_like_error` (AttributeError aborted the run); the adapted copy probes the public `candidates.looks_like_error`. (b) P3's probe re-implemented the old `int(x or 5)` expression inline, so it could never observe the fix; the adapted copy exercises the real `handle_cli` dispatch with a captured config. (c) P4's realistic-holder probe originally released the lock from a different thread than it acquired it (`check_same_thread` — the lock was in fact never released); the adapted copy holds/releases within one thread. The original script is untouched in the assess run directory; the adapted copy + output are archived beside this report. Original semantics of P4's infinite-holder probe preserved verbatim (errors by design).

## Provisional future work (not in this batch)
- U7b: durable spill-queue for events arriving under indefinite lock contention (bounded retry exhaustion currently propagates to the hooks boundary, which swallows+logs).
- Register the manifest `rollback_safety` snapshots in the restore drill so operators can find them.
- N2/N3 (backfill ordering + over-fetch), N6 (verifier self-attestation), P7 (systemd newline injection), P10 (CLI traceback on bad path) remain for later batches per the cycle-4 board.
