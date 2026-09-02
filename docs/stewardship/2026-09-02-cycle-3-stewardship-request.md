---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-3-stewardship-request
run: 682bd7e431e34f7b9efc0c881cde253a
phase: stewardship
attempt: a4ad7f0a2e7f4c2fa829295eea5e6516
attempt-history:
  - a4ad7f0a2e7f4c2fa829295eea5e6516 - original; written against the current tree with inventory re-checked live this session (HEAD/branch/worktree/remotes/status below) and the pytest baseline re-run green (174 passed in 7.98s)
  - d4b6dfdc88bd4e4eaa54b41cad66c96f - re-issue; zero drift verified (HEAD 45328db / branch main / single worktree / 11 modified files at exactly 833 insertions unchanged; find -newer artifact returns no source files; no conductor topology work; git branch/worktree show main only), all change-unit anchors re-checked live and still open (pattern.sub(block,...) count=1; storage busy_timeout/journal_mode grep=0; _looks_like_error:113 with private markers :128; cli `or 5` present; _systemd_quote :190), pytest re-run green (174 passed in 7.43s); JSON body untouched since the original attempt
  - 2c31c2f81ffc4b30b206efcfd4d59651 - re-issue; zero drift verified again (same HEAD/branch/single-worktree, 11 files / 833 insertions identical, find -newer returns 0 source files), all five grep anchors still open (pattern.sub count=1; busy_timeout/journal_mode=0; _looks_like_error=1; cli 'or 5'=1; _systemd_quote=1), pytest re-run green (174 passed in 7.31s); JSON body untouched; request re-affirmed as authoritative
skill: ce-plan (change-request description; router has no stewardship skill - ce-handoff rejected as session continuity, ce-work/ce-worktree rejected as topology choice this phase must NOT make; same route and reasoning as the fleet's two prior stewardship phases)
upstream: docs/prioritization/2026-09-02-cycle-3-batch.md (selected batch U15+U7a+U16+U17+U18+U26+U28)
---

# Stewardship request — cycle 3 reliability batch

This document describes the selected maintenance batch for the conductor to steward. It
deliberately does **not** choose Git topology: no branch names, no worktree layout, no
commit sequencing. Those are the conductor's to plan after inventorying the repository,
detecting overlap, splitting unrelated concerns, and preserving dirty state.

**The dominant inventory fact is unchanged from cycle 2's request, and must be stated
again because cycle 2's batch never landed:** the working tree still carries the
cycle-1 implementation batch uncommitted — 11 modified files
(`hermes_curator_evolver/{auto_evolve,backfill,candidates,cli,guarded_apply,storage}.py`
+ 5 test files, exactly 833 insertions, re-verified this session) — and NO cycle-2 work
has been applied on top (every cycle-2 defect was re-verified open this session by the
cycle-3 prioritize phase). Five of this batch's seven units (CU-J, CU-L, CU-M, CU-N,
CU-O) fix defects that live partly **inside** those uncommitted cycle-1 hunks; that is
new work layered on top, never a revision of cycle-1 intent, and the disposition of the
dirty state belongs to the commit gate.

