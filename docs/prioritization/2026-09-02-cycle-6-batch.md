---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-6-batch-selection
mode: repo-grounded
run: 6f5d76c84f52491ba25460c4a6e1a454
phase: prioritize
attempt: 09a07ae164554c35813deae45e4dc31f
skill: ce-pov (position over the roadmap's enumerated unit set; no ce-prioritize is installed in either roster — same route the fleet's prior prioritize phases took; no ce-* router/skill exists on this host at all, the standing disclosed deviation since pass 2)
tier: 1 - selection is a two-way door; a wrong batch costs a cycle, not the repository
disclosure: pi exposes no subagent primitive; grounding and scoring ran in-thread in one context; no panel was summoned. Scores carried from cycle-3/4/5 where no evidence moved (no independence claimed over them); new cycle-6 scores (U51-U62) and re-annotated items are this session's own.
---

# Cycle 6 implementation batch selection

Scores every unresolved roadmap packet — the cycle-6 set (U51-U62) plus the standing
cycle-1 residuals (U5/U6) and unlanded cycle-2/3/4/5 units (U8-U14, U18-U26,
U29-U31, U33/U34, U38-U42, U47-U50) — from `.hermes/plans/autonomy-prop_8c5390ffe26640fa.md`
(cycle-6 extension, lines 513-623) on the same five axes, 1-5 scale. **Impact** =
value if done. **Delay risk** = cost of leaving it undone another cycle. **Effort**
= 5 is cheapest. **Dep-freedom** = 5 means nothing gates it. **Strategic** = leverage
on later work. **Total** is the simple sum, shown for ranking only — gates override
totals. Left the board this cycle: U43/U44/U45/U46/U36/U17/U7-riders (verified fixed
by pass 6; U43 and U36 leave reopen successors U51/U52 on this board), U32/U28
(closed by supersession, cycle 5), U24 (absorption pending per KTD29 — closes when
U51+U60 land).

Grounding this cycle: pass-6 assessment (~2h ago, this run) re-derived every finding
fresh on this exact tree (`4350ee2`, source-identical to `ac9c0ee`) with 24 probes
(19 reproduced, 3 re-run after harness fixes, 2 tested-and-cleared) — every defect
this batch targets reproduced hours ago at
`/home/agent/.hermes/conductor-runs/6f5d76c84f52491ba25460c4a6e1a454-assess/repro-pass6.py`
(S1: `"10 failed, 2 passed"`/`"100 failed"` → success; S2: `{"code":200}` → error,
3/3 poisoned `error_events`; S3: 10,040-session store, limit 2 → yielded s9999/s9998,
newest never fetched, 50 pages; S4 phrase-clear; S5 summary() under a held
`_path_lock`; S6 attribution asymmetry). Verified live at selection time:
`candidates.py:100` still carries `(?<!0\s)failed`. Tree state at selection:
`4350ee2` + the uncommitted roadmap update and two docs (no code changes since
pass 6); pytest 249/249, ruff 63 errors / 48 fixable (drift 65→63→64→63, ungated).
Commit discipline: cycles 1-5 are committed on `fix/maintenance-cycles-1-5` — the
KTD16/KTD21 gate that held extension work for two cycles is **discharged**.

## Scoring

