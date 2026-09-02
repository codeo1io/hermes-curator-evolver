---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-4-batch-selection
mode: repo-grounded
run: 673d15323b9c4580a0e2ed84fa8625fc
phase: prioritize
attempt: 0dd0d167d37d4563ac3262c16faca433
skill: ce-pov (position over the roadmap's enumerated unit set; no ce-prioritize is installed in either roster - same route the fleet's prior prioritize phases took)
tier: 1 - selection is a two-way door; a wrong batch costs a cycle, not the repository
disclosure: pi exposes no subagent primitive; grounding and scoring ran in-thread in one context; no panel was summoned. Cycle-3 scores are carried unchanged where nothing moved (no independence is claimed over them); new cycle-4 scores (U35-U42) and the two re-annotated items are this session's own.
---

# Cycle 4 implementation batch selection

Scores every unresolved roadmap packet - the cycle-1 residuals, U15-U25 (cycle 2),
U26-U34 (cycle 3), and U35-U42 (cycle 4, added this cycle) from `.hermes/plans/
autonomy-prop_8c5390ffe26640fa.md` - on the same five axes, 1-5 scale. **Impact** =
value if done. **Delay risk** = cost of leaving it undone another cycle. **Effort** =
5 is cheapest. **Dep-freedom** = 5 means nothing gates it. **Strategic** = leverage
on later work. **Total** is the simple sum, shown for ranking only - gates override
totals.

Grounding this cycle: the pass-4 assessment (this run, ~1h ago) already re-derived
all 27 findings on this exact tree, and the full 12-reproducer corpus was re-run
**at selection time** this session (`/tmp/repro-at-selection-cycle4.txt`, 12/12
still reproduce): N1 `removed:['SKILL.md']` + file gone (U35/B16); N2 `--limit=2
inspected ['s1','s0']` - oldest, newest never seen (U36/B17); N3 5/5 transcripts
fetched for a 1-in-window days=30 import + bootstrap `limit=None` (U36); N4 the
just-written reference pruned at keep=0 (U16/B8); N5 `'{"a": "x\\u0000y"}'` escape
survives the sanitizer (U37/B18); N6 verifier passes 999-vs-1 grounding (U7 hygiene);
P1 `re.error: invalid group reference 1` - the auto-run crash (U15/B7); P2
`_looks_like_error('3 passed, no errors found') = True` (U28/B15); P4 live
`OperationalError: database is locked` under one concurrent writer (U7a/B10); P7
newline-bearing schedule quoted straight into the unit (U17/B9). Tree state at
selection: `45328db` + the same 11 uncommitted cycle-1 files (833 insertions, unchanged
since pass-4), pytest 174/174. No fix phase has ever run on this tree - the cycle-3
selection (U15+U7a+U16+U17+U18+U26+U28) never landed.

## Scoring

