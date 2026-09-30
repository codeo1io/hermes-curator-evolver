# Cycle 12 compounding — learnings and prevention rules

Run `143dfd64c9fe4bee8678d49d13a1d7e0` (campaign cycle 2 of goal 134d4f57) · compounding attempt
`13743bee0fda4b42bbb44e8c416efa9e`
Written 2026-09-30 from PRE-REVIEW cycle evidence only (assess, research, roadmap, prioritize
f38c44ff, stewardship, implement 43455d65, targeted_tests 2dc57c09, full_tests d486adfe
outcomes). Review and ship outcomes are next cycle's assessment inputs, per phase order.

Numbering is final on main's chain: cycle-11's doc allocated L52-L55 (next-free pointer
U105 / KTD49 / L56 at the 2026-09-30 extension), so this cycle allocates **L56-L60**.
Next free after this doc: **U115 / KTD49 / L61**.

Base: worktree `run-143dfd64c9fe-143dfd64` at `aa93a57` (landed cycle-11 tree). Batch
(prioritize f38c44ff, stewardship 8fdcf43e): U106 + U107 + U108 + U109 + U110 + U111 + N1
rider; U105 EXCLUDED at stewardship on a disproven premise.

## What the cycle produced (evidence recap)

- Assess `234f4b1c`: fresh adversarial whole-repo read (24 modules, tests, CI, skill
  surface) via ce-code-review depth:full/report-only; every finding reproduced by a
  worktree-anchored runtime probe (battery `/tmp/assess-3aedb9c5/probe_battery2.py`).
  Baseline 529/529. Two earlier attempts (b73fdbf7, 3aedb9c5) died on provider 429s
  before envelope write; a provenance audit discarded three early candidates probed
  against the stale canonical checkout and re-ran them worktree-anchored.
- Research `52eb7726`: 12 evidence-backed candidates (2 P2 / 5 P3 / 3 P4 / 2 strategic),
  fresh axes only (pi upstream surface, Agent Skills spec, OTEL v1.44.0, ecosystem);
  cycle-1 overlap audited. Attempt 32f4a1a6 aborted pre-envelope.
- Roadmap `72daf820`: "Extension 2026-09-30 - maintenance cycle 12", +40 lines, units
  U105-U114; standing U82/U98 evidence-strengthening notes; upstream zero-drift
  re-verified live (45328db, issue #12 quiet since 2026-09-24).
- Prioritize `f38c44ff`: ce-plan routed; batch = the six probe-verified defects + N1
  rider; medium risk class → full-suite ephemeral-PR CI budgeted for full_tests
  (KTD5/KTD6). Attempt e2824368 died pre-envelope.
- Stewardship `8fdcf43e`: anchor re-pin sweep (live file:line verification of every unit)
  DISPROVED U105's premise — backfill.py has no entry-type filter; U105 excluded, real
  probe surface recorded (state-DB `get_messages` path). Attempts a7b6f252/66fd1f1b died
  pre-envelope.
- Implement `43455d65`: all six units landed with 61 new behavioral pins; phantom-edit
  and phantom-green failures caught and repaired mid-flight (L56/L57). Attempts
  50faafc2/a442ba47 died pre-envelope/pre-start.
- Targeted_tests `2dc57c09`: engine impacted-runner, 19 files, 546 outcomes, exit 0.
- Full_tests `d486adfe`: engine full_command → ephemeral cloud-CI PR #16 (commit
  4fc4c518, base 20d592c): Python tests (3.12) + Lint (ruff count ceiling) both SUCCESS.

## Durable lessons (L56-L60)

1. **L56 — the delegate edit tool can report success without changing the file.** Twice
   on the same file (hygiene.py), with byte-exact anchors pulled via `cat -A`/python
   repr, the edit reported success and the file stayed byte-identical to HEAD. Prevention:
   land risky or multi-site edits as ONE atomic python in-place edit (read → replace →
   write) with a grep verification INSIDE the same command; never build on an edit until
   `git diff` shows it; edit-tool success reports are not evidence.
