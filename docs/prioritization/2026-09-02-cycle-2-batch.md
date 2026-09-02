---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-2-batch-selection
mode: repo-grounded
run: 589e5a44a79d4dbda45b3af824d14669
phase: prioritize
attempt: 5bb632663b1f4cacb6f466ae23276807
skill: ce-pov (approach-set position over the roadmap's enumerated unit set; no dedicated selection skill is installed - same route the fleet's prior prioritize phase took)
tier: 1 - selection is a two-way door; a wrong batch costs a cycle, not the repository
---

# Cycle 2 implementation batch selection

Scores every unresolved roadmap packet - the remaining cycle-1 units (U5-U14) plus the
cycle-2 packets (U15-U25) from `.hermes/plans/autonomy-prop_8c5390ffe26640fa.md`
"Extension 2026-09-02 - maintenance cycle 2" - on the same five axes, 1-5 scale.
**Impact** = value if done. **Delay risk** = cost of leaving it undone another cycle.
**Effort** = 5 is cheapest. **Dep-freedom** = 5 means nothing gates it. **Strategic** =
leverage on later work. **Total** is the simple sum, shown for ranking only - gates
override totals.

Cycle-1 units U1-U4 are landed in the uncommitted batch (verified against the working
tree this cycle by the roadmap phase) and are not scored. U7 is split for selection
into its three roadmap items - U7a WAL/busy_timeout/bounded retry (B10, upgraded to
blocking by KTD8), U7b version single-sourcing, U7c CI lint/type gates - because the
three have different scores and the roadmap itself pulled only the storage item forward.
U13's hard version gate is GONE (roadmap evidence correction: `hermes_cli/cron.py` on
this 0.20.6 host already has monitor-mode cron); it is now sequenced by KTD1/KTD7
ordering alone, still after U12.

| Item | Impact | Delay risk | Effort | Dep-freedom | Strategic | Total | Gate status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| U15 managed-block replacement safety (B7) | 5 | 5 | 4 | 5 | 5 | 24 | open |
| U7a storage WAL/busy_timeout/retry (B10) | 5 | 5 | 4 | 5 | 5 | 24 | open; KTD8-pulled forward |
| U16 numeric-flag contract repair (B8) | 5 | 4 | 4 | 5 | 4 | 22 | open |
| U17 scheduler unit hardening (B9) | 5 | 4 | 4 | 5 | 3 | 21 | open |
| U6 bootstrap default alignment | 4 | 3 | 4 | 5 | 4 | 20 | open; default flip needs README/quickstart coordination |
| U12 upstream trust interop | 5 | 4 | 3 | 3 | 5 | 20 | KTD7-gated (extensions after hardening) |
| U18 apply-loop resilience (B11) | 4 | 4 | 3 | 5 | 4 | 20 | open |
| U21 publish-safety gate | 5 | 4 | 3 | 3 | 5 | 20 | KTD7-gated; builds on U15's neutralizer |
| U5 byte-based caps | 3 | 2 | 5 | 5 | 3 | 18 | open; pairs with U6 as "caps and defaults" |
| U8 dedupe scan | 5 | 3 | 2 | 3 | 5 | 18 | KTD7-gated; wants U19 (identity) + U7's semantic rider |
| U19 identity + dedup-key unification (B12) | 3 | 3 | 3 | 5 | 3 | 17 | open |
| U22 anti-pattern ledger | 4 | 3 | 3 | 3 | 4 | 17 | KTD7-gated; after U21 |
| U7b version single-sourcing | 3 | 2 | 4 | 5 | 3 | 17 | open |
| U9 staleness + spec conformance | 4 | 2 | 3 | 3 | 4 | 16 | KTD7-gated |
| U10 missed-trigger detection | 4 | 2 | 3 | 3 | 4 | 16 | KTD7-gated |
| U23 evidence retention + compaction | 3 | 3 | 3 | 3 | 3 | 15 | KTD7-gated; shares KTD9 flag contract with U16 |
| U14 static HTML report | 3 | 1 | 4 | 4 | 2 | 14 | KTD7-gated; after U7 |
| U11 hub managed-block rebase | 4 | 2 | 2 | 2 | 4 | 14 | KTD7-gated; wants U18 |
| U20 hygiene batch (cycle-2 P3s) | 2 | 2 | 3 | 5 | 2 | 14 | open |
| U25 candidates-decide | 2 | 2 | 4 | 3 | 3 | 14 | KTD7-gated; may ride U20 |
| U13 native cron backend | 3 | 2 | 3 | 2 | 3 | 15 | version gate REMOVED; still sequenced after U12 |
| U24 outcome-linked telemetry | 3 | 2 | 2 | 2 | 3 | 12 | KTD7-gated; depends on U22 + U7a |
| U7c CI lint/type gates | 3 | 2 | 3 | 5 | 3 | 14 | open; wants a stable codebase to gate |

