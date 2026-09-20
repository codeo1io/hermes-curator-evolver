# Cycle-7 Maintenance Batch — Implementation Report

- **Run**: `78a174fbdec14ee3844ff327a59cef78` · **Phase**: implement · **Attempt**: `ac6b718a21e846fb8c7c0aa85c31a83c`
- **Date**: 2026-09-20 · **Skill**: ce-work methodology applied in-thread (no `ce-*` router installed on this host — standing deviation disclosed every pass since cycle 2)
- **Batch**: U67 + U68 (+ U5 confirm-and-close rider) = change units **CU-AF / CU-AG** per `docs/stewardship/2026-09-20-cycle-7-stewardship-request.md`, selected in `docs/prioritization/2026-09-20-cycle-7-batch.md` — the *format-and-count truth batch*
- **Base**: `main` @ `a76962c` in the conductor worktree (`run-78a174fbdec1-78a174fb`); pre-existing uncommitted campaign artifacts (roadmap extension + 4 cycle-7 campaign docs) preserved untouched and NOT folded into this batch — the commit gate belongs to the conductor. Nothing committed, pushed, or PRed (prohibited).
- **Defects discharged**: pass-7 N1 (comma-grouped counts → success), N3 (clause joins), N4 (missing HTTP success codes), N5 (CLI counter disclosure), N2 (DISTINCT burst starvation of `min_evidence`)

## Verification summary (all gates re-run fresh after the last edit)

