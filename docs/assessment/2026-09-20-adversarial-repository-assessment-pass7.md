---
date: 2026-09-20
topic: hermes-curator-evolver-adversarial-repository-assessment
mode: repo-grounded
run: 78a174fbdec14ee3844ff327a59cef78
phase: assess
action: assess:assess
attempt: 60923b6e6db4421ca9dcb56569f65512
skill: ce-code-review methodology applied directly (no compound-engineering router / ce-* skill installed on this host — same disclosed deviation as passes 2–6)
---

# Adversarial repository assessment — pass 7

**Tree reviewed:** worktree of `main` @ `a76962c` (clean; HEAD is the autonomous
ROADMAP fleet-sync; the newest substantive code is the cycle-6 batch `cf74072`
— classifier clause-scoping, backfill result-cap, storage read-only readers).

**Fresh baselines this attempt:** `pytest` (hermes-agent venv) → **287 passed**
(47.8 s; the cycle-6 commit message says 286 — actual count is 287).
`ruff check hermes_curator_evolver tests` → **63 errors, 48 fixable** (unchanged,
still ungated — P14 carried). This is pass 7; passes 1–6 live in `docs/assessment/`.

**Focus of this pass.** The cycle-6 batch rewrote the three hottest surfaces
again (`candidates._text_bears_failure`, `_iter_state_sessions`,
`EvidenceStore` read paths). Passes 2/3/6 each found regressions in exactly
such rewrites, so this pass led with empirical probes against the *new* code,
then re-derived every carried finding against current lines.
Probe corpus: 35 probes, **8 new deviations reproduced, 25 stayed-set/cleared**
(2 of my own probe expectations were wrong and corrected — B1b old-session
ordering is correct repo behavior; T2 in-place corruption turned out masked,
see N8). Full probe script embedded in the appendix.

## Methodology disclosure

No compound-engineering router or `ce-*` skill is installed on this host (the
pi skill registry exposes only `agent-reach`) — the ce-code-review methodology
ran in-thread with sequential lenses (correctness, reliability, security,
performance, maintainability, testing, docs/DX, architecture). Report-only:
nothing applied to tracked source, nothing committed, nothing pushed.
Cross-model adversarial peer skipped (same sanctioned skip as passes 2–6).
All stateful probes ran in `tempfile.mkdtemp` sandboxes; no live Hermes home
or systemd unit was touched.

## Fresh empirical reproductions (this attempt)

| ID | Probe | Result |
|----|-------|--------|
| N1 | `looks_like_error("1,000 failed")` | **False** — comma-grouped failure count classified as success |
| N1b | `looks_like_error("10,000 failed, 3 passed")` | **False** — same, with a paired pass count present |
| N1ctl | `looks_like_error("2,048 failed")` | True (accidentally — the `,048` fragment parses as 48) |
| N2 | 3 hook-shaped events, same session/task/skill/second → `summary().skills[0]` | `event_rows=3`, **`event_count=1`**; `_eligible_skill_rows(min_evidence=2)` → **0 eligible** |
| N2ctl | 3 backfill-shaped events (unique `task_id`) same second | `event_count=3` — collapse is hook-path only |
| N3 | `looks_like_error("0 failed, deploy failed: connection refused")` | **False** — one clause (comma is not a splitter), zero-count clears the failure |
| N3b | `looks_like_error("deploy failed.no errors later")` | **False** — sentence split requires whitespace after the period |
| N4 | `{"code": 203}` / `206` / `301` / `304` | **True ×4** — omitted from `_HTTP_SUCCESS_CODES` |
| N8 | garbage-overwrite an open WAL DB, same process | store keeps working; main file **stays 896 B of garbage on disk** while `summary()` reports 2 events; quarantine never fires; a fresh subprocess still reads via the `-wal` |
| B1 | honest 5-session store, `limit=2` | newest-2 selected; `pages=1, seen=5, in_window=5, selected=2` — U52 counters truthful |
| B2 | hostile always-minting fake | stops at 30 000 distinct in 0.19 s, `metadata_scan_truncated=1` — bound + disclosure work |
| B3 | 12 000-session honest store, `limit=2` | 60 pages, newest-2 selected in 0.02 s (fake I/O) — S3 stays fixed |
| stays | `"10 failed, 2 passed"`→T, `"0 failed, 12 passed"`→F, `{"code":200}`→F, `{"returncode":1}`→T, `{"ok":false}`→T, `{"exit_code":0,"error":…}`→T | 6/6 — cycle-6 truth-table base holds |
| stays | `_extract_skill_name("skill_view", {"skills":["demo"]})` → `"demo"` | S6 fix holds |
| stays | `_apply_managed_block` with `\1`/`\g<boom>` in old block and new block | rewrites literally, no crash — **P1 stays fixed** (lambda at auto_evolve.py:487) |
| S10 | `merge-check --source /nonexistent/a`, `propose --skill x --skill-file /nonexistent/nope.md`, `verify --proposal-file /nonexistent/nope.json` | raw `FileNotFoundError` tracebacks ×3 (fresh repro) |

