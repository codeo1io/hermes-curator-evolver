---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-1-batch-selection
mode: repo-grounded
run: 8a1ca9a2a18e440e86bff85efe099474
phase: prioritize
attempt: e3597415a41e4f4f9e95e2a77fb498b5
skill: ce-pov (approach-set position over the roadmap's enumerated unit set; no dedicated selection skill is installed - same route the fleet's prior prioritize phases took)
tier: 1 - selection is a two-way door; a wrong batch costs a cycle, not the repository
---

# Cycle 1 implementation batch selection

Scores every unresolved roadmap packet - the fourteen cycle-1 units (U1-U14) from
`.hermes/plans/autonomy-prop_8c5390ffe26640fa.md` - on five axes, 1-5 scale. **Impact** =
value if done. **Delay risk** = cost of leaving it undone another cycle. **Effort** = 5 is
cheapest. **Dep-freedom** = 5 means nothing gates it. **Strategic** = leverage on later work.
**Total** is the simple sum, shown for ranking only - gates override totals.

| Item | Impact | Delay risk | Effort | Dep-freedom | Strategic | Total | Gate status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| U1 NUL sanitizer + regression | 5 | 5 | 5 | 5 | 4 | 24 | open |
| U3 rollback completeness + retention | 5 | 4 | 3 | 5 | 5 | 22 | open |
| U2 tokenized classifiers | 4 | 4 | 4 | 5 | 4 | 21 | open |
| U6 bootstrap default alignment | 4 | 3 | 4 | 5 | 4 | 20 | open |
| U12 upstream trust interop | 5 | 4 | 3 | 3 | 5 | 20 | KTD1-gated (extensions after hardening) |
| U4 backfill isolation + ordering | 3 | 3 | 4 | 5 | 3 | 18 | open |
| U5 byte-based caps | 3 | 2 | 5 | 5 | 3 | 18 | open; shares guarded_apply.py with U3 |
| U8 dedupe scan | 5 | 3 | 2 | 3 | 5 | 18 | KTD1-gated; wants U2 + U7's semantic rider |
| U9 staleness + spec conformance | 4 | 2 | 3 | 3 | 4 | 16 | KTD1-gated |
| U10 missed-trigger detection | 4 | 2 | 3 | 3 | 4 | 16 | KTD1-gated |
| U7 hygiene batch | 3 | 2 | 2 | 4 | 4 | 15 | open; wants U1-U6 landed first (avoid rework) |
| U14 static HTML report | 3 | 1 | 4 | 4 | 2 | 14 | KTD1-gated; after U7 |
| U11 hub managed-block rebase | 4 | 2 | 2 | 2 | 4 | 14 | KTD1-gated; wants U3's write-path integrity |
| U13 native cron backend | 3 | 2 | 3 | 1 | 3 | 12 | hard version gate: host hermes-agent 0.20.6 < required 0.21.0 |

B-item discharge map: B1->U1, B2->U2, B3->U3, B4->U4, B5->U5, B6->U6. Selecting a unit
discharges its B-item; no B-item is selectable on its own.

## Selected batch: U1 + U2 + U3 + U4

**"Make recorded evidence true and every write reversible" - four correctness packets, zero
user-visible default changes, zero version gates, zero unsettled decisions, each verified by a
mechanical reproducer that already exists or is specified in the unit's E line.**

### Why these four

1. **U1 first, and nothing outranks it.** The NUL defect (B1) is the root cause of the
   original roadmap Problem - "observed 1 error-related event" - and it breaks the plugin's
   core promise for any poisoned skill: every auto-apply fails validation and rolls back
   forever, silently, because hooks swallow errors. Re-verified live this session: F1 still
   reports `nul_stored=True in_managed_block=True validator_ok=False`. Cheapest unit on the
   board (one sanitizer plus regression), highest delay risk (each passing day the daily timer
   keeps manufacturing perpetual-rollback loops).
2. **U2 is the truth of the queue.** F2 still reports `type=replay_benchmark is_error=True`
   for a successful `skill capabilities updated` result - the pipeline learns the opposite of
   what happened. Every downstream feature (U8 dedupe candidates, U9 staleness, U10
   missed-triggers) consumes these classifications, so classifier truth compounds across the
   whole extension roadmap.
3. **U3 is the safety net the trust story leans on.** README sells staged verify, backups,
   and restore drills; F3 still shows rollback leaving the apply's support file orphaned on
   disk, the references/ directory grows without bound, and rollback trusts manifest paths
   unvalidated. A reviewer who reproduces F3 discredits the document that says "safe by
   default". Highest strategic score among open units because U11 (hub rebase) and every
   future write-path extension build on rollback being complete.
4. **U4 completes the theme.** Same defect class - derived state silently wrong - in the
   import path: backfill assumes newest-first session ordering it never verifies and aborts
   wholesale on one bad row. Small, disjoint from U3, and it carries the batch's
   verification pattern (synthetic state-DB fixture per its E line).

### Why not the higher-scoring alternatives

- **U6 (20) over U4 (18)?** Two reasons, both gate-shaped rather than score-shaped. First,
  the roadmap's sequencing - a conductor-settled decision (KTD1, session-settled) - orders
  U1-U3 first, then U4->U5->U6->U7; following recorded sequencing is the discipline this
  selection owes its predecessor phases. Second, U6 flips user-visible installer defaults and
  therefore needs README/quickstart/examples coordination and its own focused review; it
  pairs naturally with U5 as a "caps and defaults" mini-batch in the next cycle, after U3
  lands so `guarded_apply.py` is not contended within one stewardship batch.
- **U12 (20), U8 (18)?** Both are KTD1-gated: hardening precedes extension. U12's delay risk
  (4) is real - upstream shipped approval gates the plugin is blind to - and it is recorded
  as the first extension to prioritize the moment hardening lands.
- **U13 (12)?** Hard version gate: host hermes-agent is 0.20.6, the feature needs >= 0.21.0.
  Not selectable regardless of score until the host train updates.
- **U7 (15)?** Deliberately last among hardening: it is a grab-bag across many files whose
  riders would collide with every other unit's surfaces; landing it after U1-U6 avoids
  rework and gives its CI gates a stable codebase to gate.

### Batch shape for the stewardship phase

Surfaces are disjoint with one noted adjacency: U1 touches `storage.py` (plus its backfill
sanitize call site), U2 `candidates.py`, U3 `guarded_apply.py` + `auto_evolve.py`, U4
`backfill.py`. The U1/U4 adjacency in `backfill.py` is different functions - the sanitize
call in the import write path versus the session iteration/error boundary - and should be
kept as separate hunks if they land in one change-set. Baselines exist now: F1, F2, F3
re-verified live this session; U4's fixture is specified in its E line. Original roadmap
Acceptance governs: feature branch off main, targeted tests for changed surfaces (never the
full suite as the gate), push to `fork` only.

## Next batches (provisional, not selected)

- Batch 2 (next cycle): U5 + U6 - "caps and defaults", both small, both user-facing-trust
  themed, U5 lands after U3 merged so the shared file is free.
- Batch 3: U7 - hygiene and CI gates over a stable hardening base.
- Extensions then open per roadmap order: U8 -> U12 (flagged: highest delay-risk extension,
  upstream interop) -> U9/U10 -> U11 -> U14; U13 stays behind the hermes-agent >= 0.21.0
  host gate.
