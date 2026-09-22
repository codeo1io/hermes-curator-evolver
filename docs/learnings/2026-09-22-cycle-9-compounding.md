# Cycle-9 Compounding — Durable Lessons (pre-review)

- **Run**: `d3a249d732a64103a5dadb4b9e28ab21` · **Phase**: compound · **Attempt**: `3c936159aa614146beabe89683cb8ff7`
- **Date**: 2026-09-22 · **Scope**: pre-review cycle evidence only (assessment, research, roadmap, prioritization, stewardship, implementation, targeted/full test outcomes). Review and shipping outcomes are NOT folded here — the next cycle's assessment carries them.
- **Batch compounded**: U77 + U78 + U80 + U81 + U79 (deferrable pulled in) — the "public-integrity batch" per the prioritize phase (`delegate/3b12aae2…-batch.md`), grounded in the cycle-5-run assessment (`delegate/24f53e69….json`, 10 findings) and research (`delegate/5a2e452c….json`, 9 candidates). Implementation evidence: the implement-phase results (`delegate/eb2fbb33….json`, re-shaped under `delegate/71659689….json` after an engine shape rejection) + git diff (12 M + 3 new files, +614 insertions); no separate implementation doc — the diff and phase results are the record.
- **Rule numbering**: continues cycle 8's L22–L28 and cycle 7's L16–L21 (this directory); L1–L14 are cycle 6's; L15 is the roadmap's format-matrix rule (KTD31).
- **Baselines superseded by this cycle**: pytest **410** passed (377 + 33 new), corpus `scripts/repro-pass7.py` **48/48** (35 pass-7 + 8 pass-8 + 5 pass-9), ruff full tree **16** flat on PATH 0.15.10 with the config now FROZEN in `pyproject` (CI enforces the 0.16.7 arm at ceiling 79).

## L29 — An external state flip re-ranks the whole board; security claims re-derive from code

The cycle's critical finding existed only because the repository flipped PUBLIC between cycles: a README that claimed "already-redacted session evidence" (false — `grep` found only docstrings ASSUMING redacted input, zero scrubbing code), a synthetic `ghp_` token sitting verbatim in a committed doc, and GitHub secret scanning ENABLED yet raising ZERO alerts (enabled ≠ protective — validity checks and non-provider patterns disabled). None of these were defects under the private-repo threat model; all became publishable-integrity defects the moment visibility flipped.

**Rule**: when an externally driven state flip occurs (public/private, runner topology, provider policy, dependency availability), the next assessment's FIRST lens is "what did the old state guarantee that the new state now publishes" — and every security/trust claim in docs (README, SECURITY.md, comments) is re-derived from the current code, never carried forward.

**Prevention hook**: scanner posture is queried (`gh api …/security_and_analysis` + `secret-scanning/alerts`), not assumed; doc claims map to a named enforcement point in code or they get deleted.

## L30 — Security transforms ship as one module, ≥2 enforcement layers, and a disclosure counter per layer

U77's shape was the lesson: a single `hygiene.py` module; scrubbing enforced at THREE different layers (ingest in `storage._compact`/`_json_dumps` before the length cut — a credential straddling a truncation boundary would otherwise leak its head; embed at all three `auto_evolve` points, so pre-fix rows in an older store cannot reach a published SKILL.md; validate as a named `skill_validate` error, so guarded apply rolls back instead of publishing); and each layer's activity lands in a disclosed counter (`credentials_scrubbed` deltas in backfill summaries, run-JSON summary, human CLI). Idempotence is pinned (double-scrub no-ops via markers).

**Rule**: a credential/PII transform is never a single gate — one implementation module, enforcement at every layer data crosses (ingest, publication, validation), and per-layer disclosed counters so the pipeline's behavior is observable, not assumed.

**Prevention hook**: corpus records pin both the ingest shape (f77a) and the pre-fix-row embed shape (f77b); a new embed point that forgets the scrub fails the next corpus run's f77b analog.

## L31 — Uniqueness constraints settle races at the exact scope of the identities involved

The dedupe TOCTOU fix had a trap: the obvious table-wide UNIQUE index on `(session_id, task_id, tool_name)` would have BROKEN the live hook path, whose `task_id` legitimately defaults to empty (repeated calls to one tool in one session share a key and must all count — pinned by u51/u68). The correct constraint is a PARTIAL index scoped to `task_id LIKE 'backfill:%'`, where identities are unique by construction (U74) — arbitrating exactly the concurrent-backfill race, nothing wider.

**Rule**: when adding a uniqueness constraint to settle a race, first ask what identities the race actually involves and scope the constraint to those; every legitimately-exempted repeat pattern gets a pinning test before the index ships. Migration posture: if legacy data violates the new constraint, index creation fails atomically, data survives, the gap is DISCLOSED (`dedupe_index_active=False` + warning) — never a destructive cleanup.

