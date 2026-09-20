---
date: 2026-09-20
topic: hermes-curator-evolver-cycle-7-batch-selection
mode: repo-grounded
run: 78a174fbdec14ee3844ff327a59cef78
phase: prioritize
attempt: fe9da7a90e184408a678ddcdb5bcc16b
skill: ce-prioritize position-taking over the scored board (no ce-* router or skill exists on this host — registry exposes only agent-reach — the standing disclosed deviation since pass 2; ce-code-review/ce-prioritize methodology applied in-thread)
tier: 1 - selection is a two-way door; a wrong batch costs a cycle, not the repository
disclosure: pi exposes no subagent primitive; grounding and scoring ran in-thread in one context; no panel was summoned. Scores carried from cycles 3/4/5/6 where no evidence moved (no independence claimed over them); new cycle-7 scores (U67/U68/U70/U71/U69/U72) and re-annotated items (U49, U56, U60, U62, U29) are this session's own.
---

# Cycle 7 implementation batch selection

Scores every unresolved roadmap packet — the cycle-7 set (U67/U68/U70/U71 remediation,
U69/U72 extensions) plus the standing residuals — from
`.hermes/plans/autonomy-prop_8c5390ffe26640fa.md` (cycle-7 extension, lines 671-873) on the
same five axes, 1-5 scale. **Impact** = value if done. **Delay risk** = cost of leaving it
undone another cycle. **Effort** = 5 is cheapest. **Dep-freedom** = 5 means nothing gates it.
**Strategic** = leverage on later work. **Total** is the simple sum, shown for ranking only —
gates override totals. Board movements this cycle: U69/U72 new from research; U29 closes INTO
U69 (KTD34); N7 folded into U56; U67/U68/U70/U71 minted from the pass-7 reopen set.

Grounding this cycle: pass-7 assessment (this run, ~3h ago) re-derived every finding fresh on
`a76962c` with a 35-probe corpus — every defect this batch targets reproduced hours ago at
`/tmp/repro-pass7.py` (8253 bytes, still present; N1 `"1,000 failed"` → False; N2 3-event
hook burst → `event_count=1`, eligibility 0; N3 comma-join zero-clear; N4 `candidates.py:135`
`_HTTP_SUCCESS_CODES = frozenset({200, 201, 202, 204})` — 203/206/301/304 absent, verified at
selection time). Tree state at selection: `a76962c` + the uncommitted cycle-7 roadmap append
and two docs (no code changes since pass 7); pytest 287/287, ruff 63 errors / 48 fixable
(flat since cycle 5, ungated). Cycle-6 batch is merged via PR #1 — no commit-gate debt.

## Scoring

