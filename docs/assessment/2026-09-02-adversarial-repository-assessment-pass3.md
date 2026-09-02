# Adversarial Repository Assessment — hermes-curator-evolver (pass 3)

- **Date:** 2026-09-02
- **Work order:** run 682bd7e431e34f7b9efc0c881cde253a / assess:assess / attempt 82f9771fbc264672b53841b3cff35448
- **Review run:** ce-code-review RUN_ID 20260902-075335-6da5e933 (`/tmp/compound-engineering-1000/ce-code-review/20260902-075335-6da5e933`)
- **Tree reviewed:** `main` @ 45328db + the same 11 uncommitted cycle-1 remediation files (verified unchanged since pass 2 via `find -newer`; no source file modified)
- **Fresh baselines this attempt:** pytest → 174 passed (17 files); `ruff check .` → 65 errors / 46 fixable; all `examples/*.json` parse
- **Mode:** report-only. Nothing applied, committed, or pushed.

## Methodology disclosure

Routed via the compound-engineering router to **ce-code-review** (narrowest match; no ce-assess skill exists). The pi harness exposes no subagent primitive, so the fast pass and five persona passes (correctness, security, reliability, performance, maintainability) ran **in-thread with sequential persona framing — not independent reviewers; no finding claims independent corroboration** (`independence_verified` intentionally never set, so findings-mechanics performed no confidence promotion). Cross-model adversarial peer skipped as sanctioned (host model family not discernible). Because the tree is unchanged since the prior attempt, every carried finding was **re-derived against the current tree this attempt** (fresh grep/read/line anchors), and the headline defects were **re-reproduced empirically** (R1–R4 below). New coverage this pass: README/docs claims verification, plugin.yaml/pyproject packaging, shipped SKILL.md, CI workflow, examples/, test-suite architecture.

## Fresh empirical reproductions (this attempt)

| ID | Command/result |
|----|----------------|
| R1 | `re.sub` with replacement string containing `(\1) \g<boom>` → `IndexError: unknown group name 'boom'` — the `_apply_managed_block` path (auto_evolve.py:386) with evidence-derived blocks |
| R2 | `storage._looks_like_error('3 passed, no errors found')` → **True**; `candidates._is_tool_failure(same)` → **False** |
| R3 | `parse_args(['auto-run','--max-reference-files','0'])` → `int(x or 5)` → **5** (help text says "0 disables pruning") |
| R4 | Source-order check in `semantic._semantic_candidates`: truncation to top-`limit` (line 246) precedes rerank pair construction (line 250) |

## Findings — current (3)

| # | Sev | Location | Finding |
|---|-----|----------|---------|
| C1 | P2 | `semantic.py:246` | Reranker re-ranks only the already-truncated top-`limit` embedding slice; `--rerank-candidates` can never promote a skill the embedder ranked beyond it. Existing test (`test_semantic.py:109`) uses a fake backend over fewer candidates than the limit, so the suite cannot see it. Fix: oversample (≈5×limit) before rerank, truncate after. |
| C2 | P2 | `cli.py:786` | `rollback` constrains the manifest target only when `--skills-dir` is passed; `guarded_apply.py:499` skips the root check when `allowed_target_roots is None`, against the docstring's own promise (guarded_apply.py:486). README's CLI reference teaches the unsafe default form. Fix: default to the resolved skills root or require explicit opt-in. |
| C3 | P3 | `review_queue.py:178` | `update_status` is dead surface — no CLI moves candidates pending→accepted/rejected while `candidates-list --status` advertises those filters; the human-review loop requires hand-written sqlite. |

## Findings — pre-existing, confirmed still open (15)

