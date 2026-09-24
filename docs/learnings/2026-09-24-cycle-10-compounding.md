# Cycle 10 compounding — learnings and prevention rules

> **Integration renumber note (2026-09-24, roadmap “Integration fold 2026-09-24 - run cf968161 onto main”):** merged onto main, whose learnings chain already holds L1–L14 (cycle 6), L15 (roadmap KTD31 format-matrix rule), L16–L21 (cycle 7), L22–L28 (cycle 8), L29–L34 (cycle 9) and L35–L42 (the 3ed5d14a integration fold), so this doc’s nine rules renumber: L1→L43, L2→L44, L3→L45, L4→L46, L5→L47, L6→L48, L7→L49, L8→L50, L9→L51. The headers below keep their original (void) numbers as written; cite them by the new identities. Unit/decision numbering is unaffected (U85–U89 / KTD42–KTD45 stand; next free U95 / KTD47).

> **Review-fix postscript (2026-09-24, added at integration):** the evidence recap below records the pre-review snapshot (“corpus 54 records / 54/54 sane”, “414 tests collected”). The shipped review-fixed batch state is 58 corpus records (58/58 sane, 0 deviations) and 470 tests collected — validated by ephemeral cloud-CI Actions run 35893182773 (Python tests 3.12 + ruff ceiling, both SUCCESS) on a tree blob-identical to ship commit 8b8fc23d, and by ship PR #11 CI run 35896350879. The final-review verdict was PASS_WITH_FINDINGS (0 MEDIUM / 4 LOW / 2 INFO), all prior-round MEDIUM findings confirmed fixed and pinned.

Run cf968161814b40d7ad4d5760446a4cd6 · compounding attempt a2f0be731b404a18b2774204c18e4018
Written 2026-09-24 from PRE-REVIEW cycle evidence only (assess pass 7, research, roadmap, prioritize
KTD44, stewardship, implement, targeted_tests, full_tests outcomes). Review and ship outcomes are
next cycle's assessment inputs, per phase order.

Base: stale a76962c -> origin/main 27487cd (U85). Batch (KTD44): U85 + U86 + U88.

## What the cycle produced (evidence recap)

- U85 base refresh: worktree branch had 0 own commits -> reset --hard origin/main; both dirty
  artifacts (roadmap cycle-10 extension, pass-7 assessment) carried byte-intact (sha 516dd598…
  verified on restore); canonical checkout switched fix/maintenance-cycles-1-5 -> main, ff-only to
  27487cd, parked untracked docs/learnings/2026-09-02-cycle-6-compounding.md preserved.
- U86 classifier vocabulary widening: hermes_curator_evolver/candidates.py, 5 hunks — keyword arms
  (`errors?:` prefix, `exited? N`, `timed[-\s_]*out`, `permission denied`, `failing`), count verbs
  `failed|failing|errors?` with interposed-noun binding, count-pattern entry gate, symmetric
  success phrases, structured `timed_out`/`permission_denied` statuses. Pinned: tests/test_candidates.py
  U86 section + scripts/repro-pass7.py F86 records (corpus 48 -> 54).
- U88: docs/ideation/2026-09-23-cycle-10-extension-research.md (six ranked candidates, dispositions,
  competitor table, moat statement).
