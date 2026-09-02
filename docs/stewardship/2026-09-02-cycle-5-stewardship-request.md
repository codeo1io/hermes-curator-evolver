---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-5-stewardship-request
run: 2cc5b112c9694bfaa4a47645f139983a
phase: stewardship
attempt: 85672d4fc65345f5bdb3e2f42cd7cde9
skill: ce-plan (change-request description; router has no stewardship skill - ce-handoff rejected as session continuity, ce-work/ce-worktree rejected as topology choice this phase must NOT make; same route and reasoning as the fleet's four prior stewardship phases for this repository)
upstream: docs/prioritization/2026-09-02-cycle-5-batch.md (selected batch U43 + U44 + U45/U46 + U36 + U17 + U7-riders)
---

# Stewardship request — cycle 5 reproduced-P2 discharge batch

This document describes the selected maintenance batch for the conductor to steward. It
deliberately does **not** choose Git topology: no branch names, no worktree layout, no commit
sequencing. Those are the conductor's to plan after inventorying the repository, detecting
overlap, splitting unrelated concerns, and preserving dirty state.

Inventory re-checked live this session: `main` @ `45328db` (single worktree per
`git worktree list`), remotes `origin` (pingchesu, upstream, never push) and `fork`
(codeo1io, push target per the roadmap's Repository remote rule), dirty state = **13 modified
tracked files** — the still-uncommitted cycle-1 remediation *and* the cycle-4 batch (CU-Q..CU-V)
landed on top of it — plus 6 untracked campaign-artifact paths (`.hermes/`, `docs/assessment/`,
`docs/ideation/`, `docs/implementation/`, `docs/prioritization/`, `docs/stewardship/`).
`python -m pytest` → 184 passed (selection-time). Every unit's anchor grep re-verified green-open
below, and the batch reproducers re-run reproducing **at stewardship time** (21/22 corpus; the
eight batch-target probes all reproduce: R1×4, R2, R3, R5, R6, N2/N2b/N3, P7).

```json
{
  "stewardship_request": {
    "title": "hermes-curator-evolver reproduced-P2 discharge batch (cycle 5): classifier truth table, warm-writer storage topology + all-tables schema readiness, mode-preserving atomic writes, trusted-order backfill, systemd schedule validation, hygiene riders (F821/version/README/clamp-warning)",
    "summary": "Six dependency-light, independently verifiable packets that together discharge every defect the pass-5 assessment reproduced on this tree (six of the nine open B-items: B19, B20, B21, B22, B17, B9). Theme: the evidence signal must be classified truthfully (CU-W: looks_like_error at candidates.py:242 misclassifies both directions - success shapes '0 failed, 12 passed'/'success: no tests failed' stored as errors, structured failures '{\"returncode\":1}'/'{\"code\":1}'/'{\"ok\":false}' missed - R1 x4 reproduced live; error_events is append-only history so every misclassified day is permanent and both auto-evolve thresholds and future U24/U47 read that column), stored without stalls or torn state (CU-X: storage.py:237 opens a fresh sqlite connection per record_* call, so a held lock burns 3x5s retries -> ~15.75s worst-case hook stall, R5 reproduced live; storage.py:265 _schema_ready probes only tool_events so an interrupted first init never heals, R6 reproduced live; fix pattern is upstream-merged #101191 single-flight warm writer + #101202 errno taxonomy), applied without destroying file identity (CU-Y: guarded_apply.py:41 atomic helper re-creates files at process umask - 0o640 -> 0o664 through apply AND rollback, R2 reproduced live - and :458-472 safety snapshots use plain write_bytes, R3 reproduced live, undermining the cycle-4 U35 design), and the two oldest perennials close (CU-Z: backfill.py:149/:175 take an arbitrary storage-order subset under --limit and read full history for a 1-in-window import, N2/N2b/N3 reproduced live for the third consecutive assessment; CU-AA: a newline-bearing --schedule survives auto_evolve.py:190-201 quoting verbatim into the systemd unit at :1394 and bootstrap then enables+starts it, P7 reproduced live - the only command-injection-class defect on the board, selected in cycle 4 and never landed). CU-AB rides the roadmap's own sequencing: cli.py:466 uses Any without import (F821, latent NameError for get_type_hints consumers), version drifted 0.8.0 (hermes_curator_evolver/__init__.py:11) vs 0.10.0 (plugin.yaml:2) since cycle 1, README teaches a rollback form that refuses (Q4), and _bounded at auto_evolve.py:168 silently rewrites out-of-range values (Q8). All units mechanically reproduced at stewardship time on this exact tree; the batch flips exactly R1/R2/R3/R5/R6/N2/N2b/N3/P7/N7 green while P5/P6/P8/P9/P10/N6/C1 stay open for later batches (pre-shaped next batch: U18+U19+U20+U26). Only two user-visible behavior changes, both alignment-with-documentation: backfill imports newest-first (help text already promises 'newest'), garbage schedules rejected (systemd's own grammar). No new dependencies, no model calls, no feature additions; remediation precedes extension per KTD21.",
    "repository_candidate": {
      "name": "hermes-curator-evolver",
      "path": "/work/projects/hermes-curator-evolver",
      "remote": "git@github.com:codeo1io/hermes-curator-evolver.git (fork, push target) / https://github.com/pingchesu/hermes-curator-evolver.git (origin, upstream)",
      "remote_role": "push target is the 'fork' remote (codeo1io); 'origin' (pingchesu) is upstream and must never be pushed to, per the roadmap's Repository remote section",
      "branch": "main",
      "head": "45328db",
      "committed_tree": [".github", ".gitignore", "CONTRIBUTING.md", "LICENSE", "README.md", "__init__.py", "docs", "examples", "hermes_curator_evolver", "plugin.yaml", "pyproject.toml", "tests"],
      "dirty_state_to_preserve": "13 modified tracked files = the uncommitted cycle-1 remediation AND the cycle-4 batch CU-Q..CU-V landed on top of it (hermes_curator_evolver/{auto_evolve,backfill,candidates,cli,guarded_apply,hooks,storage}.py + tests/{test_auto_evolve,test_backfill_sessions,test_candidates,test_cli,test_guarded_apply,test_storage}.py) - NOT part of this request's units; per KTD21 both land first via their own commit gate before cycle-5 work builds on them. Untracked campaign artifacts: .hermes/, docs/assessment/, docs/ideation/, docs/implementation/, docs/prioritization/, docs/stewardship/",
      "rationale": "All six packets are this repository's own Python package and its tests; every defect is reproducible inside this tree with scratch temp dirs and no network or cross-repository input. The work must build on the current dirty tree (two uncommitted batches), which is why its preservation is stated as an inventory fact rather than folded into any unit."
    },
    "change_units": [
      {
        "id": "CU-W",
        "packet": "U43",
        "title": "Error-classifier truth table (B19/Q1; reopens and completes U28)",
        "surfaces": [
          "hermes_curator_evolver/candidates.py:242 looks_like_error + its shape logic at :97-100,:210-241 (structured-first shape table: returncode/exit_code/code nonzero->error, zero->not; ok/success/status/error/exception honored; keyword fallback matches only failure-bearing phrases and never '0 failed, 12 passed'/'success: no tests failed'/empty-stderr-with-stdout/'exit code 0')",
          "hermes_curator_evolver/storage.py:14,:338 (sole consumer; keep the import+is_error column, delegate wholly - no second classifier)",
          "tests/test_candidates.py + tests/test_storage.py (R1's four shapes become a permanent corpus test; a stored-DB fixture with keyword-bearing success strings must yield zero poisoned error_events rows)"
        ],
        "must_land_before": [],
        "rationale": "Board top (24/24) and third consecutive cycle a classifier defect ranks first: success shapes stored as errors and structured failure shapes missed - reproduced live at stewardship time (R1 x4). error_events is append-only history; every day unfixed is permanently misclassified, and auto-evolve thresholds, U24 cohorts, and U47's truncation/invocation correlation all read the is_error column. Anchor re-verified: def looks_like_error at candidates.py:242; storage.py:14 import, :338 consumer."
      },
      {
        "id": "CU-X",
        "packet": "U45 + U46",
        "title": "EvidenceStore warm-writer topology + errno split, and all-tables schema readiness (B21/Q6 + B22/Q7)",
        "surfaces": [
          "hermes_curator_evolver/storage.py:237-241 connect() (one cached connection per resolved DB path per process - Path.resolve() key, single-flight open, atexit close - replacing connect-per-record_*-call)",
          "hermes_curator_evolver/storage.py:78,:244-263 (_BUSY_TIMEOUT_MS/_write_with_retry: split contention (sqlite busy/locked) from environment errors - fail fast with the real errno, no timeout burn; R5's 3x5s stall must collapse to one busy_timeout)",
          "hermes_curator_evolver/storage.py:265-277 _schema_ready (probe tool_events AND turn_events AND session_events; one table-list constant consumed by init and readiness; interrupted first init heals on next open)",
          "hermes_curator_evolver/hooks.py:13-14 (per-call connection handling rides the cached-connection path; no swallowing of environment errnos)",
          "tests/test_storage.py (new: contention fixture bounds worst-case latency; cold-burst test asserts one open per path; interrupted-init fixture heals; environment-error path returns fast with errno recorded)"
        ],
        "must_land_before": [],
        "rationale": "Two packets, one file, one root-cause family (per-call connection topology), which is why the selection folds them: R5 (~15.75s worst-case hook stall) and R6 (tool_events-only probe) both reproduced live at stewardship time. De-risked by the upstream-merged #101191 recipe (single-flight warm writer) plus the #101202 errno-taxonomy recipe (unmerged, cited as recipe-not-law). Anchor re-verified: connect at :237, _write_with_retry at :244, _schema_ready at :265, _BUSY_TIMEOUT_MS at :78."
      },
      {
        "id": "CU-Y",
        "packet": "U44",
        "title": "Mode-preserving atomic writes and atomic safety snapshots (B20/Q3+Q5)",
        "surfaces": [
          "hermes_curator_evolver/guarded_apply.py:41-67 _atomic_write_bytes/_atomic_write_text/_copy_file_atomic (copy the target's existing mode - or an explicit mode arg - onto the temp file before rename; apply, rollback, and copy paths all stop re-creating files at process umask; R2's 0o640->0o664 must flip)",
          "hermes_curator_evolver/guarded_apply.py:458-472 _snapshot_for_safety (switch dest.write_bytes at :471 to the atomic helper with fsync; a mid-snapshot interruption leaves the full snapshot or nothing)",
          "tests/test_guarded_apply.py (R2 mode reproducer as regression for apply AND rollback; torn-snapshot interruption test)"
        ],
        "must_land_before": [],
        "rationale": "Residual of the cycle-4 batch's own write path: mode loss breaks exactly the group-readable shared skill trees the plugin curates (both apply and rollback, R2 reproduced live), and the non-atomic safety snapshot undermines U35's recoverable-copy design (R3 reproduced live). Sole owner of guarded_apply.py this cycle - U18's loop-boundary remainder is explicitly held for the next batch to avoid double-opening the file. Anchor re-verified: _atomic_write_bytes :41, _snapshot_for_safety :458 with write_bytes at :471."
      },
      {
        "id": "CU-Z",
        "packet": "U36",
        "title": "Trusted-order backfill: newest-first paging, cutoff before fetch, bounded bootstrap (B17/N2+N2b+N3, +N7 summary)",
        "surfaces": [
          "hermes_curator_evolver/backfill.py:149-152 _iter_session_files (files[:limit] takes an arbitrary order - order newest-first before the limit)",
          "hermes_curator_evolver/backfill.py:175-209 _iter_state_sessions (page in trusted order - assert monotonicity or collect-sort fallback; apply the days cutoff BEFORE transcript fetch so a 1-in-window import stops fetching all pages; N2 'inspected=[s1,s0]' with newest s2 unseen must flip)",
          "hermes_curator_evolver/backfill.py:348,:377 + hermes_curator_evolver/cli.py (bootstrap/import result summary: sessions_failed must be visible in the human summary - N7 rides here)",
          "tests/test_backfill_sessions.py (N2/N2b/N3 reproducers as regressions; ordering assertion against a shuffled fixture)"
        ],
        "must_land_before": [],
        "rationale": "Third consecutive assessment reproducing byte-identical defects: --limit inspects a storage-order subset (newest session never read), the days cutoff is applied after full-history fetch, and bootstrap passes limit=None. Held in cycle 4 only for batch size; overdue. U19 (identity/dedup-key unification) shares this file and is deliberately NOT in this batch - it anchors the next one. Anchor re-verified: files[:limit] at :151-152, page_size/search_sessions paging at :187-195."
      },
      {
        "id": "CU-AA",
        "packet": "U17",
        "title": "Scheduler unit hardening: systemd schedule validation and escaping (B9/P7)",
        "surfaces": [
          "hermes_curator_evolver/auto_evolve.py:190-201 _systemd_quote/_quote_systemd_arg (a newline currently survives quoting verbatim)",
          "hermes_curator_evolver/auto_evolve.py:1394 (OnCalendar={schedule} written verbatim into the unit at :1262 service_path, which bootstrap then enables+starts - validate the schedule against a systemd-calendar subset and reject newlines/directive characters with an actionable error)",
          "hermes_curator_evolver/cli.py:345,:402 (--schedule help: state the accepted grammar and the rejection)",
          "tests/test_auto_evolve.py (P7 reproducer as regression: 'daily\\nExecStartPost=...' rejected; % escaping in ExecStart args)"
        ],
        "must_land_before": [],
        "rationale": "The only command-injection-class defect left on the board, selected in cycle 4 and never landed - demoting it again would make selection noise. P7 reproduced verbatim at stewardship time. launchd path (darwin, :1176-1179) already normalizes to canonical cadences; systemd is the open flank. Anchor re-verified: quoting at :190-201, unit write at :1262, OnCalendar at :1394, CLI help at :345/:402."
      },
      {
        "id": "CU-AB",
        "packet": "U7-riders",
        "title": "Hygiene riders: Q2 F821, U7b version single-sourcing, Q4 README rollback docs, Q8 clamp warning",
        "surfaces": [
          "hermes_curator_evolver/cli.py:466 (dict[str, Any] in _explicit_int's signature with no typing.Any import - add the import; ruff F821 gone, get_type_hints consumers survive)",
          "hermes_curator_evolver/__init__.py:11 + plugin.yaml:2 (version single-sourcing: one source of truth, equality test across __init__/plugin.yaml/bundled SKILL.md)",
          "README.md (rollback section: document the working form incl. --skills-dir and --allow-any-target, and auto_run's --max-reference-files - Q4's documented form currently refuses)",
          "hermes_curator_evolver/auto_evolve.py:168 _bounded (+ call sites :843-846) (clamp emits a warning naming old->new value - Q8's silent rewrites become observable)"
        ],
        "must_land_before": [],
        "rationale": "The roadmap's cycle-5 sequencing line routes these residuals onto the next remediation batch - this one. All are sub-unit riders: one import line, one constant unification, one docs section, one warning line. Anchor re-verified: Any at :466, '0.8.0' at __init__.py:11, '0.10.0' at plugin.yaml:2, _bounded at auto_evolve.py:168."
      }
    ],
    "must_remain_separate": [
      ["CU-W (candidates.py:242 classifier truth table) - U43", "CU-X (storage.py:237/:244/:265 connection+schema) - U45/U46"],
      ["CU-X (storage.py connection topology) - U45/U46", "CU-AB (cli.py:466 import + __init__.py:11/plugin.yaml:2 version) - U7-riders"],
      ["CU-Y (guarded_apply.py:41-67/:458-472 write path) - U44", "CU-W (candidates.py:242 classifier) - U43"],
      ["CU-Z (backfill.py:149/:175 ordering+cutoff) - U36", "CU-AA (auto_evolve.py:190-201/:1394 schedule validation) - U17"],
      ["CU-AA (auto_evolve.py systemd validation) - U17", "CU-AB (auto_evolve.py:168 _bounded warning) - U7-riders"],
      ["the uncommitted cycle-1 remediation + cycle-4 batch (13 modified tracked files)", "every CU-W..CU-AB unit of this request"],
      ["held next-batch units (U18 guarded_apply remainder, U19 backfill identity/dedup - shares CU-Z's file, U20 hygiene incl. N6, U26) and KTD21-gated extensions (U38-U42, U47-U50)", "every CU-W..CU-AB unit of this request"],
      ["CU-W's tests/test_storage.py additions (corpus + stored-DB fixture)", "CU-X's tests/test_storage.py additions (concurrency/schema tests)"],
      ["CU-AA's tests/test_auto_evolve.py additions (unit-generation regressions)", "CU-AB's tests touching auto_evolve.py:168 clamp warnings"]
    ]
  }
}
```

## Splitting notes (why these boundaries)

- **Same file ≠ same concern.** `storage.py` carries CU-W's consumer line (:338, unchanged
  semantics — the truth table lives in `candidates.py`), CU-X's connection/schema rework,
  and CU-AB has no storage surface: the CU-W/CU-X split is exactly the cycle-4 CU-R/CU-S/CU-V
  precedent. `auto_evolve.py` carries CU-AA (systemd, :190-201/:1394) and CU-AB's one-line
  `_bounded` warning (:168) — disjoint functions, separate hunks, separate commits. `cli.py`
  carries CU-Z's summary output, CU-AA's help text, and CU-AB's import line — three disjoint
  hunks. `tests/test_storage.py` and `tests/test_auto_evolve.py` are each touched by two units
  in separate test functions.
- **CU-Y is this cycle's sole `guarded_apply.py` owner** (the standing precedent): U18's
  loop-boundary remainder stays out so the most destructive file is opened once.
- **CU-Z owns `backfill.py` alone**: U19 shares the file and is deliberately next-batch.
- **The dirty tree is context, not a unit.** Both uncommitted batches (cycle-1 remediation +
  cycle-4 CU-Q..CU-V) are the substrate these six build on; per KTD21 they commit first via
  their own gate and no CU-W..CU-AB change may fold into those commits.
- **No intra-batch hard dependencies** (dep-freedom 5 across the scoring table); the soft
  coordinations are the shared test files (separate functions) and CU-X's cached connection
  being what CU-W's stored-DB fixture runs through — which is why CU-W's fixture tests are
  listed under CU-W, not CU-X.

## Verification contract for the implement phase

Mechanical gates exist before any review: re-run
`/home/agent/.hermes/conductor-runs/2cc5b112c9694bfaa4a47645f139983a-assess/repro-pass5.py` —
this batch flips exactly R1 (all four shapes), R2, R3, R5, R6, N2, N2b, N3, P7, N7 green;
P5/P6, P8, P9, P10, N6, C1 must remain reproducing (they belong to the next batch).
Targeted pytest per changed surface (`tests/test_candidates.py`, `tests/test_storage.py`,
`tests/test_guarded_apply.py`, `tests/test_backfill_sessions.py`, `tests/test_auto_evolve.py`,
`tests/test_cli.py`); full suite green above the 184 baseline; `ruff check .` shows the F821
gone and no count increase; version-equality test across `__init__.py`/`plugin.yaml`/bundled
SKILL.md. Roadmap Acceptance governs: feature branch off main, targeted tests as the gate, push
to `fork` only, both prior batches committed first (KTD21). None of that is this phase's to do.

*Read-only request; no code changed, nothing committed or pushed.*