**Prevention hook**: the exempted-pattern tests (live-path bursts) are written BEFORE the index, so the constraint cannot silently narrow semantics.

## L32 — Connection-discipline contracts are enforced by shape tests, not docstrings

Storage's `connect()` docstring has said "READERS MUST NOT TOUCH IT — readers use `_read_connection()`" since U53, yet backfill's three reader functions sat on `with store.connect()` for multiple cycles and survived every prose review (cycle-9 assess caught them by reading the call sites, not the contract). The fix landed with the enforcement pattern: a test that monkeypatches the writer `connect()` to EXPLODE and then runs every backfill reader path — any future reader drifting back onto the warm writer fails loudly.

**Rule**: an architectural contract stated in prose is unenforced until a test makes the forbidden shape fail mechanically. Grep-shape audits find drift; explosion tests prevent it.

**Prevention hook**: new reader call sites copy the explosion-test pattern; a reader that needs transactional semantics is a WRITER and says so.

## L33 — Count-ceiling lint gates pin the binary and encode the ceiling as bump-and-record data

U80's gate design acknowledged an environment truth (constraint #5442: only ruff 0.15.10 exists on run hosts; the 63+16=79 baseline was recorded on a 0.16.7 arm that cannot be re-verified locally). The gate therefore pins ruff `==0.16.7` in CI, encodes the ceiling as an explicit number with its derivation in a comment, and the policy is written down: if the first CI lint run exceeds 79, bump the ceiling to the printed count and record the delta — never weaken the frozen rule set to pass.

**Rule**: a lint gate has three parts — pinned binary version, frozen rule config in-repo, and a count ceiling recorded as data with a bump-and-record policy. Local verification limits (one arm, skew across environments) are documented in the gate itself, not discovered in CI.

**Prevention hook**: "zero new findings" is checked per touched file by stash A/B (L27); the ceiling only ever moves via a recorded bump.

## L34 — Engine result shapes are literal contracts; serialize, never hand-write

The implement work completed and verified cleanly under attempt `eb2fbb33…`, yet the phase was rejected after completion: `artifacts` must be plain path strings (not `{path,kind,description}` objects), `findings` must be `{severity,file,line,issue}` objects (not strings), `provisional_future_work` must be `{phase,note}` objects. Same family as the cycle-5 escape bug (`\s` regex text broke JSON validity): hand-authored result files fail on serialization mechanics, not substance. The re-dispatch fixed the shape with zero code change — pure waste in gate time.

**Rule**: delegate result JSON is built with `json.dump` from a dict and self-validated (shape asserts + parse round-trip) BEFORE the final message; rich structure belongs in `summary`/`evidence_refs` prose, and regex fragments or inline literals never appear raw in hand-written JSON.

**Prevention hook**: a one-line assert block at the end of every result-file build; the schema lives in project memory (#8048).

## Candidates and context for the next cycle

- **U56 (hardening batch)** — now fully unblocked by U80's freeze (the ruff-churn overlap excuse is gone): u45 bound widen (#5350), F6 (`tools.py:43` int(days) raise), corrupt-manifest JSON, caps/S9/P14/S10 legs.
- **U75 (single-writer lockfile)** — first alternate, pull-in criteria unchanged; note U78's partial index already arbitrates the backfill-side race, so U75's remaining scope is the apply path (`auto_evolve.py` run entry).
- **U69** — KTD26 re-read due now that classification truth fully landed (U73 + U79 closed the residual edges); inherits the disclosed-counter pattern (`credentials_scrubbed` is the newest member).
- **Adversarial re-review targets**: the sibling-key precedence under zero exit and the widened separator class — extend the L24 mirror-pair discipline to sibling ORDERINGS (`code` under `exit_code` and vice versa) and probe the separator class with never-seen members (`exit=2`, `exit_code -1`).
- **Standing gates**: KTD40 ledger at 2/30 days (2026-09-21, 2026-09-22) — the next research pass adds a day or resets; NS-94x upstream plugin-manifest changes are main-only, watch for release-line landing; U62 still double-gated.
- **Engine-context notes**: the run survived four provider-429 envelope failures before assess (state recon on a fresh-main scratch checkout, not the stale worktree, was the recovery pattern); the implement shape rejection consumed one full gate cycle for zero code change (L34 is the prevention); the targeted-test dispatch's file list intentionally includes six module paths that collect no tests — harmless, not a mystery.
- **Public-integrity tail**: the KTD39-annotated token doc and the SECURITY.md pattern-based-limitations disclosure are now standing honesty artifacts — the next assessment should verify they still read true against whatever the code has become.
