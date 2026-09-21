# Cycle-8 Compounding — Durable Lessons (pre-review)

- **Run**: `2fed6c7b93ea4a65a8b2fb94218cdb27` · **Phase**: compound · **Attempt**: `6aeec74290734d25b2ce6e79f95cbabc`
- **Date**: 2026-09-21 · **Scope**: pre-review cycle evidence only (assessment pass 8, research, roadmap, prioritization, stewardship, implementation, targeted/full test outcomes). Review and shipping outcomes are NOT folded here — the next cycle's assessment carries them.
- **Batch compounded**: U73 + U74 + U76 = CU-AH/CU-AI/CU-AJ per `docs/prioritization/2026-09-21-cycle-8-batch.md`, grounded in `docs/assessment/2026-09-21-adversarial-repository-assessment-pass8.md` (F1–F7 + carried re-derivation at d1a7f57). Implementation evidence: the implement-phase result (delegate spool `1181086d28174155827ca67e41ef948a.json`) + git diff (9 files, +780/−224); no separate implementation doc was written this cycle — the diff and phase result are the record.
- **Rule numbering**: continues cycle 7's L16–L21 (this file's directory) and cycle 6's L1–L14; L15 is the roadmap's format-matrix rule (KTD31).
- **Baselines superseded by this cycle**: pytest **377** passed (344 + 33 new: ~30 U73 matrix cases + 3 new unit tests), corpus `scripts/repro-pass7.py` **43/43** (35 pass-7 + 8 pass-8 records), ruff PATH 0.16.7 **63** errors on `hermes_curator_evolver tests` and **16** on `scripts/repro-pass7.py`, both flat.

## L22 — Spec-defined classes get rule encodings, never enumerations

The in-band HTTP success test missed legal codes three assessment passes in a row from the same defect shape: cycle 6 missed 203/206/3xx (fixed by enumerating them), pass 8 missed 226 IM Used (enumerated set again), and the recommended fix had already been "use the range" twice. Each enumeration fix widened the set without closing the class.

**Rule**: when a check tests membership in a **spec-defined class** (HTTP 2xx/3xx in-band, ISO dates, semver, Unicode categories), encode the class (range bounds, parser), not the observed members. Enumerations are only legitimate for genuinely **open classes** where the spec is a vocabulary (failure words, skill names).

**Prevention hook**: assessment probes must include at least one member of the class that the implementation has never seen in a fixture (226 was exactly this) before accepting a fix; the fix is rejected as incomplete if it would fail a different never-seen member (203-and-226-style misses cannot recur against a range).

## L23 — Fallback identifiers must state and test their uniqueness scope

`_tool_call_id`'s `tool-{index}` fallback was unique within one message, but the dedupe key `(session_id, task_id, tool_name)` is session-wide — two id-less calls to the same tool in different messages collided and silently imported as one event (pass-8 F2, violating U68's "count every ingested action" at the ingest layer and recreating the N2 starvation shape). The bug was invisible because the fallback's scope was implicit.

**Rule**: a synthetic identifier carries its uniqueness scope **in its derivation** (`tool-{message_index}-{index}` names its scope) and a test exercises the scope boundary the key actually lives at (same tool, two messages, one session → two events; re-import → 0 new + N disclosed skips).

**Prevention hook**: any dedupe or fallback key gets a collision test at the widest scope where the key is used; silent skips are forbidden — every dedupe refusal lands in a disclosed counter (here `tool_events_skipped_duplicate`), the pattern U69 must inherit when it retires the heuristic layer.

## L24 — Ordered-resolution rules are checked in the mirror shape

Pass-7 N3's clause scoping fixed "failure evidence, then success phrase" (a success phrase clears only its own clause). Pass-8 F1 found the mirror inside one comma-joined clause: "no tests failed, deploy failed: connection refused" — the success phrase *preceded* the genuine failure and still cleared it. The cycle-7 fix was asymmetric because only one ordering was pinned. The cycle-8 resolution is positional (KTD35): the clause's **last** success claim answers the evidence that **precedes** it; a failure keyword after it stands. This subsumes the zero-count strip-and-rescan, whose anchor had to cover both patterns (a grouped `0,000 failed` is a success claim only via the count pattern — the U67 pin caught this during test bring-up).

**Rule**: for any rule that resolves claims by order or position, the fixture set contains the mirrored ordering(s) as stay-set controls — both "X then Y" and "Y then X" must be pinned, plus the grouped-variant anchor check if two patterns can express the same claim.

**Prevention hook**: format-matrix cases ship in mirror pairs; an adversarial reviewer's first move on a positional rule is to read it backwards.

## L25 — Exception tuples are audited against the hierarchy, not the observed failures

The legacy-import gate caught `(OSError, json.JSONDecodeError)` and looked complete — but `UnicodeDecodeError` subclasses **neither**, so one undecodable transcript aborted the whole import (carried P8). The tuple had been built from the failures actually seen, not from the exception family the handler claims to tolerate.