| Gate | Baseline | Result |
|---|---|---|
| `pytest` (venv) | 287 passed (47.8s) | **334 passed in 29.51s** (+48 new U67/U68 regression cases; one pre-existing test — cycle-6's `test_u54_event_count_counts_actions_not_event_rows` — rewritten as `test_u68_event_count_counts_every_ingested_action` because it pinned the collapse premise this batch overturns; no other test deleted or weakened) |
| `ruff check hermes_curator_evolver tests` | 63 errors / 48 fixable | **63 / 48** (unchanged, ungated) |
| `repro-pass7.py` (pass-7 corpus, 35 probes) | 24/35 sane, 8 deviation classes | **35/35 sane, 0 deviations** (all N1–N5 targets flipped; all stay-green controls hold: `"2,048 failed"` → True, `"0 failed, 12 passed"` → False, `"10 failed, 2 passed"` → True, backfill-path `event_count == 3`) |

Two probes in the harness needed *harness* fixes (not repo fixes), recorded here so a future pass doesn't re-trip: **T1b** passed `report = {"skills": [...]}` but `_eligible_skill_rows` reads `report["summary"]["skills"]` — the wrapper was missing, so the gate probe could never see any row (the pass-7 T1b "deviation" was real, but via the row-level `event_count==1` check, which is now 3); **B1b**'s expected list included `s00003`, the very "old session" the probe meant to prove excluded — pass-7 already resolved this as a script expectation bug (repo correct). Both patched in `/tmp/repro-pass7.py` with fix comments.

**Flake disclosure**: `test_u45_hook_writes_are_bounded_under_one_external_holder` failed 3/17 runs early in this session (elapsed 15.11s vs the 15.0s bound — the holder releases at 10s and the busy window is 5s, so the natural worst case nearly equals the assert bound). A controlled A/B experiment (stash batch → 6 runs → restore → 6 runs, interleaved ×6) showed **no batch dependency** (6/6 vs 6/6 interleaved); the early failures tracked system load during full-suite churn. Cycle-6's implementation report discloses the same test under load. Pre-existing fragility, out of this batch's scope (U45's surface) — flagged to the next cheap-wins bundle.

## Implemented change units

### CU-AF — U67: classifier format-matrix truth (N1/N3/N4/N5)
`hermes_curator_evolver/candidates.py` + `hermes_curator_evolver/cli.py`
- **N1** `_FAILURE_COUNT_PATTERN` rewritten to `(\d{1,3}(?:,\d{3})+|\d+)` — comma-grouped thousands capture whole; the caller strips separators before `int()` so `"1,000 failed"` parses as 1000 (cycle-6's `(\d+)` bound only the trailing `000` → success). Every magnitude pinned: `1,000`/`10,000`/`1,000,000`/`2,048` (the batch's stay-green control) → failure.
- **N3** `_CLAUSE_SPLIT_PATTERN` sentence split loosened from `\s+` to `\s*` (`(?<=[.!?。！？])\s*`): unspaced joins (`"deploy failed.no errors later"`) now split into clauses, so a trailing success phrase can't erase the failure. Commas deliberately remain non-separators (they group digits and carry list items); instead the zero-count path in `_text_bears_failure` now **strips the `"0 failed"` claims themselves and rescans** — `"0 failed, deploy failed: connection refused"` fails (a further claim stands) while `"0 failed, 12 passed"` stays success.
- **N4** `_HTTP_SUCCESS_CODES` widened to the complete in-band family for the generic `code` key: all 2xx the wrappers emit (**203, 206** were cycle-6 misses) plus the redirect-following 3xx (**301/302/303/304/307/308** — these plugins run redirect-following clients; 304 is a conditional-cache success). `exit_code`/`returncode` keep strict nonzero-is-failure semantics (pinned: `{"exit_code": 301}` → error).
- **N5** `cli.py` backfill-sessions human summary now prints **every truthful counter** the JSON carries — `Sessions metadata seen / pages scanned / in window / selected` — plus a `Metadata scan truncated: yes (...)` line when the runaway bound fired (never silent).
- Regressions (+44 cases in `tests/test_candidates.py`: 17+8+18 parametrized + 1 exit-keys, per `pytest -k u67 --collect-only` — the pre-review draft said +43/16 params): `test_u67_grouped_and_plain_failure_counts` (17 params: widths × separators × zero-claim mixes), `test_u67_clause_joins_spaced_and_unspaced` (8), `test_u67_http_success_family_for_generic_code` (18), `test_u67_exit_keys_keep_strict_nonzero_semantics`; plus 2 CLI disclosure tests in `tests/test_backfill_sessions.py` (with-truncation prints the line, without-truncation stays silent).

### CU-AG — U68: attribution burst counting (N2)
`hermes_curator_evolver/storage.py`
- The `summary()` skills query's `COUNT(DISTINCT session||task||skill||created_at)` → **`COUNT(*)`**: every ingested row is a distinct attributed action. The cycle-6 DISTINCT tuple collapsed same-second hook bursts to one action, starving `min_evidence` (pass-7 N2: 3 parallel calls → `event_count=1`, gate=2 → 0 eligible).
- Design decision recorded in a SQL comment: duplicate protection lives **at ingest** (backfill's `_tool_event_exists` guards re-imports), not in the aggregation; the `tools` table already counts raw rows this way, so skills now match its semantics. `event_rows` and `event_count` both stay disclosed (equal by construction — `event_count` is the stable API name consumers read, `event_rows` discloses the raw count).
- Regressions: `test_u68_event_count_counts_every_ingested_action` in `tests/test_storage.py` (rewrites the cycle-6 U54 test whose "one underlying lookup = one action" premise this batch overturns: 3-call same-second burst → 3/3; two-tool same-second case → 2/2; cross-session/days → each counts) and `test_u68_burst_events_satisfy_min_evidence` in `tests/test_auto_evolve.py` (the end-to-end N2 starvation repro: 3 same-second events clear `min_evidence=2` via `_eligible_skill_rows`; control: 1 event stays below the gate).

### U5 rider — cap constants single-sourcing (confirm-and-close)
Verified, no code change: `_MAX_SKILL_CONTENT_CHARS` and `_AUTO_LOADED_SKILL_MAX_CHARS` are defined exactly once (`auto_evolve.py:53/55`) and consumed by reference at all 7 sites (`:116, :648, :723, :1007, :1116, :1201, :1234`); no duplicate literals in package or tests. **U5 closes confirmed.**

## How to verify

```bash
# 1. Full suite (334 expected)
/home/agent/.hermes/hermes-agent/venv/bin/python3 -m pytest tests
# 2. Ruff unchanged (63 expected)
ruff check hermes_curator_evolver tests
# 3. Pass-7 corpus end-to-end (35/35 expected)
/home/agent/.hermes/hermes-agent/venv/bin/python3 /tmp/repro-pass7.py
# 4. The five defects, one-liners
/home/agent/.hermes/hermes-agent/venv/bin/python3 -c "
from hermes_curator_evolver.candidates import looks_like_error as L
print(L('1,000 failed'))                        # N1: True  (was False)
print(L('0 failed, deploy failed: conn refused'))  # N3: True (was False)
print(L('deploy failed.no errors later'))       # N3b: True (was False)
print(L({'code': 203}), L({'code': 301}))       # N4: False False (were True True)"
# 5. N2: 3 same-second events count as 3 actions and clear min_evidence=2
/home/agent/.hermes/hermes-agent/venv/bin/python3 -m pytest tests -k "u68"
# 6. N5: human backfill summary prints the truthful counters + truncation
/home/agent/.hermes/hermes-agent/venv/bin/python3 -m pytest tests -k "u67_backfill"
```

## Changed files

| File | Change |
|---|---|
| `hermes_curator_evolver/candidates.py` | CU-AF: patterns, truth eval, HTTP set, docstrings |
| `hermes_curator_evolver/cli.py` | CU-AF: N5 human-summary disclosure |
| `hermes_curator_evolver/storage.py` | CU-AG: N2 burst counting (DISTINCT → COUNT(*)) |
| `tests/test_candidates.py` | +43 U67 format-matrix cases |
| `tests/test_storage.py` | U54→U68 rewrite: every ingested row is an action |
| `tests/test_auto_evolve.py` | +U68 eligibility burst/control test |
| `tests/test_backfill_sessions.py` | +2 N5 disclosure tests |

Respected `must_remain_separate` hints: no `hooks.py`/backfill-paging edits (U71/U70 surfaces untouched), no `semantic.py` (U56), no roadmap/ledger changes.
