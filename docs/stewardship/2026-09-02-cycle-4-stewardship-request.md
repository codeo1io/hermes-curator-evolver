---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-4-stewardship-request
run: 673d15323b9c4580a0e2ed84fa8625fc
phase: stewardship
attempt: f54a04bd758544009b750cd098b374b8
skill: ce-plan (change-request description; router has no stewardship skill - ce-handoff rejected as session continuity, ce-work/ce-worktree rejected as topology choice this phase must NOT make; same route and reasoning as the fleet's three prior stewardship phases for this repository)
upstream: docs/prioritization/2026-09-02-cycle-4-batch.md (selected batch U15 + U7a + U37 + U35 + U16 + U28)
---

# Stewardship request — cycle 4 write-path correctness batch

This document describes the selected maintenance batch for the conductor to steward. It
deliberately does **not** choose Git topology: no branch names, no worktree layout, no commit
sequencing. Those are the conductor's to plan after inventorying the repository, detecting
overlap, splitting unrelated concerns, and preserving dirty state.

Inventory re-checked live this session: `main` @ `45328db04c188dd4d8734e31c8b85f2d84f6358b`,
single worktree (`git worktree list` → this path only), remotes `origin` (pingchesu, upstream,
never push) and `fork` (codeo1io, push target per the roadmap's Repository remote rule), dirty
state = the same **11 tracked files** of the uncommitted cycle-1 remediation (833 insertions,
byte-identical since the assess pass) + 5 untracked campaign-artifact paths (`.hermes/`,
`docs/assessment/`, `docs/ideation/`, `docs/prioritization/`, `docs/stewardship/`).
`python -m pytest` → 174 passed. Every unit's anchor grep re-run green-open below, and the six
batch reproducers (N1, N4, N5, P1, P2, P4) re-run reproducing at stewardship time.

```json
{
  "stewardship_request": {
    "title": "hermes-curator-evolver write-path correctness batch (cycle 4): managed-block writer safety, storage lock resilience, NUL-escape-complete sanitization, rollback validation, numeric-flag contract, single error classifier",
    "summary": "Six dependency-light, independently verifiable packets over the freshly-landed, still-uncommitted cycle-1 remediation - the crash/deletion/corruption/drop/founding-NUL class, nothing else. Theme: an unattended run must never crash on its own managed block (CU-Q: pattern.sub at auto_evolve.py:386 still raises re.error 'invalid group reference 1' on any already-blocked skill - P1 reproduced live), never silently drop an evidence row under one concurrent writer (CU-R: storage.py:154 opens a bare sqlite3.connect with zero WAL/busy_timeout pragmas - P4 'database is locked' reproduced live), never let the founding NUL loop survive in any encoding (CU-S: _strip_nul_bytes at storage.py:71 handles the byte and the \\x00 literal but the \\u0000 escape still reaches the store - N5 reproduced live), never delete the file it just restored (CU-T: _rollback_support_files at guarded_apply.py:426 can be made to unlink the restored SKILL.md and the CLI-default overwrite case C2 is unfixed - N1 reproduced live), never prune what it just wrote (CU-U: keep=0 prunes the same-pass reference while help text documents 0 as disable - N4 reproduced live, and tests/test_auto_evolve.py:1106 codifies the bug), and never store success as failure (CU-V: _looks_like_error at storage.py:113 returns True for '3 passed, no errors found' - P2 reproduced live). All six were mechanically reproduced at stewardship time on this exact tree; the batch should flip exactly N1, N4, N5, P1, P2, P4 green while N2/N3/N6/P7/P10 stay open for later batches. No user-visible default changes, no new dependencies, no model calls, no feature additions; hardening precedes extension per KTD16.",
    "repository_candidate": {
      "name": "hermes-curator-evolver",
      "path": "/work/projects/hermes-curator-evolver",
      "remote": "git@github.com:codeo1io/hermes-curator-evolver.git (fork, push target) / https://github.com/pingchesu/hermes-curator-evolver.git (origin, upstream)",
      "remote_role": "push target is the 'fork' remote (codeo1io); 'origin' (pingchesu) is upstream and must never be pushed to, per the roadmap's Repository remote section",
      "branch": "main",
      "head": "45328db04c188dd4d8734e31c8b85f2d84f6358b",
      "committed_tree": [".github", ".gitignore", "CONTRIBUTING.md", "LICENSE", "README.md", "__init__.py", "docs", "examples", "hermes_curator_evolver", "plugin.yaml", "pyproject.toml", "tests"],
      "dirty_state_to_preserve": "11 tracked files modified - the uncommitted cycle-1 remediation (auto_evolve.py, backfill.py, candidates.py, cli.py, guarded_apply.py, storage.py, tests/test_auto_evolve.py, tests/test_backfill_sessions.py, tests/test_candidates.py, tests/test_guarded_apply.py, tests/test_storage.py; 833 insertions) - NOT part of this request's units; per KTD16 it lands first via its own commit gate. Untracked campaign artifacts: .hermes/, docs/assessment/, docs/ideation/, docs/prioritization/, docs/stewardship/",
      "rationale": "All six packets are this repository's own Python package and its tests; every defect is reproducible inside this tree with scratch temp dirs and no network or cross-repository input. The work must build on the current dirty tree (the cycle-1 remediation), which is why its preservation is stated as an inventory fact rather than folded into any unit."
    },
    "change_units": [
      {
        "id": "CU-Q",
        "packet": "U15",
        "title": "Managed-block writer replacement safety (B7/P1)",
        "surfaces": [
          "hermes_curator_evolver/auto_evolve.py:386 (pattern.sub(block, skill_text, count=1) - replacement template must be literal/lambda so \\1/\\g<...> in skill text cannot crash or inject)",
          "hermes_curator_evolver/auto_evolve.py:321,:401 (preview text persisted to references/*.md - neutralize group references there too)",
          "tests/test_auto_evolve.py (new: second-run managed-block corpus case - a skill that already carries a managed block with backreference-looking content must round-trip; separate test functions from CU-U's edits to the same file)"
        ],
        "must_land_before": [],
        "rationale": "Board top (24/24) for the third consecutive selection: the daily auto-run exits 1 with re.error on any skill that already has a managed block - reproduced live this session and at prioritization. Cheapest crash-class fix on the board. Anchor re-verified: pattern.sub at :386 count=1."
      },
      {
        "id": "CU-R",
        "packet": "U7a",
        "title": "Storage lock resilience: WAL + busy_timeout + bounded retry (B10/P4)",
        "surfaces": [
          "hermes_curator_evolver/storage.py:154-157 (connect(): sqlite3.connect(path, timeout=...) + PRAGMA journal_mode=WAL/busy_timeout/journal_size_limit, DELETE-mode fallback - port the upstream recipe slice from hermes_state.py:640-1200, research R7)",
          "hermes_curator_evolver/hooks.py:13-14 (per-call connection handling; stop swallowing OperationalError wholesale)",
          "tests/test_storage.py (new: concurrency test - a held write lock must not drop the hook event; P4 reproducer shape)"
        ],
        "must_land_before": [],
        "rationale": "Board top (24/24) alongside U15: one concurrent writer drops hook events wholesale after a 5.01s stall ('database is locked' reproduced live this session) - evidence is the product, silent loss is the worst failure mode. De-risked this cycle by R7 supplying the exact upstream recipe to port. Anchor re-verified: zero busy_timeout/journal_mode occurrences in storage.py; bare connect at :154."
      },
      {
        "id": "CU-S",
        "packet": "U37",
        "title": "NUL-escape-complete sanitization (B18/N5)",
        "surfaces": [
          "hermes_curator_evolver/storage.py:71-83 (_strip_nul_bytes: strip the real NUL byte, the \\x00 literal, AND the \\u0000 escape form; stop mangling legitimate literal documentation text)",
          "hermes_curator_evolver/storage.py:96 (both ingest paths already route through the sanitizer - hooks ingest and backfill import; no other call sites)",
          "tests/test_storage.py (new: NUL-free round-trip fixture across all three encodings; extends U1's tests)"
        ],
        "must_land_before": [],
        "rationale": "The campaign's founding Problem class, still reachable: a tool result containing the \\u0000 escape decodes to a real NUL on read and re-opens the perpetual rollback loop U1 was built to close; the current fix also mangles benign literal text (both reproduced live). Cheapest packet on the board (effort 5). Anchor re-verified: _strip_nul_bytes at :71, zero escape handling."
      },
      {
        "id": "CU-T",
        "packet": "U35",
        "title": "Rollback validation and guarded rollback (B16+C2+R8/N1)",
        "surfaces": [
          "hermes_curator_evolver/guarded_apply.py:426-468 (_rollback_support_files: validate manifest support entries - skills-root containment, target-identity refusal (never unlink the restored SKILL.md itself), registration cross-check - before any unlink)",
          "hermes_curator_evolver/guarded_apply.py:471+ (rollback_guarded_patch: pre-rollback safety snapshot of every file about to be touched, fail-closed; explicit opt-in flag for post-apply-modified files (C2 CLI-default overwrite) instead of silent overwrite; atomic temp+rename write primitive - absorbs U18's atomic-write slice)",
          "tests/test_guarded_apply.py (new: N1 reproducer promoted to regression - tampered manifest must not delete the restored file)"
        ],
        "must_land_before": [],
        "rationale": "The destructive class inside just-landed code: rollback is the trust anchor every later packet (U27 default, U30 host-ledger write side) builds on, and it can currently be made to unlink the SKILL.md it just restored (N1 reproduced live: removed ['SKILL.md'], file gone). KTD16 names U35 first among cycle-4 remediation. Sole owner of guarded_apply.py this cycle, so its rework of the write path also lands the atomic-write primitive U18 needs later. Anchor re-verified: _rollback_support_files :426, rollback_guarded_patch :471."
      },
      {
        "id": "CU-U",
        "packet": "U16",
        "title": "Numeric-flag contract repair: explicit 0 parses as 0 (B8/N4)",
        "surfaces": [
          "hermes_curator_evolver/cli.py:787-803 (the four flags - max_reference_files/max_skills/min_evidence/variants: replace `int(values.get(...) or 5)` with explicit-presence parsing so 0 survives)",
          "hermes_curator_evolver/auto_evolve.py:414 (prune guard `keep < 0` → `keep <= 0` semantics so 0 disables pruning end-to-end)",
          "tests/test_auto_evolve.py:1106 (REPLACE the existing delete-all assertion - it codifies the bug - with the disables-pruning assertion; N4 reproducer as the same-pass reference test; separate test functions from CU-Q's edits to the same file)"
        ],
        "must_land_before": [],
        "rationale": "The documented contract ('0 disables pruning') is the opposite in code: keep=0 prunes the reference the same apply just wrote (N4 reproduced live: written path == pruned path, file gone), and the existing test asserts the buggy behavior. Anchor re-verified: `or 5` at cli.py:803, `keep < 0` at auto_evolve.py:414."
      },
      {
        "id": "CU-V",
        "packet": "U28",
        "title": "Single structured error classifier (B15/P2)",
        "surfaces": [
          "hermes_curator_evolver/storage.py:113-130 (delete or delegate _looks_like_error onto the candidates-side structured-first classifier - structured payloads decided by type/exit fields, never substring guesses)",
          "hermes_curator_evolver/candidates.py:200+ (classifier target already reworked by the uncommitted cycle-1 remediation; CU-V is the delete-the-duplicate step)",
          "tests/test_storage.py + tests/test_candidates.py (extend the corpus: '3 passed, no errors found' must classify as success; P2 reproducer)"
        ],
        "must_land_before": [],
        "rationale": "Ingest corruption: success strings stored as errors ('3 passed, no errors found' → is_error True, reproduced live), which poisons the exact cohorts that gate auto-evolve thresholds and that U24 will later mine. Two classifiers for one question is the defect; one structured-first classifier is the fix. Anchor re-verified: _looks_like_error at :113 with recursive json.loads at :118."
      }
    ],
    "must_remain_separate": [
      ["CU-Q (auto_evolve.py:386 managed-block writer) - U15", "CU-U (auto_evolve.py:414 prune guard + cli.py:787-803 flag parsing) - U16"],
      ["CU-R (storage.py:154-157 connect pragmas + hooks.py:13-14) - U7a", "CU-V (storage.py:113-130 classifier) - U28"],
      ["CU-R (storage.py:154-157) - U7a", "CU-S (storage.py:71-83 sanitizer) - U37"],
      ["CU-V (storage.py:113-130) - U28", "CU-S (storage.py:71-83 sanitizer) - U37"],
      ["CU-T (guarded_apply.py:426-468/:471 rollback contract) - U35", "CU-Q (auto_evolve.py:386 writer template) - U15"],
      ["the uncommitted cycle-1 remediation (11 modified tracked files, 833 insertions)", "every CU-Q..CU-V unit of this request"],
      ["held batch-2 units (U36 backfill rewrite, U18 loop-boundary remainder, U19, U27) and KTD16-gated extensions (U38-U42)", "every CU-Q..CU-V unit of this request"],
      ["tests/test_auto_evolve.py additions of CU-Q (second-run corpus)", "tests/test_auto_evolve.py:1106 replacement of CU-U"]
    ]
  }
}
```

## Splitting notes (why these boundaries)

- **Same file ≠ same concern.** Three units touch `auto_evolve.py` (CU-Q writer, CU-U guard,
  CU-U's CLI half is in `cli.py`), three touch `storage.py` (CU-R connect, CU-S sanitizer,
  CU-V classifier), one solely owns `guarded_apply.py` (CU-T). Every coincidence is between
  disjoint functions on separate hunks - the adjacency the cycle-3 request already blessed for
  U7a+U28, now a three-way in `storage.py`. Keeping them as six units keeps each independently
  reviewable and revertable; merging by file would couple a crash fix to a classifier rewrite.
- **CU-T is this cycle's sole `guarded_apply.py` owner** (the cycle-3 U27-precedent applied to
  U18): its safety-snapshot work needs the atomic temp+rename primitive, which absorbs U18's
  highest-value slice rather than contending with it. U18's loop-boundary remainder is
  explicitly held for batch 2.
- **The dirty tree is context, not a unit.** The 11 uncommitted cycle-1 files are the substrate
  all six units build on and must be preserved as-is until their own commit gate (KTD16:
  cycle-1 batch commits first). No CU-Q..CU-V change should be folded into that commit.
- **Held work stays held.** U36 (backfill rewrite - latent defects, rewrite of uncommitted
  code), U17/U26/U6, and all extensions (U38 first when they open) are deliberately not in
  this request; landing them here would violate KTD16 and the batch selection.
- **No intra-batch hard dependencies** (dep-freedom 5 across all six in the scoring table) -
  that is precisely why this set is a coherent, parallelizable batch. The two soft
  coordinations are the shared `tests/test_auto_evolve.py` (CU-Q adds functions, CU-U replaces
  one assertion) and CU-T's write primitive being the one place atomic writes are introduced.

## Verification contract for the implement phase

Mechanical gates exist before any review: re-run the 12-reproducer corpus
(`/home/agent/.hermes/conductor-runs/673d15323b9c4580a0e2ed84fa8625fc-assess/repro-adversarial-findings-pass4.sh`;
this batch flips exactly N1, N4, N5, P1, P2, P4 - N2/N3/N6/P7/P10 must remain reproducing,
they belong to later batches); targeted pytest per changed surface
(`tests/test_auto_evolve.py`, `tests/test_storage.py`, `tests/test_candidates.py`,
`tests/test_guarded_apply.py`, `tests/test_backfill_sessions.py` for the sanitizer's import
path); full suite stays green (174 baseline). Roadmap Acceptance governs: feature branch off
main, targeted tests as the gate, push to `fork` only. None of that is this phase's to do.

*Read-only request; no code changed, nothing committed or pushed.*
