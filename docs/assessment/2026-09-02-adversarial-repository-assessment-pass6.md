---
date: 2026-09-02
topic: hermes-curator-evolver-adversarial-repository-assessment
mode: repo-grounded
run: 6f5d76c84f52491ba25460c4a6e1a454
phase: assess
action: assess:assess
attempt: 9ce2f967fe58402db266be29f077d742
skill: ce-code-review methodology applied directly (no compound-engineering router / ce-* skill installed on this host — same disclosed deviation as passes 2–5)
review-run: /home/agent/.hermes/conductor-runs/6f5d76c84f52491ba25460c4a6e1a454-assess
---

# Adversarial repository assessment — pass 6

**Tree reviewed:** `fix/maintenance-cycles-1-5` @ `4350ee2` (branch clean; `4350ee2` is an
**empty** commit — "ci: retrigger fork CI on main (workflow trigger only)"; `git diff
ac9c0ee..4350ee2 --stat` is empty, so source is identical to the docs commit `ac9c0ee`
on top of `29d7ded` (cycles 1–5 remediation: U1–U4, CU-Q..CU-V, CU-W..CU-AB)).

**Fresh baselines this attempt:** `pytest` (hermes-agent venv, pytest 9.1.1) →
**249 passed** (31.3 s, 17 files). `ruff check hermes_curator_evolver tests` →
**63 errors, 48 fixable** (nothing gates it — P14 carried). `data/evidence.sqlite`
gitignored. This is pass 6; passes 1–5 are in `docs/assessment/`.

**Focus of this pass.** Adversarial weight on the code the cycle-5 batch *rewrote*
(the U43 "truth table" classifier landed in `29d7ded`, the newest substantive change),
then the storage/session-import layer under realistic scale, then every carried finding
re-derived against current lines. Reproducers:
`repro-pass6.py` / `repro-pass6-fixups.py` (+ JSON results) beside this report in the
conductor-run dir. 24 probes: **19 reproduced, 3 probes re-run after fixing my own
harness mistakes, 2 tested-and-cleared** (quarantine-over-garbage-DB F15 works;
systemd schedule control-char injection F19 is blocked).

## Methodology disclosure

No compound-engineering router or `ce-*` skill is installed on this host (MCP `donsetch`
exposes no ce tools) — the ce-code-review methodology ran in-thread, lenses: correctness,
reliability, security, performance, maintainability, testing, docs/DX. Report-only:
nothing applied, committed, or pushed. Cross-model peer skipped (same sanctioned skip as
passes 2–5). **Probe-harness disclosure:** the first F19 attempt (before isolation) ran a
real `bootstrap` against the live host home for its 120 s timeout — no systemd units were
written (`~/.config/systemd/user/` verified: no curator units; the timer step was never
reached) and the partial backfill appended rows to the plugin's own evidence store
(`~/.hermes/plugins/curator-evolver/data/evidence.sqlite`), which is that store's normal
function; left in place (deleting from the 24 MB live DB is riskier than the rows).

## Fresh empirical reproductions (this attempt)

