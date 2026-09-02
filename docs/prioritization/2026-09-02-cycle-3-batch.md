---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-3-batch-selection
mode: repo-grounded
run: 682bd7e431e34f7b9efc0c881cde253a
phase: prioritize
attempt: da42d07596c747d88a1a7b238e7b8318
skill: ce-pov (approach-set position over the roadmap's enumerated unit set; no dedicated selection skill is installed - same route the fleet's prior prioritize phases took)
tier: 1 - selection is a two-way door; a wrong batch costs a cycle, not the repository
disclosure: pi exposes no subagent primitive; grounding and scoring ran in-thread in one context; no panel was summoned and no independence is claimed over the cycle-2 scores, which are carried where nothing changed
---

# Cycle 3 implementation batch selection

Scores every unresolved roadmap packet - the remaining cycle-1 units, the cycle-2
packets (U15-U25), and the cycle-3 packets (U26-U34) from `.hermes/plans/
autonomy-prop_8c5390ffe26640fa.md` - on the same five axes, 1-5 scale. **Impact** =
value if done. **Delay risk** = cost of leaving it undone another cycle. **Effort** =
5 is cheapest. **Dep-freedom** = 5 means nothing gates it. **Strategic** = leverage
on later work. **Total** is the simple sum, shown for ranking only - gates override
totals.

Grounding this cycle: the cycle-2 selection (U15+U7a+U16+U17+U18) was never
implemented - no fix phase has run on this tree - so its five defects were re-verified
open THIS session with bounded reads, alongside the three new cycle-3 findings:
`pattern.sub(block, …)` at `auto_evolve.py:386` still feeds evidence-derived text in as
a replacement template (U15/B7); `storage.py:154` `connect()` is still bare - no
timeout/WAL/busy_timeout (U7a/B10); `cli.py:786/803` still rewrite explicit 0 via
`int(x or 5)` (U16/B8); `_systemd_quote` (`:190`) still feeds `OnCalendar` values
through unvalidated at `:1386` (U17/B9); the apply loop at `auto_evolve.py:1479` still
has no per-candidate boundary (U18/B11); `semantic.py` still truncates to top-limit
before rerank pairs are built (U26/B13); `storage._looks_like_error` still carries its
own keyword corpus diverging from `candidates._is_tool_failure` (U28/B15);
`review_queue.update_status` still has no production caller (U25); the 100_000 hard
cap still exists as two literals (`guarded_apply.py:25`, `candidates.py:32` - U5
residual). Pass-3 re-reproduced R1-R4 empirically this session (assessment artifact,
table lines 18-21).

## Scoring

