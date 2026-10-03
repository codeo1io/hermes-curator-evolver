# Cycle 13 compounding — learnings and prevention rules

Run `63d5b40d6c6c4a819a4d33d05704a7eb` (campaign cycle 3 of goal 134d4f57) · compounding
attempt `56bb28593fd14cb8b9a442bc7f162890`
Written 2026-10-04 from PRE-REVIEW cycle evidence only (assess `7095eea6`, research
`addfd20c`, roadmap `2c7c9f62`, prioritize `1a5b08cb`, stewardship `3e09d2b4`, implement
`66d6b11c`, targeted_tests `c6f9142b`, full_tests `cdef1ff8` outcomes). Review and ship
outcomes are next cycle's assessment inputs, per phase order.

Numbering is final on main's chain: the 2026-10-03 extension allocated U115-U130 + KTD49
and left the learnings pointer at L61 (next-free U131 / KTD50 / L61), so this cycle
allocates **L61-L66**. Next free after this doc: **U131 / KTD50 / L67**.

Base: worktree `run-63d5b40d6c6c-63d5b40d` at `d40b2e9` (cycle-12 integration tree,
suite 590/590). Batch (prioritize `1a5b08cb`, stewardship `3e09d2b4`): U127 + U122 +
U126 + U130 + U120 + U119 + the ingestion-coverage rider on U127; theme "trustworthy
contracts, trustworthy evidence". A prior compound attempt (`ceda05e5`) died at turn
start on a provider failure — zero work events, no typed artifact (forensics in the
compound phase result); this attempt redid the phase from scratch.

## What the cycle produced (evidence recap)

- Assess `7095eea6`: fresh adversarial whole-repo re-read (22 modules ~10.3k LoC, 134
  tracked files) independent of cycle-12's review, plus live probe batteries built with
  programmatic, length-asserted constants — the L57/#14547 method applied from the
  start, so this cycle had zero probe-constant contradictions. 13 findings (2 high /
  4 medium / 7 low); 6 are cycle-12 KNOWN LIMITS re-verified live and promoted to
  numbered units by the roadmap extension; 7 net-new (truncated-PEM body leak,
  empty-session co_usage edges, restore-drill containment deadlock, wrong-shape
  state-db crash, audit-skills empty-on-missing-dir, `|fatal` "non-" prefix, silent
  turn/session dedupe skips). Baseline 590/590 green at `d40b2e9`; local ruff 0.15.10
  = 17 findings vs CI count-ceiling 79 at pinned 0.16.7 (mechanism intact). Earlier
  attempts `c3ff4815`/`fb16dcb7` died pre-artifact (provider).
- Research `addfd20c`: 4 ranked candidates (U115-U118) + 1 feasibility note + 7
  negative results, grounded in live upstream fetches AND read-only censuses of the
  LIVE production stores on this host. Headline: plugin state (217 MB evidence.sqlite
  + live WAL) sits INSIDE the install dir on a real install; upstream PR #27 (open
  2026-09-27) relocates exactly those call sites. KTD40 5th observation: zero drift.
- Roadmap `2c7c9f62`: +286 lines (2606 → 2892), units U115-U130 + KTD49, sequencing
  notes, discharges. The engine reset the tracked file to the pre-extension image
  after the phase — the durable copy + hash pair carried the content (L61).
- Prioritize `1a5b08cb`: batch = the two HIGH cycle-12 deferrals (U126 auto-run rc-0,
  U127 state-db limit-0 — both explicitly promised "next cycle" in commit 2de240b) +
  same-surface U130/U122 + the two NEW evidence-trust defects (U119, U120) + the
  research coverage rider; deferrals recorded with reasons.
- Stewardship `3e09d2b4`: anchor re-pin sweep over every batch surface at `d40b2e9`
  — all anchors held, no premise disproof this cycle (the L58 gate working as
  designed); request recorded without choosing Git topology.
- Implement `66d6b11c`: all six units + rider landed in order U127 → U122 → U126 →
  U130 → U120 → U119 (rider folded into U127). 5 modified files + 4 new test files
  (+138/−4 per `git diff --stat`); authoritative combined sweep 263 passed over its
  19-file set (strictly-widening differential vs all cycle-12 hygiene/backfill pins);
  26 new pin items counted by collect-only ITEMS not functions (u127:12 incl. rider,
  u126:5, u119:5, u120:4 — #14530 discipline); adversarial battery ALL-PROBES-PASS
  (`/tmp/probe-impl-66d6b11c/battery.py`); ruff clean on every touched file.
- Targeted_tests `c6f9142b`: engine impacted-runner command verbatim; the selector
  expanded 8 named surfaces to 20 files, 266/266 outcomes passed, exit 0; digest
  equality with the dispatch block asserted (`validation:v1:1814336e…`).
- Full_tests `cdef1ff8`: engine full_command verbatim → ephemeral-pr CI, PR #18 (head
  `bafa6634`): Python tests 3.12 + Lint both SUCCESS, first-try green, zero
  regressions; digest equality re-asserted on the same uncommitted delta.