| ID | Result |
|----|--------|
| S1 | `looks_like_error("10 failed, 2 passed")` → **False**; same for `"20 failed"`, `"100 failed"`, `"110 failed"`; control `"7 failed, 3 passed"` → True |
| S2 | `looks_like_error({"code": 200, "status": "OK", "body": "hello"})` → **True**; same for `code:201/204/8080`; `{"code":0}` → False |
| S2-blast | 3 × `record_tool_call(result={"code":200,"body":"OK"})` → `summary.error_events == 3/3` |
| S3 | fake SessionDB, 10 040 sessions storage-ordered oldest-first, `limit=2` → yielded `["s9999","s9998"]`; newest `s10039` **never fetched** (50 pages scanned, all ≤ s9999); `stats.sessions_skipped_old=9675` |
| S4 | `"deploy failed: connection refused; earlier healthcheck reported no errors"` → **False**; `"build exceeded memory limit; cache check: no tests failed"` → **False**; pure failure control → True |
| S5 | thread holding `_path_lock` for the store's path; concurrent `summary()` completes in **0.001 s** (does not block) — reads bypass the lock the `connect()` docstring says serializes "all use" |
| S6 | `_extract_skill_name("skill_view", {"skills":["demo-skill"]})` → **None**; `_extract_skill_name("read_file", {"skills":["demo-skill"]})` → `"demo-skill"`; 2 skill-tagged events → `summary.skills[0].event_count == 1` |
| S7 | `{"exit_code":0,"error":"warning: retry succeeded"}` → **True**; `{"exit_code":0,"status":"error"}` → True — the `looks_like_error` docstring says "zero → success" |
| S8 | two SKILL.md dirs (`alpha`,`beta`) both `name: same-name` → `discover_skill_files` returns **only `beta`**; `alpha` silently dropped |
| S9 | `skills/curator-evolution/SKILL.md` frontmatter `version: 0.11.0` vs `plugin.yaml`/`pyproject.toml`/`__init__` 0.10.0; `test_u7b_version_agrees_with_plugin_yaml` pins only `__init__`==`plugin.yaml` |
| S10 | `merge-check --source /nonexistent/a` → raw `FileNotFoundError` traceback; `propose --skill-file /nonexistent/nope.md` → raw traceback; `verify --proposal-file /nonexistent/nope.json` → raw traceback; `rollback_guarded_patch` on `{not json` manifest → raw `JSONDecodeError`; `bootstrap --schedule $'daily\nExecStartPost=…'` → **rejected** (no flag file created) but as a raw `ValueError` traceback |
| P5/P6 | `auto_evolve.py:1143` `apply_guarded_patch(` and `1155-1167` support loop: `try:` absent, `support_path.write_text(content` still at **1163** |
| P8 | legacy `sessions/` import: file containing `\xff` bytes → `UnicodeDecodeError` **aborts the whole import** (uncaught; the `except (OSError, json.JSONDecodeError)` tuple doesn't cover it) |
| P9 | `_apply_managed_block` still `re.sub(..., count=1)` → stray duplicate marker leaves 2 blocks → `auto_block_count=2` → every later staged verify fails; no repair path |
| N6 | `verify_proposal({"grounding_event_count": 999, "proposed_actions":[whole-file replacement]}, report with 1 event)` → **passes, zero failures** |
| C1 | fake embedder ranks the truly-relevant skill 3rd, reranker scores it 9.0 vs 0.1 → result `["skill-a","skill-b"]`, `skill-c` **not promoted** (`candidates[:limit]` at `semantic.py:199` precedes the rerank block at `202-213`) |
| C3 | `review_queue.py:173` `update_status` still has no production caller |
| P12 | `skill_sources.py:60` — only a skills dir *literally named* `skills` maps to a hermes home; otherwise `hermes_home()` env/default → `SOURCE_UNKNOWN` (`skill_sources.py:209`) → auto-apply silently skipped |
| Q6 | external `BEGIN EXCLUSIVE` holder on the DB → one hook-path write stalls **10.27 s** before the boundary swallows it (bounded — improved from pass 5's ~15.75 s analysis — but still 10 s on the post-tool hot path) |
| cleared | F15 quarantine: garbage non-sqlite file at the DB path → quarantined `.corrupt.20260902T…`, store rebuilt, event records fine. F19 injection: blocked (see S10 row) |

## Findings — new this pass (S1–S10)

| # | Sev | Location | Finding |
|---|-----|----------|---------|
| S1 | **P2** | `candidates.py:100` | The Q1 fix's negative lookbehind `(?<!0\s)failed` was written to exclude `"0 failed"` but excludes **any count ending in 0**: `"10 failed"`, `"20 failed"`, `"100 failed"`, `"110 failed"` are classified as *successes* (reproduced). Pytest/systemd/npm summaries with round-number failure counts — the single most common failure-report shape in this plugin's own domain (the test suite it runs!) — never reach the `is_error` column. Same blast radius as Q1/S2: `error_events` cohorts gate auto-evolve eligibility and the review queue. Fix: replace with `\b[1-9]\d*\s+failed\b` (matches any nonzero count, excludes `0 failed` by construction) — no lookbehind needed. |
| S2 | **P2** | `candidates.py:115,258-262` | `_EXIT_CODE_KEYS = ("exit_code","returncode","code")` treats the generic key `code` as an exit status, so **HTTP-shaped successes are errors**: `{"code":200}`, `{"code":201}`, `{"code":204}`, even `{"code":8080,"listening":True}` (port probes, web tooling) all → `is_error=1` (reproduced; 3/3 `error_events` in the store). The Q1 truth table added exit-key *coverage* without qualifying that `code` is overloaded. Fix: drop bare `code` (keep `exit_code`/`returncode`/`status_code`-style keys), or treat 2xx/3xx `code` values as success when paired with a success status. |
| S3 | **P2** | `backfill.py:203-207` | The metadata-collection cap `metadata_cap = max(limit, 10_000)` binds in **storage order before the client-side recency sort**, so with >10 000 sessions in state.db the newest sessions are silently never considered: reproduced with 10 040 sessions, `--limit 2` → imported `s9999/s9998` (newest of the *oldest* 10 000), newest `s10039` never fetched. This is U4/U36's membership guarantee inverted at scale, and the new docstring's claim "the cap never binds a real import below its own ``limit``" is false above 10 000 sessions. Fix: cap must respect recency — e.g. keep collecting until the *sorted* prefix contains `limit` sessions newer than cutoff (plus the anti-spin bound as a separate, documented safety valve), or push the sort into SQL (`ORDER BY last_active DESC LIMIT ?`). Also: `stats["sessions_seen"]` counts yielded+remaining_old only, so it under-reports examined metadata when `limit < in-window` (10 examined → reported 5+30=35-style gaps). |
| S4 | P3 | `candidates.py:109-112,299-300` | `_SUCCESS_COUNT_PATTERN` clears a failure hit **globally**: any `"no errors"`/`"no X failed"`/`"nothing failed"` phrase anywhere in the text converts a genuine failure into a success (`"deploy failed: connection refused; earlier healthcheck reported no errors"` → success, reproduced). Fix: scope the clear to the same sentence/line as the failure match (or require the success phrase to account for the failure count). |
| S5 | P3 | `storage.py:291-299` vs `540,599,622` | The `connect()` docstring claims "all use is serialized by the path lock the write/read helpers below acquire" — but the read helpers (`summary`, `recent_tool_events`, `recent_turns`, and backfill's `*_exists` probes) call `with self.connect() as conn:` **without** `_path_lock()` (reproduced: a read completes in 1 ms while the lock is held). On the one shared `check_same_thread=False` connection this is a real interference window: a reader's `with conn:` exit `commit()`s (or, on a reader exception, `rollback()`s) whatever transaction a writer thread has open — e.g. a reader hitting `database is locked` under external contention rolls back a hook writer's in-flight insert, and the writer then "succeeds" with its event lost. Fix: take `_path_lock()` in the read helpers (they're already connection-cached), or give reads their own short-lived read-only connection. Rider: `_apply_journal_mode` runs inside the **global** `_connection_lock` (storage.py:304-330), so one slow pragma (up to `busy_timeout` under an external lock) stalls every store on every path in the process. |
| S6 | P3 | `storage.py:219-229` | `_extract_skill_name` has two branches with different key vocabularies: tools in `SKILL_TOOL_NAMES` (`skill_view`, `skill_manage`) read only `name`/`skill`/`skill_name`, while every other tool also honors the plural `skills` list. So `skill_view({"skills":["demo-skill"]})` loses attribution entirely (→ None) while `read_file({"skills":["demo-skill"]})` is attributed — reproduced: two skill-tagged events produced `summary.skills[].event_count == 1`. Since `_eligible_skill_rows` (`auto_evolve.py:808-817`) gates auto-evolution on `event_count >= min_evidence`, this silently starves exactly the skill tools the plugin exists to watch. Fix: check `skills`/`name` uniformly in both branches. |
| S7 | P3 | `candidates.py:286-302` vs `263-272`; `tests/test_candidates.py:491` | The U43 spec lives in the `looks_like_error` docstring ("``exit_code``/``returncode``/``code`` nonzero → error, zero → success") but the code checks `error`/`exception`/`status`-failure **before** the `exit_code == 0` early return, so `{"exit_code":0,"error":"warning: retry succeeded"}` is an error. The behavior is pinned by test (test_candidates.py:491), so this is a documentation defect in the very docstring that specifies the truth table — anyone implementing from the doc (as U43's reviewer must) builds a different classifier than shipped, and the next "unify the classifiers" change unit will "fix" it wrongly. Fix: correct the docstring (zero exit is success *unless* an explicit error/status-failure field is present) or reorder the checks to match the doc — pick one and pin it. |
| S8 | P3 | `auto_evolve.py:399-…` (`discover_skill_files`) | Two skill dirs whose SKILL.md carry the same frontmatter `name:` collapse into one `dict[str, Path]` entry — one directory is **silently dropped** from discovery (reproduced: `alpha` vanished, `beta` kept). Downstream, evidence for that skill name applies to whichever dir won, and the loser is never maintained. Fix: key by path (or detect collisions and surface them in the run report) instead of `dict[frontmatter_name]`. |
| S9 | P3 | `skills/curator-evolution/SKILL.md:4` vs `plugin.yaml:2`/`pyproject.toml:7` | U7b single-sourced the version across `__init__`/`plugin.yaml` but the **bundled skill surface** still declares `version: 0.11.0` against 0.10.0 everywhere else, and `test_u7b_version_agrees_with_plugin_yaml` (`tests/test_auto_evolve.py:1238-1246`) doesn't cover it. Hermes surfaces the skill-declared version; drift here is user-visible. Fix: extend the U7b test to parse the bundled SKILL.md frontmatter and assert equality. |
| S10 | P3 | `skill_audit.py:289-290`; `cli.py` propose/verify/rollback handlers; `_run_bootstrap` | P10-class raw tracebacks persist and spread: `merge-check` with a missing dir (raw `FileNotFoundError` from `inspect_skill_structure`'s unguarded read), `propose --skill-file`/`verify --proposal-file` missing files, `rollback` against a corrupt manifest (raw `JSONDecodeError`, reproduced), and `bootstrap --schedule` garbage (excellent message, but delivered as a raw `ValueError` traceback). Every one is a one-line `parser.error(...)`/typed-exit conversion. The bootstrap schedule *content* is validated (control-char/newline injection rejected, `/tmp/pwned-flag` not created — security pass). |

## Findings — carried, re-derived against the current tree this attempt

| # | Sev | Location | Status |
|---|-----|----------|--------|
| P5 | P2 | `auto_evolve.py:1143,1107-1183` | unchanged: no per-candidate `try/except` around apply/support/prune steps — one unexpected exception mid-loop loses the whole run's JSON result after earlier candidates were already mutated |
| P6 | P3 | `auto_evolve.py:1163` | unchanged: support files still plain `write_text` (no temp+rename); note `29d7ded`'s commit message claims "mode-preserving atomic writes for snapshots and support files" — true inside `guarded_apply` only, **not** for these writes |
| P8 | P2 | `backfill.py` legacy path | unchanged + newly reproduced as `UnicodeDecodeError` aborting the whole legacy import (see table above) |
| P9 | P3 | `auto_evolve.py:486` | unchanged: `count=1` sub + no self-heal for stray duplicate managed blocks |
| N6 | P3 | `verifier.py:26` | unchanged: verifier never cross-checks claimed vs report counts (reproduced: 999 vs 1 passes) |
| C1 | P3 | `semantic.py:199` vs `202-213` | unchanged + newly reproduced functionally (reranker cannot promote past the embedder slice) |
| C3 | P3 | `review_queue.py:173` | unchanged: `update_status` has no production caller (queue transitions are dead code) |
| P12 | P3 | `skill_sources.py:60,209` | unchanged: custom `--skills-dir` not named `skills` → `SOURCE_UNKNOWN` → auto-apply silently skipped |
| P14 | P3 | `.github/workflows/ci.yaml` | unchanged: CI is pytest-only; 63 ruff errors ungated (48 fixable) |
| P15 | P3 | `cli.py:372-377` | unchanged: `bootstrap --enable` defaults True (install-and-start as the default posture) |
| caps | P3 | `guarded_apply.py:26`, `auto_evolve.py:53`, `candidates.py:32` | U5 never implemented and dropped from passes 2–5: three separate 100 000 caps, **two different units** (`_BUILTIN_HARD_CAP_CHARS`/`_MAX_SKILL_CONTENT_CHARS` in chars vs `SKILL_MD_HARD_CAP_BYTES` in bytes — a 100 000-char multibyte skill passes two and can exceed the byte one, or vice versa) |

## Verification of the cycle-1–5 batches' own goals (regression check)

- **Q1 (classifier truth table)** — base cases ✅ (`"0 failed, 12 passed"` → success;
  `{"returncode":1}`/`{"code":1}` → error; `{"code":0}` → success; `{"stdout":"ok","stderr":""}`
  no longer keyed on `stderr`) — **but** S1/S2/S4 are new defect classes in the same function.
- **Q3 (mode preservation)** ✅ reproduced: chmod 0o640 survives apply **and** rollback.
- **Q4 (README rollback)** ✅ `README.md:347-358` now documents `--skills-dir` and
  `--allow-any-target` with the unrestricted-target rationale.
- **Q5 (snapshot atomicity)** ✅ `_snapshot_for_safety` routes through the atomic writer.
- **Q6 (hook stall)** partially ✅: bounded at 10.27 s measured (was unbounded/infinite);
  still a 10 s synchronous stall on the post-tool hot path under external lock.
- **Q7 (schema probe)** ✅ all three tables probed.
- **Q2/N7** ✅ (fresh grep: `from typing import Any` present; `sessions_failed` printed).
- **N2/N2b/N3 (membership/cutoff)** ✅ below 10 000 sessions (cutoff before transcripts,
  newest-first sort) — **reopened at scale by S3**.
- **P7 (systemd OnCalendar)** ✅ `_validated_on_calendar` rejects control-char schedules.
- **U7b (version single-sourcing)** ✅ for `__init__`/`plugin.yaml`/`pyproject.toml`;
  residual S9 for the bundled skill surface.
- **249/249 tests green** at the reviewed HEAD; no regressions introduced by cycles 1–5.

## Testing gaps (fresh)

1. The classifier tests (`tests/test_candidates.py:409-500`) pin only intended truth-table
   rows; none cover counts ending in 0 (S1), HTTP-style `code` values (S2), or mixed
   success+failure text (S4). My reproducers are directly liftable as cases.
2. No test asserts `summary.skills[].event_count` against `tool_events` with plural
   `skills` args (S6) — the min_evidence gate is untested end-to-end for real skill tools.
3. No backfill test exercises >10 000 sessions (S3); the fake SessionDB pattern exists.
4. `discover_skill_files` has no duplicate-frontmatter-name test (S8).
5. CI still runs pytest only (P14) — ruff (63), build, and docs checks are unenforced.

## Verdict

Directionally the repo keeps improving: every named cycle-1–5 fix verified fixed (Q1
base, Q3, Q4, Q5, Q7, N2-class below 10k, P7, Q2/N7), test count 184 → 249, and the
storage layer survived two adversarial probes it was designed for (quarantine-on-garbage,
schedule injection). But pass 6 finds the **classifier regressed into two new
misclassification classes** (S1 round-number failures, S2 HTTP-shaped successes) feeding
the same `is_error`/`error_events` column that gates auto-evolution, plus a **membership
inversion at scale** (S3) that recreates the exact bug class N2 was fixed for. No P1s;
three P2s (S1, S2, S3), all in the ingest→eligibility pipeline, all with one-file fixes
and liftable test cases. Recommended next cycle priority: S1+S2+S4 (one classifier
change unit, with the S7 docstring decision made explicitly), then S3, S6, S5.