B-item discharge map: B7->U15, B8->U16, B9->U17, B10->U7a, B11->U18, B12->U19.
Selecting a unit discharges its B-item; no B-item is selectable on its own. Selecting
this batch discharges five of the six cycle-2 B-items; B12 is the one left open.

## Selected batch: U15 + U7a + U16 + U17 + U18

**"An unattended run must never crash, never drop evidence, never delete the wrong
thing, and must always emit a report."** Five packets, all in the P1 trust-boundary /
loss class, zero user-visible default changes (U16 aligns behavior to help text that
already documents it), zero version gates, zero unsettled decisions, each verified by a
mechanical reproducer that already exists under `/tmp/assess/ce-assess-76416fd2/` and
re-verified live this session.

### Why these five

1. **U15 first, nothing outranks it.** The re.sub replacement-template defect (B7) is a
   guaranteed crash on every auto-run after the first (any skill that already carries a
   managed block - i.e. every skill the plugin has ever touched - plus any preview
   containing `\1`), exit 1 with NO report. Re-verified live this session:
   `repro_autorun_crash.py` -> `re.error: invalid group reference 1 at position 522`,
   `stdout is valid report JSON: False`. It also closes the T18 coverage hole (no test
   starts from a pre-blocked skill), which is why 174 green tests never see it.
2. **U7a is the other 24 and the other certainty.** Under any concurrent writer the
   hooks block 5.01s each, log a warning, and drop the event - 0 of 3 recorded,
   re-verified live this session (`repro_h4_lock_drop.py` -> `returned after 5.01s` x2
   shown, `recorded of 3 attempts: 0`). Evidence is the product's entire input and grows
   ~2,200 events/day on this host, so every dropped event is unrecoverable input loss.
   Cheapest high-impact unit on the board (connect-time pragmas plus a bounded retry,
   with the reproducer doubling as the regression fixture), and KTD8 already pulled it
   forward as blocking.
3. **U16 is the batch's only data-deletion defect.** B8 lives in the just-landed U3
   code: help says `0 disables pruning`, `cli.py:803` rewrites an explicit 0 to 5, and
   `prune_auto_reference_files`' `keep < 0` guard makes a direct keep=0 delete every
   auto reference including the one the same apply just wrote -
   `tests/test_auto_evolve.py:1106` currently asserts that delete-all. It is both a fix
   and a KTD9 precedent: every future numeric flag (U23's retention included) adopts the
   parse-explicit contract this unit establishes.
4. **U17 is the security item.** B9 turns `--schedule` into arbitrary systemd unit-file
   injection (a newline writes a second `[Service]`/`ExecStart=` section, reproduced) and
   `_systemd_quote`'s missing `%` escaping lets systemd specifiers rewrite `ExecStart`
   paths. Same root cause as B7 - external data fed into a second interpretation layer -
   which is why these packets form one coherent batch rather than a grab-bag.
5. **U18 completes the guarantee.** B11's missing per-candidate boundary means one bad
   skill aborts the whole pass with no report (`repro_m12_no_report.py` -> exit 1,
   `report emitted: False`); support files are written after verification with the
   manifest registration discarded; target writes are non-atomic. Landing it with U15
   makes "run always terminates with a report" a tested property rather than an
   accident, and every U8-U14 extension inherits that safety net.

### Why not the higher-scoring / equal-scoring alternatives

- **U6 (20) and U5 (18)?** U6 flips user-visible installer defaults - a two-way door
  needing README/quickstart/example coordination and its own focused review; cycle 1's
  provisional plan already pairs it with U5 as a "caps and defaults" mini-batch, and U5
  shares `guarded_apply.py` with U18's atomic-write work (contended file within one
  batch is the exact hazard cycle 1 avoided).
