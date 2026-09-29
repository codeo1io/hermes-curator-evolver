# Cycle 11 compounding — learnings and prevention rules

Run `3d4c7adfe6a0412da0708d5a254f217c` (campaign cycle 1 of goal 134d4f57) · compounding attempt
`71912fb7f1b642a09f6895eb7e5b864a`
Written 2026-09-30 from PRE-REVIEW cycle evidence only (assess, research, roadmap, prioritize
b983684a, stewardship, implement 98647de9, targeted_tests 47a75087, full_tests d1b456e4
outcomes). Review and ship outcomes are next cycle's assessment inputs, per phase order.

Numbering is final on main's chain: cycle-10's fold renumbered its doc to L43-L51
(next-free pointer U95 / KTD47 / L52 at the 2026-09-30 extension), so this cycle allocates
**L52-L55**. Next free after this doc: **U105 / KTD49 / L56**.

Base: main `db9234cb86efe63350252086d8bd686d2a55923d` (post-cycle-10 integration). Batch
(prioritize b983684a, KTD44 lineage): U87 + U95 + U96 + U97.

## What the cycle produced (evidence recap)

- Assess `29f16b72`: full fresh read of all 21 package modules + plugin shim + config surfaces;
  live probe battery (`/tmp/assess-29f16b72/probes.py`, Python 3.11 direct import); suite
  476/476 in an ephemeral uv env; 7 fresh findings (3 MEDIUM / 4 LOW) + 1 info, all deduped
  against assessment passes 1-8 and the 2002-line roadmap.
