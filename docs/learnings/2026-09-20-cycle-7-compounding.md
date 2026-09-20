# Cycle-7 Compounding — Durable Lessons (pre-review)

- **Run**: `78a174fbdec14ee3844ff327a59cef78` · **Phase**: compound · **Attempt**: `c3fdbf11e31c4bcfb039c7eac51cf341`
- **Date**: 2026-09-20 · **Scope**: pre-review cycle evidence only (assessment pass 7, research, roadmap, prioritization, stewardship, implementation, targeted/full test outcomes). Review and shipping outcomes are NOT folded here — the next cycle's assessment carries them.
- **Batch compounded**: U67 + U68 (+ U5 confirm-and-close rider) = CU-AF/CU-AG per `docs/stewardship/2026-09-20-cycle-7-stewardship-request.md`, implemented in `docs/implementation/2026-09-20-cycle-7-batch-implementation.md`.
- **Rule numbering**: continues cycle 6's L1–L14 (`docs/learnings/2026-09-02-cycle-6-compounding.md` — see L21 below) and KTD31's L15 (format-matrix rule, in the roadmap's cycle-7 extension).

## L16 — DISTINCT-as-dedup is an aggregation bug when duplicates are guarded at ingest

The cycle-6 "attributed actions" metric (`COUNT(DISTINCT session_id, task_id, skill_name, created_at)`, storage.py) invented read-time dedup for duplicates that cannot occur through the guarded ingest path (backfill's `_tool_event_exists` refuses re-imports), and then second-precision `created_at` inside the key collapsed genuine same-second bursts — starving the `min_evidence` gate exactly for the parallel-tool-call shape the metric was built to serve (pass-7 N2).

**Rule**: count what a row *is* (an ingested action → `COUNT(*)`); enforce uniqueness where the write happens, not where the read aggregates. If a read-side collapse is ever truly needed, its key must contain a strictly-unique column (rowid) or an args-hash — never a second-precision timestamp. Design tradeoffs of this shape get recorded in a comment at the aggregation site and in the change unit's implementation doc (both done this cycle: `storage.py` skills query comment + `docs/implementation/2026-09-20-cycle-7-batch-implementation.md`).

**Prevention hook**: any new aggregate that feeds a threshold gate ships with (a) the burst fixture that the gate exists to catch, (b) the single-event control below the gate, and (c) a comment naming where duplicates are actually prevented.

## L17 — A test can enshrine the defect it was meant to police

Cycle-6's `test_u54_event_count_counts_actions_not_event_rows` *asserted the collapse* — "one underlying lookup = one action" — so the suite stayed green while the gate starved. The premise lived in a test name that sounded like a guarantee.

**Rule**: when a defect overturns a metric's premise, the old pinning test is **rewritten to the new truth in the same change unit** — never deleted silently, never left failing. The rewrite must say in its docstring which premise died and link the assessment finding (done: `tests/test_storage.py` u54→u68 rewrite cites pass-7 N2). Reviewers treat "test name asserts X" as a claim about *desirability* of X, not its truth.

**Prevention hook**: metric tests are audited at every assessment for premise drift — does the pinned expectation still match what the consuming gate (here `_eligible_skill_rows(min_evidence=…)`) needs?

## L18 — Probe harnesses need adversarial review too (both-directions proof)

Two of the pass-7 corpus's own probes were harness bugs: **T1b** passed `{"skills": […]}` where `_eligible_skill_rows` reads `["summary"]["skills"]` — a probe that could *never* see a row and would report 0 eligible forever, on any tree, fixed or not; **B1b** listed `s00003` in its expected list — the very session it existed to prove excluded. Both were fixed in place with dated comments this cycle (`/tmp/repro-pass7.py` now 35/35 sane).

**Rule**: every probe must be proven **both directions** before it becomes a gate — shown to FAIL on the broken tree and PASS on the fixed tree at least once each. A probe that cannot distinguish fixed-from-broken validates by construction and is worse than no probe (it manufactures confidence). Harness bugs get fixed in the harness, in place, with a dated comment — never by adjusting the repo to satisfy a broken probe.

**Prevention hook**: when lifting a corpus into permanent regressions (cycle-6 craft rule), the pytest port is the moment the both-directions proof happens naturally — assert the new expectation, run against the pre-change tree via stash, confirm it fails there.

## L19 — `addopts` doubles quiet flags; script validation by exit code + count, never summary-grep

`pyproject.toml` sets `addopts = "-q"`, so any CLI `-q` becomes `-qq` and pytest suppresses the final `N passed` line. Three times this cycle a green run *looked* summary-less; a validation script that greps for "passed" would misread it.

**Rule**: scripted validation reads the **exit code** plus an **independent count** (dot-count of the progress line, or a re-run without the doubled flag). Never grep for the summary line as the pass signal. (Applied: targeted_tests and full_tests phases both cross-checked dot-counts against the summary run.)

## L20 — Load-flakes get an interleaved A/B, not a hunch

`test_u45_hook_writes_are_bounded_under_one_external_holder` failed 3/17 early in the implement session (elapsed 15.11s vs the 15.0s bound — the natural worst case nearly equals the assert bound, since the holder releases at 10s and the busy window is 5s). Sequential baselines then ran 16/16 clean — order-confounded, not conclusive. The **interleaved** stash/restore A/B (×6 in one script) came back 6/6 vs 6/6: batch-independent, load-sensitive.

**Rule**: before blaming or clearing a batch for a flake, interleave stash/restore runs inside a single script (same machine state, alternating arms), and capture the failure's actual numbers to classify marginal-by-design vs pathological. Marginal-by-design bounds (assert ≈ natural worst case) are cheap-wins material (widen the bound or shorten the holder wait), not blockers.

## L21 — Compound-phase artifacts must land in the commit gate (cycle-6 citation dangles)

The cycle-6 roadmap cites `docs/learnings/2026-09-02-cycle-6-compounding.md` ("rules L1–L14 with prevention hooks") — but `git log --all -- docs/learnings/` is empty: **the file was never committed**, and the campaign's full cycle-6 lesson set was lost. Only the top-3 lessons survived, inline in the roadmap. The citation is dangling to this day.

**Rule**: every path a roadmap/doc cites is a commit-gate item. The commit phase verifies each cited path exists in the tree it ships (grep citations → `ls`). This document (`docs/learnings/2026-09-20-cycle-7-compounding.md`) is *explicitly named for the commit phase* — if it is absent from the shipped tree, L21 has repeated.

## Craft rules reaffirmed from cycle 6 (applied again this cycle)

- Adversarial probes lift into permanent regressions **in the same change unit** (+48 tests: 44 classifier matrix, 1 burst/eligibility, 2 CLI disclosure, 1 u54→u68 rewrite — the pre-review draft said 43; `pytest -k u67 --collect-only` counts 44).
- Ruff stays flat by construction: new tests used epoch-numeric/fixture shapes, no new UP017/DTZ001 traps (63/48 before and after, per-file subset stash-compared).
- Findings are pinned only after reproducing on the pre-change tree where the probe itself is new.
- Stay-green controls are named *in the batch contract before implementation* (`"2,048 failed"` stays True, backfill-path `event_count=3` survives) and asserted in the final verification — an accidental pass is a control, not luck.

## What the next cycle should inherit (context, not new packets)

1. **U55/U56 are the immediate follow-on** (cycle-7 sequencing holds: they were displaced one slot by the two P2s, which are now implemented). U56 now carries: N7 wheel packaging/version single-sourcing, S9/S10 slices, ruff gate at 63, sentence-transformers 6.x CI leg, ruff 0.16.3→0.16.8, **+ the u45 bound widening (L20)**.
2. **U70 pull-in criteria** (unchanged): take it as a third unit only if the MRU early-stop probe stays ≤ ~80 lines; hostile-store fallback and truthful counters are the AC.
3. **U71 pairs with U69** on `storage.py` (once-per-batch lesson: cycle-6 CU-AE + this cycle's CU-AG both touched it; do not interleave a third storage change unit with them).
4. **History correction candidate** (new, small): pre-fix comma-formatted successes are permanently poisoned rows in the append-only `error_events` (every day between cycle 6 and cycle 7 with `"1,000 failed"`-shaped output was ingested as success). A summary-level correction entry (not row edits — append-only holds) is a cheap slice for U56 or the next batch; estimate the poisoned-row count first via a one-off scan before deciding.
5. **Review checklist seeds** (for the upcoming review phase, from implement evidence): the widened `_CLAUSE_SPLIT_PATTERN` on pathological text (`...` ellipses); any consumer besides `_eligible_skill_rows` assuming `event_count ≤ event_rows`; docs still describing the 4-code HTTP set; the U68 design choice (raw `COUNT(*)`, no report-layer dedupe) vs the AC's parenthetical alternative — recorded deliberately in the SQL comment and implementation doc.
