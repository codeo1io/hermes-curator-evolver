---
date: 2026-09-22
topic: hermes-curator-evolver-cycle-3-batch-selection
mode: repo-grounded
run: 3ed5d14a80a245f3bb71735d577be08a
phase: prioritize
attempt: 1daa24af09274bc79cdda20cf018a988
skill: ce-plan (narrowest installed match for sequencing/batch decision; no ce-prioritize exists in this host's roster — this artifact inherits the fleet's established five-axis batch-selection format from docs/prioritization/2026-09-02-cycle-6-batch.md)
tier: 1 - selection is a two-way door; a wrong batch costs a cycle, not the repository
disclosure: no subagent primitive in this harness; grounding and scoring ran in-thread, one context, no panel. The decisive new evidence this cycle is git-topological, not judgment: origin/main commit counts per file since merge-base a76962ce (measured below), which turns merge-risk from opinion into count.
---

# Cycle 3 implementation batch selection (run 3ed5d14a, pre-cycle-7 worktree)

> **Integration note (2026-09-24, roadmap KTD46):** this selection ran on the run's pre-cycle-7 worktree under its own — now void, per KTD41 — numbering: U77/U78 were later superseded by main's U79 and U76/U78; the survivors renumbered U79→U90, U80→U91, U81→U92, U82→U93, U83→U94, and the proposed KTD39 became main's KTD40. The batch that shipped is U93+U94. The merge-collision table below is era-accurate for 2026-09-22; main has since integrated cycle 9.

## The board and the constraint that dominates it

Unresolved units visible in THIS worktree's roadmap: cycle-1 residuals (U5/U6), unlanded cycle-2..5 units (U8-U14, U18-U26, U29-U31, U33/U34, U38-U42, U47-U50), cycle-6 extensions (U51-U62, partially sequenced by the cycle-6 outcome), plus this run's new U77-U83 and KTD39-proposed.

The dominating constraint: **this worktree is 6 commits behind origin/main (merge-base a76962ce), and those 6 commits ARE main's cycles 7-8** — they executed the pre-U63 board's sequencing (U63-U72) and the cycle-8 packet (U73/U74/U76). Any unit this run implements that main already implemented or has in-flight gets discarded or hand-reconciled at merge. Measured per-file divergence (git log/diff merge-base..origin/main):

| file | main commits | main diff | collision class |
|---|---|---|---|
| review_queue.py | **0** | none | free |
| restore_drill.py | **0** | none | free |
| backfill.py | 1 | +31/-4 | moderate |
| storage.py | 1 | +17/-4 | moderate |
| cli.py | 2 | +23/-0 | moderate (additive) |
| candidates.py | 2 | +154/-52 | heavy rewrite |
| auto_evolve.py | 1 | +165/-155 | heavy rewrite |

## Gates (override totals)