```json
{
  "stewardship_request": {
    "title": "hermes-curator-evolver reliability batch (cycle 3): managed-block replacement safety, storage lock resilience, numeric-flag contract, scheduler unit hardening, apply-loop resilience, single error classifier, rerank oversampling",
    "summary": "Seven packets, one property: an unattended run must never crash, never drop evidence, never delete the wrong thing, never corrupt the evidence record, never silently cap the reranker, and must always emit a report (KTD12: this precedes all extensions). CU-J fixes the re.sub replacement-template defect - pattern.sub(block, ...) at auto_evolve.py:386 feeds evidence-derived text in as a template, so any skill that already carries a managed block (every skill the plugin has touched) plus a preview containing \\1 crashes the auto-run with exit 1 and NO report (pass-3 R1: IndexError 'unknown group name') - via a lambda replacement and preview neutralization, closing the T18 coverage hole. CU-K makes evidence persistence survive concurrent writers: storage.py:154 connect() is bare (no timeout/WAL/busy_timeout; hooks open a store per event), so a 5.01s lock blocks each hook, logs a warning, and drops the event (B10; corroborated upstream by NousResearch/hermes-agent#101035). CU-L repairs the numeric-flag contract: help says '0 disables pruning' but cli.py:786/803's int(x or 5) coerces explicit 0 to 5 while the API's keep=0 guard deletes every auto reference including the one the same apply wrote (pass-3 R3), and the landed test asserts the delete-all (tests/test_auto_evolve.py:1106). CU-M closes scheduler unit injection: --schedule reaches OnCalendar= (auto_evolve.py:1386) unvalidated - a newline writes a second [Service]/ExecStart= section - and _systemd_quote (:190) never escapes % so systemd specifiers rewrite ExecStart paths. CU-N gives the run loop a per-candidate error boundary (auto_evolve.py:1479, three try: in the whole file today), moves support-file writes inside the guarded transaction with checked manifest registration, and makes target writes atomic (temp+rename) in guarded_apply.py. CU-O unifies the error classifier: storage._looks_like_error (storage.py:113-128) carries its own keyword corpus that marks '3 passed, no errors found' as an error (pass-3 R2) while candidates._is_tool_failure correctly says False - every such row corrupts error_events, which gate auto-evolve thresholds and future U24 cohorts; the private classifier is deleted or delegated onto the single structured-first one. CU-P fixes rerank recall: semantic.py truncates to top-limit BEFORE rerank pairs are built, so --rerank-candidates can never promote a below-fold skill (pass-3 R4) - oversample, rerank, then truncate. All seven are verified by existing mechanical reproducers plus targeted tests; no user-visible default changes, no new features, no model dependencies.",
    "repository_candidate": {
      "name": "hermes-curator-evolver",
      "path": "/work/projects/hermes-curator-evolver",
      "remote": "git@github.com:codeo1io/hermes-curator-evolver.git",
      "remote_role": "push target is the 'fork' remote (codeo1io); 'origin' (pingchesu/hermes-curator-evolver) is upstream and must never be pushed to, per the roadmap's Repository remote section",
      "branch": "main",
      "head": "45328db04c188dd4d8734e31c8b85f2d84f6358b",
      "committed_tree": [".github", ".gitignore", "CONTRIBUTING.md", "LICENSE", "README.md", "__init__.py", "docs", "examples", "hermes_curator_evolver", "plugin.yaml", "pyproject.toml", "tests"],
      "uncommitted_baseline": "11 modified files carrying the cycle-1 batch (U1-U4) - hermes_curator_evolver/{auto_evolve,backfill,candidates,cli,guarded_apply,storage}.py and tests/{test_auto_evolve,test_backfill_sessions,test_candidates,test_guarded_apply,test_storage}.py, 833 insertions, pytest 174 passed in 7.98s re-run this session. Cycle-2 work is absent on top; all line anchors in this request were verified against the CURRENT tree (with the cycle-1 edits), not HEAD.",
      "rationale": "All seven packets are this repository's own Python package and tests; no second repository is involved. The tree is NOT clean - see preexisting_dirty_state_to_preserve; overlap detection must treat the cycle-1 hunks as settled context and the conductor's inventory must also expect SEVEN new untracked phase-artifact directories (see below), none of which any unit may touch. Every defect reproduces inside this tree with scratch temp dirs; no host mutation is required."
    },
    "change_units": [
      {
        "id": "CU-J",
        "packet": "U15",
        "title": "Managed-block replacement safety (literal block, neutralized previews, second-run regression)",
        "surfaces": [
          "hermes_curator_evolver/auto_evolve.py (modify: block-writer sub at :386 - lambda replacement so evidence text is never a template; preview neutralization for content entering managed blocks ~:323-333 - strip control characters, remove plugin markers, bound length)",
          "tests/test_auto_evolve.py (add: second-run corpus - skills that ALREADY carry a managed block, previews containing \\1, \\g<0>, newline, and an embedded auto:end marker)",
          "tests/test_candidates.py (adjacent only: neutralizer exercised through the candidate path; separate hunks)"
        ],
        "must_land_before": ["CU-N"],
        "rationale": "The only guaranteed steady-state crash on the board (score 24): any skill the plugin has ever touched carries a managed block, and any preview with a backreference kills the run with no report - 174 green tests never see it because none starts pre-blocked (T18). Re-verified live this session by the prioritize phase (pattern.sub(block, ...) confirmed at :386). The neutralizer is also the substrate U21 reuses next cycle. Discharges B7. Evidence: pass-3 R1 one-shot -> after fix, exit 0 + valid report JSON + literal block; repro corpus /tmp/assess/ce-assess-76416fd2/repro_autorun_crash.py; new second-run tests green."
      },
      {
        "id": "CU-K",
        "packet": "U7a",
        "title": "Storage lock resilience: WAL, busy_timeout, bounded retry",
        "surfaces": [
          "hermes_curator_evolver/storage.py (modify: connect() at :154 only - journal_mode=WAL, busy_timeout, bounded retry; no ingest-path changes - CU-O owns those lines)",
          "hermes_curator_evolver/hooks.py (modify: error handling around per-event store opens)",
          "tests/test_storage.py (add: concurrency test - repro_h4_lock_drop.py shape)"
        ],
        "must_land_before": [],
        "rationale": "The other certainty (score 24) and the batch's only unrecoverable-input loss: under any concurrent writer every hook currently blocks 5.01s and drops its event (0 of 3 recorded, cycle-2 reproduction; bare connect re-verified live this session). KTD8 pulled exactly this item forward as blocking; upstream #101035 reports the same class. Smallest high-impact change in the batch. Shares storage.py with CU-O in DISJOINT functions - separate hunks, no shared edit. Discharges B10. Evidence: repro_h4_lock_drop.py -> all events recorded, no unbounded stalls; targeted pytest on storage + hooks."
      },
      {
        "id": "CU-L",
        "packet": "U16",
        "title": "Numeric-flag contract repair: explicit zeros honored, prune-0 disables",
        "surfaces": [
          "hermes_curator_evolver/cli.py (modify: parse-explicit 0 at :786/:803 for --max-reference-files, --max-skills, --min-evidence, --variants - int(x or 5) never swallows an explicit 0)",
          "hermes_curator_evolver/auto_evolve.py (modify: prune guard so keep=0 disables pruning rather than deleting everything)",
          "tests/test_auto_evolve.py (REPLACE the assertion at :1106 - it currently codifies the delete-all bug)"
        ],
        "must_land_before": [],
        "rationale": "The batch's only data-deletion defect and a KTD9 precedent: help, code, and test disagree today (pass-3 R3 re-verified the 0->5 coercion live). Fixes defects inside the uncommitted cycle-1 code - new work on top, not a cycle-1 revision. The :1106 replacement belongs to this unit and nobody else. Discharges B8. Evidence: R3 one-shot -> 0 reaches config unchanged, keep=0 prunes nothing; targeted pytest on auto_evolve + cli tests."
      },
      {
        "id": "CU-M",
        "packet": "U17",
        "title": "Scheduler unit hardening: schedule validation and %% escaping",
        "surfaces": [
          "hermes_curator_evolver/auto_evolve.py (modify: _systemd_quote at :190 - escape %; OnCalendar= interpolation at :1386 - validate schedule, reject embedded newlines/control characters)",
          "tests/test_auto_evolve.py (add: unit-content tests - newline and % specifiers rejected/escaped)"
        ],
        "must_land_before": [],
        "rationale": "The security item (score 21): --schedule becomes arbitrary systemd unit-file injection today (a newline writes a second [Service]/ExecStart= section, reproduced in cycle 2; _systemd_quote and OnCalendar anchors re-verified live this session). Same external-data-into-second-interpreter root cause as CU-J, which is why the batch is coherent rather than a grab-bag. Vector is the local operator's CLI, so it never slips ahead of the certainties. Discharges B9. Evidence: repro_h3_systemd.py -> newline rejected, no file written, %% present for %-bearing paths; scratch XDG_CONFIG_HOME only."
      },
      {
        "id": "CU-N",
        "packet": "U18",
        "title": "Apply-loop resilience: per-candidate boundary, transactional support files, atomic writes",
        "surfaces": [
          "hermes_curator_evolver/auto_evolve.py (modify: candidate loop at :1479 - per-candidate try/except recording failed:<class> and continuing, report always emitted; support-file ordering - written before/within verification, size-bounded, register_support_file_in_manifest return checked)",
          "hermes_curator_evolver/guarded_apply.py (modify: target writes atomic - temp+rename; CU-N owns this file for the cycle)",
          "tests/test_guarded_apply.py + tests/test_auto_evolve.py (add: interruption + boundary fixtures)"
        ],
        "must_land_before": [],
        "rationale": "Completes the always-report guarantee as a tested property (cycle-2 reproduction: one bad skill aborts the pass with no report). Landing last wraps code CU-J/CU-L have settled; owning guarded_apply.py outright is WHY U27 is out of this batch - the rollback-default work in :486-501 must not ride, per the prioritize phase's contention call. Every extension inherits the boundary. Discharges B11. Evidence: repro_m12_no_report.py -> exit 0, report emitted, failed candidate counted, survivor applied."
      },
      {
        "id": "CU-O",
        "packet": "U28",
        "title": "One error classifier, one source of truth",
        "surfaces": [
          "hermes_curator_evolver/storage.py (modify: _looks_like_error at :113-128 deleted or delegated onto the candidates-side structured-first classifier; keyword corpus moves to the single module)",
          "hermes_curator_evolver/candidates.py (touch: classifier becomes the shared importable function - signature-compatible for both call sites)",
          "tests/test_storage.py + tests/test_candidates.py (extend: U2's adversarial corpus test covers the ingest path)"
        ],
        "must_land_before": [],
        "rationale": "The batch's data-corruption packet (score 21): today '3 passed, no errors found' persists as is_error=1 (pass-3 R2, markers re-verified live at :113-128), and those rows gate auto-evolve thresholds and are exactly what U24 will mine - corrupted input now is corrupted cohorts later. Deletes a two-source-truth problem in the same shape as CU-L's contract repair. Shares storage.py with CU-K in disjoint functions (connect :154 vs ingest :113) - separate hunks. Discharges B15. Evidence: R2 one-shot -> is_error=0; stored-DB fixture with keyword-bearing success strings yields zero error_events rows; both test modules green."
      },
      {
        "id": "CU-P",
        "packet": "U26",
        "title": "Rerank oversampling: recall below the embedding fold",
        "surfaces": [
          "hermes_curator_evolver/semantic.py (modify: candidate selection at ~:246 - oversample the embedding top-k (min(5x limit, all)) before rerank pair construction; truncate to limit only AFTER rerank; no-rerank path unchanged)",
          "tests/test_semantic.py (add: below-fold fixture - best skill embeds past the limit but reranks first; selected after fix)"
        ],
        "must_land_before": [],
        "rationale": "Converts an advertised flag from silently capped to real (score 19): --rerank-candidates currently cannot promote anything the embedder ranked below the limit, so it mostly reorders the slice the embedder already chose (pass-3 R4). semantic.py is touched by NO other unit - fully parallel. Must not grow into U8's dedupe semantic rider. Discharges B13. Evidence: R4 source-order check inverted by the below-fold pytest; lexical-only path byte-identical behavior asserted."
      }
    ],
    "preexisting_dirty_state_to_preserve": [
      "THE CYCLE-1 BATCH (uncommitted, 11 modified files, 833 insertions): hermes_curator_evolver/{auto_evolve,backfill,candidates,cli,guarded_apply,storage}.py + tests/{test_auto_evolve,test_backfill_sessions,test_candidates,test_guarded_apply,test_storage}.py. Authorized prior output implementing U1-U4; pytest 174 passed re-run this session. Must NOT be absorbed into, reverted by, or reformatted by any cycle-3 unit; disposition is the commit gate's. CU-L and CU-O intentionally FIX defects inside it (new work on top, not modification of its intent).",
      "Untracked phase artifacts, none of which any unit edits: docs/assessment/ (three adversarial assessments), docs/ideation/ (cycle-2 and cycle-3 research), docs/prioritization/ (three batch selections), docs/stewardship/ (two prior requests + this file), and .hermes/plans/autonomy-prop_8c5390ffe26640fa.md (the configured roadmap - founding proposal plus three append-only extensions, the cycle-3 one verified byte-identical-prefix by pre-image sha256 this run).",
      "data/, *.sqlite, backups/ - gitignored plugin runtime state (evidence DBs, session imports, skill backups). No unit mutates or commits these; all verification happens in scratch temp dirs exactly as the reproducers do.",
      "logs/, .pytest_cache/, __pycache__/, .ruff_cache/ - untracked runtime/caches; leave as-is."
    ],
    "must_remain_separate": [
      "U27 (rollback target-root default) was sequenced onto this batch by the roadmap but HELD by the prioritize phase on file contention: its guarded_apply.py:486-501 surface overlaps CU-N's atomic-write work - the exact hazard cycle 2 named dropping U5. CU-N must not 'while we're in there' also constrain rollback roots; U27 heads batch 2.",
      "U19 (identity/dedup unification), U20 (P3 hygiene), U25 (candidates-decide) are batch 2's head; nothing here may fold them in - including the tempting one-line cutoff fix in report paths CU-J's tests pass through.",
      "U12 and U21-U34 extensions are KTD7/KTD12-gated behind this batch: no trust-interop, publish-safety, ledger, telemetry, doctor, circuit-breaker, or fleet work may ride - even though U21 would reuse CU-J's neutralizer and U29's ledger was verified live on this host.",
      "CU-P changes only the rerank path's candidate pool; it must not absorb U8's dedupe scan or any embedding-model option (U7's semantic rider).",
      "CU-K changes only the connect site and hook error path; U7b (version single-sourcing) and U7c (CI lint/type gates) stay out.",
      "CU-O deletes or delegates exactly one function; it must not rewrite the storage schema, retention (U23), or the sqlite robustness items CU-K owns.",
      "tests/test_auto_evolve.py:1106's replacement belongs to CU-L and to nobody else; it must not be 'fixed' incidentally by CU-J's or CU-N's test additions.",
      "CU-M's verification must never install, start, or overwrite a real user unit: scratch XDG_CONFIG_HOME only (the assessment's repro_h3_systemd.py demonstrates the pattern; real ~/.config/systemd/user verified untouched after that run).",
      "The cycle-1 dirty hunks are context, not cargo: any cycle-3 changeset that also lands, rewraps, or reverts cycle-1 edits mixes two authorized batches - the conductor's overlap detection should flag that, and the commit gate owns the sequencing decision.",
      "The founding Acceptance contract governs topology-neutral constraints: feature branch off the current default branch, targeted tests for changed surfaces (never the full suite as the gate), push to 'fork' only, no upstream merge - but which branches/worktrees realize that is the conductor's choice, not this request's.",
      "No host-side mutation outside the repository: no Hermes config changes, no skill-directory writes, no ledger writes (U30 is a later, explicitly gated packet), no timer installs. Every unit is package code plus tests, verified against scratch fixtures."
    ],
    "verification_protocol": {
      "per_unit": [
        "CU-J: R1 one-shot -> exit 0 + valid report JSON + literal block; repro_misc2.py -> no marker imbalance; python3 -m pytest tests/test_auto_evolve.py -q (second-run corpus green)",
        "CU-K: repro_h4_lock_drop.py -> 3 of 3 recorded under a concurrent writer; python3 -m pytest tests/test_storage.py tests/test_hooks.py -q (hooks test file if absent: storage-level concurrency test + hooks error-path unit)",
        "CU-L: R3 one-shot -> keep=0 prunes nothing, 0 reaches config; python3 -m pytest tests/test_auto_evolve.py tests/test_cli*.py -q (or the CLI config test module that exists)",
        "CU-M: repro_h3_systemd.py -> newline schedule rejected, no file written, %% present for %-bearing path; python3 -m pytest tests/test_auto_evolve.py -q (unit-content tests)",
        "CU-N: repro_m12_no_report.py -> exit 0, report emitted, failed candidate counted; python3 -m pytest tests/test_guarded_apply.py tests/test_auto_evolve.py -q (interruption + boundary fixtures)",
        "CU-O: R2 one-shot -> is_error=0 for '3 passed, no errors found'; python3 -m pytest tests/test_storage.py tests/test_candidates.py -q (adversarial corpus on the ingest path)",
        "CU-P: R4 below-fold fixture -> below-fold best skill selected with rerank enabled; python3 -m pytest tests/test_semantic.py -q (lexical-only path unchanged)"
      ],
      "batch_gate": "Full suite green at the full-tests phase (baseline 174 passing re-run this session at this exact tree); each unit's reproducer re-run green as its completion proof recorded in its PhaseResult; no cycle-1 hunk reverted (git diff of the cycle-1 files still contains its intent after the cycle-3 edits); ruff error count not worsened from 65 (no CI gate exists yet - U7c - but the batch must not add debt); no new default behavior on any flag."
    }
  }
}
```