| # | Sev | Location | Finding (fresh evidence) |
|---|-----|----------|--------------------------|
| P1 | **P1** | `auto_evolve.py:386` | **re.sub replacement injection (R1).** Evidence previews flow into the replacement string; `\1`/`\g<name>` raises IndexError and — with no per-candidate guard (P5) — aborts the whole auto-run. Fix: `pattern.sub(lambda _: block, ...)` or escape backslashes. |
| P2 | **P2** | `storage.py:127` | **Error-classifier false positives (R2).** `is_error` for "no errors found" → 1; corrupts `error_events` (storage.py:289/307/318) which gate auto-evolve thresholds and replay-benchmark mining. Consolidate on one structured-first classifier. |
| P3 | **P2** | `cli.py:803` | **`--max-reference-files 0` contradiction (R3).** CLI coerces 0→5 vs help; API `keep=0` (auto_evolve.py:838 → 402-433) prunes ALL auto references including the file written by the same pass (1052-1066), leaving the managed block pointing at a deleted file. |
| P4 | **P2** | `storage.py:154` | sqlite connect without timeout/WAL/busy_timeout; hooks open a store per event (hooks.py:14/31/52) vs concurrent timer → `database is locked`; every `with self.connect() as conn:` is a transaction context, not a close (also review_queue.py:66, one connection per enqueued candidate). |
| P5 | **P2** | `auto_evolve.py:1040` | No per-candidate try/except (only 3 `try:` in the file: 255/313/427); one raising candidate aborts the pass **after earlier applies**, losing the result JSON. Compounds P1. |
| P6 | **P2** | `auto_evolve.py:1052` | Support files written after apply+verify with unchecked `write_text`; unverified content lands in the skills tree; partial failure leaves SKILL.md referencing missing files. |
| P7 | **P2** | `auto_evolve.py:1386` | `OnCalendar={schedule}` written verbatim; `_quote_systemd_arg` (190-202) doesn't reject newlines → newline-bearing `--schedule`/ExecStart args inject extra directives (e.g. `ExecStartPost=`) into the service. Local self-config footgun; bootstrap then enables+starts the unit. |
| P8 | **P2** | `backfill.py:435` | Legacy `session_*.json` path lacks the per-session boundary the state path just gained; `except (OSError, json.JSONDecodeError)` misses `UnicodeDecodeError`; any import error aborts the whole backfill. |
| P9 | **P2** | `auto_evolve.py:383` | Stray/duplicate managed-block markers → block append → `skill_validate` "multiple/unbalanced auto blocks" (skill_validate.py:78-82) fails every later staged verify; skill locked out of auto-evolution until hand-edited. |
| P10 | P3 | `cli.py:701` | Bad `--proposal-file/--skill-file/--input-jsonl/--source` paths → raw tracebacks. |
| P11 | P3 | `storage.py:280` | `summary()` computes `cutoff_iso(days)` 3× (280/299/303); per-event uncompiled substring error scan. |
| P12 | P3 | `skill_sources.py:67` | Custom `--skills-dir` not literally named `skills` → every skill classifies `unknown`/not-writable → auto-apply silently disabled, no warning. |
| P13 | P3 | `__init__.py:16` | Version drift, now four layers: package `0.8.0` vs plugin.yaml/pyproject `0.10.0` vs shipped SKILL.md `0.11.0` vs README roadmap `v0.14 ✅`; runtime schema_versions also drift (0.8/0.10/0.1-0.2). |
| P14 | P3 | `.github/workflows/ci.yaml:32` | 65 ruff errors (46 fixable) and CI runs pytest only — no lint step anywhere (no pre-commit config either), so the baseline grows unnoticed. |
| P15 | P3 | `cli.py:497` (advisory, owner: human) | `bootstrap` grants unattended-write authority in one command (`--proposal-only` is the non-default opt-out; scheduler command bakes `--apply-low-risk --approve-auto-apply`, auto_evolve.py:1299-1304). Mitigations are real (provenance gate, bounded blocks, staged verify, drill gate); this is a product trust-boundary choice, flagged for explicit human decision. |

## Docs/DX verification (new coverage this pass — mostly good)

- ✅ README/SKILL.md claim "reads state.db through Hermes' read-only SessionDB API" — **accurate** (backfill.py:393-394: `SessionDB(db_path=..., read_only=True)`, `search_sessions`/`get_messages`).
- ✅ README uninstall `rm -rf .../data .../backups` matches the actual default backup dir (auto_evolve.py:164-165).
- ✅ All `examples/*.json` parse; scheduler/platform claims match `_scheduler_backend` behavior.
- ✅ CI exists (pytest 3.11/3.12, least-privilege `permissions: contents: read`).
- ⚠️ Docs gaps: no SECURITY.md/threat-model doc, no CHANGELOG for the 0.8→0.14 feature series, README rollback example omits `--skills-dir` (reinforces C2), version badges/roadmap disagree with package versions (P13).

## Testing gaps (fresh greps)

1. No test feeds backslash-group evidence text through `_apply_managed_block`/`run_auto_evolve` (grep: zero matches).
2. No storage-side test asserting `is_error=False` for keyword-bearing success strings.
3. Only a default-value assertion exists for `max_reference_files` (test_auto_evolve.py:1113); no 0-semantics test.
4. Rerank test uses a fake backend over ≤limit candidates — truncation flaw invisible.
5. No concurrency test (hooks vs timer on evidence.sqlite); no corrupt/non-UTF-8 legacy-session test; no mid-loop candidate-exception test; no support-file write-failure test.
6. No newline-bearing scheduler-arg rejection test; no CLI-default rollback escape test; no version-consistency test; no lint gate.

## Verdict

Unchanged tree since pass 2; all previously reported high/medium defects remain open, re-verified with fresh line anchors, and the four headline defects re-reproduced empirically (R1–R4). New this pass: three current findings (rerank recall ceiling, rollback default, dead review-queue surface), four-layer version drift, missing lint gate in CI, and a docs layer that is otherwise accurate. The uncommitted cycle-1 remediation remains regression-free (174/174) and sound. Priority for the next fixing phase: P1 (lambda/escaped replacement) + storage classifier consolidation, then P5/P8 exception boundaries, then P7/C2 hardening.

*Report-only assessment. No code changed, nothing committed or pushed.*