- Validation (recorded outcomes, not re-run here): targeted pytest EXIT=0 over the dispatch surface
  list; corpus 54/54 sane 0 deviations; ruff 16 flat (ceiling 79); full_tests via engine
  full_command -> ephemeral cloud-CI PR #9 (commit 2d530e6ee7bd, branch conductor/ci-2d530e6ee7bd,
  Actions run 35888011758): Python tests (3.12) + Lint both SUCCESS; PR file list == the 6-file
  batch exactly. 414 tests collected (roadmap's 410 estimate corrected).

## Reusable lessons / prevention rules

- L1 (regex boundary rule): a keyword arm ending in a NON-WORD character (``errors?:``) cannot sit
  inside a `\b(...)\b` group — the trailing `\b` between `:` and whitespace never matches. Place
  such arms outside the group with their own leading `\b`. Cost us one probe iteration; now
  documented in candidates.py at the pattern.
- L2 (symmetric-success discipline): every failure-arm widening needs (a) its symmetric success
  phrases (`no tests failing`, `no parse errors` joining the `no … failed` family) and (b) KTD35
  positional-rule pins. Widening verbs without widening the success-answer family silently flips
  success narratives to failure — our probe harness caught exactly that in iteration 2.
- L3 (entry gates): count-only clauses (`2 errors`, `4 validation errors`) carry no keyword, so a
  keyword-gated scan never sees them; nonzero counts are self-evidencing and must gate entry
  themselves, while zero-only counts still resolve to the success answer (`0 errors` never fails).
- L4 (probe-first vocabulary work): iterating with a two-set probe (MISS set = phrasings that must
  flip, CTRL set = controls that must hold) found 3 self-inflicted regressions across 3 iterations
  before any test file was touched. Write the probe before the arm.
- L5 (dirty-worktree base refresh): before any rebase, prove the branch has 0 own commits
  (`git log origin/main..HEAD` empty), back up dirty artifacts to /tmp, reset --hard, restore, and
  sha-verify the restore. Canonical refresh via branch-switch + ff-only preserves untracked files.
- L6 (pytest collection semantics as free coverage): passing SOURCE modules and scripts/repro-pass7.py
  as pytest args imports them at collection — the corpus harness runs at collection time, and any
  deviation fails with a collection error. Exit 0 on such a command is genuine corpus coverage.
- L7 (ephemeral cloud-CI full validation): the engine's github_ci_validate.py performs commit + PR +
  CI + close itself in an ephemeral clone; the local worktree stays untouched (byte-identity proof:
  HEAD + git status + 3 file shas identical pre/post). Verify the validated tree by diffing the PR
  file list against the intended batch — it matched all 6 files exactly.
- L8 (gh default-repo trap): `gh pr view N` without `-R` resolved the WRONG repository's PR #9 and
  nearly caused a false triage. Always pass `-R codeo1io/hermes-curator-evolver` in this fleet.
- L9 (append-only race protocol, second proof): the prioritize phase's assert-pre-image-first
  discipline fired on an engine-side fold (91d4c0e9 -> 123d50a4) BEFORE any byte was written;
  re-hash + prefix-verify + re-append onto the moved pre-image is the complete recovery. Never
  force-write over a moved pre-image.

## Status ledger for the next cycle

- U85 DONE (pre-review evidence above). U86 DONE, corpus 54 records, expect 54/54 on re-run.
  U88 DONE (ideation doc written). U89 NOT pulled in — pull-in criteria include the full
  3.11+3.12 matrix; PR lane ran 3.12 only, the 3.11 leg fires on push-to-main at ship — the
  merge-release stage must confirm it (u45/u82 load-marginals, project memory #5350).
- U87 (dependency-aware impact analysis, upstream issue #12 spec) = cycle-11 ANCHOR per KTD44;
  its evidence base is docs/ideation/2026-09-23-cycle-10-extension-research.md R1.
- Pass-7 F6-F11 lows: verify-only on the 27487cd base (they were derived on a76962c); re-derive
  before scheduling any as units.
- Pass-7 F2/F3/F5: already fixed by the upstream merges U85 pulled in — verify presence locally,
  never re-fix.
- U62 ledger 3/30 (research pass); next observation ~2026-10-05. R5 (one-shot-run signal) needs a
  state.db run-mode design probe before any unit is scheduled.
- Roadmap append chain (pre-review): … 6f014c28 -> 91d4c0e9 -> (engine fold) 123d50a4 ->
  516dd598 -> this cycle's compounding append (post-image recorded in the phase result).

## Cited paths (commit-gate: every path must exist in the shipped tree)

hermes_curator_evolver/candidates.py · tests/test_candidates.py · scripts/repro-pass7.py ·
docs/ideation/2026-09-23-cycle-10-extension-research.md · docs/assessment/2026-09-23-adversarial-repository-assessment-pass7.md ·
docs/learnings/2026-09-24-cycle-10-compounding.md · .hermes/plans/autonomy-prop_8c5390ffe26640fa.md
Known-dangle disclosure: docs/learnings/2026-09-02-cycle-6-compounding.md (cited above for the U85
preservation note) exists only UNTRACKED in the canonical checkout — the documented cycle-6
dangling citation (project memory #5351). Committing it alongside this cycle's ship commit would
close that historical dangle; until then this citation resolves only outside this worktree.
External refs: PR https://github.com/codeo1io/hermes-curator-evolver/pull/9 ·
Actions run 35888011758 · upstream issue pingchesu/hermes-curator-evolver#12.
