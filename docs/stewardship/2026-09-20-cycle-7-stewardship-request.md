---
date: 2026-09-20
topic: hermes-curator-evolver-cycle-7-stewardship-request
mode: stewardship-handoff
run: 78a174fbdec14ee3844ff327a59cef78
phase: stewardship
attempt: 0fedd069851b495898d3defc9adb79a3
skill: ce-stewardship handoff (no ce-* router or skill exists on this host — registry exposes only agent-reach — the standing disclosed deviation since pass 2; handoff structure follows the cycle-4/5/6 requests in this directory)
tier: 1 - the request is a contract draft; Conductor owns topology, overlap detection, and dirty-state preservation
---

# Cycle-7 stewardship request — the format-and-count truth batch

Authoritative JSON form lives in the phase_result (`stewardship_request` field) at the delegate
spool for attempt `0fedd069851b495898d3defc9adb79a3`. This document is the human-readable
companion with rationale; where they differ, the JSON governs.

## What is requested (selected in the prioritize phase, docs/prioritization/2026-09-20-cycle-7-batch.md)

One coherent code batch, two change units + one doc rider, all on
`/work/projects/hermes-curator-evolver` (canonical) mirrored in this conductor worktree:

- **CU-AF — U67, classifier format-matrix completeness.** Make `looks_like_error` truthful
  about grouped numbers (`"1,000 failed"` is a failure), comma/unspaced clause joins
  (`"0 failed, deploy failed: ..."` is a failure), and the full HTTP success set
  (203/206/301/304 are not errors); make the human-format CLI summary print the truthful
  counters it already computes for JSON (`metadata_scan_truncated`, sessions skipped).
  N-probes: N1/N1b/N1ctl-control/N3/N3b/N4/N5 from pass 7.
- **CU-AG — U68, attribution burst counting.** `skills[].event_count` must count same-second,
  same-task hook events individually (today DISTINCT `(session_id, task_id, skill_name,
  created_at)` collapses a 3-event burst to 1 and `min_evidence=2` starves the skill);
  `event_rows` stays disclosed beside it; backfill-path counting (unique task_ids) unchanged.
  N-probe: N2/N2ctl-control.
- **Rider — U5, confirm-and-close (docs-only).** Cap constants are single-sourced as of
  `a76962c` (`auto_evolve.py:53` `_MAX_SKILL_CONTENT_CHARS`, `:55`
  `_AUTO_LOADED_SKILL_MAX_CHARS`, consumed via keyword defaults at :116/:648/:723/:1007/
  :1116/:1201 — the cycle-2 "confirm single-sourcing" residual). Expected outcome: a
  confirmation note in the batch docs and U5's status moved to closed. If divergence is found,
  it becomes a third small CU — not folded into CU-AF/AG.

## Surfaces (file:line at a76962c, the branch base)

CU-AF: `hermes_curator_evolver/candidates.py:109` (`_FAILURE_COUNT_PATTERN`), `:116`
(`_CLAUSE_SPLIT_PATTERN`), `:135` (`_HTTP_SUCCESS_CODES`), `:337-343` (truth evaluation);
`hermes_curator_evolver/cli.py:885-905` (human summary disclosure); `tests/test_candidates.py`
(corpus v3 + format matrix), `tests/test_candidates_cli.py` (disclosure tests).
CU-AG: `hermes_curator_evolver/storage.py:652-675` (aggregation query, DISTINCT at :661);
`hermes_curator_evolver/auto_evolve.py:808` (`_eligible_skill_rows`), `:864` (caller),
`:97` (`min_evidence` default — read/verify, change only if the fix demands); tests in
`tests/test_storage.py` (summary/event_count), `tests/test_auto_evolve.py` (eligibility +
burst/control fixtures).
Rider: `hermes_curator_evolver/auto_evolve.py:53,55` (read-only verification).

## must_remain_separate (rationale)

1. **CU-AF vs CU-AG** — disjoint defect classes (text classification vs SQL counting), disjoint
   files, independently reviewable and revertable; a revert of either must not touch the other.
2. **CU-AF's classifier patterns vs its CLI-disclosure slice** — separable if the steward
   prefers finer units: `candidates.py` truth vs `cli.py` disclosure share only the theme.
   (Cycle-6 precedent kept U51 as one CU including test/docstring reconciliation — either split
   is acceptable; the patterns fix and its format-matrix tests must land together, never split.)
3. **The rider (U5) vs everything** — doc-only unless divergence surfaces; must not be folded
   into a code CU.
4. **This batch vs U70/U71/U56 (excluded near-misses)** — hard exclusion: U71 edits
   `storage.py` connection lifecycle (same file as CU-AG — taints the surgical diff), U56's
   ruff gate + 48 auto-fixables touch every file this batch opens, U70 opens `backfill.py`
   (different theme; only enters via the documented pull-in criteria after CU-AF/AG go green).
5. **Code vs docs** — this run's four uncommitted docs (roadmap append, pass-7 assessment,
   cycle-7 research, cycle-7 batch selection) plus this request must ride separately from the
   code units (the cycle-5/6 fix-then-docs commit shape), so per-CU diffs stay reviewable and
   the dirty state Conductor must preserve is explicit: 1 modified (roadmap) + 4 untracked
   (assessment, ideation, prioritization, this file), zero code changes since `a76962c`.

## What the batch must NOT do

- No behavior change beyond: the two truth corrections, the counting fix, CLI disclosure
  lines, and their tests. No refactor rides along (ruff auto-fixes belong to U56, next batch).
- No new dependency, no CI change, no push/PR (later phases), no `repro-pass7.py` deletion —
  it lifts into `tests/` as corpus v3 and the original stays as the assessment's evidence.
- Stay-green controls are contract, not advice: `"2,048 failed"` stays True (N1ctl);
  backfill-shaped events keep `event_count == event_rows` (N2ctl); B-class honest-store
  behaviors stay green; full suite at ≥ 287 + new tests; ruff ≤ 63.
