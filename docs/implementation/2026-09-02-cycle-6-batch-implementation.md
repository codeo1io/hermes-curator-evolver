# Cycle-6 Maintenance Batch — Implementation Report

- **Run**: `6f5d76c84f52491ba25460c4a6e1a454` · **Phase**: implement · **Attempt**: `c2f3f08acfd3485fb815e0588848d68a`
- **Date**: 2026-09-02 · **Skill**: ce-work methodology applied in-thread (no `ce-*` router installed on this host — standing deviation disclosed every pass since cycle 2)
- **Batch**: U51 + U52 + U53(+U54) = change units **CU-AC / CU-AD / CU-AE** per `docs/stewardship/2026-09-02-cycle-6-stewardship-request.md`, discharging B23 (U51), B24 (U52), B25 (U53), B26 (U54 rides CU-AE per KTD22 one-packet-per-root-cause)
- **Base**: branch `fix/maintenance-cycles-1-5` @ `4350ee2`, single working tree (no conductor worktree assigned); pre-existing uncommitted campaign artifacts (roadmap extension + 4 cycle-6 campaign docs) preserved untouched and NOT folded into this batch — the commit gate belongs to the conductor. Nothing committed, pushed, or PRed (prohibited).

## Verification summary (all gates re-run fresh after the last edit)

| Gate | Baseline | Result |
|---|---|---|
| `pytest` (venv) | 249 passed | **286 passed** (+37 new regression tests; zero pre-existing tests deleted or weakened). Flake disclosure: two of ~9 full runs reported `1 failed` under visible system load (42s wall vs ~27–30s normal); the name was not captured before the suite went green again, and 7 consecutive re-runs plus a full-CPU-load run are 286/286. The load-sensitive candidates are pre-existing wall-clock-bounded tests (`test_u45_hook_writes_are_bounded_under_one_external_holder` asserts `elapsed < 15.0`; `test_record_retries_through_held_write_lock` waits on an external holder), not batch tests — all 37 new tests use deterministic epoch fixtures, and the one thread-join in `test_u53_...` was widened to a 10s timeout (a real deadlock still fails it). |
| `ruff check hermes_curator_evolver tests` | 63 errors | **63 errors** (no count increase; the only additions — 2 UP017/DTZ001 candidates in new tests — were reworked to epoch-numeric fixtures so the count stays exactly at baseline) |
| `repro-pass6.py` (pass-6 corpus) | 19 reproduced | **7 batch targets flipped; 10 stay-set confirmed** |

Batch-target flips: **F1** (`{"code":200/201/204}` → success), **F2** (`10/20/100/110 failed` → error at every digit width; `0 failed` stays success), **F4** (success phrase on another clause no longer clears a failing clause), **F7** (10,040-session store, `--limit 2` yields `s10039`/`s10038` — the NEWEST two — in 51 pages, not 50 pages of the oldest region), **F18** (HTTP-200 payload no longer poisons `error_events`: 3 tool events, 0 error events), **F24** (`sessions_seen` = 10 metadata rows examined, `sessions_selected` = 3), **S6** (skill attribution symmetric — verified in-session during stewardship and now pinned by `test_u54_skill_attribution_is_symmetric_across_all_tools`).

**F5 is intentionally unchanged** (values `exit0+error→True`, `exit0+status:error→True`, `returncode0+exception→True`): S7's defect was the *docstring contradicting the pinned truth table* — the behavior was already correct and is now pinned by `test_u51_zero_exit_truth_matches_the_pinned_code_order`, and the `looks_like_error` docstring states the explicit-fields-first order. **F6 flips to the NEW contract**: a reader completes in ~0.001 s while `_path_lock` is held *because* it runs on its own cached read-only connection — no longer "fine by accident".

Stay-reproducing (correct — homes outside this batch): **F8** (support-step crash — U18; verified byte-identical on the pre-change tree via `git archive HEAD` extraction before pinning it to my edits), **F11/F12/F13/F13b** (raw tracebacks on missing files — U55), **F14** (duplicate frontmatter name silently drops a skill — U55), **F16** (inflated grounding count — U56), **F17** (rerank ceiling — U26), **F19** (bootstrap schedule traceback — U55), **F22** (legacy latin-1 session aborts whole import — U60), **F23** (hook write stalls 0.0 s vs documented ~10.5 s bound — U56 doc truth). F9/F15 (mode preservation, quarantine) stay green.

## Implemented change units