| Item | Impact | Delay risk | Effort | Dep-freedom | Strategic | Total | Gate status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| U15 managed-block replacement safety (B7) | 5 | 5 | 4 | 5 | 5 | 24 | open |
| U7a storage WAL/busy_timeout/retry (B10) | 5 | 5 | 4 | 5 | 5 | 24 | open; KTD8-pulled forward |
| U16 numeric-flag contract repair (B8) | 5 | 4 | 4 | 5 | 4 | 22 | open |
| U17 scheduler unit hardening (B9) | 5 | 4 | 4 | 5 | 3 | 21 | open |
| U28 single error classifier (B15) | 4 | 4 | 4 | 5 | 4 | 21 | open; new this cycle |
| U18 apply-loop resilience (B11) | 4 | 4 | 3 | 5 | 4 | 20 | open |
| U6 bootstrap default alignment | 4 | 3 | 4 | 5 | 4 | 20 | open; default flip needs README/quickstart coordination |
| U12 upstream trust interop | 5 | 4 | 3 | 3 | 5 | 20 | KTD7/KTD12-gated |
| U21 publish-safety gate | 5 | 4 | 3 | 3 | 5 | 20 | gated; builds on U15's neutralizer |
| U26 rerank oversampling (B13) | 4 | 3 | 4 | 5 | 3 | 19 | open; new this cycle |
| U29 host-ledger read integration | 4 | 3 | 3 | 4 | 5 | 19 | KTD12-gated; new this cycle |
| U5 residual (confirm + close) | 3 | 2 | 5 | 5 | 3 | 18 | open; rides the U7 batch |
| U27 rollback target-root default (B14) | 4 | 2 | 4 | 5 | 3 | 18 | open but held - see below |
| U8 dedupe scan | 5 | 3 | 2 | 3 | 5 | 18 | gated; wants U19 + U7's semantic rider |
| U30 plugin-apply ledger attribution | 4 | 3 | 3 | 4 | 4 | 18 | gated; after U29 |
| U33 circuit breaker | 4 | 3 | 4 | 3 | 4 | 18 | gated; U22's escalation tier |
| U19 identity + dedup-key unification (B12) | 3 | 3 | 3 | 5 | 3 | 17 | open |
| U22 anti-pattern ledger | 4 | 3 | 3 | 3 | 4 | 17 | gated; after U21 |
| U31 doctor --host-compat sweep | 4 | 2 | 3 | 4 | 4 | 17 | gated; after U29/U30 |
| U7b version single-sourcing | 3 | 2 | 4 | 5 | 3 | 17 | open |
| U9 staleness + spec conformance | 4 | 2 | 3 | 3 | 4 | 16 | gated |
| U10 missed-trigger detection | 4 | 2 | 3 | 3 | 4 | 16 | gated |
| U32 context-budget report | 3 | 2 | 4 | 4 | 3 | 16 | gated; after U8 |
| U23 evidence retention + compaction | 3 | 3 | 3 | 3 | 3 | 15 | gated; shares KTD9 flag contract with U16 |
| U13 native cron backend | 3 | 2 | 3 | 2 | 3 | 13 | gated; still sequenced after U12 |
| U7c CI lint/type gates | 3 | 2 | 3 | 5 | 3 | 14 | open; wants a stable codebase to gate |
| U14 static HTML report | 3 | 1 | 4 | 4 | 2 | 14 | gated; after U7 |
| U11 hub managed-block rebase | 4 | 2 | 2 | 2 | 4 | 14 | gated; wants U18 |
| U20 hygiene batch (cycle-2 P3s) | 2 | 2 | 3 | 5 | 2 | 14 | open |
| U25 candidates-decide | 2 | 2 | 4 | 3 | 3 | 14 | gated; may ride U20 |
| U24 outcome-linked telemetry | 3 | 2 | 2 | 2 | 3 | 12 | gated; depends on U22 + U7a + U28 |
| U34 fleet-library conflict report | 2 | 2 | 3 | 2 | 2 | 11 | KTD14 demand-gated |

B-item discharge map: B7->U15, B8->U16, B9->U17, B10->U7a, B11->U18, B12->U19,
B13->U26, B14->U27, B15->U28. Selecting a unit discharges its B-item; no B-item is
selectable on its own. This batch discharges seven of the nine open B-items; B12 (U19)
and B14 (U27) stay open for the next batch.

## Selected batch: U15 + U7a + U16 + U17 + U18 + U26 + U28

The cycle-2 reliability batch, unchanged at its core because none of it landed - every
one of its five defects was re-verified open this session - plus the two cycle-3
remediation packets that are small, mechanically reproduced, and disjoint from the
contended surfaces. **"An unattended run must never crash, never drop evidence, never
delete the wrong thing, never corrupt the evidence record, never silently cap the
reranker, and must always emit a report."** All seven are in the P1/loss/corruption
class; zero user-visible default changes (U16 aligns behavior to help text that
already documents it); zero version gates; zero unsettled decisions; each verified by
a mechanical reproducer that exists (pass-3 R1-R4 one-shots plus the cycle-2 repro
corpus under `/tmp/assess/ce-assess-76416fd2/`).

### Why cycle 2's five stand unchanged

They were selected last cycle on evidence that is still true today (verified live this
session, anchors above), they remain the top of the board (24/24/22/21/20), and
re-selecting anything else would demote verified crash/data-loss defects for novelty's
sake. U15 and U7a are still the two certainties: the auto-run crash on any
already-blocked skill, and the 5.01s lock-and-drop on any concurrent writer.

### Why U26 and U28 ride

1. **U28 (21) is the batch's one data-corruption packet and unblocks honest
   telemetry.** Every ingest today writes `is_error=1` for success strings like
   "3 passed, no errors found" (`storage.py:113-128`, re-verified; pass-3 R2). Those
   rows gate auto-evolve thresholds and are exactly what U24 will mine - corrupted
   input now means corrupted cohorts later. The fix is delete-or-delegate one private
   classifier onto the candidates-side structured-first one, with U2's adversarial
   corpus test extended to the ingest path. Strategic 4: it converts a two-source
   truth problem into the KTD9-style single-contract precedent, same shape as U16.
2. **U26 (19) converts an advertised flag from silently capped to real.**
   `--rerank-candidates` currently cannot promote anything the embedder ranked below
   the limit (truncation at `semantic.py:246` precedes pair construction), so the flag
   mostly reorders the slice the embedder already chose. Fix is oversample-then-truncate
   plus one below-fold fixture (pass-3 R4 is that test). `semantic.py` is touched by
   nothing else in the batch - fully disjoint.