2. **L57 — a remembered green is not a green.** The U106/U108 pin suites were recorded
   as passing in runs that could not have executed them (the pins carried positional-arg
   calls against a keyword-only API — a deterministic TypeError); the earlier "green"
   was a phantom-era reconstruction, and the truth surfaced only when the full battery
   ran after unrelated later edits. Prevention: after ANY phantom-edit discovery, re-run
   every suite whose green predates the discovery and distrust intermediate records; the
   authoritative green is the last complete run after the final edit; a test that has
   never failed was possibly never run.
3. **L58 — research citations must be live-verified before unitization.** Research C1
   claimed `backfill.py:187 imports only type=='message'`; the file contains no
   entry-type filter at all (line 187 is the limit guard), so U105 was built on a
   nonexistent mechanism and had to be excluded at stewardship, leaving a wrong citation
   in the roadmap extension. Prevention: stewardship's anchor re-pin sweep (every unit's
   file:line pinned against the live worktree file before the batch is described) is the
   gate that catches premise drift — keep it mandatory for every batch, and fold
   corrective notes at the very next compounding (as this one does for U105).
4. **L59 — envelope-first is survival, not style.** This single run lost seven attempts
   (b73fdbf7, 3aedb9c5, 32f4a1a6, e2824368, a7b6f252, 66fd1f1b, 50faafc2/a442ba47) to
   the 429/abort-before-envelope class — completed work, no envelope, attempt dead.
   The attempts that survived (8fdcf43e, 43455d65) wrote the phase_result envelope as
   the FIRST substantive action or as mid-batch insurance and refined afterward.
   Prevention: write the envelope the moment the substantive result exists, then polish.
5. **L60 — bash probes resolve against the ambient checkout unless anchored.** The
   assess wave lost three candidates to probes that silently resolved against the stale
   canonical tree (the worktree and canonical coexist on this host); the read tool
   anchors to the session CWD, bash does not. Prevention: every probe, pin batch, and
   grep is explicitly worktree-anchored (cwd + HEAD verification in the same command);
   on any tree doubt, discard the whole wave and re-run rather than salvaging probes.

## Candidates and context for cycle 13

- **U83 is now unblocked and first in line**: it consumes U87's impact report, whose
  numbers U106 just made trustworthy (distinct-count fix); dependency order recorded at
  prioritize f38c44ff.
- **U98+U69 flagship stays design-probe-first** (KTD48 undecided; host contract before
  code, per cycle-11's defer reasons).
- **U105 re-probe**: the real question is whether the HOST pi-collector `get_messages`
  API surfaces `custom_message` entries (state-DB path, backfill.py:246-259); fixtures
  already carry them (`tests/fixtures/state_db/sessions/*.json`).
- **U112** OTEL semconv spike (both agent-spans + mcp still status: Development;
  revisit trigger recorded), **U113** GHA test-results ingestion (live-API-in-CI design
  decision owed), **U114** blocked on pi not being installed on GH runners.
- KTD40 ledger re-observation due ~2026-10-05 (streak 4/30 at the cycle-12 extension).

## Verification trail (recorded outcomes, not re-run here)

- Focused battery (implement): 15 files, 0 failures; supplementary full suite 590
  passed / 0 failed in 52.55s (529 baseline + 61 new pins) —
  `/tmp/final-sweep-43455d65.log`.
- Targeted (engine impacted-runner, 19 files, `-n 8`): exit 0, 546 outcomes, 0 FAILED —
  `/tmp/targeted-2dc57c09.log`.
- Full (engine `github_ci_validate.py --repo .` → ephemeral-pr): ok=true, PR #16,
  Python tests (3.12) SUCCESS + Lint (ruff count ceiling) SUCCESS —
  `/tmp/fulltests-d486adfe.log`.
