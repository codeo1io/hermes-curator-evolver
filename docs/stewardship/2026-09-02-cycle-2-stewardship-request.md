---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-2-stewardship-request
run: 589e5a44a79d4dbda45b3af824d14669
phase: stewardship
attempt: ac686b0997a142e38670aaf1226a4085
attempt-history:
  - ca6e033af2a94d118eabaa5beb70a9d2 - original; wrote this request against the then-current tree
  - 0e0d79440bba479ca16eebd3f144c219 - re-issue; verified byte-identical tree (HEAD/status/mtimes/anchors), pytest 174/174 exit 0, re-affirmed unchanged; added this lineage
  - ac686b0997a142e38670aaf1226a4085 - re-issue; zero drift again (git branch/worktree show no conductor topology work yet; find -newer artifact returns nothing; anchors live; no cycle-2 code: 0 busy_timeout, 0 %% escapes), pytest re-run green; JSON body still untouched since the original attempt
skill: ce-plan (change-request description; router has no stewardship skill - ce-handoff rejected as session continuity, ce-work/ce-worktree rejected as topology choice this phase must NOT make; same route and reasoning as the fleet's prior stewardship phase)
upstream: docs/prioritization/2026-09-02-cycle-2-batch.md (selected batch U15+U7a+U16+U17+U18)
---

# Stewardship request — cycle 2 integrity batch

This document describes the selected maintenance batch for the conductor to steward. It
deliberately does **not** choose Git topology: no branch names, no worktree layout, no
commit sequencing. Those are the conductor's to plan after inventorying the repository,
detecting overlap, splitting unrelated concerns, and preserving dirty state.

**One thing is different from cycle 1 and must shape the inventory: the working tree
carries the cycle-1 implementation batch uncommitted.** 11 modified files
(`hermes_curator_evolver/{auto_evolve,backfill,candidates,cli,guarded_apply,storage}.py`
+ 5 test files, ~833 insertions, verified landed by this run's roadmap phase: U1-U4).
That work is prior authorized output, not noise: every cycle-2 unit edits files it
touched, CU-G fixes defects *inside* it, and its disposition (commit or otherwise)
belongs to the commit gate - no cycle-2 unit may absorb, revert, or reformat it.

```json
{
  "stewardship_request": {
    "title": "hermes-curator-evolver integrity batch (cycle 2): managed-block replacement safety, storage lock resilience, numeric-flag contract, scheduler unit hardening, apply-loop resilience",
    "summary": "Five packets with one property: an unattended run must never crash, never drop evidence, never delete the wrong thing, and must always emit a report (KTD7: this precedes all extensions). CU-E fixes the re.sub replacement-template defect - a preview containing \\1 crashes every auto-run after the first with exit 1 and NO report, re-verified live this session (re.error: invalid group reference 1 at position 522; stdout is valid report JSON: False) - and neutralizes previews entering managed blocks, closing the T18 coverage hole (no existing test starts from a pre-blocked skill). CU-F makes evidence persistence survive concurrent writers: today a 5.01s lock blocks each hook, logs a warning, and drops the event - 0 of 3 recorded, re-verified live - via WAL journal mode, busy_timeout, and bounded retry at the storage connect site (B10, corroborated upstream by NousResearch/hermes-agent#101035). CU-G repairs the numeric-flag contract inside the just-landed cycle-1 code: help says '0 disables pruning' but the CLI or-coercion rewrites an explicit 0 to 5, the prune guard treats 0 as delete-everything (including the reference written by the same apply), and the landed test asserts the delete-all - help, code, and test are brought into agreement with 0 meaning disable, for four flags (KTD9 precedent). CU-H closes scheduler unit injection: --schedule is interpolated into OnCalendar= unvalidated (a newline writes an arbitrary second [Service]/ExecStart= section, reproduced) and _systemd_quote never escapes % so systemd specifiers rewrite ExecStart paths. CU-I gives the run loop a per-candidate error boundary so one bad skill no longer aborts the whole pass with no report (re-verified: report emitted: False), moves support-file writes inside the guarded transaction with size bounds and checked manifest registration, and makes target writes atomic (temp+rename). All five are verified by existing mechanical reproducers re-run green plus targeted tests; no user-visible default changes, no new features, no model dependencies.",
    "repository_candidate": {
      "name": "hermes-curator-evolver",
      "path": "/work/projects/hermes-curator-evolver",
      "remote": "git@github.com:codeo1io/hermes-curator-evolver.git",
      "remote_role": "push target is the 'fork' remote (codeo1io); 'origin' (pingchesu/hermes-curator-evolver) is upstream and must never be pushed to, per the roadmap's Repository remote section",
      "branch": "main",
      "head": "45328db04c188dd4d8734e31c8b85f2d84f6358b",
      "committed_tree": [".github", ".gitignore", "CONTRIBUTING.md", "LICENSE", "README.md", "__init__.py", "docs", "examples", "hermes_curator_evolver", "plugin.yaml", "pyproject.toml", "tests"],
      "uncommitted_baseline": "11 modified files carrying the cycle-1 batch (U1-U4) - hermes_curator_evolver/{auto_evolve,backfill,candidates,cli,guarded_apply,storage}.py and tests/{test_auto_evolve,test_backfill_sessions,test_candidates,test_guarded_apply,test_storage}.py, ~833 insertions, pytest 174/174 at assess baseline. Cycle-2 units build on top of this state; all line anchors in this request were verified against the CURRENT tree (with those edits), not HEAD.",
      "rationale": "All five packets are this repository's own Python package and tests. Unlike cycle 1's request, the tree is NOT otherwise clean - see preexisting_dirty_state_to_preserve; overlap detection must treat the cycle-1 hunks as settled context. Every defect is reproducible inside this tree with scratch temp dirs (the assessment reproducers under /tmp/assess/ce-assess-76416fd2/ all run against it without host mutation)."
    },
    "change_units": [
      {
        "id": "CU-E",
        "packet": "U15",
        "title": "Managed-block replacement safety (literal block, neutralized previews, second-run regression)",
        "surfaces": [
          "hermes_curator_evolver/auto_evolve.py (modify: block-writer sub at :386 - lambda replacement so evidence text is never a template; preview neutralization helper for content entering managed blocks ~:323-333 - strip control characters, remove plugin markers, bound length)",
          "tests/test_auto_evolve.py (add: second-run corpus - skills that ALREADY carry a managed block, previews containing \\1, \\g<0>, newline, and an embedded auto:end marker)",
          "tests/test_candidates.py (adjacent only: preview neutralizer is exercised through the candidate path; separate hunks)"
        ],
        "must_land_before": ["CU-I"],
        "rationale": "The only guaranteed steady-state crash on the board: any skill the plugin has ever touched carries a managed block, and any preview with a backreference then kills the run with no report - 174 green tests never see it because none starts pre-blocked (T18). Cheapest certainty (score 24). The neutralizer is also the substrate U21 (publish-safety) will reuse next cycle. Discharges B7. Evidence: python /tmp/assess/ce-assess-76416fd2/repro_autorun_crash.py -> exit 0, valid report JSON, block literal; repro_misc2.py -> no unbalanced-managed-block-markers; new second-run tests green."
      },
      {
        "id": "CU-F",
        "packet": "U7a",
        "title": "Storage lock resilience: WAL, busy_timeout, bounded retry",
        "surfaces": [
          "hermes_curator_evolver/storage.py (modify: connect site at :155 - journal_mode=WAL, busy_timeout, bounded retry around the write path; do NOT touch the :79 sanitizer - that is settled cycle-1 work)",
          "hermes_curator_evolver/hooks.py (modify: error handling at the EvidenceStore call :13 - a failed record attempt is retried then logged with an explicit lost-event marker, never silently swallowed)",
          "tests/test_storage.py (add: concurrent-writer test shaped on repro_h4_lock_drop.py - a BEGIN EXCLUSIVE holder must not cause dropped events)"
        ],
        "rationale": "The other certainty (score 24) and the batch's only unrecoverable-input loss: evidence is the product's entire input and grows ~2,200 events/day on this host; under any concurrent writer every hook currently blocks 5.01s and drops its event (0 of 3 recorded, re-verified live this session). KTD8 pulled exactly this U7 item forward as blocking; upstream #101035 reports the same class. Smallest high-impact change in the batch. Discharges B10. Evidence: repro_h4_lock_drop.py -> all events recorded, no 5.01s stalls beyond the bounded retry budget; targeted pytest on storage + hooks."
      },
      {
        "id": "CU-G",
        "packet": "U16",
        "title": "Numeric-flag contract repair: explicit zeros honored, prune-0 disables",
        "surfaces": [
          "hermes_curator_evolver/cli.py (modify: parse-explicit 0 for --max-reference-files, --max-skills, --min-evidence, --variants at :787/:788/:800/:803 - unset and explicit 0 are different values; help at :242 stays)",
          "hermes_curator_evolver/auto_evolve.py (modify: prune guard at :414 - keep == 0 means disable, only keep < 0 is invalid)",
          "tests/test_auto_evolve.py (modify: REPLACE the delete-all assertion at :1106 with a disables-pruning assertion - the current test codifies the bug; separate hunk from CU-E's additions to the same file)"
        ],
        "must_land_after": ["CU-E"],
        "rationale": "The batch's only data-deletion defect, and it sits inside the just-landed cycle-1 U3 code: three artifacts disagree (help says 0 disables; CLI rewrites 0 to 5; the function deletes everything on direct keep=0, including the reference the same apply just wrote). Establishes the KTD9 parse-explicit contract every future numeric flag (U23 retention included) adopts by construction. Discharges B8. Evidence: repro_h2_prune_zero.py -> keep=0 prunes nothing, flag value reaches config unchanged; the replaced test proves the suite cannot pass both ways."
      },
      {
        "id": "CU-H",
        "packet": "U17",
        "title": "Scheduler unit hardening: schedule validation and %% escaping",
        "surfaces": [
          "hermes_curator_evolver/auto_evolve.py (modify: schedule validation before :1386's OnCalendar interpolation - reject newlines and section-injection characters with an actionable error; _systemd_quote at :190 - escape % as %% alongside \\\\\" and \\\"; assert single ExecStart in the generated unit)",
          "tests/test_auto_evolve.py (add: newline-bearing --schedule rejected with no file written; %h-bearing and space-bearing skills paths render escaped in unit content; scratch XDG_CONFIG_HOME so no host unit is ever touched)"
        ],
        "must_land_after": ["CU-E"],
        "rationale": "The security item: --schedule is operator input interpolated into a systemd unit file unvalidated - reproduced writing a literal second [Service]/ExecStart= section - and unescaped % lets systemd specifiers rewrite ExecStart. Same root cause class as B7 (external data into a second interpretation layer), which is what makes the batch coherent. Delay risk is bounded because the vector is the local operator's own CLI, but the blast radius is arbitrary unit content. Discharges B9. Evidence: repro_h3_systemd.py -> injected schedule rejected at the CLI, no file written; %-bearing path rendered with %%."
      },
      {
        "id": "CU-I",
        "packet": "U18",
        "title": "Apply-loop resilience: per-candidate boundary, transactional support files, atomic writes",
        "surfaces": [
          "hermes_curator_evolver/auto_evolve.py (modify: candidate loop :846-1135 - per-candidate try/except recording failed:<class> and continuing, report always emitted; support files :1057-1065 - written before/within verification, size-bounded, register_support_file_in_manifest return checked)",
          "hermes_curator_evolver/guarded_apply.py (modify: :315 write_text - temp file + os.replace for atomicity; do NOT touch _BUILTIN_HARD_CAP_CHARS - that is U5's)",
          "tests/test_auto_evolve.py (add: first candidate raises, second applies, one report reflects both)",
          "tests/test_guarded_apply.py (add: interrupted write leaves old-or-new full file, never partial)"
        ],
        "must_land_after": ["CU-E", "CU-G"],
        "rationale": "Completes the batch's guarantee as a tested property: repro_m12_no_report.py shows one bad skill aborting the entire pass with no report today. The atomic-write change is why U5 stays out of this batch (shared guarded_apply.py). Every U8-U14 extension inherits the always-report boundary. Discharges B11. Evidence: repro_m12_no_report.py -> exit 0, report emitted, failed candidate counted, survivor applied; interruption fixture green."
      }
    ],
    "preexisting_dirty_state_to_preserve": [
      "THE CYCLE-1 BATCH (uncommitted, 11 modified files, ~833 insertions): hermes_curator_evolver/{auto_evolve,backfill,candidates,cli,guarded_apply,storage}.py + tests/{test_auto_evolve,test_backfill_sessions,test_candidates,test_guarded_apply,test_storage}.py. Authorized prior output implementing U1-U4; pytest 174/174. Must NOT be absorbed into, reverted by, or reformatted by any cycle-2 unit; its disposition is the commit gate's. CU-G intentionally FIXES defects inside it (that is new work on top, not modification of its intent).",
      "docs/assessment/2026-09-02-adversarial-repository-assessment.md, docs/ideation/2026-09-02-cycle-2-extension-research.md, docs/prioritization/2026-09-02-cycle-2-batch.md, docs/stewardship/2026-09-02-cycle-1-stewardship-request.md (+ this file) - untracked phase artifacts; no unit edits them; disposition is the commit gate's.",
      ".hermes/plans/autonomy-prop_8c5390ffe26640fa.md - untracked configured roadmap (founding proposal + cycle-1 and cycle-2 append-only extensions, the latter verified byte-identical-prefix this run). No unit edits it.",
      "data/, *.sqlite, backups/ - gitignored plugin runtime state (evidence DBs, session imports, skill backups). No unit mutates or commits these; all verification happens in scratch temp dirs exactly as the reproducers do.",
      "logs/, .pytest_cache/, __pycache__/, .ruff_cache/ - untracked runtime/caches; leave as-is."
    ],
    "must_remain_separate": [
      "U5 (byte-based caps) shares guarded_apply.py with CU-I's atomic-write change and is deferred precisely to avoid doubling churn there: CU-I must not 'while we're in there' switch _BUILTIN_HARD_CAP_CHARS to bytes.",
      "U7b (version single-sourcing across __init__.py/pyproject/plugin.yaml/bundled SKILL.md/README) and U7c (CI lint/type gates) are the rest of U7 and stay out: CU-F changes only the connect site and hook error path.",
      "U19 (identity/dedup unification) and U20 (P3 hygiene) are next cycle's batch head; nothing here may fold them in - including the tempting one-line M9 cutoff fix in the report path CU-E's tests pass through.",
      "U21-U25 extensions are KTD7-gated behind this batch: no publish-safety scrubbing, ledger, telemetry, retention, or candidates-decide work may ride, even though U21 would reuse CU-E's neutralizer.",
      "The cycle-1 dirty hunks are context, not cargo: any cycle-2 commit that also lands, rewraps, or reverts cycle-1 edits mixes two authorized batches - the conductor's overlap detection should flag that, and the commit gate owns the sequencing decision.",
      "tests/test_auto_evolve.py:1106's replacement belongs to CU-G and to nobody else; it must not be 'fixed' incidentally by CU-E's or CU-I's test additions.",
      "CU-H's verification must never install, start, or overwrite a real user unit: scratch XDG_CONFIG_HOME only (the assessment's repro_h3_systemd.py already demonstrates the pattern; the real ~/.config/systemd/user was verified untouched after that run).",
      "The founding Acceptance contract governs topology-neutral constraints: feature branch off the current default branch, targeted tests for changed surfaces (never the full suite as the gate), push to 'fork' only, no upstream merge - but which branches/worktrees realize that is the conductor's choice, not this request's.",
      "No host-side mutation outside the repository: no Hermes config changes, no skill-directory writes, no timer installs. Every unit is package code plus tests, verified against scratch fixtures."
    ],
    "verification_protocol": {
      "per_unit": [
        "CU-E: python /tmp/assess/ce-assess-76416fd2/repro_autorun_crash.py -> exit 0 + valid report JSON + literal block; repro_misc2.py -> no marker imbalance; python3 -m pytest tests/test_auto_evolve.py -q (second-run corpus green)",
        "CU-F: python /tmp/assess/ce-assess-76416fd2/repro_h4_lock_drop.py -> 3 of 3 recorded under a concurrent writer; python3 -m pytest tests/test_storage.py tests/test_hooks.py -q (hooks test file if absent: storage-level concurrency test + hooks error-path unit)",
        "CU-G: python /tmp/assess/ce-assess-76416fd2/repro_h2_prune_zero.py -> keep=0 prunes nothing, 0 reaches config; python3 -m pytest tests/test_auto_evolve.py tests/test_cli*.py -q (or the CLI config test module that exists)",
        "CU-H: python /tmp/assess/ce-assess-76416fd2/repro_h3_systemd.py -> newline schedule rejected, no file written, %% present for %-bearing path; python3 -m pytest tests/test_auto_evolve.py -q (unit-content tests)",
        "CU-I: python /tmp/assess/ce-assess-76416fd2/repro_m12_no_report.py -> exit 0, report emitted, failed candidate counted; python3 -m pytest tests/test_guarded_apply.py tests/test_auto_evolve.py -q (interruption + boundary fixtures)"
      ],
      "batch_gate": "Full suite green at the full-tests phase (baseline 174 passing at this exact tree, per the cycle-2 assessment); the five reproducers re-run green as each unit's completion proof recorded in its PhaseResult; no cycle-1 hunk reverted (git diff of the cycle-1 files still contains its intent after the cycle-2 edits)."
    }
  }
}
```

## Repository and change-unit decisions with rationale

1. **Single repository: hermes-curator-evolver, fork remote only.** Every packet's output
   is this repository's package and tests. `git remote -v` (re-checked live this session)
   shows `fork` (git@github.com:codeo1io/hermes-curator-evolver.git) and `origin`
   (pingchesu/hermes-curator-evolver, upstream author); push-to-fork-only is restated as
   fact, not topology.
2. **Five change units, not one monolith.** CU-E=auto_evolve.py(block writer + preview
   neutralizer), CU-F=storage.py+hooks.py, CU-G=cli.py+auto_evolve.py(prune guard)+its
   test replacement, CU-H=auto_evolve.py(unit generation), CU-I=auto_evolve.py(loop)+
   guarded_apply.py(atomic writes). Three units share `auto_evolve.py` (E, G, H, I — four
   counting CU-I) but in disjoint regions (writer ~:323-:386, prune ~:414, timer
   ~:190/:1386, loop :846-1135/:1057-1065): the constraint is separate hunks with the
   recorded intra-file ordering, not file ownership.
3. **Ordering: CU-E strictly first; CU-F parallel-eligible; CU-G and CU-H after CU-E;
   CU-I last.** CU-E precedes CU-G/CU-I because the second-run corpus and literal-writer
   it establishes is the context the other units' auto_evolve tests build on; CU-I last
   because its loop boundary wraps code CU-E/CU-G have just settled. CU-F touches no file
   any other unit modifies and can proceed in parallel with everything.
4. **Slip designation: CU-I first, then CU-H.** If the cycle cannot fit all five, CU-I
   (lowest score of the batch, 20; largest surface) slips first and CU-H second — its
   vector is the local operator's own CLI, so exploitability trails the crash/loss/drop
   certainties. Must-lands are CU-E, CU-F, CU-G (the two 24-score certainties plus the
   only data-deletion defect). A slip is recorded, not silent — the unit returns to the
   head of the next batch.
5. **Dirty state is preserved, not absorbed.** The cycle-1 batch is the dominant new
   inventory fact versus cycle 1's request: overlap detection must treat its hunks as
   settled context, and any cycle-2 changeset that also rewraps or reverts them mixes two
   authorized batches. CU-G fixing defects inside cycle-1 code is new work layered on top
   — the request says so explicitly so it is not mistaken for a cycle-1 revision.
6. **Runtime state and host are off-limits.** `data/`, `*.sqlite`, `backups/`, `logs/`
   are live plugin state; verification happens in scratch temp dirs exactly as the
   assessment reproducers already do. CU-H specifically must never touch the real
   `~/.config/systemd/user` (the assessment demonstrated the scratch pattern and verified
   the real directory clean afterward).
7. **No topology chosen.** Branch names, worktree layout, and commit sequencing are
   absent from the request by design; `branch`/`head`/`uncommitted_baseline` appear only
   as current-state facts the conductor inventories against.
