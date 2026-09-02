---
date: 2026-09-02
topic: hermes-curator-evolver-adversarial-repository-assessment
mode: repo-grounded
run: 589e5a44a79d4dbda45b3af824d14669
phase: assess
action: assess:assess
attempt: 76416fd23b10470085a01aea9a411f82
skill: ce-code-review methodology (adversarial repository assessment; no dedicated ce-assess skill is installed in this delegate environment - same route the fleet's prior phases recorded)
---

# Adversarial repository assessment

Fresh pass over the working tree at `45328db` plus uncommitted cycle-1 changes.
Every finding below was reproduced or read directly from current code; none is
carried forward from a prior assessment. Reproduction scripts live in
`/tmp/assess/` (see "Reproductions").

Baseline: `python -m pytest -q` → 174 passed. `ruff check .` (no repo config,
defaults) → 65 diagnostics.

## Findings

### H1. `re.sub` replacement-template injection in the managed-block writer

`hermes_curator_evolver/auto_evolve.py:386`

```python
return pattern.sub(block, skill_text, count=1)
```

`block` is built from recorded tool-result previews
(`auto_evolve.py:326,464,726`) and is passed as the *replacement template*, not
a literal. The pattern has no capture groups, so:

| Preview content | Observed result |
| --- | --- |
| `C:\1Users\test` | `re.error: invalid group reference 1` — `auto-run` exits 1, no report |
| `text \g<0> here` | the **entire original skill body is duplicated into the managed block** |
| `literal \n newline` | silently rewritten to a real newline |
| `\gZZ` | `re.error: missing <` |

End-to-end (`/tmp/assess/repro_autorun_crash.py`): a single `skill_manage`
result preview containing `\1`, against a skill that already carries a managed
block, produces `exit 1`, `re.error: invalid group reference 1 at position 522`,
and **no report at all**. The steady state of this tool *is* "skill already has
a managed block" — every run after the first. Fix: `block.replace("\\", "\\\\")`
or `pattern.sub(lambda m: block, skill_text, count=1)`.

Why 174 tests miss it: no test starts from a skill that already contains a
managed block (only two references to the marker in `tests/test_auto_evolve.py`,
both asserting the marker appears after a *first* write). See T18.

### H2. `--max-reference-files 0`: help, code, and test disagree; data loss

- `hermes_curator_evolver/cli.py:242` — help text: `"(0 disables pruning)"`.
- `hermes_curator_evolver/cli.py:803` — `int(values.get("max_reference_files") or 5)`:
  an explicit `0` is falsy, so it is silently rewritten to `5`. The documented
  value can never reach the pruning function through the CLI.
- `hermes_curator_evolver/auto_evolve.py:414` — the guard is `if keep < 0`, so
  `keep == 0` passes through and `generated[keep:]` at :422 becomes "all files".
  Reproduced directly: `prune_auto_reference_files(dir, "demo", 0)` deleted the
  reference file written by that same apply, leaving the SKILL.md pointer
  (`Detailed evidence moved to references/...`) dangling.
- `tests/test_auto_evolve.py:1106` asserts the delete-all behaviour, i.e. the
  test codifies the opposite of the help text.

### H3. systemd unit injection and `%`-specifier mangling

- `hermes_curator_evolver/auto_evolve.py:1386` — `f"OnCalendar={on_calendar}"`.
  `--schedule` is user input interpolated raw into the timer unit. Reproduced:
  `install-auto --schedule $'daily\n[Service]\nExecStart=/bin/touch /tmp/pwned'`
  wrote a second `[Service]` section with that `ExecStart=` into
  `hermes-curator-evolver-auto.timer` (same-user config injection; `Type=oneshot`
  permits multiple `ExecStart` lines, so the injected command would run).
- `hermes_curator_evolver/auto_evolve.py:190` — `_systemd_quote` escapes only
  `\` and `"`, never `%`. Reproduced: a skills dir `/tmp/weird 100%/skills`
  lands in `ExecStart` unescaped; systemd expands `%h`, `%n`, `%i`, `%/`
  specifiers inside `ExecStart` and silently rewrites the scheduled command.
  Only `%%` survives a unit file.

### H4. Evidence is silently dropped under write contention

`hermes_curator_evolver/storage.py:155` (`sqlite3.connect(self.db_path)` — no
`timeout=`, no WAL, no retry) combined with `hermes_curator_evolver/hooks.py:13`
(a fresh `EvidenceStore` per hook invocation).

Reproduced with another curator process holding `BEGIN EXCLUSIVE` (i.e. the
daily timer or a backfill running while a session is live): all 3 hook calls
blocked for the full 5.01 s default timeout, logged
`curator-evolver post_tool_call failed: database is locked`, and recorded
**0 of 3** tool events. Evidence is the product's entire input, and the loss is
invisible to the user (warning-only).

### M5. Backfill dedup collision drops events from ID-less transcripts

`hermes_curator_evolver/backfill.py:271-272`

```python
call_id = _tool_call_id(call, call_index)      # call_index resets per message
task_id = f"backfill:{session_id}:{call_id}"
```

`call_index` comes from `enumerate(calls)` inside a per-message loop, so two
messages each carrying a call at index 0 produce the same `task_id`
(`backfill:<sid>:tool-0`) and the same `tool_name`. `_tool_event_exists` then
treats the second as a duplicate and skips it. Reproduced
(`/tmp/assess/repro_backfill_dedup.py`): a 3-call legacy session imported
**1** tool event.

### M6. Marker injection permanently blocks a skill's auto-evolution

`hermes_curator_evolver/auto_evolve.py:326,464,726` never strip the plugin's own
managed-block markers from evidence previews. Reproduced: a preview containing
`<!-- curator-evolver:auto:end -->` produced a SKILL.md that fails
`_run_builtin_cheap_check` with `unbalanced-managed-block-markers:1!=2`, so the
apply is rolled back — and because the evidence does not change, the next daily
run regenerates the identical bad block and fails again, forever, with no
signal beyond a `verify-failed` candidate row.

### M7. Reference-spill support files bypass the verification gate

`hermes_curator_evolver/auto_evolve.py:1057-1065` — `support_path.write_text(...)`
runs *after* `apply_guarded_patch` has already verified and committed, with no
size bound and no error handling. `register_support_file_in_manifest`'s return
value is discarded, so a failed snapshot is silent. The SKILL.md managed block
points at a file the verify command never saw.

### M8. Two skill-identity schemes; semantic ordering silently no-ops

`auto_evolve.discover_skill_files` (auto_evolve.py:280-297) keys skills on the
frontmatter `name:` field; `semantic._skill_name` (semantic.py:66-73) keys on the
directory name. Reproduced with `name: front-name` in `dir-name-v2/`:
`discover_skill_files` → `front-name`, `_skill_name` → `dir-name-v2`. In
`_select_candidate_skill_names` (auto_evolve.py:690) every semantic result whose
dir name differs is dropped by `if name not in eligible_set`, so
`--semantic-candidates` / `--rerank-candidates` degrade to evidence order with
only a `fallback` key as a hint. The opt-in model path can do nothing while
reporting success.

### M9. `summary()` computes the cutoff three times

`hermes_curator_evolver/storage.py:65` is called three separate times inside
`summary()` (tool window, turn window, session window). A clock tick between
calls yields mutually inconsistent counts inside a single report and makes
outputs non-reproducible at the second boundary.

### M10. Backfill reads every transcript before applying the date cutoff

`hermes_curator_evolver/backfill.py:175-231` fetches the full message list for
every session in `_iter_state_sessions`; the `days` cutoff is applied by the
*caller* at backfill.py:410. `backfill-sessions --days 1` on a large `state.db`
still reads every message of every session. `collected` (backfill.py:212) also
holds all session metadata in memory when `limit` is unset.

### M11. Restore drill opens the live evidence DB read-write

`hermes_curator_evolver/restore_drill.py:330` — `sqlite3.connect(str(path))`,
while the docstring at :303 states "The drill must not mutate the live evidence
database". A WAL or hot-journal DB can be checkpointed/recovered on connect or
close. Should be `file:...?mode=ro` (the pattern `review_queue._connect`
already uses at review_queue.py:98).

### M12. No per-candidate exception boundary in `run_auto_evolve`

The loop at auto_evolve.py:846-1135 has no try/except. The H1 crash aborts the
whole pass with `exit 1` and no report or summary; the daily systemd/launchd
timer records only a traceback. One bad skill should be a counted skip like the
backfill path already does (backfill.py:405-411).

### L13. Version governance drift

`hermes_curator_evolver/__init__.py:11` = `0.8.0`; `pyproject.toml:7` and
`plugin.yaml:2` = `0.10.0`; `hermes_curator_evolver/skills/curator-evolution/SKILL.md:4`
= `0.11.0`; README "Roadmap status" ends at `v0.14` while the README "Model
usage plan" table ends at `v0.13`. Five inconsistent version signals.

### L14. `or <default>` coercion swallows explicit zeros

`hermes_curator_evolver/cli.py:787,788,800,803` — `int(values.get(...) or N)`
rewrites `--max-skills 0` → 3, `--min-evidence 0` → 2, `--variants 0` → 1,
`--max-reference-files 0` → 5. Explicit user input is silently replaced.

### L15. Raw tracebacks for ordinary user mistakes

- `merge-check --source /nope/a` → `FileNotFoundError` traceback
  (`skill_audit.py:288-289` calls `read_text` with no existence check).
- `candidates-list --queue-db /nope/q.sqlite` → `FileNotFoundError` traceback
  (`review_queue.py:85`).
- `candidates-mine` on a bad JSONL line → `json.decoder.JSONDecodeError`
  traceback with no file/line context (`cli.py` `_load_jsonl_records`).

### L16. Non-atomic target writes

`guarded_apply.py:315` (`target.write_text`) and `auto_evolve.py:1057` write in
place with no temp+rename. A crash mid-write leaves a truncated SKILL.md that
only a manual rollback would repair.

### L17. Unbounded drill-directory accumulation

`restore_drill.py:430` deliberately leaves every `tempfile.mkdtemp()` in place
for operator inspection, with no retention bound or cleanup command.

### T18. Test gap: the managed-block *replace* path is untested

No test in `tests/test_auto_evolve.py` starts from a skill that already contains
a managed block, so the `re.sub` branch at auto_evolve.py:386 — the path taken
by every run after the first — has zero coverage. This is exactly why H1
survives a 174-test suite.

### T19. No lint configuration or CI lint gate

`ruff check .` with no repo config reports 65 diagnostics (46 auto-fixable):
29×UP017, 8×BLE001, 5×F401, 5×SIM103, 4×I001, 3×N999, 3×PLR0402, 3×UP035,
1×B009/ISC004/SIM102/SIM118/UP012. `.github/workflows/ci.yaml` runs pytest only.

### T20. Review queue has no decide surface

`review_queue.update_status` (review_queue.py:173) exists but no CLI command
exposes it. `candidates-mine` / `candidates-list` are the only queue commands,
so a reviewer must hand-edit SQLite to accept or reject anything — the
"human-review queue" loop is not closable from the product's own interface.

## Reproductions

| Finding | Script |
| --- | --- |
| H1 | `/tmp/assess/repro_sub_escape2.py`, `/tmp/assess/repro_autorun_crash.py` |
| H2 | inline python in transcript; `/tmp/assess/repro_misc2.py` |
| H3 | `install-auto` invocations (transcript); `/tmp/assess/repro_misc.py` |
| H4 | inline python in transcript (BEGIN EXCLUSIVE holder) |
| M5 | `/tmp/assess/repro_backfill_dedup.py` |
| M6 | `/tmp/assess/repro_misc2.py` |
| M8 | `/tmp/assess/repro_misc.py` |
| M9 | `/tmp/assess/repro_misc.py` |
| M12 | inline python in transcript (good+bad pair, no report) |