3. **Both are cheap riders, not scope creep.** Two files added to the batch's surface
   set, both with ready mechanical tests, both independent of every other packet's
   behavior. The roadmap sequenced exactly this ("U26-U28 riding that batch", KTD12).

### Why not the alternatives

- **U27 (18), despite the roadmap's U26-U28 line?** Held deliberately: its surface is
  `guarded_apply.py:486-501`, which overlaps U18's atomic-write work in the same file -
  the exact contended-file hazard cycle 2 named when it dropped U5 from that batch -
  and its delay risk is only 2 (rollback is an on-demand failure path, not a default
  run surface). It becomes the head of batch 2. This is a selection refinement of the
  roadmap's sequencing note, not a contradiction of its order: U27 still lands before
  any extension.
- **U6 (20)?** Same call as cycle 2: user-visible default flip needing
  README/quickstart/example coordination and its own focused review; belongs to the
  "caps and defaults" batch over the now-stable write path.
- **U12 (20), U21 (20), U29 (19)?** All KTD7/KTD12-gated - remediation precedes
  extension, a conductor-settled decision this cycle re-affirmed as KTD12. U29 is the
  strongest new extension (ledger verified live on this host) and is the first
  extension to pull the moment hardening lands; U21 additionally builds on U15's
  neutralizer.
- **U19 (17)?** Discharges B12, but the broken paths are opt-in flags; next-batch head
  with U27 and U20, unchanged from cycle 2's judgment.
- **U28 vs U7a same-file worry?** Noted as adjacency: U7a touches `storage.py:154`
  connect-time pragmas, U28 touches `:113-128` ingest classification - disjoint
  functions in one file, kept as separate hunks; the hazard cycle 2 flagged was
  same-function contention (U5/U18 in the apply path), which this is not.

### Batch shape for the implement phase

Surfaces, with the three adjacencies called out: U15 `auto_evolve.py:386`
(`pattern.sub(lambda _: block, …)` or escaped replacement) + second-run corpus test;
U16 `cli.py:786/803` parse-explicit 0 (for `--max-reference-files`, `--max-skills`,
`--min-evidence`, `--variants`) + `auto_evolve.py` prune guard + REPLACING the
assertion at `tests/test_auto_evolve.py:1106` (it codifies the bug); U17
`auto_evolve.py:190/1386` schedule validation + `%%` escaping + unit-content tests;
U18 `auto_evolve.py:1479` candidate-loop boundary + support-file ordering +
`guarded_apply.py` temp+rename atomic writes + interruption fixture; U7a
`storage.py:154` connect-time WAL/busy_timeout/bounded retry + `hooks.py` error
handling + concurrency test (`repro_h4_lock_drop.py` shape); U26 `semantic.py:246`
oversample-then-truncate + below-fold rerank fixture (R4 shape); U28 `storage.py:113`
delegate or delete `_looks_like_error` onto the candidates classifier + corpus test
extension (R2 shape). Adjacency 1: U15/U16/U18 all touch `auto_evolve.py` - separate
hunks. Adjacency 2: U18 owns `guarded_apply.py` this batch (why U27 is out).
Adjacency 3: U7a/U28 share `storage.py` - connect vs ingest, separate hunks.
Mechanical gates already exist and were re-run this session by pass-3 (R1-R4) plus the
cycle-2 corpus. Original roadmap Acceptance governs: feature branch off main, targeted
tests per changed surface (never the full suite as the gate), push to `fork` only -
remote policy per KTD2/KTD11/KTD15, and NOT this phase.

## Next batches (provisional, not selected)

- Batch 2 (next cycle): U27 + U19 + U20 - "correctness tails": discharges B14 and
  B12, closes the cycle-2 P3 list; U25 rides as the cheap review-queue surface;
  U5's confirm-and-close residual rides whichever batch touches the U7 hygiene set.
- Batch 3: U5/U6 + U7b/U7c - "caps, defaults, and gates" over the now-stable write
  path (U7c's lint/type CI gate lands last so it gates a settled codebase; it also
  finally enforces the ruff 65 that CI currently never checks).
- Extensions then open per roadmap order with U12 first (highest delay risk), then
  U21 -> U22 + U33 (escalation tier) -> U29 -> U30 -> U31 (ledger read before write,
  doctor last) -> U8 then U32 -> U23 -> U24 last (needs U22, U7a, and U28's clean
  cohorts). U34 stays KTD14 demand-gated. U13 stays behind U12 per sequencing; its
  version gate is already lifted.

*Read-only selection; no code changed, nothing committed or pushed.*