- Research `491ec50b`: six axes refreshed 2026-09-29 — upstream zero drift (fork point
  `45328db` == upstream/main tip; sole open issue #12 = U87's independent corroboration),
  host +5 commits (observer-hooks v1, ~27-hook roster; gitleaks secrets authority), index
  101,156 (+564/6d), SkillClaw decelerating, new entrant skillhex, dep floors (sentence-
  transformers 3 majors stale, never gate-exercised). Six candidates C1-C6 → roadmap U95-U104.
- Roadmap `fe6e3dfb`: extension "2026-09-30 - maintenance cycle 11", +263 lines, units
  U95-U104 + KTD47/KTD48, prefix 34a2bff8 intact → post-image 64f285d5 (2265 lines).
- Implement `98647de9`: U87 impact module + storage read API + CLI + README; U95 hygiene
  family table (KTD47); U96 drill `mode=ro&immutable=1` + evidence-root containment (U94
  parity refusal); U97 prose vocabulary (corpus 58→66). Full suite 476→**521 passed**;
  ruff delta-clean vs 13 pre-existing baseline findings.
- Validation (recorded outcomes, not re-run here): targeted_tests engine runner exit 0,
  **477 tests** across its 14-file impact-derived set; full_tests engine full_command →
  ephemeral cloud-CI **PR #14** (commit `776528617895`, Actions run 36629513668): Python
  tests (3.12) + Lint (ruff count ceiling) both SUCCESS, PR file list == the 12-file batch
  (+1291/−9), PR closed by the script as ephemeral teardown.

## Reusable lessons / prevention rules

- **L52 (probe-absence rule)**: a probe that returns zero hits is not evidence of absence
  unless the probe payload itself can satisfy the pattern under test. The assess F1 probe
  fed a 58-char fake `github_pat_…` token to a `{82}` quantifier — 0 hits was guaranteed by
  construction, and "the arm is unshipped" survived three phases on that foundation while
  the arm shipped all along (`hygiene.py:37`, blob md5 `dcee9610…` = the WITH-arm file).
  Prevention: before trusting a negative probe, assert the probe could have matched
  (`re.fullmatch` the payload against the pattern, or length-check it); and settle
  presence claims by grepping the blob for the pattern's literal prefix, never by probe
  zero alone. A probe that cannot fail on the broken tree validates by construction
  (cycle-7 L18's rule, now double-instantiated).
- **L53 (hashing-is-not-reading)**: blob-identity hashing (md5/sha across worktree,
  canonical checkout, `git show <tree>:<path>`) proves only that the bytes are identical,
  not what those bytes say. The stewardship phase triple-verified md5 `dcee9610` and still
  recorded the wrong verdict twice (arm "absent"), because the verdict's content claim was
  never tested — only its identity claim. Prevention: a content verdict ("X ships at
  line N") must cite the discriminating check that could have failed —
  `git show <tree>:<path> | grep -c 'github_pat_'` — alongside any identity hash. Identity
  hashes answer "did the file change"; they never answer "what does the file contain".
- **L54 (read-open side effects on SQLite/WAL)**: a `mode=ro` connection to a quiescent
  WAL database materializes `-shm`/`-wal` companion files that a read-only closer cannot
  checkpoint (db bytes stay unchanged; the next write-mode close removes them). It is a
  durable observable side effect from a path that presents as a benign touch — exactly
  assess F2's shape. `immutable=1` materializes nothing and is correct for owned quiescent
  snapshots (U96's drill probe), but must never be the default read mode on a live store:
  it can skip a hot `-wal`'s committed frames. Prevention: any "this read is side-effect
  free" claim needs a directory-listing probe before/after on a quiescent WAL fixture, and
  the open mode is chosen by store liveness — `mode=ro` for live, `mode=ro&immutable=1`
  for owned snapshots. (The impact CLI inherits this: its disclosed residue on quiescent
  dbs self-heals at the next writer; an `--immutable` flag is a cheap future rider.)
- **L55 (verifiable-verdict rule)**: a "verified" claim must carry the exact command and
  the discriminating literal that could have failed it. This cycle's costliest loop was
  two consecutive phases recording contradictory triple-verified verdicts about the same
  bytes, both citing only an md5 — evidence that could not detect the error it was cited
  for. The loop ended the moment the decisive one-liner ran (blob grep = 1). Prevention:
  when recording a verification, ask "what output would have proven me wrong?" and cite
  that command's output; if nothing in the citation could have failed, the verification
  did not happen. (This generalizes L52/L53 from probes and hashes to all verdicts.)

## Prevention hooks landed in code this cycle

- U95's family table makes the spec↔ship divergence class structurally harder: every
  family is a table entry with a graduated probe pair (positive through scrub AND the
  `skill_validate` publish gate), so a missing family fails a named test instead of
  surfacing as prose divergence (KTD47's intent).
- U96's `mode=ro&immutable=1` drill open and the U94-parity refusal string pin the
  read-only contract: the drill's own test now fails if the probe ever materializes WAL
  companions or accepts an out-of-root `db_path`.
- U87's KTD43 dry-run pin (db sha256 unchanged) is a standing guard for every future
  impact-CLI edit.

## Inherited context for the next cycle

- Cycle-12 flagship candidate: U98+U69 (observer-hook ingestion + skill-lifecycle), with
  KTD48 (observer-hook storage policy, PROPOSED) decided first; alternates U103/U88/U104;
  U83 (merge-check consumes U87's report) follows U87.
- KTD40 ledger: streak 4/30 at the 2026-09-29 observation (101,156 skills, PR #101237
  open); re-observe ~2026-10-05; ungate only via stewardship amendment.
- Review fold should carry: the F1 corrective note (already recorded in the roadmap
  outcome section), unit status flips for U87/U95/U96/U97, and the commit-gate citation
  for THIS file (`docs/learnings/2026-09-30-cycle-11-compounding.md` — the cycle-6 L21
  dangling-citation lesson applies verbatim).
- Engine note (outside the repo's concern, but it shaped evidence): full_tests on this
  public repo routes through an ephemeral GitHub CI PR that the script creates, validates,
  and closes itself — PR #14's file list is the authoritative statement of the batch tree,
  and its Actions run is the authoritative gate result.

## Review-fix postscript (2026-09-30, attempt ca62b53d)

The independent review (6c88622e, verdict NEEDS_CHANGES, 8 findings) found two
medium defects that were invisible to a green suite, both now fixed and pinned
discriminatorily:

- The curl arm's joiner class lacked `:`, so curl's canonical `curl: (7)` output
  misclassified as success — and the corpus pins carried other arms, so they stayed
  green with the arm deleted. L52's probe rule generalizes: a pin that cannot fail
  when its arm is removed is not a pin. Every new arm now ships with a
  discriminating pin (an input where that arm is the only thing that can fail).
- The KTD43 "no writes of any kind" contract was false on the missing-store path
  (`EvidenceStore.__init__` mkdir+init_db) while every test seeded an existing
  store. L55's verifiable-verdict rule generalizes: an absence claim ("never
  writes") needs a test of the absent case, not just the present one —
  `test_missing_store_not_created_and_reported` pins file, parent-dir, and
  sidecar absence before and after.

Findings 3-8 (gh-prefix `{36,}` + `gha_`, publish-gate PAT pin, literal `5xx` with
symmetric answers, refusal-string shape-parity wording, outcome-section claim
corrections, markdown cell escaping) folded alongside; full record in the roadmap's
"Review fix 2026-09-30" block. Next-free identifiers unchanged: U105 / KTD49 / L56.