1. **Non-duplication gate** — the unit must not be already implemented on origin/main nor an open finding already registered on main's board awaiting main's cycle 9. Kills: the entire pre-U63 board for THIS worktree (executed by main's cycles 7-8); U77/U78 here (identical defects are main's open cycle-8 review P3/P4s — the correct home is main's tree where the code has moved); U56/U75 (main's declared cycle-9 opener; U56 additionally has a baseline-mismatch trap here — venv ruff 12 vs main's pinned-63, binary-skew).
2. **Merge-conflict budget** — prefer files with zero main-side commits; accept moderate only with a re-anchor plan. review_queue.py/restore_drill.py = 0/0.
3. **Completable end-to-end** — one implement window, tests + lint-flat discipline (new code adds zero lint counts), self-verifiable in this worktree without CI (CI prohibited and self-hosted runner red-by-flake).

## Five-axis scores (1-5; Impact=value if done; Delay risk=cost of waiting a cycle; Effort=5 cheapest; Dep-freedom=5 ungated; Strategic=leverage on later work)

| unit | Imp | Delay | Eff | Dep | Strat | Total | gate outcome |
|---|---|---|---|---|---|---|---|
| U82 review-queue busy-retry parity | 3 | 3 | 5 | 5 | 4 | 20 | **SELECTED** (free merge surface) |
| U83 restore-drill manifest-path parity | 3 | 4 | 5 | 5 | 3 | 20 | **SELECTED** (free merge surface) |
| U79 MRU early-terminate probing | 4 | 3 | 3 | 4 | 4 | 18 | first alternate (moderate surface: backfill +31/-4 on main; re-anchor cost disclosed) |
| U78 legacy containment + output parity | 4 | 3 | 3 | 5 | 3 | 18 | deferred to main's line (gate 1: main's open P3/P4s; gate 2: backfill/cli churn) |
| U80 compression-aware linking | 4 | 3 | 2 | 4 | 4 | 17 | deferred (schema migration across diverged branches; storage +17/-4 on main) |
| U77 classifier numeric hardening | 5 | 4 | 4 | 5 | 4 | 22 | **gated out here** — highest total on the board, correct home is main's tree (candidates.py +154/-52 rewrite; defect already on main's cycle-9 board) |
| U81 host-budget caps | 3 | 2 | 3 | 2 | 3 | 13 | deferred (auto_evolve +165/-155 on main; host verdict surface still moving on weekly releases) |
| KTD39 U62 single-gating | n/a | — | — | — | — | — | decision, not implementation — routed to stewardship with the 2026-09-22 evidence already recorded |
| pre-U63 standing board | — | — | — | — | — | — | gated out for this worktree (gate 1: executed by main's cycles 7-8); verify statuses on merge, do not re-implement |

## Selected batch: U82 + U83 — "secondary-surface hardening parity"

**Theme:** the two surfaces that DIDN'T get the disciplines the primary surfaces already have. The evidence store got busy-retry/WAL-layer hardening (U45, storage.py:66-97); the review queue's `_connect` (review_queue.py:87-91) still does raw `sqlite3.connect` with no busy_timeout — the exact class U45 closed. Rollback got manifest path validation and tamper refusal (U3/N1); the restore drill still `json.loads` manifests unguarded (restore_drill.py:70, :180) and copies `backup_path`/`target_path` (:205) with no under-skills-dir validation — the drill (the operator's safety net) is weaker than the machinery it rehearses.

**Why this batch wins despite modest totals:** it is the only pair on the board that is simultaneously (a) real current-tree defects verified this run, (b) untouched by origin/main — the diff carries forward on any merge with zero reconciliation, and (c) small enough to complete end-to-end with tests in one implement window (U82: connection-layer mirror, no schema migration; U83: route drill manifests through the validated loader + tampered-manifest test). Impact 3+3 is honest, not padded: today the plugin is effectively single-writer, so U82's crash window is latent; U83's tamper window requires a hostile/corrupt manifest. But both are the asymmetry class this roadmap has consistently closed (U45, U3/N1 precedents), and the shared hardening helper U82 produces is the same seam U79/U80 will need later (strategic 4).

**First alternate: U79** (MRU early-terminate; impact 4 — the only selected-class perf win that main lacks). Pull-in criteria: U82 AND U83 land green with lint flat AND the implement window has substantive time left AND the implementer accepts the disclosed re-anchor cost (main's backfill.py moved +31/-4; the state-db probe loop must re-anchor on merge). Otherwise U79 waits for main's line next cycle.

**Explicit deferrals with rationale:**
- U77/U78 → main's cycle-9 line. They are the highest-severity OPEN defects on main's own review board (2026-09-21, attempt b52ac9e3) and the fixing code (candidates.py, backfill.py, cli.py renderers) has already moved there. Fixing them in this 6-behind base produces a discarded diff; the roadmap block already instructs drop-if-main-unitizes-first.
- U80 → next candidate after merge (schema change; do it once, on the post-merge schema).
- U81 → post-merge + host-surface settle (weekly release cadence still moving the budget-verdict surface).
- U56/U75 and the pre-U63 board → main's line entirely.

## Batch acceptance evidence (what the implement phase must show)

- U82: a concurrent-holder test bounding queue wait (wide margin — do NOT inherit U45's marginal 15.0s-vs-15.11s tightness) + connection hardening shared with/reusing storage.py's helper; no schema migration; review_queue.py-only diff.
- U83: tampered-manifest drill test (refusal identical to rollback's) + corrupt-manifest JSON clean error + no path escape above the skills dir; restore_drill.py(+loader)-scoped diff.
- Both: pytest count 287 → 287+n green; venv ruff stays 12 (or documents binary-skew); no new lint from PATH 0.16.7 rule set; corpus harness unaffected (43/43 on main; N/A count on this base — probe corpus landed with cycle 7).

## Grounding trail

- Current-state cites: review_queue.py:81-91 (`_connect`, raw connect, no busy_timeout); restore_drill.py:70/:180 (unguarded json.loads), :185-205 (backup/target copy, no under-skills-dir check).
- Divergence measurement: `MB=$(git merge-base HEAD origin/main)` → a76962ce09294e04bd6a4bfa08523066a72e7a9b; per-file `git log --oneline $MB..origin/main -- <f> | wc -l` and `git diff --numstat $MB..origin/main -- <f>` (table above).
- Main's cycle-8 state and cycle-9 opener (U75+U56): origin/main roadmap lines 1224-1275 (cycle-8 status block); review P3/P4 findings from attempt b52ac9e3 spool record.
- Inputs: this run's assess (579cf498), research (411a6de9, docs/ideation/2026-09-22-cycle-3-extension-research.md), roadmap append (453ecae9, block at line 670, units U77-U83/KTD39).