| Item | Impact | Delay risk | Effort | Dep-freedom | Strategic | Total | Gate status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| U51 classifier truth table, 2nd reopen (B23/S1+S2+S4+S7) | 5 | 5 | 4 | 5 | 5 | 24 | open; 3rd consecutive cycle a classifier defect tops the board; corpus already written in repro-pass6.py |
| U52 backfill cap-in-recency-order (B24/S3; U36 reopened at scale) | 4 | 4 | 4 | 5 | 4 | 21 | open; P2; every >10k-store run imports the oldest region |
| U18 apply-loop resilience (P5/P6) | 4 | 4 | 3 | 5 | 4 | 20 | open; re-derived fresh this pass (write_text at auto_evolve.py:1163); held — disjoint next slot |
| U6 bootstrap default alignment | 4 | 3 | 4 | 5 | 4 | 20 | open; user-visible default flip — needs docs pairing; next batch |
| U53 read-path concurrency contract (B25/S5) | 4 | 3 | 3 | 5 | 4 | 19 | open; #101279 multi-writer growth raises its ceiling; delicate — pairs with U54 |
| U26 rerank oversampling (C1) | 4 | 3 | 4 | 5 | 3 | 19 | open; re-derived fresh (semantic.py:199 vs 202-213); disjoint next slot |
| U29 host-ledger read integration | 4 | 3 | 3 | 4 | 5 | 19 | gated; strategic up — 3rd writer (sync) now attributable via U57 |
| U47 routing-budget curation | 4 | 2 | 4 | 5 | 4 | 19* | KTD26-gated; wants U51's honest error/usage signal |
| U38 source-aware evidence pipeline | 5 | 3 | 4 | 5 | 5 | 22* | KTD26-gated; #101266 (−93.9%) + source_filter shortcut recorded |
| U39 symlink-parity discovery | 4 | 3 | 5 | 5 | 3 | 20* | KTD26-gated |
| U21 publish-safety gate | 5 | 4 | 3 | 3 | 5 | 20 | gated; after the write path this cycle's batch stabilizes |
| U12 upstream trust interop | 5 | 4 | 3 | 3 | 5 | 20 | gated |
| U54 symmetric skill attribution (B26/S6) | 3 | 2 | 4 | 5 | 3 | 17 | open; rides U53's file — land together |
| U55 duplicate-name collision reporting (B27/S8) | 3 | 2 | 4 | 5 | 4 | 18 | open; held — its output format should be designed with U59's vocabulary, next batch |
| U56 hygiene batch (S9+S10+caps+P14 ruff gate+Q6 residual) | 3 | 3 | 3 | 5 | 3 | 17 | open; held — ruff gate + 48 auto-fixables would churn files U51-U54 are open on |
| U19 identity/dedup-key unification | 3 | 3 | 3 | 5 | 3 | 17 | open; pairs with U52's file — immediately next |
| U31 doctor --host-compat sweep | 4 | 2 | 3 | 4 | 4 | 17* | gated; +3 new probes this cycle (manifest, curator-tick, index URL) |
| U48 hub-provenance (3-source per KTD27) | 4 | 2 | 3 | 4 | 4 | 17* | KTD26-gated; broadened this cycle — one subsystem with U57 |
| U49 agentskills spec conformance | 3 | 2 | 4 | 5 | 3 | 17* | KTD26-gated; spec re-verified unchanged this cycle |
| U60 outcome-delta gate (absorbs U24) | 5 | 3 | 3 | 2 | 5 | 18* | KTD26-gated; hard-dep U51 — first extension of the NEXT cycle |
| U57 bundled-origin provenance | 4 | 2 | 4 | 4 | 4 | 18* | KTD26-gated; top-ranked extension (85%/Low); live host baseline (81/80/1) cited |
| U40 host-linter apply gate | 4 | 2 | 4 | 4 | 4 | 18* | KTD26-gated |
| U41 cron-referenced-skill protection | 4 | 2 | 4 | 5 | 3 | 18* | KTD26-gated |
| U8 dedupe scan | 5 | 3 | 2 | 3 | 5 | 18 | gated; wants U19 |
| U30 plugin-apply ledger attribution | 4 | 3 | 3 | 4 | 4 | 18 | gated; after U29 |
| U33 circuit breaker | 4 | 3 | 4 | 3 | 4 | 18 | gated |
| U58 staleness reconciliation vs native curator | 4 | 2 | 3 | 4 | 4 | 17* | KTD26-gated; flag-collision decision vs U50 recorded in its AC |
| U59 lifecycle: pinned/absorbed_into | 3 | 2 | 3 | 4 | 3 | 15* | KTD26-gated; wants U55 first |
| U23 evidence retention + compaction | 3 | 4 | 3 | 3 | 3 | 16 | gated; delay-risk raised — #101316's 90-day auto-prune makes this store the only long-horizon record; recipe now upstream |
| U42 workspace-scoped backfill | 3 | 2 | 4 | 5 | 2 | 16* | KTD26-gated |
| U9 staleness (+U49 pin) | 4 | 2 | 3 | 3 | 4 | 16 | gated |
| U10 missed-trigger detection | 4 | 2 | 3 | 3 | 4 | 16 | gated |
| U22 anti-pattern ledger | 4 | 3 | 3 | 3 | 4 | 17 | gated; U60 supersedes its outcome-measured half (KTD29) |
| U20 hygiene (cycle-2 P3s) | 2 | 2 | 3 | 5 | 2 | 14 | open; N7 slice discharged in cycle 5 (pass-6 verified) |
| U25 candidates-decide | 2 | 2 | 4 | 3 | 3 | 14 | gated |
| U14 static HTML report | 3 | 1 | 4 | 4 | 2 | 14 | gated |
| U5 residual (confirm + close) | 3 | 2 | 5 | 5 | 3 | 18 | open; rides any batch |
| U11 hub managed-block rebase | 4 | 2 | 2 | 2 | 4 | 14 | gated; wants U18 |
| U13 native cron backend | 3 | 2 | 3 | 2 | 3 | 13 | gated |
| U61 knowledge-unit demotion | 3 | 2 | 2 | 3 | 3 | 13* | KTD26-gated; most speculative survivor |
| U50 hub-source staleness | 3 | 1 | 3 | 2 | 3 | 12 | KTD24 demand-gated |
| U34 fleet-library conflict report | 2 | 2 | 3 | 2 | 2 | 11 | KTD14 demand-gated |
| U62 ecosystem duplicate check | 3 | 1 | 4 | 1 | 2 | 11 | double-gated: KTD26 + KTD28 (index 404, PR unmerged — unbuildable today) |
| U24 outcome-linked telemetry | — | — | — | — | — | absorption pending | KTD29: closes when U51+U60 land |