- **U12 (20) and U21 (20)?** Both are KTD7-gated: hardening precedes extensions, a
  conductor-settled decision. U21 additionally builds on U15's neutralizer - selecting
  it into the same batch would create an in-batch dependency and break end-to-end
  independence. U12 remains the first extension to prioritize the moment hardening
  lands (highest delay-risk extension per cycle 1, unchanged).
- **U19 (17)?** Discharges B12, but the broken paths are opt-in flags
  (`--semantic-candidates`/`--rerank-candidates`), not defaults, so delay risk is
  moderate; it is the head of the next batch alongside U20.
- **U7b/U7c?** Real but not blocking anything in this batch; they want the stable
  codebase this batch creates, which is exactly the sequencing cycle 1 recorded for U7's
  grab-bag remainder.
- **U13?** Version gate is gone (this cycle's roadmap correction), but its sequencing
  (after U12) is unchanged and its dep-freedom is genuinely low (native-cron semantics
  interplay); nothing about the correction argues for pulling it into this batch.

### Batch shape for the implement phase

Surfaces, with the two adjacencies called out: U15 `auto_evolve.py` (block writer +
preview neutralizer) + `tests/test_auto_evolve.py` second-run corpus; U16 `cli.py`
(parse-explicit 0 for `--max-reference-files`, `--max-skills`, `--min-evidence`,
`--variants`) + `auto_evolve.py` prune guard + REPLACING the assertion at
`tests/test_auto_evolve.py:1106` (the test currently codifies the bug); U17
`auto_evolve.py` (schedule validation + `%%` escaping) + unit-content tests; U18
`auto_evolve.py` (candidate loop boundary, support-file ordering) + `guarded_apply.py`
(temp+rename atomic writes) + interruption fixture; U7a `storage.py` (connect-time WAL,
busy_timeout, bounded retry) + `hooks.py` error handling + concurrency test
(`repro_h4_lock_drop.py` is the shape). Adjacency 1: U15/U16/U18 all touch
`auto_evolve.py` - keep them as separate hunks. Adjacency 2: U18/U5 share
`guarded_apply.py`; U5 is out of the batch partly for this reason. Mechanical gates
already exist and re-verified live this session: `repro_autorun_crash.py`,
`repro_m12_no_report.py`, `repro_h2_prune_zero.py`, `repro_h3_systemd.py`,
`repro_h4_lock_drop.py`, `repro_misc2.py`. Original roadmap Acceptance governs: feature
branch off main, targeted tests per changed surface (never the full suite as the gate),
push to `fork` only - remote policy per KTD2/KTD11, and NOT this phase.

## Next batches (provisional, not selected)

- Batch 2 (next cycle): U19 + U20 - "correctness tails": discharges B12, closes the
  cycle-2 P3 list, frees `--semantic-candidates` for U8's semantic rider.
- Batch 3: U5 + U6 + U7b/U7c - "caps, defaults, and gates" over the now-stable write
  path (U7c's lint/type CI gate lands last so it gates a settled codebase).
- Extensions then open per roadmap order with U12 first (highest delay risk), then
  U21 -> U22 (write-path hardening features, U21 reusing U15's neutralizer), U25 as a
  cheap rider, U23 then U24 last (U24 needs U22's ledger and U7a's lock-free reads).
  U8 follows U19; U13 stays behind U12 per roadmap sequencing - its version gate is
  already lifted, so nothing external blocks it beyond ordering.