## Findings — new this pass

| # | Sev | Location | Finding |
|---|-----|----------|---------|
| N1 | **P2** | `candidates.py:109,337-343` | **Comma-grouped failure counts are successes.** `_FAILURE_COUNT_PATTERN = (\d+)\s+failed` binds only the trailing digit group of a comma-formatted count: `"1,000 failed"` → group `"000"` → `int == 0` → the clause is treated as a zero-failure success report (reproduced; `"10,000 failed, 3 passed"` also False). Same ingest path and blast radius as S1 — `is_error`/`error_events` gate auto-evolve eligibility and the review queue. Fix: accept grouped numbers — `(\d{1,3}(?:,\d{3})+|\d+)\s+failed` — and parse after stripping commas. |
| N2 | **P2** | `storage.py:652-675` (DISTINCT at 661) + `auto_evolve.py:808-813` | **`skills[].event_count` undercounts same-second bursts; the min_evidence gate starves burst traffic.** The U54 "attributed actions" metric counts DISTINCT `(session_id, task_id, skill_name, created_at)` but `created_at` is second-precision (`storage.py:185`, `timespec="seconds"`) and hook-path events share one task_id (hooks.py passes the per-task id; empty string when unset). Three same-session/same-second/same-skill events → `event_rows=3, event_count=1`, and `_eligible_skill_rows` (default `min_evidence=2`, `auto_evolve.py:97`) excludes the skill — reproduced with the gate returning 0 eligible rows. Parallel tool calls in one assistant message land in the same second, so this is the common agent-loop shape; it re-creates exactly the S6 starvation U54 was meant to end. Backfill imports are immune (unique `task_id` per call — verified). Fix: count distinct on a genuinely unique key (rowid, or session+task+skill+created_at+args hash), or keep raw `COUNT(*)` and dedupe at the report layer. |
| N3 | P3 | `candidates.py:116` (`_CLAUSE_SPLIT_PATTERN`) + 337-343 | **Clause scoping misses commas and unspaced sentence joins.** The splitter handles `;`, newlines, and punctuation-followed-by-whitespace, so `"0 failed, deploy failed: connection refused"` is ONE clause: the zero count wins and the failure is cleared (reproduced); `"deploy failed.no errors later"` likewise. Mixed prose summaries ("checks: 0 failed, deploy failed") silently become successes. Fix: also split on commas before the count parse, or let a zero-count clear keywords only when it is the clause's sole failure claim. |
| N4 | P3 | `candidates.py:135` | **`_HTTP_SUCCESS_CODES` closes only 4 of the in-band success statuses.** `{200,201,202,204}` — `203`, `206`, and every 3xx (`301`, `302`, `304` …) still classify as errors (reproduced 4/4). Web tooling that reports redirects or partial content through the generic `code` key keeps poisoning `error_events` — S2's class narrowed, not closed. Fix: treat `200 <= code < 400` as in-band success (the no-failure-field precondition already guards abuse). |
| N5 | P3 | `cli.py:885-905` vs `backfill.py:201,285` | **The "never silently" truncation disclosure is JSON-only.** `backfill.py` promises the runaway bound is recorded "never silently", and it does write `metadata_scan_truncated=1` into the result dict — but the human-format CLI summary prints none of the new truthful counters nor the truncation flag (only `--format json` surfaces them; text output prints seen/imported/skipped/failed). A truncated scan on a real store is invisible to the operator reading the default output. One-line conditional print. |
| N6 | P3 | `backfill.py:222-253` | **U52 traded the cap for a full metadata scan of every state-db store.** The metadata cap is gone for honest stores: every `backfill-sessions`/bootstrap now pages through *all* sessions (12 000 → 60 pages, measured) and sorts them client-side, holding every in-window session dict in memory before slicing `limit` (500 by default). Correctness holds (B3), and the hostile-store bound (line 249, `max(limit,10_000)*3` = 30 000 distinct, 0.19 s measured) works — but a long-lived host with 100 k+ sessions pays a full-store metadata read on every timer tick, and the pass-6 recommended fix (push ordering into SQL, `ORDER BY last_active DESC LIMIT ?`) was not taken. Performance/architecture note, not a correctness bug. |
| N7 | P4 | `hermes_curator_evolver/__init__.py:28,30` + `pyproject.toml` (`[tool.hatch.build.targets.wheel]`) | **Version single-sourcing degrades on wheel installs.** The wheel ships only the `hermes_curator_evolver` package — the root `plugin.yaml` that `_plugin_version()` reads is NOT in the wheel, so every pip-installed copy takes the hardcoded `"0.10.0"` fallback, which now exists twice (lines 28 and 30). The next version bump must update `plugin.yaml` + both literals in lockstep or drift returns; no test pins the fallback path. Fix: move `plugin.yaml` inside the package (and read it via `importlib.resources`), or derive the fallback from package metadata. |
| N8 | P4 | `storage.py:492-530` (`init_db`/`_quarantine_corrupt_db`) | **In-place corruption is masked by the warm caches; quarantine can never fire mid-process.** With connections cached (writer since U45, reader since U53), garbage-overwriting the DB file leaves `_schema_ready()`'s probe being served from the warm page cache — the store keeps accepting INSERTs and `summary()` reports data (2 events) while the main file on disk is 896 bytes of garbage (verified byte-level). Everything written after corruption lives only in the `-wal`; if that is lost, it is gone. `_quarantine_corrupt_db` evicts neither cache entry. Pre-existing class (writer cache), enlarged by the second cache. Fix: evict both cached connections for the path inside quarantine, and/or re-validate the header on `init_db`. |