Carried scores are cycle-3/4/5's where no evidence moved; re-annotated this cycle:
U51-U62 (new, this session's), U29 (third writer attributable), U23 (delay-risk
3→4, #101316 horizon), U20 (N7 discharged), U22 (U60 supersedes its measured half),
U48 (scope broadened per KTD27). The * marks extension packets gated by KTD26
(remediation precedes extension) — U38's raw 22 would top the board otherwise;
the gate holds because the classifier's reopen (U51) poisons the exact signal U38's
pipeline would carry.

## Selected batch: U51 + U52 + U53(+U54)

The **ingest→store truth batch** — the fourth consecutive "signal first" batch, and
the one that closes the pass-6 P2 set entirely: after it lands, every defect pass-6
*reproduced* is fixed except S8/S9/S10 (named next-batch homes U55/U56) and the
carried P5/P6/P8/P9/N6/C1/C3/P12/P15 (all sequenced). Banner: **"The evidence rows
are classified truthfully whatever their shape, imported from the newest sessions
not the oldest, attributed one action at a time, and read without tearing the
writer's transaction."**

| CU | Packet | Files | AC summary (full AC/E in the roadmap, lines 541-556) |
| --- | --- | --- | --- |
| CU-AC | U51 (B23/S1+S2+S4+S7) | `candidates.py`, `tests/test_candidates.py` | paired-count truth for all digit widths; `code`-shape HTTP-success values (200/201/202/204) not errors absent failure context; success-phrase scoping; docstring and `test_candidates.py:491` agree in one commit; repro-pass6 S1/S2/S4/S7 corpus becomes the permanent adversarial test v2 |
| CU-AD | U52 (B24/S3) | `backfill.py`, `cli.py`, `tests` | `metadata_cap` caps the *result* after trusted-order paging, never the scan; monotonicity assertion; truthful `sessions_skipped_old`; 10,040-session fixture yields the 2 newest in bounded pages |
| CU-AE | U53 + U54 (B25+S6) | `storage.py`, `tests` | readers on read-only connections (`mode=ro`) or the same lock discipline — never an implicit commit over another thread's txn; docstring corrected to the actual guarantee; PRAGMA off the global lock; one shared skill-name extraction entry point (`skill_view` lists == `read_file` payloads); `event_count` counts actions, not event rows |

Why these four, in one sentence each:

- **U51 (24)** — third consecutive cycle a classifier defect tops the board, and the
  stakes compound: `error_events` is append-only, so every day on the current truth
  table permanently poisons rows that U24/U60's cohorts and U47's correlation must
  read. Blast radius maximal, effort modest, the adversarial corpus is already
  written and lifted.
- **U52 (21)** — the other reproduced P2: on any store above ~10k sessions the
  importer walks 50 pages to fetch the *oldest* region while logging
  `sessions_skipped_old` about the sessions it actually wanted. The cycle-5 fix
  made paging trusted-order; the cap must bind after ordering — a one-mechanism
  fix with a ready 10,040-session fixture.
- **U53 (19) + U54 (17)** — same file, one contract: pass-6 proved the read side
  both bypasses the documented lock *and* can commit/rollback another thread's
  in-flight transaction, while the attribution asymmetry makes the same lookup
  count twice depending on which tool surfaced it. Upstream #101279 (multi-writer
  shared-brain) says this class grows; landing them together opens `storage.py`
  once. U54 is the four-point-effort rider on U53's connection work.