| Item | Impact | Delay risk | Effort | Dep-freedom | Strategic | Total | Gate status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| U15 managed-block replacement safety (B7) | 5 | 5 | 4 | 5 | 5 | 24 | open; 3rd selection |
| U7a storage WAL/busy_timeout/retry (B10) | 5 | 5 | 4 | 5 | 5 | 24 | open; recipe now upstream-provided (R7) |
| U37 NUL-escape-complete sanitization (B18) | 5 | 4 | 5 | 5 | 4 | 23 | open; new this cycle |
| U35 rollback validation + guarded rollback (B16) | 5 | 4 | 3 | 5 | 5 | 22 | open; new this cycle; KTD16-first |
| U16 numeric-flag contract repair (B8, +N4) | 5 | 4 | 4 | 5 | 4 | 22 | open; N4 re-reproduced |
| U17 scheduler unit hardening (B9) | 5 | 4 | 4 | 5 | 3 | 21 | open |
| U28 single error classifier (B15) | 4 | 4 | 4 | 5 | 4 | 21 | open |
| U18 apply-loop resilience (B11) | 4 | 4 | 3 | 5 | 4 | 20 | open; guarded_apply contended |
| U6 bootstrap default alignment | 4 | 3 | 4 | 5 | 4 | 20 | open |
| U12 upstream trust interop (+R5 sidecar) | 5 | 4 | 3 | 3 | 5 | 20 | KTD7/KTD12/KTD16-gated |
| U21 publish-safety gate | 5 | 4 | 3 | 3 | 5 | 20 | gated; builds on U15 |
| U36 trusted-order backfill w/ drift detection (B17) | 4 | 3 | 4 | 5 | 4 | 20 | open; new this cycle; held - see below |
| U38 source-aware evidence pipeline (R1) | 5 | 3 | 4 | 5 | 5 | 22* | KTD16-gated (*extension gate caps it) |
| U26 rerank oversampling (B13) | 4 | 3 | 4 | 5 | 3 | 19 | open |
| U29 host-ledger read integration | 4 | 3 | 3 | 4 | 5 | 19 | KTD12/KTD16-gated |
| U39 symlink-parity discovery (R2, #101063) | 4 | 3 | 5 | 5 | 3 | 20* | KTD16-gated |
| U5 residual (confirm + close) | 3 | 2 | 5 | 5 | 3 | 18 | open; rides the U7 batch |
| U27 rollback target-root default (B14) | 4 | 2 | 4 | 5 | 3 | 18 | open; held (cycle-3 precedent) |
| U8 dedupe scan | 5 | 3 | 2 | 3 | 5 | 18 | gated; wants U19 |
| U30 plugin-apply ledger attribution | 4 | 3 | 3 | 4 | 4 | 18 | gated; after U29 |
| U33 circuit breaker | 4 | 3 | 4 | 3 | 4 | 18 | gated; U22's escalation tier |
| U40 host-linter apply gate (R4) | 4 | 2 | 4 | 4 | 4 | 18* | KTD16-gated |
| U19 identity + dedup-key unification (B12) | 3 | 3 | 3 | 5 | 3 | 17 | open |
| U22 anti-pattern ledger | 4 | 3 | 3 | 3 | 4 | 17 | gated; after U21 |
| U31 doctor --host-compat sweep | 4 | 2 | 3 | 4 | 4 | 17 | gated; after U29/U30 |
| U41 cron-referenced-skill protection (R6) | 4 | 2 | 4 | 5 | 3 | 18* | KTD16-gated |
| U7b version single-sourcing | 3 | 2 | 4 | 5 | 3 | 17 | open |
| U9 staleness + spec conformance (+linter watch) | 4 | 2 | 3 | 3 | 4 | 16 | gated |
| U10 missed-trigger detection | 4 | 2 | 3 | 3 | 4 | 16 | gated |
| U32 context-budget report | 3 | 2 | 4 | 4 | 3 | 16 | gated; after U8 |
| U42 workspace-scoped backfill (R9) | 3 | 2 | 4 | 5 | 2 | 16* | KTD16-gated |
| U7c CI lint/type gates | 3 | 2 | 3 | 5 | 3 | 14 | open; wants a stable codebase |
| U14 static HTML report | 3 | 1 | 4 | 4 | 2 | 14 | gated; after U7 |
| U11 hub managed-block rebase | 4 | 2 | 2 | 2 | 4 | 14 | gated; wants U18 |
| U20 hygiene batch (cycle-2 P3s, +N7/N8) | 2 | 2 | 3 | 5 | 2 | 14 | open |
| U25 candidates-decide | 2 | 2 | 4 | 3 | 3 | 14 | gated; may ride U20 |
| U23 evidence retention + compaction | 3 | 3 | 3 | 3 | 3 | 15 | gated; shares KTD9 flag contract |
| U24 outcome-linked telemetry | 3 | 2 | 2 | 2 | 3 | 12 | gated; needs U22+U7a+U28 |
| U13 native cron backend | 3 | 2 | 3 | 2 | 3 | 13 | gated; after U12 |
| U34 fleet-library conflict report | 2 | 2 | 3 | 2 | 2 | 11 | KTD14 demand-gated |

Carried scores are cycle-3's where no evidence moved; re-annotated this cycle:
U7a (R7 supplies the port recipe - effort already 4, now de-risked), U16 (N4
re-reproduced at selection time - the same-pass reference deletion is the concrete
failure its "0 disables pruning" AC prevents), U12 (R5 grows scope - score holds).
New scores (U35-U42) are this session's; the * marks extension packets whose raw
total exceeds their gate - KTD16 (remediation precedes extension) overrides totals,
and every U38-U42 item is explicitly sequenced behind U35-U37 by the roadmap.

B-item discharge map: B7->U15, B8->U16, B9->U17, B10->U7a, B11->U18, B12->U19,
B13->U26, B14->U27, B15->U28, B16->U35, B17->U36, B18->U37. Selecting a unit
discharges its B-item; no B-item is selectable alone. This batch discharges six of
the twelve open B-items; B9, B11, B12, B13, B14, B17 stay open.

## Selected batch: U15 + U7a + U37 + U35 + U16 + U28

The write-path correctness batch over the freshly-landed remediation: every packet
fixes a reproduced crash, a reproduced destructive deletion, a reproduced data
corruption, a reproduced silent drop, or the founding error-loop class itself.
**"An unattended run must never crash on its own managed block, never delete the
file it just restored, never corrupt or silently drop an evidence row, never prune
what it just wrote, and the NUL loop the campaign was created to kill must be closed
in every encoding that reaches the store."** All six are in the crash/loss/deletion/
corruption class; zero user-visible default changes (U16 aligns behavior to help
text that already documents it); zero version gates; zero unsettled decisions; each
verified by a mechanical reproducer that exists and was re-run at selection time.

### Why the two certainties stay

U15 and U7a remain the board's top pair (24/24) for the third consecutive selection
because nothing has landed: the auto-run still exits 1 with `re.error: invalid group
reference 1` on any skill that already carries a managed block (P1, re-reproduced
this session), and one concurrent writer still drops hook events wholesale after a
5.01s lock stall (P4, re-reproduced this session). Re-selecting anything above them
would demote verified crash/data-loss defects. U7a is additionally de-risked this
cycle: research R7 supplies the upstream recipe to port (`hermes_state.py:640-1200`
WAL + busy_timeout + journal_size_limit + DELETE-fallback slice).

### Why the two new must-haves enter

1. **U37 (23) is the campaign's founding class, still reachable.** The original
   Problem was a NUL byte surviving sanitization into a perpetual rollback loop;
   U1 closed the byte and the `\x00` literal, but the `\u0000` escape still reaches
   the store (`N5: '{"a": "x\\u0000y"}'`, re-reproduced at selection time) and the
   current fix mangles legitimate literal text. Cheapest packet on the board
   (effort 5), single function + ingest paths, and it closes U1 for real. The
   roadmap paired it with U28 (same file, separate hunks) - selected together.
2. **U35 (22) is the destructive class inside just-landed code.** The rollback
   path the cycle-1 batch added can be made to unlink the SKILL.md it just restored
   (`N1: removed:['SKILL.md'], file gone`, re-reproduced), and its CLI-default
   overwrite case (C2) is unfixed. Rollback is the trust anchor every future
   packet (U30's ledger write-side especially) builds on; KTD16 names it first
   among cycle-4 remediation. Its safety-snapshot primitive also absorbs U18's
   atomic-write slice - see below.

### Why U16 and U28 ride

U16 (22) now carries N4's concrete failure: keep=0 prunes the reference the same
apply just wrote (re-reproduced), i.e. the documented "0 disables pruning" is the
opposite in code, and `tests/test_auto_evolve.py:1106` codifies the bug. U28 (21)
is the batch's ingest-corruption packet (`'3 passed, no errors found'` stored as an
error, re-reproduced) - the rows it corrupts gate auto-evolve thresholds and are
exactly what U24 will later mine. Both ride the same file-pairing the roadmap
sequenced (U28 with U37).

### Why not the alternatives

- **U36 (20, new) - the one deliberate hold against the roadmap's pairing note.**
  Its two defects are latent on every real host: the actual driver's
  `search_sessions` is a deterministic newest-first total order (verified live
  against v2026.8.31 this session, `hermes_state.py:13155-13201`), so N2's
  wrong-set import fires only under a non-conforming storage, and N3 is
  slow-not-wrong (the days cutoff is applied after the over-fetch; results stay
  correct, bootstrap is just unbounded). Meanwhile KTD17 has U36 *supersede* the
  just-landed collect-then-sort iterator - a rewrite of 833 lines that have never
  been committed, landing in the same batch that also rewrites storage ingest
  (U37/U28) would churn three surfaces of uncommitted code at once. It is the head
  of batch 2 beside U19 (same file, dedup keys), which is the roadmap's own
  pairing. This refines the sequencing note (U36 deferred one batch), it does not
  contradict its order: U36 still lands before any extension.
- **U18 (20)?** Held on the cycle-3 U27-precedent: U35 owns `guarded_apply.py`
  this batch (its B-item is newer and more destructive), and U18's highest-value
  slice - atomic temp+rename writes - is the same primitive U35's pre-rollback
  safety snapshot needs, so it is absorbed there rather than contended. The
  loop-boundary remainder rides batch 2.
- **U17 (21)?** Held a third time: config-time input validation on an install
  path (the operator attacking their own `--schedule`) versus this batch's
  runtime destruction class; `auto_evolve.py` already carries two hunks (U15+U16).
  Unchanged from cycle-3's judgment; batch-2 candidate.
- **U26 (19)?** Dropped from the batch it rode in cycle 3: its rider slots went to
  the two new must-haves (U35, U37). Fully disjoint (`semantic.py`), zero-delay-risk
  change - it rides again whenever a slot frees.
- **U6 (20)?** Third-cycle judgment unchanged: user-visible default flip needing
  README/quickstart/example coordination and its own focused review; belongs to
  the caps-and-defaults batch over the now-stable write path.
- **U38 (22*) and the extensions?** KTD16-gated: remediation precedes extension,
  conductor-settled since KTD1. U38 is the strongest of them (evidence quality is
  the product's input; no dependencies) and is the first extension to pull the
  moment hardening lands - its allowlist-not-blocklist design is already decided
  (KTD18).

### Batch shape for the implement phase

Surfaces, with the adjacencies called out: U15 `auto_evolve.py:386` lambda/escaped
replacement + neutralized previews + second-run corpus test (P1 reproducer is the
crash test); U35 `guarded_apply.py:426-468` support-file validation (skills-root
containment, target-identity refusal, registration cross-check) + pre-rollback
safety snapshot in `rollback_guarded_patch` (:471, fail-closed) + explicit flag for
post-apply-modified files (C2) + N1 reproducer promoted to a regression test; U16
`cli.py:787-803` parse-explicit 0 for the four flags + `auto_evolve.py:414` guard +
REPLACING the delete-all assertion at `tests/test_auto_evolve.py:1106` + N4
reproducer as the disables-pruning test; U7a `storage.py:154` connect-time
WAL/busy_timeout/bounded retry ported from the host recipe + `hooks.py` error
handling + concurrency test (P4 reproducer shape); U28 `storage.py:113-130`
delegate-or-delete `_looks_like_error` onto the candidates-side structured-first
classifier + corpus extension (P2 reproducer); U37 `storage.py:71-83` escape-aware
strip at both ingest paths + NUL-free round-trip fixture + U1 test extension (N5
reproducer). Adjacency 1: U15/U16 share `auto_evolve.py` (:386 vs :414, separate
hunks). Adjacency 2: U7a/U28/U37 share `storage.py` (:154 connect vs :113-130
classifier vs :71-83 sanitizer - three disjoint functions, three hunks; extends the
U7a+U28 adjacency cycle 3 already blessed). Adjacency 3: U35 solely owns
`guarded_apply.py`. Mechanical gates exist: the 12-reproducer corpus
(`/tmp/repro-at-selection-cycle4.txt`; this batch should flip exactly N1, N4, N5,
P1, P2, P4 green while N2/N3/N6/P7/P10 remain for later batches) plus targeted
pytest per changed surface. Original roadmap Acceptance governs: feature branch
off main, targeted tests per changed surface (never the full suite as the gate),
push to `fork` only - remote policy per KTD2/KTD11/KTD15/KTD20, and NOT this phase.

## Next batches (provisional, not selected)

- Batch 2: U36 + U18 (loop-boundary remainder) + U19 + U27 - the backfill/apply
  tails over now-committed code; U26 and U17 ride if slots free; discharges B17,
  B11, B12, B14 (+B13/B9).
- Batch 3: U5r + U6 + U7b + U7c + U20 (+U25) - caps, defaults, and gates over the
  settled write path; U7c lands last so the ruff gate (65 errors today) gates a
  stable codebase; N6's verifier cross-check and N9's lint debt close here.
- Extensions then open per KTD16 with U38 first (highest raw total among gated
  items, no dependencies), then U39 -> U40 -> U41 -> U42, alongside the standing
  roadmap order U12 -> U21 -> U22 + U33 -> U29 -> U30 -> U31 -> U8 then U32 -> U23
  -> U24 (needs U22, U7a, U28's clean cohorts - this batch supplies two of three).
  U34 stays KTD14 demand-gated.

*Read-only selection; no code changed, nothing committed or pushed.*