### CU-AC — U51: classifier truth table v2 (B23; S1/S2/S4/S7 → F1/F2/F4/F5/F18)
`hermes_curator_evolver/candidates.py` (one file, one owner)
- S1: `(?<!0\s)failed` lookbehind **removed** — bare `failed` keyword restored; paired-count truth moved to a real count parse. New `_FAILURE_COUNT_PATTERN` (`(\d+)\s+failed\b`): a clause with explicit counts is a failure iff any count > 0, at **every digit width** (`10`, `20`, `100`, `110` now fail; `0 failed, 12 passed` stays success; `2 packages failed` has no paired count and fails via keyword).
- S4: new `_CLAUSE_SPLIT_PATTERN` (lines / sentences / `；`) + `_text_bears_failure()` — a success phrase (`_SUCCESS_COUNT_PATTERN`) clears only the failure keywords **in its own clause**; `"deploy failed: connection refused; earlier healthcheck reported no errors"` is an error again.
- S2: new `_HTTP_SUCCESS_CODES = {200, 201, 202, 204}`; the generic ambiguous `code` key carries in-band HTTP success → **not** a process failure **unless** an explicit failure field exists (`error` / `exception` / `ok: False` / `success: False` / failure `status` word) — `{"code": 200, "error": "boom"}` stays an error. Unambiguous `exit_code`/`returncode` keep strict nonzero-is-failure semantics (`exit_code: 200` → error). `port_ok 8080` / `errno 0` shapes preserved.
- S7: `looks_like_error` docstring rewritten to match the code's actual order (explicit failure fields outrank a zero exit) — behavior pinned, not changed.
- Regressions (30 new cases in `tests/test_candidates.py`): `test_u51_paired_failure_counts_bind_at_every_digit_width` (9 params), `test_u51_http_shaped_code_values` (13 params), `test_u51_success_phrases_clear_only_their_own_clause` (7 params), `test_u51_zero_exit_truth_matches_the_pinned_code_order`; plus `test_u51_http_success_code_never_poisons_error_events` in `tests/test_storage.py` (append-only `error_events` makes misclassification permanent — S2's worst consequence).

### CU-AD — U52: backfill metadata cap binds the RESULT after trusted-order paging (B24; S3 → F7/F24)
`hermes_curator_evolver/backfill.py` (one file, one owner)
- `_iter_state_sessions` rewritten: **scan → client sort newest-first → cutoff → `selected = in_window[:limit]`** — the cap now bounds the selected result, never the collection window (assessment F7: 10,040 sessions with `--limit 2` used to fetch `s9999`/`s9998` from the oldest storage-order region while `s10039` was never read).
- Paging terminates on empty page / short page / a page adding no new ids (shifting-tail defense, R8); a genuinely minting-forever fake is stopped by a last-resort bound `max(limit, 10_000) * 3` metadata rows, disclosed via `stats["metadata_scan_truncated"] = 1` — never a silent drop.
- Truthful counters (F24): `sessions_pages_scanned`, `sessions_metadata_seen` (distinct metadata rows), `sessions_seen` (all examined), `sessions_in_window`, `sessions_skipped_old` (actually-old sessions, counted once), `sessions_selected`. The caller's state-db branch no longer double-counts (`sessions_seen += 1` per yield removed; dead `session_dt < cutoff` check removed).
- Monotonicity assertion: yielded sessions are strictly newest-first.
- Regressions in `tests/test_backfill_sessions.py`: `test_u52_cap_binds_in_recency_order_on_a_10040_session_store` (the full F7 reproducer as a permanent fixture — 10,040 rows, oldest-first storage order, asserts `["s10039","s10038"]`, 51 pages, exactly 2 transcripts fetched, every counter) and `test_u52_runaway_bound_discloses_instead_of_walking_forever` (infinite-mint fake terminates, distinct ids, `metadata_scan_truncated` set). Existing `test_u36_limit...` updated to the honest accounting (`sessions_seen` 2→3, `+sessions_selected == 2`).

### CU-AE — U53+U54: storage read-path concurrency contract + symmetric attribution (B25+B26)
`hermes_curator_evolver/storage.py` (one file, one owner; U53/U54 are disjoint hunks — flagged for separate commits per the stewardship doc)
- **U53**: module-level `_read_connections` cache; new `_read_connection()` — `file:...?mode=ro` URI with `PRAGMA query_only=1`, cached per resolved path with configure-then-publish single-flight (`setdefault`), closed by `close()` and `_close_cached_connections`. `summary` / `recent_tool_events` / `recent_turns` read through it (no `with conn:` commit-on-exit hazard — the legacy `with self.connect() as conn:` reader could COMMIT an unrelated open writer transaction). `connect()` pragma setup moved outside the global connection lock (readers no longer serialize behind writer setup) and its docstring rewritten: it is the warm **writer** connection; readers must not touch it (assessment S5/F6 + the F6 probe's `docstring_claims` literal, which described "all reads take the path lock" — now false by design).
- **U54**: `_extract_skill_name` unified — `name`/`skill`/`skill_name` then `skills` list, for **every** tool (the skill-tool early return that ignored `{"skills": [...]}` was S6's asymmetry; `Read` of a `SKILL.md` still does not attribute). `skills[].event_count` now counts **attributed actions** (`COUNT(DISTINCT session||task||skill||created_at)`) with the raw `event_rows` (`COUNT(*)`) alongside — a lookup surfaced through two differently-tagged events (same session/task/second) is one action; distinct-task or distinct-session usage counts separately. Second-granularity `created_at` makes the identity a heuristic and this is disclosed in the SQL comment. `SKILL_TOOL_NAMES` kept as the documented vocabulary constant (interface stability).
- Regressions in `tests/test_storage.py`: `test_u53_reader_runs_on_its_own_read_only_connection_under_a_held_lock` (reader ≠ warm conn; ro conn rejects DELETE; `summary()` completes under a held `_path_lock`), `test_u53_reader_never_commits_or_rolls_back_a_writers_transaction` (snapshot isolation asserted; rollback still discards), `test_u54_skill_attribution_is_symmetric_across_all_tools`, `test_u54_event_count_counts_actions_not_event_rows` (event_rows 2 / event_count 1 for the double-tagged pair; 4/3 after two distinct actions).
- Propagation: `_eligible_skill_rows` consumes `summary()`, so U54's counts flow to auto-evolve ranking without touching `auto_evolve.py` (out of batch).

## Deviations / notes for review

1. **S7 is a docstring-only fix** — F5's probe values are unchanged by design (behavior was already correct; the docstring lied). The new `test_u51_zero_exit_truth...` pins the order so a silent reorder now fails loudly.
2. **F8 was re-verified against the pre-change tree** (full package extracted from `git archive HEAD` into /tmp) before attributing `crashed: false` to the probe's own semantics — no regression from this batch; its home stays U18.
3. **`error_events` history is append-only**: rows poisoned by S2 before this fix stay poisoned (documented in the stewardship doc; no history rewrite in scope).
4. **New tests avoid wall-clock and tz-lint traps**: the U52 fixtures use deterministic epoch-second `last_active` values parsed by the library's own `_parse_dt`, keeping the ruff count exactly at the 63 baseline (U56's ruff gate consumes the pre-existing 48 auto-fixables next batch).
5. **Commit topology left to the conductor** as specified: code units are separable per the 8 `must_remain_separate` pairs (CU-AC `candidates.py` + its tests; CU-AD `backfill.py` + its tests; CU-AE `storage.py` + its tests, U53/U54 disjoint hunks for separate commits).

## How to verify (fresh clone)

```bash
cd /work/projects/hermes-curator-evolver
/home/agent/.hermes/hermes-agent/venv/bin/python3 -m pytest          # 286 passed
/mnt/workpool/home/agent/.local/bin/ruff check hermes_curator_evolver tests   # Found 63 errors (baseline)
/home/agent/.hermes/hermes-agent/venv/bin/python3 /home/agent/.hermes/conductor-runs/6f5d76c84f52491ba25460c4a6e1a454-assess/repro-pass6.py
# F1/F2/F4/F7/F18/F24 flipped; F6 completes under lock via ro connection; F5 values intentionally unchanged
```

## Files changed (this batch, all uncommitted)

```
M  hermes_curator_evolver/candidates.py   (+112/-… CU-AC)
M  hermes_curator_evolver/backfill.py     (+111/… CU-AD)
M  hermes_curator_evolver/storage.py      (+292/… CU-AE)
M  tests/test_candidates.py               (+84 CU-AC tests)
M  tests/test_storage.py                  (+160 CU-AE tests + U51 fixture)
M  tests/test_backfill_sessions.py        (+110 CU-AD tests)
A  docs/implementation/2026-09-02-cycle-6-batch-implementation.md  (this report)
```

Pre-existing from earlier cycle-6 phases (untouched here, ride the batch commit gate): `M .hermes/plans/autonomy-prop_8c5390ffe26640fa.md`, `?? docs/assessment/…pass6.md`, `?? docs/ideation/…cycle-6-extension-research.md`, `?? docs/prioritization/2026-09-02-cycle-6-batch.md`, `?? docs/stewardship/2026-09-02-cycle-6-stewardship-request.md`.