**Rule**: when a handler claims "tolerate all bad X", deliberately enumerate the exception family for X (decode/parse: `UnicodeDecodeError`, `json.JSONDecodeError`, `OSError` — and note `UnicodeDecodeError` is a `ValueError` subclass, not an `OSError`) and pin one fault-injected test per member.

**Prevention hook**: review checklist item for every broadening `except` clause: list the hierarchy members of the claimed failure class; each either appears in the tuple or is named in a comment explaining why not.

## L26 — Accumulator loops get per-item containment, proven by injection

The auto-evolve apply loop was one of three unguarded regions (only 3 `try:` blocks in 1,200+ lines); a single poison candidate — a malformed patch, an unreadable target — would have lost the **entire run record**, not just that candidate (carried P5). Cycle 8 wraps the mutation-bearing body per-candidate: a raising apply becomes a `status="failed"` row with the error string, the loop continues, the run JSON always lands, and the summary carries a `failed` count.

**Rule**: any loop whose output is a durable record (run JSON, report, manifest) wraps each item in try/except that yields a failed item-row; containment is never assumed — it is **pinned by fault injection** (monkeypatch the called function to raise for one item; assert later items still apply, the poison item is recorded failed, and its target file is untouched when the raise precedes any write).

**Prevention hook**: `tests/test_auto_evolve.py::test_u76_poison_candidate_does_not_abort_apply_loop` is the template; every new accumulator loop copies the pattern (blind-except `BLE001` with a targeted noqa, matching backfill's per-session guard).

## L27 — New code adds zero lint counts; per-file stash A/B is the enforcement tool

The batch's verification plan said "ruff flat" — and the plan earned its keep: two separate +2 `UP017` regressions from **new** code (the new backfill tests, then the corpus-script additions using `datetime.now(timezone.utc)`) were caught by per-file stash/pop A/B against the pre-change tree and flattened by writing `datetime.UTC` in the new lines only. Pre-existing counts (63 pkg+tests, 16 scripts scope) stayed byte-identical; no old line was churned.

**Rule**: "flat" is checked **per touched file** by stashing the batch and counting before/after — a whole-tree count can hide a new-code regression inside an unrelated pre-existing total. Fixes adapt the new code (UTC alias), never the pre-existing lines; different scopes (pkg+tests vs scripts/) are counted separately with the same binary (PATH ruff 0.16.7 applies the repo rules; the venv's 0.15.10 does not).

**Prevention hook**: every batch's verification plan names the scopes and the per-file A/B; `datetime.UTC` (not `timezone.utc`) in all new lines.

## L28 — After an interruption, complete the remainder — never redo proven work

The implement phase was interrupted mid-unit (attempt 1: all three source units landed and probe-verified; the two test units, full verification, and lint flattening were not). Attempt 1 honestly reported `failed` with a precise completed/remaining split; the re-dispatch then completed **only the deltas** — the tree's already-verified state was cited, not rebuilt. The full-suite count matched the recovered verification exactly (377), proving nothing was redone or lost.

**Rule**: on interruption recovery, inventory what the working tree already proves (compiles, probes, targeted tests), record it in the failed report, and on re-dispatch do only the remainder — re-running proven verification "to be safe" wastes the gate's time and invites confounds.

**Prevention hook**: failed phase reports carry an explicit COMPLETED/REMAINING split so the engine can re-dispatch narrowly.

## Candidates and context for cycle 9

- **U75 (single-writer lockfile)** — first alternate with recorded pull-in criteria (all green + matrix passing + refusal test <60 lines); the F5 TOCTOU stands until then. `auto_evolve.py`'s run entry is the surface; must_remain_separate from the U76 containment block.
- **U56 (hardening batch)** — now carries F6 (`tools.py:43` int(days) raise), F7/B28 (corrupt-manifest JSON), S9/caps/P14/S10, the CI ruff pin (binary skew 0.16.7 vs 0.15.10), and the u45 bound widen (#5350's cheap win). Held a third cycle for ruff-churn overlap with U73/U74 files — that overlap is now gone.
- **U69** — unblocked by U74's landing: its counters are the disclosure pattern the probe-then-early-terminate design (N6, SQL-side MRU at `hermes_state_sessions.py:1365`) must inherit; KTD26 re-read of U38/U47/U60 is due now that classification truth landed.
- **Adversarial re-review target**: the positional rule (L24/KTD35) — next assessment's first classifier lens; its mirror-pair discipline is the attack surface. U19 (heuristic layer) flagged for post-U74 re-read.
- **Standing gates**: U62 double-gated (index LIVE, PR #101237 open — re-verify next research pass); U70 shippable on v0.21.3; hermes-dojo is the new direct competitor absent from the cycle-7 table.
- **Engine-context note**: the cycle-8 validation dispatches listed `storage.py`/`test_storage.py` as changed though the batch never touched them (conservative surface derivation) — harmless, covered by the runs; next assessment should not chase it as a mystery diff.