| Item | Impact | Delay risk | Effort | Dep-freedom | Strategic | Total | Gate status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| U67 classifier format-matrix (N1+N3+N4+N5; U51 3rd reopen) | 5 | 5 | 4 | 5 | 5 | 24 | open; 4th consecutive cycle a classifier defect tops the board; corpus already written in repro-pass7.py |
| U68 attribution burst counting (N2; U54 reopen) | 5 | 3 | 4 | 5 | 4 | 21 | open; P2; aggregation is query-time so undercounts are recoverable — but the gate starves today |
| U18 apply-loop resilience (P5/P6) | 4 | 4 | 3 | 5 | 4 | 20 | open; carried; disjoint next slot with U19 |
| U6 bootstrap default alignment | 4 | 3 | 4 | 5 | 4 | 20 | open; user-visible default flip — needs docs pairing; next batch |
| U69 authoritative attribution from host (RF-55/56) | 5 | 3 | 3 | 4 | 5 | 20* | KTD26-gated; top extension survivor; absorbs U29; structural end of the N2/S6 class |
| U38 source-aware evidence pipeline | 5 | 3 | 4 | 5 | 5 | 22* | KTD26-gated; dependency is now U67's honest signal |
| U70 backfill MRU early-stop (N6; U52 reopen) | 3 | 3 | 4 | 5 | 3 | 18 | open; P3-perf (results correct); first alternate — pull-in criteria below |
| U55 duplicate-name collision reporting | 3 | 2 | 4 | 5 | 4 | 18 | open; held — output format rides U59's vocabulary, next batch |
| U47 routing-budget curation | 4 | 2 | 4 | 5 | 4 | 19* | KTD26-gated; wants U67's honest usage signal |
| U26 rerank oversampling (C1) | 4 | 3 | 4 | 5 | 3 | 19 | open; carried; disjoint next slot |
| U56 hygiene (+N7 version single-sourcing, ST-6 CI leg, ruff bump) | 3 | 3 | 3 | 5 | 3 | 17 | open; held — ruff gate + 48 auto-fixables + CI-leg churn exactly the files U67/U68 open |
| U19 identity/dedup-key unification | 3 | 3 | 3 | 5 | 3 | 17 | open; pairs with U18 |
| U71 corruption visibility + host-sqlite alignment (N8) | 3 | 3 | 3 | 5 | 3 | 17 | open; held — same file as U68 (storage.py) but delicate connection-lifecycle work; open storage.py once per batch (cycle-6 lesson); pairs with U69 |
| U21 publish-safety gate | 5 | 4 | 3 | 3 | 5 | 20 | gated (KTD26) |
| U12 upstream trust interop | 5 | 4 | 3 | 3 | 5 | 20 | gated (KTD26) |
| U8 dedupe scan | 5 | 3 | 2 | 3 | 5 | 18 | gated; wants U19 |
| U30 plugin-apply ledger attribution | 4 | 3 | 3 | 4 | 4 | 18 | gated; after U29→U69 |
| U33 circuit breaker | 4 | 3 | 4 | 3 | 4 | 18 | gated |
| U57 bundled-origin provenance | 4 | 2 | 4 | 4 | 4 | 18* | KTD26-gated |
| U40 host-linter apply gate | 4 | 2 | 4 | 4 | 4 | 18* | KTD26-gated |
| U41 cron-referenced-skill protection | 4 | 2 | 4 | 5 | 3 | 18* | KTD26-gated |
| U60 outcome-delta gate (absorbs U24) | 5 | 3 | 3 | 2 | 5 | 18* | KTD26-gated; U51-dep satisfied at tested edges, full satisfaction rides U67; replay harness optional (benchmarks public) |
| U58 staleness reconciliation vs native curator | 4 | 2 | 3 | 4 | 4 | 17* | KTD26-gated |
| U49 agentskills spec conformance | 3 | 2 | 4 | 5 | 3 | 17* | KTD26-gated; evidence moved (SKILL.md:4 top-level `version` non-conformant; `metadata.version` is spec-native) — impact up, still gated |
| U23 evidence retention + compaction | 3 | 4 | 3 | 3 | 3 | 16 | gated; #101316 horizon still raising delay risk |
| U42 workspace-scoped backfill | 3 | 2 | 4 | 5 | 2 | 16* | KTD26-gated |
| U72 read-only MCP exposure | 3 | 2 | 4 | 4 | 3 | 16* | KTD26-gated + demand-gated on a real consumer |
| U9 staleness (+U49 pin) | 4 | 2 | 3 | 3 | 4 | 16 | gated |
| U10 missed-trigger detection | 4 | 2 | 3 | 3 | 4 | 16 | gated |
| U22 anti-pattern ledger | 4 | 3 | 3 | 3 | 4 | 17 | gated; U60 supersedes its measured half (KTD29) |
| U5 residual (confirm + close) | 3 | 2 | 5 | 5 | 3 | 18 | open; rides U67's file — confirm cap constants single-sourced across guarded_apply/candidates and close |
| U20 hygiene (cycle-2 P3s) | 2 | 2 | 3 | 5 | 2 | 14 | open; carried |
| U25 candidates-decide | 2 | 2 | 4 | 3 | 3 | 14 | gated |
| U14 static HTML report | 3 | 1 | 4 | 4 | 2 | 14 | gated |
| U11 hub managed-block rebase | 4 | 2 | 2 | 2 | 4 | 14 | gated; wants U18 |
| U13 native cron backend | 3 | 2 | 3 | 2 | 3 | 13 | gated |
| U61 knowledge-unit demotion | 3 | 2 | 2 | 3 | 3 | 13* | KTD26-gated |
| U50 hub-source staleness | 3 | 1 | 3 | 2 | 3 | 12 | KTD24 demand-gated |
| U34 fleet-library conflict report | 2 | 2 | 3 | 2 | 2 | 11 | KTD14 demand-gated |
| U62 ecosystem duplicate check | 3 | 1 | 4 | 1 | 2 | 11 | double-gated: KTD26 + KTD28 (demand gate met by third-party aggregators; HERMES_INDEX_URL liveness + PR #101237 NOT re-verified this cycle) |
| U29 host-ledger read | — | — | — | — | — | closing | closes INTO U69 per KTD34; dependency line updated, history preserved |

Carried scores are cycles 3/4/5/6's where no evidence moved; re-annotated this cycle: U67/U68/
U70/U71/U69/U72 (new), U49 (impact up — concrete plugin-side spec evidence), U56 (scope grew:
+N7, +ST-6 CI leg, +ruff 0.16.8 bump), U60 (benchmarks public; U51-dep state clarified),
U62 (demand gate met), U29 (absorbed by U69). The * marks KTD26-gated packets (remediation
precedes extension); U38's raw 22 and U69's 20 would both place above the batch line without
the gate — the gate holds because the classifier's 3rd reopen (U67) poisons the exact signal
both would carry, and N2's starvation (U68) blocks the eligibility every extension reads.

## Selected batch: U67 + U68 (+ U5 confirm-and-close rider)

The **format-and-count truth batch** — the fifth consecutive signal-first batch, closing the
pass-7 P2 set entirely: after it lands, every defect pass-7 *reproduced* is either fixed
(N1-N5) or has a named next-batch home (N6→U70, N7→U56, N8→U71). Banner: **"Failure text is
classified truthfully whatever its formatting — grouped counts, comma-joined clauses, every
success-shaped HTTP code — and burst evidence counts one action at a time, so the eligibility
gate stops starving the common agent-loop shape."**

| CU | Packet | Files | AC summary (full AC/E in the roadmap, cycle-7 extension) |
| --- | --- | --- | --- |
| CU-AF | U67 (N1+N3+N4+N5) | `candidates.py`, `cli.py`, `tests/test_candidates.py`, `tests/test_candidates_cli.py` | grouped-number failure counts parse (`\d{1,3}(?:,\d{3})+` and plain, separator-stripped); clause splitting handles comma joins + unspaced sentence joins, zero-count clears only a sole failure claim; `_HTTP_SUCCESS_CODES` covers 2xx with the 3xx decision documented; human CLI summary prints every truthful counter + `metadata_scan_truncated`; repro-pass7 corpus lifts as adversarial test v3 in a full format matrix (widths × separators × clause joins × HTTP codes — L15) |
| CU-AG | U68 (N2) | `storage.py`, `auto_evolve.py`, tests | same-second/same-task/same-skill hook events count individually (rowid- or hash-unique key, or COUNT(*) + report-layer dedupe — design recorded); 3-event probe → `event_count=3`; `min_evidence=2` returns the skill eligible; backfill-path immunity (unique task_ids) test-preserved; `event_rows` AND `event_count` both stay disclosed |
| rider | U5 (confirm + close) | `guarded_apply.py`/`candidates.py` read-only check | cap constants single-sourced (`_MAX_SKILL_CONTENT_CHARS`, `_AUTO_LOADED_SKILL_MAX_CHARS` — cycle-2 correction line) or the divergence recorded and U5 closed with a note |

Why these two, in one sentence each:

- **U67 (24)** — fourth consecutive cycle a classifier defect tops the board, and the stakes
  are the same as U51's but cheaper: `error_events` is append-only, so every day of
  comma-formatted successes silently poisoning `is_error` is permanent history. The corpus is
  already written (`/tmp/repro-pass7.py`), the file is the same one cycle-6 just stabilized,
  and N5 (CLI human disclosure) rides the same theme in the adjacent file.
- **U68 (21)** — the other reproduced P2, and the one that blocks every downstream consumer:
  parallel tool calls in one assistant message are the COMMON agent-loop shape, and the
  min_evidence gate currently returns zero eligible skills for exactly that shape. The fix is
  a surgical aggregation-query change (query-time computation — no history rewrite needed),
  and it must precede U69's structural ingestion so the near-term gate unblocks now.

### Why the near-misses stay out

- **U70 (18)** — real and research-armed (host MRU ordering source-verified), but it is a
  P3 *performance* property on already-correct results, a different theme from the batch's
  truth banner. First alternate with explicit pull-in criteria: joins only if U67/U68 are
  green with CI time remaining AND the monotonicity-probe + early-stop stays under ~80 lines
  including tests. Otherwise next batch's lead unit.
- **U71 (17)** — same file as U68 (`storage.py`) but delicate connection-lifecycle work
  (cache invalidation across quarantine events, host-sqlite alignment). Cycle-6's lesson —
  open `storage.py` once per batch — argues for landing U68's surgical query change now and
  U71's lifecycle work next, paired with U69 which shares its host-alignment surface.
- **U56 (17)** — scope grew usefully (N7, ST-6 CI leg, ruff bump) but every slice churns
  exactly the files this batch opens; the ruff gate belongs with the batch that consumes the
  48 auto-fixables. Next batch, after the code batch lands.
- **U55 (18)** — unchanged from cycle-6: its output format is U59's vocabulary; landing it
  now ships a report U59 would immediately redesign.
- **U6 (20)** — user-visible default flip; ships honestly only with README/quickstart
  pairing, not as a rider.
- **U18 (20)** — real P5/P6, but pairs with U19 as the next disjoint pair; this batch
  already carries four code files across both halves of the ingest pipeline.
- **Every extension (U38-U42, U47-U49, U57-U62, U69, U72)** — KTD26: remediation precedes
  extension. U69 (20 raw) anchors the next extension batch, unlocked the moment this lands.
- **U62** stays double-gated (KTD28 un-re-verified this cycle).

B/N-item discharge map: N1+N3+N4+N5→U67, N2→U68 (N2's structural end→U69), N7→U56,
N6→U70, N8→U71. This batch discharges the entire pass-7 P2/P3 ingest set except the three
named next-batch homes. No N-item is selectable alone.

## Batch-level verification plan (for the implement phase)

1. Re-run `/tmp/repro-pass7.py` after landing: N1 (`"1,000 failed"`, `"10,000 failed, 3
   passed"`), N1ctl (`"2,048 failed"` must STAY True), N3/N3b, N4 (203/206/301/304 → not
   errors) must flip; N2 probe → `event_count=3` and `_eligible_skill_rows(min_evidence=2)`
   returns the skill; N2ctl (backfill-shaped, unique task_ids) must STAY `event_count=3`;
   N5 CLI human output shows the counters. N6/N7/N8 may still reproduce (U70/U56/U71).
   B-class behaviors (honest-store selection, truthful JSON counters) must stay green.
2. `python3 -m pytest` full suite green at the new baseline (287 + corpus v3 + burst/control
   attribution fixtures + CLI disclosure tests); `ruff check hermes_curator_evolver tests`
   ≤ 63 errors (gate lands with U56, next batch).
3. L15 check: the truth-table test enumerates the format MATRIX — digit widths × grouping
   separators (`,` `.` space `_`) × clause-join shapes (comma, unspaced period, semicolon) ×
   HTTP code table — not a width sweep.
4. No default behavior change except the two truth corrections, the counting fix, and the
   CLI disclosure lines; `event_rows` stays disclosed next to `event_count` everywhere both
   appeared.
5. U5 rider: single-sourcing confirmed or divergence recorded; U5's roadmap status moves to
   closed with a note (history preserved, KTD23 pattern).

## Reproduction / verification pointers

```bash
python3 /tmp/repro-pass7.py                                       # N-probe corpus (24/35 matched at assess; 8 deviation classes)
/home/agent/.hermes/hermes-agent/venv/bin/python3 -m pytest -q    # 287 passed (assess baseline)
ruff check hermes_curator_evolver tests 2>&1 | tail -1            # 63 errors, 48 fixable
git -C /work/projects/hermes-curator-evolver log --oneline -1     # a76962c
git -C /work/projects/hermes-curator-evolver status --short       # roadmap append + 2 docs, no code changes since pass 7
grep -n "_HTTP_SUCCESS_CODES" hermes_curator_evolver/candidates.py # :135 frozenset({200, 201, 202, 204}) — N4 verified at selection
sed -n '671,873p' .hermes/plans/autonomy-prop_8c5390ffe26640fa.md  # cycle-7 extension: AC/E source for U67/U68/U70/U71/U69/U72
```