### Why the near-misses stay out

- **U55 (18)** — real (S8 reproduced: a duplicate frontmatter name silently drops a
  directory), but its *output format* is U59's vocabulary (which dir wins, dropped
  path, manifest state); landing it now would ship a report U59 immediately
  redesigns. Next batch, with U59's design.
- **U56 (17)** — every slice is small, but the ruff-gate slice (P14) belongs with
  the batch that consumes the 48 auto-fixables, and those edits would churn exactly
  the files (`candidates.py`, `storage.py`) CU-AC/CU-AE are open on. Next batch,
  after the code batch lands.
- **U6 (20)** — flips a user-visible default (bootstrap enabled+apply); ships
  honestly only with its README/quickstart pairing, not as a fifth unit.
- **U18 (20)** — P5/P6 are re-derived and real, but `guarded_apply.py`/apply-loop
  work pairs naturally with U19 (identity/dedup) as the next disjoint pair; this
  batch already carries the two heaviest files (`storage.py`, `candidates.py`).
- **Every extension (U38-U42, U47-U50, U57-U62)** — KTD26: remediation precedes
  extension. U38 (22 raw) and U57 (top research survivor) anchor the next
  extension batch, unlocked the moment this one lands; U60 hard-depends on U51.
- **U62** stays double-gated (KTD28: index URL 404, PR unmerged — unbuildable).

B-item discharge map: B23→U51, B24→U52, B25→U53, B26→U54. This batch discharges
**four of the six** new B-items; B27 (U55) and B28 (U56) are named next-batch homes.
No B-item is selectable alone.

## Batch-level verification plan (for the implement phase)

1. Re-run `/home/agent/.hermes/conductor-runs/6f5d76c84f52491ba25460c4a6e1a454-assess/repro-pass6.py`
   after landing: S1 (all paired-count shapes, every digit width), S2
   (`{"code":200/201/204}` not error; 3× `record_tool_pass` → `error_events` 0/3),
   S4, S7 must flip; S3 must yield the two newest sessions with bounded pages and
   truthful skip counters; S5 must show readers honoring the new contract (block
   briefly or complete via read-only connection) with the writer's transaction
   intact; S6 must attribute both surface forms with `event_count=1` for the
   double-tagged case. S8/S9/S10 may still reproduce (U55/U56, next batch).
   History note: `error_events` is append-only — rows poisoned before the fix stay
   poisoned; the fix guarantees future ingest only. No re-classification pass is
   in scope (that would rewrite evidence history).
2. `python3 -m pytest` full suite green at the new baseline (249 + the lifted
   corpus v2 + the 10,040-session fixture + concurrency/attribution tests);
   `ruff check hermes_curator_evolver tests` ≤ 63 errors (never rises; the gate
   lands with U56, next batch).
3. Docstring/test truth unification: `grep` shows exactly one definition of the
   zero-vs-nonzero verdict truth across `candidates.py` docstrings and
   `tests/test_candidates.py`.
4. No default behavior change except verdict corrections (the two
   misclassification classes), the newest-vs-oldest import fix, and read-only
   reader connections — each already documented as aligning behavior with stated
   contracts.

## Reproduction / verification pointers

```bash
python3 /home/agent/.hermes/conductor-runs/6f5d76c84f52491ba25460c4a6e1a454-assess/repro-pass6.py        # S-probe corpus (19 reproduced at assess)
python3 /home/agent/.hermes/conductor-runs/6f5d76c84f52491ba25460c4a6e1a454-assess/repro-pass6-fixups.py # fixup probes
/home/agent/.hermes/hermes-agent/venv/bin/python3 -m pytest -q                                            # 249 passed (assess baseline)
ruff check hermes_curator_evolver tests 2>&1 | tail -1                                                     # 63 errors, 48 fixable
git -C /work/projects/hermes-curator-evolver log --oneline -1                                               # 4350ee2
git -C /work/projects/hermes-curator-evolver status --short                                                 # roadmap + 2 docs, no code changes since pass 6
grep -n "U5[1-6]\.\|^KTD26\|^KTD29" /work/projects/hermes-curator-evolver/.hermes/plans/autonomy-prop_8c5390ffe26640fa.md  # AC/E source, lines 541-563, 615-618
```