## Durable lessons (L61-L66)

1. **L61 — planning-phase tracked-file edits do not survive the phase; the hash chain
   plus a durable out-of-repo copy are the real record.** The roadmap phase extended
   the tracked roadmap and recorded a post-image sha — but the very next phases found
   the worktree reset to the pre-extension image: the engine reverts planning-phase
   tree edits, and only the recorded sha pair + the byte-identical `/tmp` copy carry
   the content forward. Compounding must therefore RE-MATERIALIZE the chain
   (tracked pre-image + durable extension copy → assert the reconstruction hashes to
   the recorded post-image) before appending its own block; the commit-phase tree
   then contains the fully reconstructed file. This cycle's reconstruction also
   caught a record defect: the transmitted post-image string was 66 characters — not
   a possible sha256 — with a duplicated `7f`; the true image is
   `ff56a3741431a57f7f7784d8f0ca1515f65f162fe306fd34e2ee0d1147a9c2e3` (pre-image
   `883c26e4…` matched exactly, 2606+286=2892 lines matched). Prevention: every
   planning phase that edits a tracked artifact leaves (a) a byte-identical durable
   copy outside the repo and (b) pre/post sha256 in its result; every later append
   verifies the reconstruction hash BEFORE writing; a recorded hash whose LENGTH is
   wrong for its algorithm is a transcription typo — re-derive from artifacts, then
   correct the record in the very next append (as this cycle does).
2. **L62 — `IS NOT NULL` does not exclude empty strings; optional-key joins need both
   guards and both pins.** storage.py's co_usage join guarded
   `other.session_id IS NOT NULL` while the hook path defaults `session_id=""`
   (hooks.py:31) — two skills that never truly co-occurred got a fabricated impact
   edge (`shared_sessions=1, error_events=1`) off their session-less events, feeding
   impact.py's ≥2-shared-sessions review escalation. U120 added
   `AND other.session_id != ''` on both sides of the join (probe pair now yields NO
   edge; real same-session co-usage unchanged). Prevention: for every join or
   aggregation over an optional key, pin a NULL-key row AND an empty-string-key row
   as SEPARATE cases; when a producer defaults an optional identifier to `""`, decide
   once whether to normalize at write time or guard at every read, and audit join
   sites by grepping for the default (`session_id: str = ""`), not just for `NULL`.
3. **L63 — paired-delimiter redaction leaks the body when only one delimiter is
   present.** hygiene.py's PEM arms required BEGIN…END for the block arm, so a
   truncated paste (BEGIN + 1003-char body, no END) matched only the bare-header
   arm: the marker line was replaced while the ENTIRE base64 body survived verbatim
   into stored tool-event previews. U119 added a truncated arm — BEGIN marker +
   lookahead requiring real body material (a 20+ char base64 run on the next line),
   redacting through the first blank line or end-of-input — so prose that merely
   mentions the marker keeps its surrounding text, and a proper BEGIN…END block is
   still captured by the block arm first. Prevention: for every paired-delimiter
   secret format, pin the UNPAIRED cases (head-only and tail-only); redaction pins
   must be length-asserted against the BODY (the secret), not the marker — proving
   the marker was replaced proves nothing about the secret.