## Repository and change-unit decisions with rationale

1. **Single repository: hermes-curator-evolver, fork remote only.** Every packet's
   output is this repository's package and tests. `git remote -v` re-checked live this
   session: `fork` (codeo1io, push target) and `origin` (pingchesu, upstream author);
   push-to-fork-only is restated as fact, not topology.
2. **Seven change units, not one monolith.** CU-J=U15 (auto_evolve block writer +
   preview neutralizer), CU-K=U7a (storage connect + hooks), CU-L=U16 (cli parse +
   prune guard + its test replacement), CU-M=U17 (systemd quote + schedule
   validation), CU-N=U18 (candidate loop + guarded_apply atomic writes), CU-O=U28
   (storage classifier unification), CU-P=U26 (semantic oversampling). Lettering
   continues the fleet's CU-A..CU-I; no unit spans two packets.
3. **The one new intra-file overlap: storage.py carries two units.** CU-K (connect
   :154) and CU-O (ingest classifier :113-128) touch disjoint functions - the hazard
   cycle 2 flagged was same-function contention (U5/U18 in the apply path), which this
   is not - so both stay in-batch with separate-hunk discipline and an explicit
   must-not-touch contract in each unit's surfaces. The conductor's overlap detection
   should treat any hunk that mixes connect lines with classifier lines as a violation.
