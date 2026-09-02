---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-1-stewardship-request
run: 8a1ca9a2a18e440e86bff85efe099474
phase: stewardship
attempt: cc4e4ac627b04985b43993e1532ca6d1
skill: ce-plan (change-request description; router has no stewardship skill - ce-handoff rejected as session continuity, ce-proof as external publishing; same route and reasoning as the fleet's prior stewardship phases)
upstream: docs/prioritization/2026-09-02-cycle-1-batch.md (selected batch U1+U2+U3+U4)
---

# Stewardship request — cycle 1 correctness batch

This document describes the selected maintenance batch for the conductor to steward. It
deliberately does **not** choose Git topology: no branch names, no worktree layout, no commit
sequencing. Those are the conductor's to plan after inventorying the repository, detecting
overlap, splitting unrelated concerns, and preserving dirty state.

```json
{
  "stewardship_request": {
    "title": "hermes-curator-evolver correctness batch (cycle 1): NUL sanitizer, tokenized classifiers, rollback completeness, backfill isolation",
    "summary": "Four dependency-light, independently verifiable packets that make recorded evidence true and every write reversible - the roadmap's correctness core (KTD1: hardening precedes extension). CU-A fixes the NUL-sanitizer no-op that is the root cause of the campaign's founding Problem: a NUL byte in a recorded tool result survives sanitization and every later auto-apply for that skill fails validation and rolls back forever (F1 re-verified live this session: nul_stored=True in_managed_block=True validator_ok=False). CU-B replaces substring-based failure/workflow classification with structured signals so successful results stop being learned as failures (F2: type=replay_benchmark is_error=True on a success payload). CU-C makes rollback complete (support files restored, not orphaned - F3), validates manifest paths stay under the skills directory, bounds the unbounded references/curator-evolver-auto-*.md growth, and stops forwarding the full parent environment to verify commands. CU-D removes the state-DB import's unverified newest-first ordering assumption and its wholesale exception. All fixes verified by re-running the existing reproducers green plus targeted tests; no user-visible defaults change, no new features, no model dependencies.",
    "repository_candidate": {
      "name": "hermes-curator-evolver",
      "path": "/work/projects/hermes-curator-evolver",
      "remote": "git@github.com:codeo1io/hermes-curator-evolver.git",
      "remote_role": "push target is the 'fork' remote (codeo1io); 'origin' (pingchesu/hermes-curator-evolver) is upstream and must never be pushed to, per the roadmap's Repository remote section",
      "branch": "main",
      "head": "45328db04c188dd4d8734e31c8b85f2d84f6358b",
      "committed_tree": [".github", ".gitignore", "CONTRIBUTING.md", "LICENSE", "README.md", "__init__.py", "docs", "examples", "hermes_curator_evolver", "plugin.yaml", "pyproject.toml", "tests"],
      "rationale": "All four packets are this repository's own Python package and tests. The worktree is otherwise clean (two untracked phase-artifact paths, listed below); no cross-repository inputs are required - unlike the founding proposal's error event, every defect here is reproducible inside this tree with scratch temp dirs."
    },
    "change_units": [
      {
        "id": "CU-A",
        "packet": "U1",
        "title": "NUL byte sanitizer with end-to-end regression",
        "surfaces": [
          "hermes_curator_evolver/storage.py (modify: sanitizer at :81 - strip the NUL byte itself, both raw and escaped-literal forms)",
          "hermes_curator_evolver/backfill.py (modify: ensure the import write path routes through the same sanitizer - separate hunk from CU-D's iteration rework)",
          "tests/test_storage.py (modify: NUL-bearing tool result persisted clean)",
          "tests/test_backfill_sessions.py (modify: NUL survives neither hooks ingest nor backfill import)"
        ],
        "must_land_before": ["CU-D"],
        "rationale": "Root cause of the founding Problem ('observed 1 error-related event') and the batch's only perpetual-failure defect: hooks swallow errors, so a poisoned skill silently rolls back on every daily run with no detection or bounded recovery - exactly the class the roadmap exists to fix. Cheapest unit on the board; each day it waits the timer manufactures another silent loop. Discharges B1. Evidence command: F1 re-run -> validator_ok=True; targeted pytest on storage + backfill."
      },
      {
        "id": "CU-B",
        "packet": "U2",
        "title": "Tokenized failure and workflow classification",
        "surfaces": [
          "hermes_curator_evolver/candidates.py (modify: _is_tool_failure :200 - structured signals (JSON success/error keys, exit codes, exception markers) instead of substrings; _looks_workflow :175-184 - command-sequence evidence instead of two backtick spans)",
          "tests/test_candidates.py (modify: adversarial corpus - success payloads containing 'cap'/'capability'/'capture', prose with two inline-code spans, single commands)"
        ],
        "rationale": "Queue truth: today the pipeline records the opposite of what happened (F2) and invents workflow skills from prose (F5). Every extension unit (U8 dedupe, U9 staleness, U10 missed-triggers) consumes these classifications, so this is the compounding correctness fix. Fully disjoint from the other units' files. Discharges B2 (F5 rider included). Evidence: F2 -> is_error=False; F5 -> no skill_new; corpus test green."
      },
      {
        "id": "CU-C",
        "packet": "U3",
        "title": "Rollback completeness, path validation, spill retention, verify-env hygiene",
        "surfaces": [
          "hermes_curator_evolver/guarded_apply.py (modify: rollback_guarded_patch :390-416 - restore/remove every manifest-registered support file; validate backup_path/target_path resolve under the skills directory before copying; _run_verify :44-56 - constructed environment instead of full os.environ)",
          "hermes_curator_evolver/auto_evolve.py (modify: retention bound on references/curator-evolver-auto-*.md near :398/:1023 - keep most-recent N per skill, N configurable, default small)",
          "tests/test_guarded_apply.py (modify: orphan-free rollback, tampered-manifest refusal, bounded references growth, verify env)",
          "tests/test_auto_evolve.py (modify: retention pruning)"
        ],
        "rationale": "The safety net the README trust story sells: staged verify, backups, restore drills. F3 shows rollback leaving the apply's support file orphaned; the references directory grows without bound across daily runs; and rollback trusts manifest paths unvalidated - a reviewer reproducing any of these discredits the 'safe by default' claim. Highest strategic score among open units (U11 hub rebase and every future write-path extension build on rollback being complete). Deliberately excludes U5's byte-cap switch and U7's preview-escaping in auto_evolve.py - see must_remain_separate. Discharges B3. Evidence: F3 -> no orphan on disk; two-apply scratch test shows bounded references/; tampered manifest refused."
      },
      {
        "id": "CU-D",
        "packet": "U4",
        "title": "Backfill per-session isolation and explicit ordering",
        "surfaces": [
          "hermes_curator_evolver/backfill.py (modify: session iteration :374-376 - explicit timestamp comparison, no ordering assumption, client-side sort; :385 - per-session error boundary with counted skips surfaced in the import summary; document the ordering contract at the SessionDB call)",
          "tests/test_backfill_sessions.py (modify: oldest-first/shuffled synthetic state-DB fixture imports the identical session set; a corrupted row yields a counted skip, not an aborted import)"
        ],
        "must_land_after": ["CU-A"],
        "rationale": "Same defect class as the rest of the batch - derived state silently wrong: silent truncation when SessionDB ordering differs, wholesale abort on one bad row. Small, and it completes the batch's verification pattern with its own synthetic fixture. Lands after CU-A because both touch backfill.py and its test file: CU-A's sanitize call site and CU-D's iteration rework must be separate hunks, sanitizer first. Discharges B4."
      }
    ],
    "preexisting_dirty_state_to_preserve": [
      ".hermes/plans/autonomy-prop_8c5390ffe26640fa.md - untracked configured roadmap: founding proposal (23 lines) plus this run's append-only 'Extension 2026-09-02 - maintenance cycle 1' (U1-U14, B1-B6, KTD1-KTD6, sequencing, rejections). No packet edits it; disposition is the commit gate's.",
      "docs/prioritization/2026-09-02-cycle-1-batch.md - untracked cycle-1 selection artifact (five-axis table, gates, batch rationale). No packet edits it.",
      "data/, *.sqlite, backups/ - gitignored plugin runtime state (evidence DBs, session imports, skill backups). No packet mutates or commits these; all fix verification happens in scratch temp dirs, exactly as the assessment reproducers do.",
      "logs/ - untracked runtime logs directory (outside .gitignore patterns but never staged by prior phases); leave as-is.",
      ".pytest_cache/, __pycache__/ - ignored test/build caches."
    ],
    "must_remain_separate": [
      "U5 (byte-based caps) shares guarded_apply.py with CU-C and was deferred precisely to avoid doubling churn on the rollback file: CU-C must not 'while we're in there' switch _BUILTIN_HARD_CAP_CHARS to bytes. U5 lands next cycle after CU-C merges.",
      "U6 (bootstrap default alignment) is a user-visible default flip needing README/quickstart/examples coordination: nothing in this batch touches cli.py or README.md.",
      "U7 riders on this batch's surfaces must not ride: WAL/busy_timeout in storage.py (:139) is U7's - CU-A changes only the sanitizer; preview escaping in auto_evolve.py (:321/:401) is U7's - CU-C touches auto_evolve.py only for retention pruning; the verifier grounding cross-check, version single-sourcing, merge-check error handling, and CI gates are all U7's, in files this batch otherwise never opens (verifier.py, __init__.py/pyproject/plugin.yaml, skill_audit.py, .github/workflows/ci.yaml).",
      "semantic.py batch_size/rerank changes belong to U8's implementation, not CU-B's classifier work.",
      "Extensions U8-U14 are KTD1-gated behind all of U1-U7: no packet may add dedupe scanning, staleness reporting, missed-trigger joins, hub rebase, upstream interop, cron backends, or HTML output.",
      "The founding Acceptance contract governs topology-neutral constraints: work lands on a feature branch off the current default branch, targeted tests for changed surfaces (never the full suite as the gate), push to 'fork' only, no upstream merge - but which branches/worktrees realize that is the conductor's choice, not this request's.",
      "No host-side mutation outside the repository: no Hermes config changes, no skill-directory writes, no timer installs. Every packet is package code plus tests, verified against scratch fixtures."
    ],
    "verification_protocol": {
      "per_unit": [
        "CU-A: bash repro F1 -> nul_stored False / in_managed_block False / validator_ok True; python3 -m pytest tests/test_storage.py tests/test_backfill_sessions.py -q",
        "CU-B: bash repro F2 -> is_error False for the success payload; F5 -> no skill_new; python3 -m pytest tests/test_candidates.py tests/test_candidates_cli.py -q",
        "CU-C: bash repro F3 -> rolled_back_target True AND orphan_support_file_on_disk False; python3 -m pytest tests/test_guarded_apply.py tests/test_auto_evolve.py -q",
        "CU-D: new synthetic state-DB fixture (shuffled + corrupt row) -> identical session set imported, corrupted row counted; python3 -m pytest tests/test_backfill_sessions.py -q"
      ],
      "batch_gate": "Full suite green at the full-tests phase; reproducers F1/F2/F3 re-run green as the per-unit completion proof recorded in each unit's PhaseResult."
    }
  }
}
```

## Repository and change-unit decisions with rationale

1. **Single repository: hermes-curator-evolver, fork remote only.** Every packet's output is
   this repository's package and tests. `git remote -v` shows two remotes: `fork`
   (git@github.com:codeo1io/hermes-curator-evolver.git) and `origin`
   (https://github.com/pingchesu/hermes-curator-evolver.git, upstream author). The roadmap's
   standing policy - push to `fork`, never `origin` - is restated in `repository_candidate`
   as fact, not as a topology choice.
2. **Four change units, not one monolith.** New surfaces are disjoint by file:
   CU-A=storage.py(+backfill sanitize hunk), CU-B=candidates.py, CU-C=guarded_apply.py+auto_evolve.py,
   CU-D=backfill.py(iteration). The one genuine overlap is CU-A/CU-D sharing `backfill.py` and
   `tests/test_backfill_sessions.py` - different functions, so the constraint is separate hunks
   with CU-A first, and overlap detection should treat CU-D's changes as additive on top of
   CU-A's, never as a rewrite of them.
3. **CU-A strictly first; CU-B and CU-C order-free; CU-D last among neighbors.** CU-A precedes
   CU-D for the file-adjacency reason above and because evidence truth at write time is
   upstream of everything the other units read. CU-B and CU-C share no files with anything
   else in the batch and can proceed in parallel or any order.
4. **Slip designation: CU-D first, then CU-B.** If the cycle cannot fit all four, CU-D (lowest
   impact score, 3) slips first and CU-B second; CU-A (root cause of the founding Problem) and
   CU-C (the trust-story safety net plus the only unbounded-resource defect) are the must-lands.
   A slip is recorded, not silent - the deferred unit returns to the head of the next batch.
5. **Dirty state is preserved, not absorbed.** The untracked roadmap and selection artifact are
   prior-phase work products listed for inventory; no packet edits them, and their disposition
   (including making the configured roadmap durable) belongs to the commit gate.
6. **Runtime state is off-limits.** `data/`, `*.sqlite`, `backups/`, `logs/` are the plugin's
   live evidence/backups on this host; fixes are proven in scratch temp dirs exactly as the
   assessment reproducers already do, so verification never depends on - or disturbs - real
   recorded evidence.
7. **No topology chosen.** Branch names, worktree layout, and commit sequencing are absent from
   the request by design; `branch`/`head` appear only as current-state facts the conductor
   inventories against.