4. **L64 — an exit-code contract is only as good as its outermost frame.** Cycle-12's
   U107 wired five rc-1 branches, but auto-run's failure path ended in a bare
   `return` (cli.py:932): the run JSON honestly reported `apply_failed: 1` and
   verify `passed: false` while the process exited 0 — invisible to every
   systemd-timer/script consumer (live rig reproduced it end-to-end). U126 keys the
   return on `summary.apply_failed` (U111's machine token) with deliberate no-ops
   (no candidates, dry-run all-planned, approval-required refusal, drill-gate skip)
   pinned to stay 0, and U130's README table is cross-checked against
   `grep -n "return 1" cli.py`. Prevention: exit-code audits enumerate EVERY return
   in the dispatcher — grep for bare `return` too, not only failure paths that
   already print errors; every rc-1 contract gets a failure pin AND a
   deliberate-zero differential pin so the fix cannot invert no-op semantics.
5. **L65 — argument-contract guards belong at the entry function, not in one CLI
   wrapper.** Cycle-12's U109 put the `--limit 0` ValueError in cli.py's wrapper
   only; the library entry `backfill_sessions(state_db=…, limit=0)` silently
   imported unbounded — live on a copy of the real store: 5,034 sessions seen, 568
   imported, 25,447 tool events, `result["limit"] == 0` recorded as if a real cap,
   rc 0. U127 hoisted the guard to `backfill_sessions` entry: one ValueError site,
   raised before ANY source is opened, so CLI/bootstrap/legacy/state-db all agree;
   `limit=None` (omitted) stays unbounded. Prevention: when adding a contract guard
   for a CLI flag that fronts a library function, pin the LIBRARY path too; the
   guard lives at the lowest function every caller shares, and wrappers only
   translate (ValueError → clean `error:` line + rc 1).
6. **L66 — triage a dead attempt by its event log before redoing anything.** The
   engine's prior-attempt forensics resolved this phase's dead compound attempt
   (`ceda05e5`) in one read: the event log held exactly three lifecycle events
   (turn_started → session_reaped, provider family → turn_completed:failed), zero
   work events, no typed artifact, and the worktree matched the prior phase's
   declared delta exactly (implement's 5 M + 4 ??, roadmap untouched) — a
   TURN-START death, licensing immediate from-scratch redo with no salvage
   archaeology. Cycle-12's seven deaths (and this cycle's assess deaths) were the
   opposite shape: real work, no envelope. Prevention: always read the event log AND
   diff the worktree against the prior phase's declared delta FIRST; zero work
   events → redo immediately; work events without an envelope → mine the durable
   trail (/tmp artifacts, spool, tree delta) and verify against the current work
   order before adopting; either way the adopt-or-redo decision is recorded in the
   result with its evidence legs, never implied.

## Candidates and context for cycle 14

- **U115 + U121 together as the centerpiece batch** (plugin-state relocation +
  manifest-recorded store root): live 217 MB exposure on this host, upstream PR #27
  open-not-merged moving exactly these call sites, KTD40 zero drift — deferring one
  more cycle is low-cost but it needs a cycle where it IS the batch (one-time
  migration, ImportError fallback, status disclosure, launchd logs).
- **U83 is the cycle-14 lead feature** — its edge-truth prerequisite is NOW
  satisfied: U87 landed in cycle 12, U106 fixed the distinct-count fan-out, U120
  (this cycle) removed the fabricated empty-session edges. Build merge-check on
  true edges.
- **U128 + U124 together** (same file candidates.py:97-160, deliberately disjoint
  arms, one differential battery; U128 needs explicit negation/zero-count parses,
  not arm-adding).
- **U116** (sessions.source + session_model_usage ingestion) cycle 14/15 —
  stewardship-flag if batched with any other schema unit.
- **U118 + KTD49 before any U114 resumption** (pi 1.0.0 removed `pi skills`; pick
  the verification surface: startup diagnostics, `/skill:name` probe, or RPC/SDK).
- Unchanged gates: U112 (semconv still v1.44.0), U113 (live-API-in-CI design
  decision owed), U62 (KTD40-gated). Cycle-14 small-slot alternates: U117, U123,
  U125, U129, U103, U88, U104.
- **KTD40 ledger re-observation due ~2026-10-05** (streak 5/30 at the 2026-10-03
  extension; PR #27 is the item to watch for merge movement).

## Verification trail (recorded outcomes, not re-run here — compound runs no tests)

- Implement combined sweep: 263 passed / 0 failed over its 19-file authoritative
  set; adversarial battery ALL-PROBES-PASS — `/tmp/probe-impl-66d6b11c/battery.log`.
- New pins: 26 collect-only items (u127:12, u126:5, u119:5, u120:4) across 4 new
  test files; four-file run 26 passed.
- Targeted `c6f9142b`: 266/266 outcomes passed, exit 0 —
  `/tmp/targeted-c6f9142b/run.out` + `inner.out`.
- Full `cdef1ff8`: ephemeral-pr PR #18 (head `bafa6634`), Python tests 3.12 SUCCESS
  + Lint SUCCESS, ok:true — `/tmp/full-cdef1ff8/run.out`.
