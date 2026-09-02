---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-5-batch-selection
mode: repo-grounded
run: 2cc5b112c9694bfaa4a47645f139983a
phase: prioritize
attempt: 139e9a8607c64db28c8ac3921231b579
skill: ce-pov (position over the roadmap's enumerated unit set; no ce-prioritize is installed in either roster - same route the fleet's prior prioritize phases took)
tier: 1 - selection is a two-way door; a wrong batch costs a cycle, not the repository
disclosure: pi exposes no subagent primitive; grounding and scoring ran in-thread in one context; no panel was summoned. Scores carried from cycle-3/4 where no evidence moved (no independence claimed over them); new cycle-5 scores (U43-U50) and re-annotated items are this session's own.
---

# Cycle 5 implementation batch selection

Scores every unresolved roadmap packet — cycle-1 residuals (U5/U6/U7-remnants), the
unlanded cycle-2/3 units (U17-U20, U25, U26, U28-superseded), cycle-4's U36-U42, and
cycle-5's U43-U50 — from `.hermes/plans/autonomy-prop_8c5390ffe26640fa.md` on the same
five axes, 1-5 scale. **Impact** = value if done. **Delay risk** = cost of leaving it
undone another cycle. **Effort** = 5 is cheapest. **Dep-freedom** = 5 means nothing
gates it. **Strategic** = leverage on later work. **Total** is the simple sum, shown
for ranking only — gates override totals.

Grounding this cycle: the pass-5 assessment (this run, ~1h ago) re-derived all 23
findings on this exact tree, and the 22-probe corpus was re-run **at selection time**
this session (`/home/agent/.hermes/conductor-runs/2cc5b112c9694bfaa4a47645f139983a-assess/repro-pass5.py`):
21/22 reproduce — every defect this batch targets re-reproduced minutes ago: R1 the
four classifier misclassifications (U43/B19), R2 mode 0o640→0o664 through apply and
rollback (U44/B20), R3 safety snapshot on plain `write_bytes` (U44/B20), R4 the
README-documented rollback form refusing (U7-docs rider), R5 ~15.75s worst-case hook
stall (U45/B21), R6 schema-ready probing only `tool_events` (U46/B22), plus the
carried N2/N2b/N3 backfill set (U36/B17) and P7 systemd newline injection (U17/B9).
Tree state at selection: `45328db` + the uncommitted cycle-1 and cycle-4 batches
(19 dirty/untracked paths, unchanged since pass-5), pytest 184/184 re-run at
selection time, ruff 64 errors / 45 fixable. The cycle-4 batch closed U15, U35,
U16, U37, U27/C2 and partially U28 — the unification exists (`candidates.py:242`)
but its truth table is wrong, which is why U43 supersedes U28 on this board.

## Scoring

