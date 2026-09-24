---
date: 2026-09-22
topic: hermes-curator-evolver-cycle-3-stewardship-request
mode: repo-grounded
run: 3ed5d14a80a245f3bb71735d577be08a
phase: stewardship
attempt: 88ad3d72c0bf44f9898fb9c4c240ea79
skill: ce-plan (batch-to-contract translation; no topology choices made here per fleet rule — branches/worktrees are Conductor's)
note: the authoritative artifact is the phase_result JSON's stewardship_request object (delegate spool attempt 88ad3d72); this document is the human-readable companion.
---

# Stewardship request — cycle 3, run 3ed5d14a (batch U82 + U83)

> **Integration note (2026-09-24, roadmap KTD46):** per KTD41 the run's numbering was void at integration — this contract's U82 is main-chain **U93** and its U83 is **U94** (implemented and merged; see the roadmap "Integration fold 2026-09-24"). Code line cites are pre-cycle-7-era addresses.

## Title

Secondary-surface hardening parity: review-queue busy-retry (U82) + restore-drill manifest-path validation (U83)

## Summary

The selected cycle-3 batch (docs/prioritization/2026-09-22-cycle-3-batch.md) closes the two parity gaps where secondary surfaces lack disciplines the primary surfaces already have: (U82) `review_queue.py`'s `_connect` opens SQLite with no busy_timeout/journal hardening — the exact class U45 closed for the evidence store (storage.py:66-97 layer + `_is_busy_error` :142); (U83) `restore_drill.py` parses manifests unguarded (json.loads :70/:180) and copies `backup_path`→`target_path` (:185-205) with no under-skills-dir validation, while rollback already refuses tampered manifests and validates paths via `guarded_apply._resolve_within` (:132-141). Both units are verified live defects in this tree, their files have ZERO origin/main commits since merge-base a76962ce (merge-free carry-forward), and each is completable end-to-end with tests in one implement window. Acceptance evidence expectations are in the prioritization artifact: concurrent-holder test with WIDE margin (not U45's 15.0/15.11s tightness); tampered-manifest refusal identical to rollback's + corrupt-JSON clean error; pytest 287 → 287+n; venv ruff flat at 12; zero new PATH-ruff (0.16.7) findings.

## Repositories

- `/work/projects/hermes-curator-evolver` (campaign home; origin = codeo1io/hermes-curator-evolver, upstream push-disabled)
- `/home/agent/.hermes/conductor-worktrees/hermes-curator-evolver-a47fdea793/run-3ed5d14a80a2-3ed5d14a` (this run's worktree — the pre-cycle-7 base, 6 commits behind origin/main, where the batch executes)

## Surfaces (file:line, current-tree addresses)

Code (U82): `hermes_curator_evolver/review_queue.py:81-107` (`_connect` :87-91 raw `sqlite3.connect`, no busy_timeout; call sites :81, :107+)
Code (U82 reuse-only): `hermes_curator_evolver/storage.py:66-98` (WAL/busy layer, `_is_busy_error` :142 — import/reuse; see separation hint #3)
Code (U83): `hermes_curator_evolver/restore_drill.py:70` and `:180` (unguarded `json.loads`), `:185-205` (`backup_path`/`target_path` copy, no under-skills-dir check)
Code (U83 reuse-only): `hermes_curator_evolver/guarded_apply.py:132-141` (`_resolve_within` — the U3/N1 validator to route through)
Tests (new): `tests/test_review_queue.py` (+concurrent-holder, wide margin), `tests/test_restore_drill.py` (+tampered-manifest refusal, +corrupt-JSON clean error)

## Must remain separate

1. `U82 review_queue.py` vs `U83 restore_drill.py` — disjoint files, no shared behavior; land as two change units (one batch) so each is independently reviewable/revertable; the only acceptable shared element is a test helper, not production code.
2. Run bookkeeping vs code — the worktree's current dirty state (`.hermes/plans/autonomy-prop_8c5390ffe26640fa.md` modified; `docs/ideation/2026-09-22-cycle-3-extension-research.md` and `docs/prioritization/2026-09-22-cycle-3-batch.md` untracked) is run documentation, NOT implementation; preserve it and do not fold it into the code change units.
3. `review_queue.py` behavioral change vs any `storage.py` helper extraction — if U82 chooses to extract a shared connection-hardening helper out of storage.py instead of mirroring constants, that extraction is its own tiny change unit touching a file main HAS modified (+17/−4) — keep it isolated so the merge-free property of the queue/drill diffs stays auditable.
4. This batch vs U77/U78 (and the pre-U63 board) — those belong to origin/main's line (candidates.py/backfill.py/cli.py rewritten there; defects are main's open cycle-8 review findings); must NOT be implemented in this worktree's batch.

## Dirty state to preserve

`git status --short` at request time: ` M .hermes/plans/autonomy-prop_8c5390ffe26640fa.md` (roadmap append, post-image sha256 c3dac983a93777da6d34c56bf14d4c370609f80e7b3bd9fd0c9bcfb6ea3ddd75, 733 lines), `?? docs/ideation/2026-09-22-cycle-3-extension-research.md`, `?? docs/prioritization/2026-09-22-cycle-3-batch.md`. Baselines for the implement window: pytest 287 passed; venv ruff 12 (binary-skew caveat vs PATH 0.16.7 — compare like-for-like only).
