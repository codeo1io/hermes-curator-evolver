---
date: 2026-09-21
topic: hermes-curator-evolver-cycle-8-batch-selection
mode: repo-grounded
run: 2fed6c7b93ea4a65a8b2fb94218cdb27
phase: prioritize
attempt: eeaed08997354fe2a32c48ff3d24b46b
skill: ce-prioritize position-taking over the scored board (no ce-* router or skill exists on this host — registry exposes only agent-reach — the standing disclosed deviation since pass 2; scoring methodology applied in-thread)
tier: 1 - selection is a two-way door; a wrong batch costs a cycle, not the repository
disclosure: pi exposes no subagent primitive; grounding and scoring ran in-thread in one context; no panel was summoned. Scores carried from cycles 3-7 where no evidence moved (no independence claimed over them); new cycle-8 scores (U73/U74/U75/U76) and re-annotated items (U18, U56, U62, U70) are this session's own.
---

# Cycle 8 implementation batch selection

Scores every unresolved roadmap packet — the cycle-8 set (U73/U74/U75/U76 remediation,
minted from the pass-8 findings) plus the standing residuals — from
`.hermes/plans/autonomy-prop_8c5390ffe26640fa.md` (cycle-8 extension, lines 1010-1222) on
the same five axes, 1-5 scale. **Impact** = value if done. **Delay risk** = cost of leaving
it undone another cycle. **Effort** = 5 is cheapest. **Dep-freedom** = 5 means nothing gates
it. **Strategic** = leverage on later work. **Total** is the simple sum, shown for ranking
only — gates override totals. Board movements this cycle: U73/U74/U75/U76 minted from the
pass-8 reopen set (F1-F7 + carried P5/P8 newly homed); **U18's P5 half is absorbed by U76**
(P5 apply-loop containment), U18's residual shrinks to P6 (support-file atomic writes);
U56's scope grew again (+F6 tool-payload validation); U62's KTD28 was re-verified this cycle
(index LIVE, 98,326 skills, PR #101237 still open — stays double-gated); U70's feasibility
was CONFIRMED on the installed v0.21.3 host (no upstream wait).

Grounding this cycle: pass-8 assessment (this run, same day) re-derived every finding fresh
on shipped `main@d1a7f57` — every defect this batch targets was reproduced hours ago with
one-liner probes recorded verbatim in
`docs/assessment/2026-09-21-adversarial-repository-assessment-pass8.md` (F1 `"no tests
failed, deploy failed: connection refused"` → False while `"0 failed, …"` → True; F2 a
2-message id-less session imports 1 of 2 events; F3 `{"code": 226}` → error; F4
`{"status": 500}` → success). Tree state at selection: `d1a7f57` + the uncommitted cycle-8
roadmap append and the pass-8 assessment doc (no code changes since pass 8); pytest 344/344
(28.96s, no `-q`), PATH ruff 0.16.7 at 63 errors / 48 fixable (flat), corpus
`scripts/repro-pass7.py` 35/35 sane.

## Scoring

| Item | Impact | Delay risk | Effort | Dep-freedom | Strategic | Total | Gate status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| U73 classifier truth-table completion (F1+F3+F4; the S1/S2/N1/N3/N4 class, 5th iteration) | 5 | 5 | 4 | 5 | 5 | 24 | open; F1 is a P2 and the class's FOURTH fresh defect in as many passes — the asymmetry means every comma-joined success-shaped clause still poisons `error_events` permanently (append-only history); probes pre-written in the pass-8 appendix |
| U74 ingest identity integrity (F2) | 5 | 4 | 5 | 5 | 4 | 23 | open; P2; unlike N2 (query-time, recoverable) F2's dropped rows are NEVER STORED — permanent evidence loss for id-less/legacy transcripts; fix is a fallback-id + counter, the smallest unit on the board |
| U76 crash containment for apply/import loops (carried P5+P8, both P2; absorbs U18's P5 half) | 4 | 4 | 4 | 5 | 3 | 20 | open; both defects carried since pass 2/6; mid-loop exception loses the run JSON AFTER skills mutated; a `\xff` legacy file aborts the WHOLE import; two fault-injection tests, no design risk |
| U75 single-writer lockfile (F5) | 4 | 3 | 4 | 5 | 4 | 20 | open; P3; lost-update needs timer+CLI overlap (rare) vs. F1/F2 corrupting evidence on EVERY pass; lock policy (stale recovery, fail-fast UX) deserves undivided review — first alternate, pull-in criteria below |
| U69 authoritative attribution from host (RF-55/56) | 5 | 3 | 3 | 4 | 5 | 20* | KTD26-gated; feasibility RE-CONFIRMED this cycle (hook registered `hermes_cli/plugins.py:129`; `tools/skill_usage.py` facts durable); structural end of the N2/S6/F2 heuristic layer — must come AFTER U74 proves the disclosure counters it may retire |
| U38 source-aware evidence pipeline | 5 | 3 | 4 | 5 | 5 | 22* | KTD26-gated; dependency is U73's honest signal (poisoned today by F1) |
| U6 bootstrap default alignment | 4 | 3 | 4 | 5 | 4 | 20 | open; carried; user-visible default flip needs docs pairing; next batch |
| U70 backfill MRU early-stop (N6) | 3 | 3 | 4 | 5 | 3 | 18 | open; feasibility CONFIRMED (SQL-side `ORDER BY last_active DESC … LIMIT ? OFFSET ?` at `hermes_state_sessions.py:1365`; plugin already imports `hermes_state.SessionDB` at `backfill.py:481`) — still a P3 performance property on correct results |
| U47 routing-budget curation | 4 | 2 | 4 | 5 | 4 | 19* | KTD26-gated; wants U73's honest signal |
| U26 rerank oversampling (C1) | 4 | 3 | 4 | 5 | 3 | 19 | open; carried |
| U21 publish-safety gate | 5 | 4 | 3 | 3 | 5 | 20 | gated (KTD26) |
| U12 upstream trust interop | 5 | 4 | 3 | 3 | 5 | 20 | gated (KTD26) |
| U56 hygiene (+F6, +N7, +ST-6 CI leg, ruff bump) | 3 | 3 | 3 | 5 | 3 | 17 | open; held — the 48 ruff auto-fixables churn exactly the files U73/U74 open (`candidates.py`, `backfill.py`); one file open once per batch (cycle-6 lesson) |
| U8 dedupe scan | 5 | 3 | 2 | 3 | 5 | 18 | gated; wants U19 |
| U30 plugin-apply ledger attribution | 4 | 3 | 3 | 4 | 4 | 18 | gated; after U69 |
| U33 circuit breaker | 4 | 3 | 4 | 3 | 4 | 18 | gated |
| U55 duplicate-name collision reporting | 3 | 2 | 4 | 5 | 4 | 18 | open; held — rides U59's vocabulary |
| U57 bundled-origin provenance | 4 | 2 | 4 | 4 | 4 | 18* | KTD26-gated |
| U40 host-linter apply gate | 4 | 2 | 4 | 4 | 4 | 18* | KTD26-gated |
| U41 cron-referenced-skill protection | 4 | 2 | 4 | 5 | 3 | 18* | KTD26-gated |
| U60 outcome-delta gate (absorbs U24) | 5 | 3 | 3 | 2 | 5 | 18* | KTD26-gated |
| U58 staleness reconciliation | 4 | 2 | 3 | 4 | 4 | 17* | KTD26-gated |
| U49 agentskills spec conformance | 3 | 2 | 4 | 5 | 3 | 17* | KTD26-gated |
| U23 evidence retention + compaction | 3 | 4 | 3 | 3 | 3 | 16 | gated |
| U42 workspace-scoped backfill | 3 | 2 | 4 | 5 | 2 | 16* | KTD26-gated |
| U72 read-only MCP exposure | 3 | 2 | 4 | 4 | 3 | 16* | KTD26-gated + demand-gated |
| U18 residual (P6 support-file atomic writes only; P5 absorbed by U76) | 3 | 2 | 4 | 5 | 3 | 17 | open; board note: absorbed half recorded, history preserved |
| U10 missed-trigger detection | 4 | 2 | 3 | 3 | 4 | 16 | gated |
| U9 staleness (+U49 pin) | 4 | 2 | 3 | 3 | 4 | 16 | gated |
| U22 anti-pattern ledger | 4 | 3 | 3 | 3 | 4 | 17 | gated |
| U20 hygiene (cycle-2 P3s) | 2 | 2 | 3 | 5 | 2 | 14 | open; carried |
| U25 candidates-decide | 2 | 2 | 4 | 3 | 3 | 14 | gated |
| U14 static HTML report | 3 | 1 | 4 | 4 | 2 | 14 | gated |
| U11 hub managed-block rebase | 4 | 2 | 2 | 2 | 4 | 14 | gated; wants U18 |
| U13 native cron backend | 3 | 2 | 3 | 2 | 3 | 13 | gated |
| U61 knowledge-unit demotion | 3 | 2 | 2 | 3 | 3 | 13* | KTD26-gated |
| U71 corruption visibility (N8) | 3 | 3 | 3 | 5 | 3 | 17 | open; held — delicate connection-lifecycle work, pairs with U69 |
| U19 identity/dedup-key unification | 3 | 3 | 3 | 5 | 3 | 17 | open; NOTE: U74 touches the same dedupe key — U19's scope must be re-read after U74 lands |
| U50 hub-source staleness | 3 | 1 | 3 | 2 | 3 | 12 | KTD24 demand-gated |
| U34 fleet-library conflict report | 2 | 2 | 3 | 2 | 2 | 11 | KTD14 demand-gated |
| U62 ecosystem duplicate check | 3 | 1 | 4 | 1 | 2 | 11 | double-gated: KTD26 + KTD28 (re-verified this cycle: index LIVE 98,326 skills, PR #101237 still OPEN — technical gate half-met) |
| U68 / U67 / U5 / U29 | — | — | — | — | — | closed | shipped in cycle 7 (b1401a4) — pass-8 verified all claims fixed |

Carried scores are cycles 3-7's where no evidence moved; re-annotated this cycle: U73/U74/
U75/U76 (new), U18 (P5 half absorbed by U76), U56 (scope +F6), U62 (KTD28 re-verified,
still gated), U70 (feasibility confirmed), U19 (dependency note: re-read after U74). The *
marks KTD26-gated packets (remediation precedes extension); U38's raw 22 and U69's 20 would
both place above the batch line without the gate — the gate holds because F1 (U73) still
poisons the exact signal both would carry, and F2 (U74) is the ingest layer U69 would
eventually own: proving its disclosure counters first is the dependency direction that
ends the class instead of re-finding it.

## Selected batch: U73 + U74 + U76

The **evidence-truth end-to-end batch** — classification truth (F1/F3/F4), ingest truth
(F2), run-state truth (P5/P8) — closing **every P2 that pass 8 reproduced** in one cycle:
after it lands, every pass-8 finding is either fixed (F1-F4, P5, P8) or has a named
next-batch home (F5→U75 first alternate, F6/F7→U56). Banner: **"Evidence is truthful
end-to-end: failure text is classified honestly whatever its clause shape, every ingested
action is stored and counted visibly, and no single bad candidate or bad legacy file can
destroy the run's record."**

| CU | Packet | Files | AC summary (full AC/E in the roadmap, cycle-8 extension, lines ~1046-1093) |
| --- | --- | --- | --- |
| CU-AH | U73 (F1+F3+F4) | `candidates.py`, `tests/test_candidates.py` (+ corpus) | clauses split on commas before the keyword scan; success phrases strip-and-rescan exactly like zero-counts (a success phrase clears only the claim it answers); `_HTTP_SUCCESS_CODES` → range `200 <= code < 400`; integer `status` under the same range + `status` strings beginning 4xx/5xx → failure; L15 FORMAT-MATRIX grows success-phrase co-occurrence shapes + a status-payload table; N1/N3/N4 stay-set controls stay green; corpus grows to 35+7 = 42 probes (`repro-pass7.py` extension or `scripts/repro-pass8.py`) |
| CU-AI | U74 (F2) | `backfill.py`, tests | id-less fallback becomes session-unique (`tool-{message_index}-{index}`); skipped duplicates counted and DISCLOSED (`tool_events_skipped_duplicate` in `summary()` stats + human-format output); keyed re-imports stay idempotent (0 new events); `event_rows` retained (KTD32/KTD36) |
| CU-AJ | U76 (P5+P8) | `auto_evolve.py`, `backfill.py`, tests | per-candidate try/except in the apply loop — poison candidate records an error row and the loop continues, run JSON ALWAYS lands; legacy import catches UnicodeDecodeError per file — skip + count (`legacy_skipped_undecodable`), never abort; two fault-injection tests |

Why these three, in one sentence each:

- **U73 (24)** — the class's fifth board-topping entry and the last cheap one: the corpus,
  the matrix harness, and the probes are all already written; every day unfixed, F1 writes
  permanently-wrong `is_error` history for every comma-joined success-shaped clause, and
  the KTD26 gate on U38/U47/U60 stays shut on its account.
- **U74 (23)** — the smallest unit on the board guarding a permanent loss: U68 proved the
  COUNT(*) side, but F2 shows distinct rows never reaching storage at all for id-less
  transcripts — and its visible-drop counter (KTD36) is the disclosure pattern U69 must
  inherit, so this lands before the structural ingestion, not after.
- **U76 (20)** — two carried-since-pass-2/6 P2s homed at last, both pure fault-tolerance
  with pre-derivable tests; a batch whose banner is "evidence is truthful" cannot leave the
  evidence RECORDER able to lose the run record itself.

Coherence: all three units are the same property at three pipeline stages — classify
truthfully (U73), store completely (U74), record survivably (U76) — in three disjoint file
clusters (`candidates.py` / `backfill.py` ingest / `auto_evolve.py`+`backfill.py` legacy
loop), so they parallelize without reopening a file the cycle-6 lesson warns about; the one
shared file (`backfill.py`, U74+U76-legacy-half) is a read-path vs. import-loop split with
no overlap.

### Why the near-misses stay out

- **U75 (20)** — same integrity theme but the failure needs concurrent invocation
  (timer+CLI overlap) while F1/F2 corrupt evidence on every single pass; and its lock
  policy (stale-lock recovery, fail-fast reason strings, evidence-root path) is design
  surface that deserves its own review attention rather than riding as a fourth unit.
  First alternate with explicit pull-in criteria: joins the batch ONLY if U73/U74/U76 are
  green with the full matrix passing AND its refusal test (lock held → second run exits
  clean with reason, writes nothing) fits under ~60 lines; otherwise it is next batch's
  opener with U56.
- **U69 (20\*)** — KTD26 gate as always, plus a NEW dependency direction this cycle: U69
  may RETIRE U74's heuristic layer (KTD32), so U74's counters must exist and prove the
  disclosure pattern first; jumping straight to U69 would re-derive F2's visibility rules
  under time pressure instead of inheriting them.
- **U56 (17)** — held a third cycle for the same reason: its 48 ruff auto-fixables churn
  `candidates.py`/`backfill.py` exactly when U73/U74 open them; batching the churn after
  the correctness fixes keeps the review diff pure.
- **U70 (18)** — feasibility now confirmed (nothing upstream to wait for) but it is
  performance on already-correct results; wrong theme for the truth banner, next batch.
- **U6 (20)** — user-visible default flip needs its docs pairing; carries one more cycle.
- **U38/U47/U21/U12/U60 and other gated extensions** — KTD26 holds until this remediation
  batch lands; U38's dependency is literally U73's honest signal.

### Verification plan the implement phase inherits

Full suite green at 344 + new (matrix, ingest, fault-injection) tests; corpus run 42/42
sane (35 stay-green + 7 pass-8 probes) via dot-count or no-`-q` invocation (#5349);
`ruff check` with the SAME binary both arms (PATH 0.16.7, #5442) flat at 63; every probe in
the pass-8 appendix returns the fixed verdict; `event_rows` + new counters visible in
human-format output; no Git topology decisions made here (per campaign rule) — change
units only.