| Item | Impact | Delay risk | Effort | Dep-freedom | Strategic | Total | Gate status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| U43 error-classifier truth table (B19/Q1) | 5 | 5 | 4 | 5 | 5 | 24 | open; new this cycle; 3rd consecutive cycle a classifier defect tops the board |
| U44 mode-preserving atomic writes + snapshots (B20/Q3+Q5) | 4 | 4 | 4 | 5 | 4 | 21 | open; new this cycle |
| U17 scheduler unit hardening (B9/P7) | 5 | 4 | 4 | 5 | 3 | 21 | open; **selected in cycle-4, never landed** - demoting again would repeat that |
| U36 trusted-order backfill (B17/N2+N2b+N3) | 4 | 4 | 4 | 5 | 4 | 21 | open; 3rd assessment reproducing; held cycle-4 (batch size), overdue |
| U45 warm-writer topology + errno split (B21/Q6, research S3) | 4 | 4 | 3 | 5 | 4 | 20 | open; new; recipe upstream-provided (#101191 merged) |
| U18 apply-loop resilience (B11/P5+P6) | 4 | 4 | 3 | 5 | 4 | 20 | open; **contended: shares guarded_apply.py with U44** - hold |
| U6 bootstrap default alignment | 4 | 3 | 4 | 5 | 4 | 20 | open; user-visible default change - pair with docs, next batch |
| U46 schema-ready probes all tables (B22/Q7) | 3 | 3 | 5 | 5 | 3 | 19 | open; new; rides U45's file |
| U26 rerank oversampling (B13/C1) | 4 | 3 | 4 | 5 | 3 | 19 | open; held - batch size (semantic.py is a clean disjoint next slot) |
| U7-riders: Q2 F821 + U7b version single-source + Q4 docs + Q8 warn | 3 | 3 | 4 | 5 | 3 | 18 | open; roadmap says these ride the next remediation batch |
| U5 residual (confirm + close) | 3 | 2 | 5 | 5 | 3 | 18 | open; rides with U7-riders |
| U19 identity + dedup-key unification (B12) | 3 | 3 | 3 | 5 | 3 | 17 | open; pairs with U36's file - immediately next |
| U38 source-aware evidence pipeline (R1) | 5 | 3 | 4 | 5 | 5 | 22* | KTD21-gated (remediation first); shortcut now exists (source_filter) |
| U47 routing-budget curation (S1) | 4 | 2 | 4 | 5 | 4 | 19* | KTD21-gated; wants U43's honest error/usage signal |
| U48 hub-provenance awareness (S2) | 4 | 2 | 3 | 4 | 4 | 17* | KTD21-gated; feeds U29 |
| U29 host-ledger read integration | 4 | 3 | 3 | 4 | 5 | 19 | KTD12/KTD21-gated |
| U39 symlink-parity discovery (R2) | 4 | 3 | 5 | 5 | 3 | 20* | KTD21-gated |
| U8 dedupe scan | 5 | 3 | 2 | 3 | 5 | 18 | gated; wants U19 |
| U30 plugin-apply ledger attribution | 4 | 3 | 3 | 4 | 4 | 18 | gated; after U29 |
| U49 agentskills spec conformance (S4) | 3 | 2 | 4 | 5 | 3 | 17* | KTD21-gated; rides U9 |
| U21 publish-safety gate | 5 | 4 | 3 | 3 | 5 | 20 | gated; builds on the write path this batch hardens |
| U12 upstream trust interop (+sidecar) | 5 | 4 | 3 | 3 | 5 | 20 | gated |
| U33 circuit breaker | 4 | 3 | 4 | 3 | 4 | 18 | gated; U22's escalation tier |
| U40 host-linter apply gate (R4) | 4 | 2 | 4 | 4 | 4 | 18* | KTD21-gated |
| U41 cron-referenced-skill protection (R6) | 4 | 2 | 4 | 5 | 3 | 18* | KTD21-gated |
| U20 hygiene batch (cycle-2 P3s, +N7/N8/N6) | 2 | 2 | 3 | 5 | 2 | 14 | open; next batch with U19 |
| U25 candidates-decide | 2 | 2 | 4 | 3 | 3 | 14 | gated; may ride U20 |
| U42 workspace-scoped backfill (R9) | 3 | 2 | 4 | 5 | 2 | 16* | KTD21-gated |
| U9 staleness (+U49 pin) | 4 | 2 | 3 | 3 | 4 | 16 | gated |
| U10 missed-trigger detection | 4 | 2 | 3 | 3 | 4 | 16 | gated |
| U22 anti-pattern ledger | 4 | 3 | 3 | 3 | 4 | 17 | gated; after U21 |
| U23 evidence retention + compaction | 3 | 3 | 3 | 3 | 3 | 15 | gated; KTD9 flag contract |
| U24 outcome-linked telemetry | 3 | 2 | 2 | 2 | 3 | 12 | gated; needs U43 (honest error_events) + U22 + U7a |
| U31 doctor --host-compat sweep | 4 | 2 | 3 | 4 | 4 | 17 | gated; after U29/U30 |
| U14 static HTML report | 3 | 1 | 4 | 4 | 2 | 14 | gated |
| U11 hub managed-block rebase | 4 | 2 | 2 | 2 | 4 | 14 | gated; wants U18 |
| U13 native cron backend | 3 | 2 | 3 | 2 | 3 | 13 | gated; after U12 |
| U50 hub staleness report (S5) | 3 | 1 | 3 | 2 | 3 | 12 | KTD24 demand-gated; needs U48 |
| U34 fleet-library conflict report | 2 | 2 | 3 | 2 | 2 | 11 | KTD14 demand-gated |
| U32 context-budget report | — | — | — | — | — | closed | superseded by U47 (KTD23) |
| U28 single error classifier | — | — | — | — | — | closed | superseded by U43 (unification landed, truth table defective) |

Carried scores are cycle-3/4's where no evidence moved; re-annotated this cycle:
U17 (+delay-risk context — selected in cycle 4 and never landed), U36 (held for
batch size in cycle 4, now in its third assessment reproducing), U24 (dependency
now names U43: cohort deltas are only honest once the classifier's truth table is).
New scores (U43-U46, U47-U50) are this session's; the * marks extension packets
whose raw total exceeds their gate — KTD21 (remediation precedes extension, and
both uncommitted batches must be committed first) overrides totals, and every
U38-U42/U47-U50 item is explicitly sequenced behind U43-U46 by the roadmap.

B-item discharge map: B9->U17, B11->U18, B12->U19, B13->U26, B17->U36,
B19->U43, B20->U44, B21->U45, B22->U46. This batch discharges **six of the nine
open B-items** (B9, B17, B19, B20, B21, B22); B11, B12, B13 stay open for the
next batch. No B-item is selectable alone.

## Selected batch: U43 + U44 + U45(+U46) + U36 + U17 + U7-riders

The **discharge-every-reproduced-P2 batch**: after this batch lands, every defect
that pass-5 *reproduced on this tree* is either fixed or has a named next-batch
home; the only remaining P2s would be C1 (U26), P5/P6 (U18), P8 (U19/U20) — all
already sequenced. Batch banner: **"The evidence signal must be classified
truthfully, stored without stalls or torn state, applied without destroying file
identity, and the two oldest surviving injection/ordering defects stop being
perennials."**

| CU | Packet | Files | AC summary (full AC/E in the roadmap, lines 452-478) |
| --- | --- | --- | --- |
| CU-W | U43 (B19/Q1) | `candidates.py`, `storage.py`, tests | structured-first shape table (`returncode`/`exit_code`/`code`/`ok`/`success`/`status`); keyword fallback never matches success shapes; R1 corpus becomes a permanent test; stored-DB fixture yields zero poisoned `error_events` |
| CU-X | U45 + U46 (B21/Q6 + B22/Q7) | `storage.py`, `hooks.py`, tests | one cached connection per resolved path (single-flight, atexit close), contention-vs-environment errno split (fast-fail, no timeout burn); `_schema_ready` probes all three tables and heals interrupted inits |
| CU-Y | U44 (B20/Q3+Q5) | `guarded_apply.py`, tests | atomic writes copy target mode onto the temp file (apply + rollback + snapshot); `_snapshot_for_safety` goes atomic+fsync; R2/R3 reproducers flip |
| CU-Z | U36 (B17/N2+N2b+N3) | `backfill.py`, `cli.py`, tests | newest-first trusted paging with monotonicity assertion + collect-sort fallback; cutoff applied before transcript fetch; `--limit` bounds after ordering; bootstrap bounded; `sessions_failed` printed (N7 rides here) |
| CU-AA | U17 (B9/P7) | `auto_evolve.py`, `cli.py`, tests | `--schedule` validated against systemd calendar subset (no newlines/directive chars), rejected with actionable error; `%` escaped in unit args; injection reproducer flips |
| CU-AB | U7-riders (Q2 + U7b + Q4 + Q8) | `cli.py`, `__init__.py`/`plugin.yaml`, `README.md`, tests | `from typing import Any` (F821 gone, `get_type_hints` survives); version single-sourced with equality test; README rollback form + `--allow-any-target`/rollback `--skills-dir`/`--max-reference-files` documented; `_bounded` clamps emit a warning naming old→new |

Why these six, in one sentence each:

- **U43 tops the board (24)** for the third consecutive cycle that a classifier
  defect has: every evidence row ingested while it is wrong is misclassified
  forever (`error_events` is append-only history), and both U24's cohorts and
  U47's truncation/invocation correlation read that column — it is the highest
  blast-radius, lowest-effort item on the board.
- **U17 (21)** was *selected in cycle 4 and never landed*; it is the only
  command-injection-class defect left on the board and its reproducer still fires.
  Demoting it a second time would make selection noise, not prioritization.
- **U36 (21)** has been reproduced by three consecutive assessments (N2's
  `inspected ['s1','s0']` is byte-identical across passes 4 and 5); it was held in
  cycle 4 purely for batch size. Every backfill run on a non-newest-first driver
  inspects the wrong sessions and every bootstrap fetches full history.
- **U44 (21)**: mode loss (0o640→0o664, apply *and* rollback) breaks exactly the
  group-readable shared skill trees the plugin curates, and the non-atomic
  snapshot undermines U35's own safety design — fixing the landed batch's
  residual beats opening a new surface.
- **U45+U46 (20+19)** share `storage.py` and a root cause family (per-call
  connection topology); #101191 supplies the merged upstream recipe, and the
  15.75s hook stall is the worst unattended latency on the board. U46 is a
  five-point-effort rider on the same file.
- **U7-riders (18)**: the roadmap's cycle-5 sequencing line explicitly routes
  the version/lint/docs residuals onto "the next remediation batch" — this one.
  Q2's F821 is a latent NameError for any `get_type_hints` consumer; U7b's
  version drift has been open since cycle 1; Q4's README teaches a rollback
  command that refuses.

### Why the near-misses stay out

- **U18 (20)** shares `guarded_apply.py` with U44 — landing both in one batch
  double-opens the file with the most destructive surface; U18 anchors the next
  batch (with U19 on `backfill.py`, U20, U26 on `semantic.py`).
- **U6 (20)** flips a user-visible default (bootstrap enabled+apply) — it needs
  its README/quickstart/doc pairing to ship honestly, not a rider slot.
- **U26 (19)** is a clean, disjoint, small unit — the ideal *first* slot of the
  next batch rather than the seventh unit of this one.
- **Every extension (U38-U42, U47-U50)** stays gated by KTD21: remediation
  precedes extension, and both uncommitted batches (cycle-1 + cycle-4) must be
  committed before cycle-5 work builds on them. U24 explicitly depends on U43.
- **U32/U28** are closed on this board (superseded by U47/U43 per KTD23/Q1).

### Batch-level verification plan (for the implement phase)

1. Re-run `/home/agent/.hermes/conductor-runs/2cc5b112c9694bfaa4a47645f139983a-assess/repro-pass5.py`
   after landing: R1 (all four shapes), R2, R3, R5, R6, and the N2/N2b/N3 and P7
   probes must all flip to fixed; R8 stays not-reproduced; P5/P6, P8, P9, P10,
   N7, C1 may still reproduce (next-batch items — N7 is targeted by CU-Z's
   summary AC and should flip too).
2. `python3 -m pytest` full suite green at the new baseline (184 + the new
   targeted tests); `ruff check .` shows the F821 gone and no new diagnostics
   (absolute count may drop via U7-riders' `--fix`ables, never rise).
3. Version equality test passes across `__init__.py` / `plugin.yaml` / bundled
   SKILL.md / result `schema_version`.
4. No default behavior change reaches users except U36's (import the *newest*
   sessions instead of an arbitrary subset — aligning behavior with the help
   text that already promises "newest") and U17's (garbage schedules now
   rejected — aligning with systemd's own grammar).

## Reproduction / verification pointers

```bash
python3 /home/agent/.hermes/conductor-runs/2cc5b112c9694bfaa4a47645f139983a-assess/repro-pass5.py   # 21/22 reproduce at selection time (R8 cleared)
python3 -m pytest                                                                                   # 184 passed (selection-time re-run)
ruff check . 2>&1 | tail -1                                                                         # 64 errors / 45 fixable
git -C /work/projects/hermes-curator-evolver log --oneline -1                                        # 45328db
git -C /work/projects/hermes-curator-evolver status --short | wc -l                                  # 19 (both prior batches uncommitted)
grep -n "^U4[3-9]\.\|^U50\.\|^KTD2[1-5]" /work/projects/hermes-curator-evolver/.hermes/plans/autonomy-prop_8c5390ffe26640fa.md  # AC/E source, lines 421-511
```
