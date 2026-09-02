---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-6-independent-review
run: 6f5d76c84f52491ba25460c4a6e1a454
phase: independent_review
attempt: 70e9220a4caf4846bd6d12223e3bd8b4
skill: ce-code-review lenses applied in-thread (no ce-* router/skill installed on this host — same disclosed deviation as passes 2-6 and this run's assess/research/roadmap/prioritize/stewardship/implement phases)
reviewed: the uncommitted cycle-6 batch tree (HEAD 4350ee2 + working-tree diff of 3 modules + 3 test files, per docs/stewardship/2026-09-02-cycle-6-stewardship-request.md)
upstream: docs/implementation/2026-09-02-cycle-6-batch-implementation.md, docs/prioritization/2026-09-02-cycle-6-batch.md, .hermes/plans/autonomy-prop_8c5390ffe26640fa.md (Extension 2026-09-02)
---

# Independent adversarial review — cycle-6 batch (U51+U52+U53(+U54) = CU-AC/CU-AD/CU-AE)

**VERDICT: PASS — approve for the commit gate.** All four packets' acceptance
criteria are verified met against direct evidence re-derived by this review (not
taken from the implementer). Three P3 findings are recorded — every one is a
pre-existing-class gap narrowed-but-not-eliminated or a cost observation, none is
a regression introduced by the batch, none blocks the commit. Two are new corpus
for the next batch.

## What this review did independently

1. **Re-ran the authoritative pass-6 corpus** on the batch tree:
   `repro-pass6.py` + `repro-pass6-fixups.py`, both exit 0. Flip matrix matches
   the stewardship verification contract exactly — flipped: **F1** (`code:200/201/204`
   → success), **F2** (`10/20/100/110 failed` → error; `0 failed` stays success),
   **F4** (cross-clause success phrase no longer clears a failing clause), **F7**
   (10,040-session store, limit 2 → `s10039`/`s10038`, newest fetched), **F18**
   (3× `{"code":200}` → `error_events` 0), **F24** (`sessions_seen`=10 metadata
   rows, `sessions_selected`=3), **F6 → new contract** (reader completes under a
   held `_path_lock` via its own read-only connection). **F5 values intentionally
   unchanged** — S7's defect was the docstring contradicting the pinned order; the
   docstring now states the order and a new test pins it. Stay-set confirmed:
   F8, F11/F12/F13/F13b, F14, F16, F17, F19, F22, F23 (homes U18/U55/U56/U26/U60);
   F9/F15 stay green.
2. **Re-ran the full suite fresh**: `286 passed in 30.68s`, exit 0 (my run — not
   the implementer's log). Test-count delta vs HEAD verified per-file by
   `pytest --collect-only` diff: `test_backfill_sessions.py` 18→20,
   `test_candidates.py` 61→91, `test_storage.py` 15→20 — **+37, zero deletions in
   any file**; the one modified baseline assertion (`test_u36_limit...`
   `sessions_seen` 2→3 + new `sessions_selected==2`) is the honest-accounting
   change U52/F24 demands, and pins strictly more than before.
3. **Wrote 12 fresh adversarial probes of my own** (disjoint from the
   implementer's corpus): `/home/agent/.hermes/conductor-runs/6f5d76c84f52491ba25460c4a6e1a454-independent_review/review-probes.py`
   (+ `.json`). Notable results:
   - **Hot-WAL crash recovery (durability)**: a child process committed then died
     via `os._exit(0)` leaving `evidence.sqlite` + `-shm` + `-wal`; a fresh
     process constructed the store and read `tool_events=1`, exit 0. The main
     durability risk of `mode=ro` readers (SQLITE_READONLY_RECOVERY on a hot WAL)
     is structurally prevented: `EvidenceStore.__init__` eagerly runs
     `init_db()`, which opens the writer connection (and recovers the WAL)
     before any reader can exist.
   - **URI quoting**: a db path containing `?` and `#` reads correctly through
     the `as_uri()?mode=ro` path (close/reopen on a second store instance).
   - **Concurrent hammering**: a reader thread looping `summary()` while the
     writer committed 200 real events → zero reader errors, all 200 rows
     readable, writer survived. No phantom commit/rollback possible
     (`query_only=1`; DELETE on the reader raises OperationalError — pinned in
     `test_u53_reader_runs_on_its_own_read_only_connection_under_a_held_lock`).
   - **Close/reopen**: `close()` then `summary()` re-opens the read connection;
     a write after close still lands and is read back.
   - **Backfill invariants**: newest-first storage with duplicate timestamps
     handled (no false monotonicity fire); short-page shifting fake terminates
     in 1 page; `sessions_in_window + sessions_skipped_old == sessions_seen ==
     sessions_metadata_seen` holds.
   - **Classifier corners**: fullwidth-`；` clause split works with an English
     keyword; `10 FAILED` / `  10  failed  ` / multi-line splits correct;
     `{"code":302}`→error, `{"code":500}`→error, `{"code":200,"status":"error"}`→error,
     `{"returncode":0,"error":"boom"}`→error, `[{"code":200},{"code":1}]`→error.
4. **Read every hunk** of the 3 module diffs and 3 test diffs; grepped consumers
   (`reports.py:67`, `auto_evolve.py:811/824/842/844` read `event_count`, which
   still exists — `event_rows` is additive); confirmed scope discipline: only
   `candidates.py`, `backfill.py`, `storage.py` + their tests touched;
   `cli.py:551` (bootstrap) and `cli.py:878` (backfill-sessions) both route
   through `backfill_sessions` → share `_iter_state_sessions` (U52's
   "bootstrap paths share the ordering guarantee" ✓); legacy-dump branch keeps
   its per-file counters (`backfill.py:522/:531`).
5. **Security boundaries**: no new network/subprocess/eval anywhere in the diff;
   the host state DB is still opened `read_only=True`; plugin writes confined to
   its own evidence DB; readers now *provably* cannot write (`mode=ro` +
   `query_only`, probed); skills/ tree untouched; **nothing committed or pushed**
   — HEAD `4350ee2` throughout; the `cfc425b` ref visible in `--all` is
   pre-existing on `remotes/fork/main`, not created by this run; stash
   round-trips used for the HEAD comparison left `git stash list` empty and the
   12-entry status byte-identical.

## Acceptance-criteria scorecard

| Packet | AC item | Status |
|---|---|---|
| U51 | `N failed` error at ALL digit widths, no lookbehind tricks | ✅ lookbehind removed; count-parse; `10/20/100/110/7 failed` and `10 FAILED` verified; ⚠️ finding R-1 (comma groups) |
| U51 | `code` = exit semantics except 200/201/202/204 or explicit ok/success/status companion | ✅ `_HTTP_SUCCESS_CODES` + `explicit_failure` outranking; `exit_code:200`→error preserved |
| U51 | no distant success phrase clears an error | ✅ clause scoping (`_CLAUSE_SPLIT_PATTERN` + `_text_bears_failure`) |
| U51 | docstring/test agree, one truth | ✅ old "zero → success" unqualified claim gone; new docstring states explicit-fields-first order (candidates.py:351-373); pinned by `test_u51_zero_exit_truth_matches_the_pinned_code_order` |
| U51 (E) | repro probes flip; zero poisoned `error_events`; 249-suite green | ✅ F1/F2/F4/F18 flipped; `test_u51_http_success_code_never_poisons_error_events` (storage fixture; the AC's `record_tool_pass` name is this repo's `record_tool_call`); 286 green |
| U52 | cap the RESULT after trusted-order paging; monotonicity assertion | ✅ `selected = in_window[:limit]` after client sort; assertion at backfill.py:287-296 |
| U52 | `sessions_skipped_old` counts sessions not pages; bootstrap shares ordering; 10,040 fixture lands | ✅ counted once in the iterator; cli.py:551/:878 both route through it; `test_u52_cap_binds_in_recency_order_on_a_10040_session_store` |
| U53 | readers read-only (`mode=ro`), cannot commit/rollback; docstring truthful; PRAGMA off the global lock | ✅ `_read_connection()` + `query_only=1`; configure-then-publish outside `_connection_lock` in both `connect()` and `_read_connection()`; docstring rewritten (old phrase grep-gone) |
| U54 | one shared extraction entry point; both surface forms attribute; `event_count` counts actions; asymmetry test lands | ✅ `_extract_skill_name` unified; `test_u54_*`; ⚠️ finding R-2 (identity granularity) |

## Findings (none block the commit)

- **R-1 (P3, pre-existing class — new corpus for next batch)** —
  `hermes_curator_evolver/candidates.py:109`: `_FAILURE_COUNT_PATTERN` parses
  digit groups without thousands separators, so `"1,000 failed"` captures the
  trailing group `000` → classified **success**, while `"1,200 failed"` captures
  `200` → error (inconsistent by last-digit-group). The cycle-5 lookbehind had
  the identical blind spot (`(?<!0\s)` also cleared `1,000 failed`), so this is
  NOT a regression — U51's "all digit widths" truth holds for plain integers
  and is blind only to locale-formatted counts. Fix next batch: normalize
  `[\d,]+` groups before the count parse, and lift these cases into the corpus.
- **R-2 (P3, disclosed heuristic — needs an in-code comment and a schema-era
  follow-up)** — `hermes_curator_evolver/storage.py:657-668`: the action
  identity for `skills[].event_count` is
  `(session_id, task_id, skill_name, created_at-second)`. Fresh probes: two
  *genuine* distinct uses of a skill in the same second+session+task collapse
  to 1 (under-count); the S6 double-tag spanning a second boundary still counts
  2 (residual over-count). The under-count direction is conservative for
  `min_evidence` but biases burst-used skills toward stale/retire scoring in
  `auto_evolve`. Disclosed in the implementation doc and the test comment — but
  NOT in the code at the query (see R-6). Follow-up home: an explicit action-id
  when the schema next changes (U60's cohort work).
- **R-3 (P3, cost observation — AC-conformant)** —
  `hermes_curator_evolver/backfill.py:249`: every import now metadata-scans the
  whole store (the 10,040/limit-2 case reads 51 pages / 10,040 rows to fetch 2
  transcripts; last-resort bound is 3× the legacy 10k, disclosed via
  `metadata_scan_truncated`). This is exactly what "cap the result, never the
  scan" requires and upstream #101316's 90-day horizon bounds it in practice;
  recorded so the next batch can weigh a recency fast path if imports feel slow.
- **R-4 (info)** — `candidates.py` `_HTTP_SUCCESS_CODES` covers only
  200/201/202/204 (the AC's exact set): 301/302/304 in a generic `code` key
  classify as errors. AC-conformant; add to the corpus if any tool wrapper ever
  stores redirects.
- **R-5 (info, pre-existing)** — the failure-keyword vocabulary is
  English-only: CJK failure prose with no English keyword (e.g. `部署失败`)
  stays success. The clause *splitter* handles `；` correctly (probed with an
  English keyword). Vocabulary breadth is a standing limitation, not this
  batch's.
- **R-6 (info, doc accuracy)** — `docs/implementation/2026-09-02-cycle-6-batch-implementation.md`
  says U54's heuristic is "disclosed in the SQL comment"; no such comment exists
  at `storage.py:657` (disclosure lives in the doc and the test). Fold the
  one-line comment in with R-2's fix.

## Durability / recovery (checked, all green)

Writer paths are byte-for-byte semantics-preserving (`_write_with_retry`, WAL
fallback, quarantine, atexit teardown extended to read connections). The one new
durability risk class a read-only reader could introduce — failing to recover a
hot WAL left by a crashed writer — is structurally prevented by
`EvidenceStore.__init__` → `init_db()` → writer-open-first, and was probed
empirically (crash simulation → fresh-process read succeeds). Snapshot isolation
under an open writer transaction is pinned by
`test_u53_reader_never_commits_or_rolls_back_a_writers_transaction` and my
hammer probe.

## Prohibitions honored

This phase is report-only: nothing committed, pushed, or PRed; no repo source
modified (git status after review: same 7 modified + 5 untracked campaign docs +
this review doc); `final_validation`/`commit`/`push`/`pr`/`ci` not begun.