4. **Ordering: CU-J strictly first; CU-K, CU-O, CU-P parallel-eligible; CU-L and CU-M
   after CU-J; CU-N last.** CU-J precedes the others' auto_evolve test work because
   the second-run corpus and literal writer it establishes is their context; CU-N last
   because its loop boundary wraps code CU-J/CU-L settle, and it owns guarded_apply.py
   outright. CU-P touches a file no other unit modifies; CU-K/CU-O are disjoint within
   storage.py.
5. **Slip designation: CU-P first, then CU-N.** If the cycle cannot fit all seven:
   CU-P (lowest score, 19; opt-in rerank path, no default impact) slips first; CU-N
   (20; largest surface, and its known trigger - the R1 crash - is already fixed by
   CU-J, so slipping it loses defense-in-depth, not a certainty) slips second.
   Must-lands are CU-J and CU-K (the two 24-score certainties) plus CU-L (the only
   data-deletion defect); CU-O (21, corruption, small) is strongly preferred over any
   slip. A slip is recorded, not silent - the unit returns to the head of the next
   batch.
6. **Dirty state is preserved, not absorbed** - unchanged in substance from cycle 2's
   request, with the inventory now larger: seven untracked phase-artifact locations
   (four docs/ subdirectories plus the untracked roadmap) join the 11 modified
   cycle-1 files. CU-L and CU-O fix defects inside the cycle-1 hunks as new work on
   top, explicitly, so it is not mistaken for a cycle-1 revision.
7. **Runtime state and host are off-limits**, now including the host skill ledger:
   `~/.hermes/skills/.curator_ledger.jsonl` is live upstream state that this batch
   only ever reads for research; U30's write integration is a later, KTD13-scoped
   packet and nothing here may touch it.
8. **No topology chosen.** Branch names, worktree layout, and commit sequencing are
   absent by design; `branch`/`head`/`uncommitted_baseline` appear only as
   current-state facts the conductor inventories against (single worktree, branch
   main, verified this session).