## Findings — carried, re-derived against the current tree

| # | Sev | Location | Status |
|---|-----|----------|--------|
| P5 | P2 | `auto_evolve.py:1107-1183` (apply at 1143) | unchanged: no per-candidate `try/except` (the file's only `try:`s are at 351/409/531) — one unexpected exception mid-loop loses the run's JSON after earlier candidates already mutated skills |
| P8 | P2 | `backfill.py:525` | unchanged: legacy `session_*.json` path still catches only `(OSError, json.JSONDecodeError)` — a `\xff` file's `UnicodeDecodeError` aborts the whole legacy import |
| P9 | P3 | `auto_evolve.py:482-488` | half-fixed: the re.sub **injection** crash is fixed (lambda, verified live); the stray/duplicate-marker lockout remains — `count=1` replaces only the first block pair and an unpaired marker appends a second, after which every staged verify fails with no repair path |
| N6′ | P3 | `verifier.py:26` | unchanged: verifier never cross-checks claimed vs report counts |
| C1 | P3 | `semantic.py:203` vs `206-215` | unchanged: `candidates = candidates[: max(1, limit)]` precedes the rerank block — the reranker can only permute the embedder's slice |
| C3 | P3 | `review_queue.py:173` | unchanged: `update_status` still has no production caller (queue transitions remain dead surface) |
| P12 | P3 | `skill_sources.py:60,209` | unchanged: a custom `--skills-dir` not literally named `skills` classifies `SOURCE_UNKNOWN` → auto-apply silently skipped |
| P14 | P3 | `.github/workflows/ci.yaml` | unchanged: CI is pytest-only; 63 ruff errors (48 auto-fixable) ungated; dev extra doesn't even install ruff |
| S9 | P3 | `hermes_curator_evolver/skills/curator-evolution/SKILL.md:4` | unchanged: bundled skill declares `version: 0.11.0` vs `0.10.0` everywhere else; the U7b test still doesn't cover the skill surface |
| S10 | P3 | `cli.py` handlers | re-reproduced fresh today: `merge-check` missing dir, `propose --skill-file`, `verify --proposal-file` all surface raw `FileNotFoundError` tracebacks |
| caps | P3 | `guarded_apply.py:26`, `auto_evolve.py:53`, `candidates.py:32` | unchanged: three separate 100 000 caps in two different units (chars vs bytes) |
| P6 | P3 | `auto_evolve.py:1163` | unchanged: support files plain `write_text` after the guarded apply verified only SKILL.md |

## Verification of the cycle-6 batch's own goals (regression check)

- **U51/CU-AC (classifier)** — S1 ✅ (`"10 failed"` → True at every width tested), S2 ✅
  base (`{"code":200}` → False), S4 ✅ (two-line shape → True), S5 docstring ✅ (now
  documents the explicit-fields-first order). **But N1/N3/N4 are new defect classes
  in the same function** — the third consecutive pass to find fresh
  misclassifications in this classifier.
- **U52/CU-AD (backfill)** — S3 ✅ stays fixed (12k store selects the true newest-2,
  B3); truthful counters ✅ (B1); hostile-pagination bound + disclosure ✅ (B2).
  Residuals: N5 (disclosure not in human output), N6 (full-scan cost).
- **U53+U54/CU-AE (storage)** — S5 ✅ (readers on read-only connections; `summary()`
  no longer commits/rolls back the writer), S6 ✅ (skill attribution symmetric,
  verified). **But U54's new DISTINCT metric introduces N2**, and the second
  connection cache enlarges N8.
- **P1** — ✅ stays fixed (`_apply_managed_block` lambda replacement, verified live
  with backreference-bearing blocks).
- **287/287 tests green** at HEAD; no regressions from the cycle-6 batch.

## Testing gaps (fresh)

1. No classifier test covers comma-grouped counts (N1), comma-joined clauses (N3),
   or `code` values outside the 4-status set (N4) — all directly liftable from the
   probe corpus.
2. No test pins `summary().skills[].event_count` against same-second hook-shaped
   events (N2); the min_evidence gate is still untested end-to-end for bursts.
3. No test asserts the human-format backfill output contains the truncation
   disclosure (N5) or any of the new counters.
4. The version-fallback path of `_plugin_version()` (missing plugin.yaml) is
   untested (N7).
5. CI remains pytest-only (P14): ruff, build, and the bundled-skill version check
   (S9) are unenforced.

## Verdict

The cycle-6 batch did what it claimed: every named S1–S6 goal verified fixed, the
hostile-store bound works, and the storage reader split removes the S5 commit
interference. But the pattern of the last three passes continues — **each rewrite
of the classifier introduces a new misclassification class** (N1 comma-grouped
counts, N3 clause-scoping gaps, N4 incomplete HTTP set — all feeding the
`is_error` column that gates auto-evolution), and **U54's new distinct-count
metric re-creates the very starvation it fixed** for same-second bursts (N2).
No P1s; two P2s (N1, N2), both one-file fixes with liftable test cases.
Recommended next cycle: N1+N3+N4 as one classifier unit (with a
comma-aware count grammar), then N2 (unique event key), then N5 (one-line
disclosure print) alongside the P5/P8 carries.

## Appendix — probe corpus (deviations + controls)

Run: `python /tmp/repro-pass7.py` against this worktree (hermes-agent venv).
35 probes: 8 deviations (N1 ×2, N2 ×2, N3 ×2, N4 ×4 counted as one finding
each in the table above), 27 stays-set/cleared including my own two corrected
expectations. Deviating probes:

```python
looks_like_error("1,000 failed")                          # False (want True)  -> N1
looks_like_error("10,000 failed, 3 passed")               # False (want True)  -> N1
looks_like_error("0 failed, deploy failed: connection refused")  # False      -> N3
looks_like_error("deploy failed.no errors later")         # False (want True)  -> N3
for code in (203, 206, 301, 304):
    looks_like_error({"code": code})                      # True  (want False) -> N4

# N2: hook-shaped same-second burst (task_id constant, second-precision stamps)
store = EvidenceStore(tmp / "ev.sqlite")
same = datetime.now(timezone.utc).isoformat(timespec="seconds")
for _ in range(3):
    store.record_tool_call(tool_name="skill_view", args={"name": "demo-skill"},
                           result={"ok": True}, task_id="", session_id="sess-1",
                           created_at=same)
row = store.summary(days=30)["skills"][0]
# -> event_rows=3, event_count=1
auto_evolve._eligible_skill_rows({"skills": [dict(row)]}, min_evidence=2)  # -> []

# N8: in-place corruption under warm caches
p.write_bytes(b"NOT A DATABASE" * 64)          # after a record + summary
EvidenceStore(p).record_tool_call(...)          # still succeeds
p.read_bytes()[:16]                             # b'NOT A DATABASENO' — garbage on disk
EvidenceStore(p).summary(days=30)["tool_events"]  # 2 — served from cache/WAL
```
