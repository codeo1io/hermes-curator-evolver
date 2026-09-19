---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-6-stewardship-request
run: 6f5d76c84f52491ba25460c4a6e1a454
phase: stewardship
attempt: 644faa78a1194caf8bfa590617648228
skill: ce-plan (change-request description; router has no stewardship skill and no ce-* router/skill is installed on this host at all — ce-handoff rejected as session continuity, ce-work/ce-worktree rejected as topology choice this phase must NOT make; same route and reasoning as the fleet's five prior stewardship phases for this repository)
upstream: docs/prioritization/2026-09-02-cycle-6-batch.md (selected batch U51 + U52 + U53(+U54))
---

# Stewardship request — cycle 6 ingest→store truth batch

This document describes the selected maintenance batch for the conductor to steward. It
deliberately does **not** choose Git topology: no branch names, no worktree layout, no commit
sequencing. Those are the conductor's to plan after inventorying the repository, detecting
overlap, splitting unrelated concerns, and preserving dirty state.

Inventory re-checked live this session: single worktree per `git worktree list` at
`/work/projects/hermes-curator-evolver` on branch `fix/maintenance-cycles-1-5` @ `4350ee2`
(source-identical to `ac9c0ee`; `4350ee2` is a workflow-trigger-only empty commit); remotes
`origin` (pingchesu, upstream, never push) and `fork` (codeo1io, push target per the roadmap's
Repository remote rule). Dirty state = **1 modified tracked file** (the append-only cycle-6
roadmap extension) **+ 4 untracked campaign docs** (pass-6 assessment, cycle-6 ideation,
cycle-6 batch selection, this request) — **no uncommitted code**: cycles 1-5 are committed on
this branch, so the KTD16/KTD21 commit-first gate that shaped the last two stewardship
requests is discharged. The batch reproducers re-run **at stewardship time** on this exact
tree (`repro-pass6.py` + `repro-pass6-fixups.py`): every batch-target defect class reproduces
— F1/F18 (code:200/201/204 → error; 3/3 poisoned `error_events`), F2 (all digit widths of
"N failed" cleared), F4 (success-phrase-anywhere clears a real failure), F5 (docstring-truth
contradiction cases), F6 (read completed in 0.002s while `_path_lock` held), F7 (10,040-store
limit 2 → yielded s9999/s9998, newest never fetched, 50 pages), F24 (`sessions_seen`
accounting). S6's attribution asymmetry re-verified directly:
`_extract_skill_name('skill_view', {'skills': ['x']})` → `None` while the identical
`skills`-list shape on any non-skill tool attributes `x` (the `SKILL_TOOL_NAMES` early return
at storage.py:222-226 reads only `name`/`skill`/`skill_name`).

```json
{
  "stewardship_request": {
    "title": "hermes-curator-evolver ingest→store truth batch (cycle 6): error-classifier truth table v2 — paired-count truth for all digit widths, HTTP-success `code` shapes, success-phrase scoping, docstring/test truth unification (U51); backfill cap-in-recency-order with honest skip accounting (U52); storage read-path concurrency contract + symmetric skill attribution (U53+U54)",
    "summary": "Four dependency-light, independently verifiable packets (three change units) that together discharge all three pass-6 P2s and the two storage.py P3s — B23, B24, B25, B26; four of the six new B-items. Theme: the evidence rows are classified truthfully whatever their shape, imported from the newest sessions not the oldest, attributed one action at a time, and read without tearing the writer's transaction. CU-AC (U51, candidates.py): the classifier's second reopen in three consecutive cycles — the cycle-5 `(?<!0\\s)failed` lookbehind meant to clear '0 failed' also clears every failure count ending in zero ('10 failed', '100 failed', '10 failed, 2 passed' — F2 reproduced at stewardship time), structured `{'code':200}`/201/204 (HTTP success codes stored verbatim by tool wrappers) classify as errors via the nonzero-exit branch and then poison append-only `error_events` history 3/3 (F1/F18), a success phrase anywhere in the payload clears a real failure ('deploy failed: connection refused; earlier healthcheck reported no errors' — F4), and the `looks_like_error` docstring that specifies the U43 truth table says 'zero → success' while the code checks error/exception/status-failure BEFORE the zero-exit return (F5) — the doc or the order must be picked and pinned, in one commit with tests/test_candidates.py:491/:505. CU-AD (U52, backfill.py): `metadata_cap = max(limit, 10_000)` binds while pages are still in the OLDEST region — on a 10,040-session store with limit 2 the importer yielded s9999/s9998, never fetched the newest session, walked 50 pages, and logged sessions_skipped_old=9675 about the sessions it actually wanted (F7); the cap must bound the RESULT after trusted-order paging, never the scan, and `sessions_seen`/`sessions_skipped_old` must count what actually happened (F24). CU-AE (U53+U54, storage.py): the warm-connection `connect()` docstring at :291-299 promises 'all use is serialized by the path lock the write/read helpers below acquire' but the readers at :540/:599/:622 use `with self.connect()` with no `_path_lock` (F6: summary() completed in 0.002s while the lock was held), and a reader's `with conn:` block on the shared cached connection can COMMIT or ROLL BACK another thread's in-flight transaction; PRAGMA setup runs under the global `_connection_lock` (:316). Readers need read-only connections (`file:...?mode=ro`) or the same lock discipline, the docstring must state the actual guarantee, and `_extract_skill_name` (:219-229) needs one shared extraction entry point so `skill_view` list-forms attribute like every other surface and `skills[].event_count` counts actions, not event rows (S6, re-verified live). Only two user-visible behavior changes, both alignment-with-truth: the two misclassification classes flip (note: `error_events` is append-only — rows poisoned before the fix stay poisoned; no history rewrite is in scope), and >10k-store imports fetch newest-first (the help text already promises 'newest'). No new dependencies, no model calls, no feature additions; remediation precedes extension per KTD26 — U55/U56 and the extension set stay out.",
    "repository_candidate": {
      "name": "hermes-curator-evolver",
      "path": "/work/projects/hermes-curator-evolver",
      "remote": "git@github.com:codeo1io/hermes-curator-evolver.git (fork, push target) / https://github.com/pingchesu/hermes-curator-evolver.git (origin, upstream)",
      "remote_role": "push target is the 'fork' remote (codeo1io); 'origin' (pingchesu) is upstream and must never be pushed to, per the roadmap's Repository remote section",
      "branch": "fix/maintenance-cycles-1-5",
      "head": "4350ee2",
      "committed_tree": [".github", ".gitignore", "CONTRIBUTING.md", "LICENSE", "README.md", "__init__.py", "docs", "examples", "hermes_curator_evolver", "plugin.yaml", "pyproject.toml", "skills", "tests"],
      "dirty_state_to_preserve": "1 modified tracked file (.hermes/plans/autonomy-prop_8c5390ffe26640fa.md — the append-only cycle-6 roadmap extension, prior sections byte-identical, pre-image sha256 recorded inside it) + 4 untracked campaign docs (docs/assessment/2026-09-02-adversarial-repository-assessment-pass6.md, docs/ideation/2026-09-02-cycle-6-extension-research.md, docs/prioritization/2026-09-02-cycle-6-batch.md, docs/stewardship/2026-09-02-cycle-6-stewardship-request.md). NO uncommitted code: cycles 1-5 are committed on this branch, so unlike cycles 4-5 there is no substrate-commit gate to sequence around.",
      "rationale": "All four packets are this repository's own Python package and its tests; every defect reproduces inside this tree with scratch temp dirs and no network or cross-repository input (re-run at stewardship time). The dirty state is documentation-only campaign output that must ride the batch's commit gate, not fold into any code unit."
    },
    "change_units": [
      {
        "id": "CU-AC",
        "packet": "U51",
        "title": "Error-classifier truth table, second reopen (B23/S1+S2+S4+S7)",
        "surfaces": [
          "hermes_curator_evolver/candidates.py:100 (_FAILURE_KEYWORD_PATTERN's '(?<!0\\s)failed' lookbehind clears every count ending in zero — replace with explicit paired-count parsing: N>0 failed is an error at ANY digit width, '0 failed' alone is success)",
          "hermes_curator_evolver/candidates.py:109-115 (_SUCCESS_COUNT_PATTERN clears a verdict from a phrase ANYWHERE in the payload — scope the clear so a real failure ('deploy failed: connection refused') is not erased by a distant 'no errors' tail)",
          "hermes_curator_evolver/candidates.py:117 + :262-282 (_EXIT_CODE_KEYS/structured branch: 'code' carries exit-code semantics, so {'code':200}/201/204 — HTTP success codes stored verbatim — classify as errors; honor recognized in-band success statuses or explicit ok/success/status companions before the nonzero exit branch)",
          "hermes_curator_evolver/candidates.py:286-305 (looks_like_error docstring says 'zero → success' while :262-272 checks error/exception/status-failure first — pick docstring-fix or check-reorder and pin it in the same commit)",
          "tests/test_candidates.py (corpus v2 lifted verbatim from repro-pass6.py F1/F2/F4/F5 + the existing U43 corpus at :491/:505 stays green)",
          "tests/test_storage.py (stored-DB fixture: 3x record_tool_pass({'code':200}) yields zero poisoned error_events rows)"
        ],
        "must_land_before": [],
        "rationale": "Board top (24/25) and third consecutive cycle a classifier defect ranks first; error_events is append-only history, so every day unfixed permanently poisons the rows U24/U60 cohorts, U47's correlation, and auto-evolve thresholds read. F1/F2/F4/F5 all reproduced live at stewardship time. Sole owner of candidates.py this cycle."
      },
      {
        "id": "CU-AD",
        "packet": "U52",
        "title": "Backfill cap-in-recency-order + honest accounting (B24/S3; completes U36 at scale)",
        "surfaces": [
          "hermes_curator_evolver/backfill.py:203-215 (metadata_cap loop: cap the RESULT after trusted-order paging yields the newest 'cap' sessions — never cap the scan; monotonicity assertion on page order)",
          "hermes_curator_evolver/backfill.py (sessions_seen / sessions_skipped_old accounting: count sessions actually skipped, not pages walked — F24 shows the counters misreport)",
          "tests/test_backfill_sessions.py (10,040-session fixture: limit 2 yields the TWO NEWEST sessions in bounded pages with truthful counters; the N2/N2b/N3 corpus stays green)"
        ],
        "must_land_before": [],
        "rationale": "The other reproduced P2: every import on a >10k-session store walks 50 pages to fetch the OLDEST region while logging skips about the sessions it wanted (F7 reproduced live at stewardship time, byte-identical to assess). Sole owner of backfill.py this cycle — U19 (identity/dedup) deliberately held to the next batch per the selection's near-miss rationale."
      },
      {
        "id": "CU-AE",
        "packet": "U53 + U54",
        "title": "EvidenceStore read-path concurrency contract + symmetric skill attribution (B25/S5 + B26/S6)",
        "surfaces": [
          "hermes_curator_evolver/storage.py:291-299 (connect() docstring promises path-lock serialization of ALL use — correct it to state the actual guarantee delivered by this unit)",
          "hermes_curator_evolver/storage.py:540 (summary), :599 (recent_tool_events), :622 (recent_turns) — 'with self.connect() as conn' readers take no _path_lock and a 'with conn:' block on the shared cached connection can commit/rollback another thread's in-flight transaction; move readers to read-only connections (file:...?mode=ro) or the same lock discipline, with no implicit commit ever issued",
          "hermes_curator_evolver/storage.py:316 (PRAGMA busy_timeout under the global _connection_lock — move off the global lock path)",
          "hermes_curator_evolver/storage.py:219-229 (_extract_skill_name: SKILL_TOOL_NAMES early return reads only name/skill/skill_name, so skill_view's 'skills'-list form returns None while the identical shape on any other tool attributes — one shared extraction entry point; skills[].event_count counts actions, not event rows)",
          "hermes_curator_evolver/storage.py:362/:395/:409/:416 (writer paths — context only; their semantics are unchanged)",
          "tests/test_storage.py (reader-under-held-lock fixture per the new contract; concurrent-writer transaction-survival test; attribution symmetry test: both surface forms attribute, event_count=1 for the double-tagged case)"
        ],
        "must_land_before": [],
        "rationale": "Two packets, one file, one contract — folded per KTD22's one-packet-per-root-cause precedent: pass-6 proved the read side both bypasses the documented lock (F6: 0.002s while held) and can tear the writer's transaction, while the attribution asymmetry (S6, re-verified live this session) makes the same lookup count twice depending on which tool surfaced it. Upstream #101279 (multi-writer shared-brain) says this class grows. U53 and U54 are separate concerns in one file — separate hunks."
      }
    ],
    "surfaces": [
      "hermes_curator_evolver/candidates.py:100",
      "hermes_curator_evolver/candidates.py:109-115",
      "hermes_curator_evolver/candidates.py:117",
      "hermes_curator_evolver/candidates.py:262-282",
      "hermes_curator_evolver/candidates.py:286-305",
      "hermes_curator_evolver/backfill.py:203-215",
      "hermes_curator_evolver/storage.py:219-229",
      "hermes_curator_evolver/storage.py:291-299",
      "hermes_curator_evolver/storage.py:316",
      "hermes_curator_evolver/storage.py:540",
      "hermes_curator_evolver/storage.py:599",
      "hermes_curator_evolver/storage.py:622",
      "hermes_curator_evolver/storage.py:362",
      "hermes_curator_evolver/storage.py:395",
      "hermes_curator_evolver/storage.py:409",
      "hermes_curator_evolver/storage.py:416",
      "tests/test_candidates.py",
      "tests/test_backfill_sessions.py",
      "tests/test_storage.py"
    ],
    "must_remain_separate": [
      ["CU-AC (candidates.py:100/:109-115/:117/:262-282/:286-305 classifier truth) - U51", "CU-AE (storage.py:291-299/:540/:599/:622/:316 reader contract + :219-229 attribution) - U53/U54"],
      ["CU-AD (backfill.py:203-215 cap-after-ordering + accounting) - U52", "CU-AE (storage.py reader contract) - U53/U54"],
      ["CU-AC (candidates.py classifier) - U51", "CU-AD (backfill.py ordering) - U52"],
      ["U53 (storage.py:291-299/:540/:599/:622/:316 read-path contract)", "U54 (storage.py:219-229 _extract_skill_name) - same file, disjoint hunks: separate commits inside CU-AE"],
      ["the modified roadmap (.hermes/plans/autonomy-prop_8c5390ffe26640fa.md) and the 4 untracked campaign docs (assessment/ideation/prioritization/stewardship)", "every CU-AC/CU-AD/CU-AE unit of this request"],
      ["held next-batch units: U55 (auto_evolve.py:399 duplicate-name collisions), U56 hygiene (S9 bundled-SKILL.md version at skills/curator-evolution/SKILL.md:4, S10 traceback sites skill_audit.py:289-290 + cli handlers + _run_bootstrap, cap unification candidates.py:32/guarded_apply.py:26/auto_evolve.py:53, P14 ruff gate, Q6 residual), U18 (auto_evolve.py:1143/1155-1167 apply loop), U19 (backfill.py identity/dedup), U26 (semantic.py:199)", "every CU-AC/CU-AD/CU-AE unit of this request"],
      ["KTD26-gated extensions (U38-U42, U47-U50, U57-U62) and U62's double gate (KTD28: skills-index URL 404)", "every CU-AC/CU-AD/CU-AE unit of this request"],
      ["CU-AC's tests/test_storage.py additions (stored-DB zero-poison fixture)", "CU-AE's tests/test_storage.py additions (lock/reader/attribution fixtures) - separate test functions"]
    ]
  }
}
```

## Splitting notes (why these boundaries)

- **One file, one owner, this cycle.** `candidates.py` is CU-AC's alone; `backfill.py` is
  CU-AD's alone; `storage.py` is CU-AE's alone. No file is opened by two units (the cycle-5
  three-way `cli.py` situation does not arise — `cli.py` has no batch surface beyond none;
  the U52 counters live in `backfill.py`'s result dict).
- **CU-AE carries two packets by design, split internally.** U53 (reader/lock contract) and
  U54 (attribution symmetry) share `storage.py` and were selected to land together
  (KTD22 root-cause precedent), but they are disjoint hunks — readers vs. one pure helper —
  and should not merge into one commit. The writers at :362/:395/:409/:416 are context,
  unchanged.
- **CU-AC's only storage surface is its fixture.** The classifier lives entirely in
  `candidates.py`; `storage.py:179/:338-...` consume it unchanged. That is why the
  stored-DB fixture is listed under CU-AC while CU-AE owns the file's behavior.
- **The dirty tree is campaign documentation, not substrate.** Unlike cycles 4-5 there is
  no uncommitted code to commit first; the roadmap edit and four docs ride the batch's own
  commit gate and must not fold into any code unit's commit.
- **No intra-batch hard dependencies** (dep-freedom 5 across the scoring table); the soft
  coordination is `tests/test_storage.py`, touched by two units in separate functions.

## Verification contract for the implement phase

Mechanical gates exist before any review: re-run
`/home/agent/.hermes/conductor-runs/6f5d76c84f52491ba25460c4a6e1a454-assess/repro-pass6.py`
(+ `-fixups.py`) — this batch flips exactly F1, F18, F2, F4, F5, F7, F24 and the S6
attribution asymmetry green; F6 flips to the NEW contract (readers honor the lock or run
read-only with the writer's transaction intact); F8 (P5/P6), F11-F13b (S10), F14 (S8),
F16 (N6), F17 (C1), F22 (P8), F23 residual must remain reproducing (next-batch homes U18,
U56, U55, U60, U26). History note: `error_events` rows poisoned before the fix stay
poisoned — no re-classification pass is in scope. Targeted pytest per changed surface
(`tests/test_candidates.py`, `tests/test_backfill_sessions.py`, `tests/test_storage.py`);
full suite green above the 249 baseline; `ruff check hermes_curator_evolver tests` ≤ 63
errors (the gate itself lands with U56, next batch). Roadmap Acceptance governs: push to
`fork` only. None of that is this phase's to do.

*Read-only request; no code changed, nothing committed or pushed.*
