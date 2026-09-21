---
date: 2026-09-21
topic: hermes-curator-evolver-adversarial-repository-assessment
mode: repo-grounded
run: 2fed6c7b93ea4a65a8b2fb94218cdb27
phase: assess
action: assess:assess
attempt: 3ccd151387d6408199972038ff0caed2
skill: ce-code-review methodology applied directly (no compound-engineering router / ce-* skill installed on this host — same disclosed deviation as passes 2–7)
---

# Adversarial repository assessment — pass 8

**Tree reviewed:** worktree branch fast-forwarded to `main` @ `d1a7f57`
(= origin/main; the merge that shipped cycle-7's `b1401a4` batch and the
roadmap-md-cleanse merge). Clean tree, nothing modified by this pass.

**Fresh baselines this attempt:** `pytest` (hermes-agent venv, no `-q`)
→ **344 passed** (28.96 s). `ruff check` with PATH ruff 0.16.7 (the binary
that applies the repo rule set — the venv's 0.15.10 ignores it) → **63
errors, 48 fixable**, unchanged. `python scripts/repro-pass7.py` → **35/35
sane, 0 deviations**: every cycle-7 claim re-verified fresh (N1/N3/N4
classifier probes, N2 COUNT(\*)=3 on a same-second burst, N5 human-format
disclosure present). All stateful probes ran in `tempfile.mkdtemp`
sandboxes.

**Focus of this pass.** Cycle-7 rewrote the classifier truth table (N1/N3/N4),
changed `skills[].event_count` to `COUNT(*)` (N2), and added backfill
disclosure (N5). Passes 3–7 each found a fresh defect in exactly such
rewrites, so this pass attacked the three new surfaces first (empirically),
then swept the modules no prior pass deep-read (guarded_apply, restore_drill,
reports, tools, paths, hooks) and re-derived every carried finding against
current lines.

## Fresh findings (this pass)

### F1 (P2) — success phrases still clear a whole comma-joined clause; asymmetric with the N3 fix
`candidates.py:402` (+ pattern at :147). The zero-count branch cycle-7 added
(:395-404) strips only the zero-count claim and rescans the remainder — but
the plain keyword branch still lets ANY success phrase clear the ENTIRE
clause, including a distinct, genuine failure claim joined by comma:

```
"0 failed, deploy failed: connection refused"            -> True   (N3 fix works)
"no tests failed, deploy failed: connection refused"     -> False  (F1: cleared)
"nothing failed, deploy failed: connection refused"      -> False  (F1: cleared)
```

`"no tests failed"` matches `_SUCCESS_COUNT_PATTERN`'s `\bno\s+(?:\w+\s+)?failed\b`
and clears the clause wholesale, while the semantically identical zero-count
form strips-and-rescans. Same ingest path and blast radius as N1/N3
(`is_error` gates `_eligible_skill_rows` and the review queue). **Fourth
consecutive pass with a fresh misclassification class in this function.**
Fix: route success phrases through the same strip-and-rescan treatment the
zero-count claims got (a success phrase may only clear the failure claim it
answers, e.g. by splitting clauses on commas before the keyword scan).

### F2 (P2) — id-less tool calls collide across messages; backfill silently drops distinct events
`backfill.py:71` + `:356-358`. `_tool_call_id`'s fallback `tool-{index}` is
unique only within ONE message's `tool_calls` list, but the ingest dedupe key
is `(session_id, task_id="backfill:{session}:{call_id}", tool_name)`. Two
assistant messages each carrying an id-less call to the same tool both mint
`task_id = backfill:s1:tool-0` → the second DISTINCT call is skipped as a
re-import. Reproduced: a 2-message, 2-call session imports **1** event
(want 2); `summary()` counters confirm the undercount. There is no duplicate
counter and no log — the drop is fully silent (`grep duplicate backfill.py`
→ nothing). This violates U68's own goal ("count every ingested skill
action") at the ingest layer and re-creates N2-style evidence starvation for
id-less transcripts (normalized/legacy exports — exactly the shape the
fallback exists for), directly feeding the `min_evidence` gate. Fix: make
the fallback unique across the session (`tool-{message_index}-{index}` or a
running per-import counter).

### F3 (P3) — `_HTTP_SUCCESS_CODES` is still an enumerated set, not a range
`candidates.py:164-166`. Cycle-7 widened the set (3xx added) but kept
enumeration; `{"code": 226}` (IM Used) still classifies as an error
(reproduced). This is the class's third iteration (S2 → N4 → F3): every
enumeration misses some in-band status. Pass-7's recommended fix — accept
`200 <= code < 400`, with the no-failure-field precondition already guarding
abuse — was not taken and would close the class permanently.

### F4 (P3) — numeric/HTTP-line `status` is a blind spot
`candidates.py:285-287` (+ `_STATUS_FAILURE_WORDS` at :167). `status` is only
inspected as a STRING against a fixed word list. Reproduced:

```
{"status": 500}                          -> False (success)
{"status": "500 Internal Server Error"}  -> False (success)
```

Tool wrappers that report HTTP status numerically or as a status-line under
`status` poison nothing — they are silently successes, so `error_events`
undercounts and auto-evolve never sees the failure signal. Fix: accept int
`status` in the structured pass (mirror the `code` range rule), and treat a
`status` string starting with a 4xx/5xx number as failure.

### F5 (P3) — no cross-process mutual exclusion for auto-evolve runs
`grep -rn "flock|fcntl|filelock|LockFile" hermes_curator_evolver/` → **zero
lock constructs**. The storage layer serializes writes in-process
(`_path_lock`, storage.py:425-460) and retries under EXTERNAL SQLite
contention, but the skill-file mutation path is a bare check-then-write:
`guarded_apply.py:344-345` (`sha256_file(target) != expected_sha256` gate)
→ `:380` (`_atomic_write_text(target, new_content)`). Two overlapping
auto-evolve runs (the installed user timer + a manual CLI — the plugin
explicitly ships both) both pass the hash gate against the same original,
both write, and both record `applied` manifests: last writer wins, the audit
trail claims two independent successes, and one candidate's content is
silently lost. Not corruption (backups exist for both), but a lost-update
race with a misleading provenance record. Fix: a run-level lockfile around
`run_auto_evolve` (cheap; the timer path is the only realistic overlapper).

### F6 (P4) — agent tool input unvalidated
`tools.py:43`: `days = int(payload.get("days") or 7)` raises `ValueError` on
`{"days": "week"}` / `TypeError` on `{"days": []}` — raw exception surfaces
to the agent instead of a structured error payload. Same class for
non-string `skill`. Minor DX.

### F7 (P4) — S10-class raw tracebacks extend to rollback/proposal paths
Re-reproduced today: `merge-check --source /nonexistent/a --target
/nonexistent/b` and `verify --proposal-file /nonexistent/nope.json` surface
raw `FileNotFoundError` tracebacks. Additionally `rollback_guarded_patch`
(`guarded_apply.py:607` area) does an uncaught `json.loads` on the manifest —
a corrupt manifest surfaces as a traceback rather than a structured refusal.

## Cycle-7 verification (regression check)

| Claim | Verdict |
|-------|---------|
| N1 comma-grouped counts | ✅ `"1,000 failed"` → True, `"10,000 failed, 3 passed"` → True |
| N3 clause scoping | ✅ `"0 failed, deploy failed: …"` → True; `"deploy failed.no errors later"` → True |
| N4 HTTP set | ✅ 203/206/301/304 → not errors (226 remains — F3) |
| N2 COUNT(*) | ✅ 3 same-second hook events → `event_count=3`; min_evidence gate passes |
| N5 disclosure | ✅ human-format backfill output prints truncation + U52 counters |
| probe corpus | ✅ `scripts/repro-pass7.py` 35/35 sane, 0 deviations |
| tests | ✅ 344/344 green at `d1a7f57` (344, not the 334 in the campaign docs — 10 review-phase tests landed after the doc) |
| P1 (backreference injection) | ✅ stays fixed (repro corpus covers it) |

## Findings — carried, re-derived against `d1a7f57` lines

| # | Sev | Location (current) | Status |
|---|-----|--------------------|--------|
| P5 | P2 | `auto_evolve.py:988+` (apply at ~1143; file's only `try:`s: 351/409/531) | unchanged — one unexpected exception mid-loop loses the run JSON after earlier candidates already mutated skills |
| P8 | P2 | `backfill.py:55` (`read_text` utf-8) + `:524-526` (catches only OSError/JSONDecodeError) | unchanged — a `\xff` legacy file's UnicodeDecodeError aborts the whole legacy import |
| P9 | P3 | `auto_evolve.py:479-487` | unchanged residual — stray/unpaired marker appends a second block → `duplicate-managed-block` verify failure forever, no repair path |
| N6′ | P3 | `verifier.py:18-21` | unchanged — no claimed-vs-report count cross-check |
| C1 | P3 | `semantic.py:203` | unchanged — reranker can only permute the embedder's already-sliced top-N |
| C3 | P3 | `review_queue.py:173` | unchanged — `update_status` has no production caller |
| P12 | P3 | `skill_sources.py:60,209` | unchanged — custom `--skills-dir` not literally named `skills` → SOURCE_UNKNOWN → silent skip |
| P14 | P3 | `.github/workflows/ci.yaml:34` | unchanged — pytest-only; 63 ruff errors (48 auto-fixable) ungated; main CI additionally red-by-flake from load-marginal u45 (U56 widening queued) |
| S9 | P3 | `hermes_curator_evolver/skills/curator-evolution/SKILL.md:4` | unchanged — `version: 0.11.0` vs `0.10.0` everywhere else (plugin.yaml:2, pyproject.toml:7, `__init__.py:28,30`) |
| N6 | P3 | `backfill.py:218-244` | unchanged — full metadata scan of every state-db store per backfill (no SQL-side ORDER BY); correct but O(store) per timer tick |
| N7 | P4 | `__init__.py:28,30` + wheel target | unchanged — fallback literal twice; wheel doesn't ship plugin.yaml so pip installs always take the fallback |
| N8 | P4 | `storage.py:508-527` | unchanged — quarantine moves the file but never evicts the warm cached writer/reader connections, so in-process corruption stays masked |
| caps | P3 | `auto_evolve.py:53` (chars), `candidates.py:32` (bytes), `guarded_apply.py:26` (chars) | unchanged — three separate 100 000 constants in two units |
| P6 | P3 | `auto_evolve.py:1163` | unchanged — support files plain `write_text` after guarded apply verified only SKILL.md |
| S10 | P3 | `cli.py` handlers | re-reproduced fresh today (see F7) |

## Testing gaps (fresh)

1. No classifier test covers success-phrase co-occurrence with genuine
   failure claims (F1) — the asymmetric-clearing case is liftable verbatim.
2. No test covers id-less `tool_calls` across multiple messages (F2) — the
   ingest undercount is directly liftable from the probe above.
3. No test covers `status` numeric/status-line payloads (F4) or `code` values
   outside the enumerated set (F3, e.g. 226).
4. No concurrency test for overlapping auto-evolve runs (F5).
5. CI remains pytest-only (P14); ruff, build, and the version-drift check
   (S9) are unenforced, and the u45 flake keeps main red-by-flake.

## Verdict

Cycle-7's five claimed fixes all verified fixed against the shipped tree,
with all 344 tests green and the 35-probe corpus clean. But the pattern
holds for a fourth pass: **the classifier rewrite traded N3 for F1** (the
strip-and-rescan fix was applied to zero-count claims only, leaving generic
success phrases clearing whole clauses), and **the N2 fix moved the
starvation into the ingest layer** (F2: id-less calls collide across
messages and drop silently — no counter, no log). Two new P2s, both
one-file fixes with liftable test cases. The remaining fresh findings (F3
enumerated-set continuation, F4 status blind spot, F5 no run lock) are all
in the same evidence-integrity theme. Recommended next cycle: F1+F3+F4 as
one classifier unit (comma-splitting + range-based codes + numeric status),
then F2 (session-unique call-id fallback + a dropped-duplicates counter),
then F5 (run lockfile) alongside the P5/P8 carries.

## Appendix — fresh probe corpus (deviations, verbatim)

```python
from hermes_curator_evolver.candidates import looks_like_error

# F1: success-phrase asymmetric clearing (comma-joined clause)
looks_like_error("no tests failed, deploy failed: connection refused")  # False (want True)
looks_like_error("nothing failed, deploy failed: connection refused")   # False (want True)
looks_like_error("0 failed, deploy failed: connection refused")         # True (control)

# F3: enumerated set still misses in-band statuses
looks_like_error({"code": 226})                                          # True (want False)

# F4: status key blind spot
looks_like_error({"status": 500})                                        # False (want True)
looks_like_error({"status": "500 Internal Server Error"})                # False (want True)

# F2: id-less tool calls across messages collapse at ingest
# two messages, each tool_calls=[{"name": "bash", "arguments": ...}] with NO id:
#   _tool_call_id(call, 0) -> "tool-0" for BOTH
#   task_id = f"backfill:s1:tool-0" for BOTH
#   _tool_event_exists(...) -> second event skipped
# result: imported tool_events == 1 for a 2-call session (want 2)
```
