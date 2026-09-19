# Improve error behavior in curator-evolver

Autonomous proposal prop_8c5390ffe26640fa (score 0.622, risk 0.30000000000000004).

## Problem
Observed 1 error-related event(s) requiring investigation. Recommended approach: Add detection, bounded recovery, and explicit validation around the failing behavior.

## Plan
- Reproduce and baseline the observed problem.
- Implement candidate 'guarded' in an isolated/reversible workspace.
- Run targeted and full deterministic tests.
- Run trajectory/adversarial evaluation and compare to baseline.
- Submit for independent review and only then request approval for consequential promotion.
- After approval, route implementation through Conductor and measure the real outcome.

## Repository remote
Push feature branches to the git remote named `fork` (codeo1io fork), never to `origin` and never to upstream.

## Acceptance
- The failing behavior described above is reproduced and understood.
- The change lands on a feature branch off the current default branch.
- Targeted tests for changed surfaces pass (never the full suite).
- The branch is pushed to the repository fork/remote; do not merge to upstream.

---

## Extension 2026-09-02 - maintenance cycle 1

Provenance: adversarial assessment (`ce-code-review`, verdict not phase-clean, 16 findings - 6 P2, 10 P3) at HEAD `45328db` plus extension research (`ce-ideate`, 7 ranked survivors, 8 rejections with reasons). Durable artifacts: `/home/agent/.hermes/conductor-runs/8a1ca9a2a18e440e86bff85efe099474-assess/` (`review.md`, `review.json`, `repro-adversarial-findings.sh` - five reproducers F1-F5, all reproduce) and `/home/agent/.hermes/conductor-runs/8a1ca9a2a18e440e86bff85efe099474-research/` (`research.md` + four evidence dossiers). Declared deviations: no subagent primitive in this harness, so all review lenses and ideation frames ran in one context; no independence is claimed.

The original Problem above ("observed 1 error-related event") is now root-caused: a NUL byte inside a recorded tool result survives sanitization (`hermes_curator_evolver/storage.py:81` strips the four-character literal `\x00`, not the byte), and every later auto-apply for that skill fails skill validation and rolls back forever - a perpetual error loop with no detection or bounded recovery, exactly the class this plan targets. U1 closes it; the remaining packets harden the same write path and then extend it.

### Completed in cycle 1

- 2026-09-02 `assess` - fresh adversarial review of all 38 Python files; verdict not phase-clean; 0 P1 / 6 P2 / 10 P3; pytest 156/156 at HEAD; five reproducers written, all reproduce (F1 NUL, F2 "cap" substring, F3 rollback orphan, F4 chars-vs-bytes cap, F5 workflow false positive).
- 2026-09-02 `research` - extension candidates grounded in live upstream state (hermes-agent v0.21.0 / v2026.8.31: native curator subsystem, protected-instruction-file approval gate PR #81152, native cron; issues #67582/#77264/#66180; SkillClaw; agentskills.io spec); 7 survivors, 8 rejections recorded below.
- 2026-09-02 `roadmap` - this extension; append-only, all prior sections preserved byte-identical.

### Blocking issues discovered (assessment)

B1. NUL sanitizer is a no-op against real NUL bytes (`hermes_curator_evolver/storage.py:81`): poisoned evidence flows DB -> managed block -> `skill_validate` fails "contains NUL byte" -> every auto-apply for the skill rolls back forever. Reproduced end-to-end (F1: `nul_stored=True in_managed_block=True validator_ok=False`). -> U1.
B2. Failure classification by substring: `_is_tool_failure` treats any text containing "cap" as a tool failure (`hermes_curator_evolver/candidates.py:200`), so the successful result `{"success": true, "message": "skill capabilities updated"}` is classified `replay_benchmark` with `is_error=True` (F2). -> U2.
B3. Rollback is incomplete and spills are never pruned: `rollback_guarded_patch` (`hermes_curator_evolver/guarded_apply.py:390-416`) restores only SKILL.md while support files registered via `register_support_file_in_manifest` (:341) are left on disk (F3: target rolled back, orphan support file remains), and `references/curator-evolver-auto-<ts>.md` files created at `auto_evolve.py:398/:1023` are pruned nowhere - unbounded growth per apply. Rollback also copies `manifest['backup_path']` to `manifest['target_path']` with no under-skills-dir path validation. -> U3.
B4. State-DB import assumes newest-first session ordering it does not verify (`hermes_curator_evolver/backfill.py:374-376`) - silent truncation if ordering differs - and one blanket `except Exception` (:385) aborts the whole import on a single bad row. -> U4.
B5. Size caps count characters, not bytes (`hermes_curator_evolver/guarded_apply.py:25`, enforced at :99-100): a 60,031-CJK-character SKILL.md is 180,031 bytes yet passes the 100k gate (F4), while candidates.py already caps in bytes (`SKILL_MD_HARD_CAP_BYTES`). -> U5.
B6. Bootstrap defaults to install + enable + unattended auto-apply in one command (`hermes_curator_evolver/cli.py:348-353` `--enable` default True; :497 `apply_low_risk = not proposal_only`), inconsistent with `install-auto`'s opt-in `--enable` (:436). -> U6.

The ten P3s ride inside U7 except where a unit already owns the surface: verifier self-attestation (`verifier.py:25-27`), unescaped untrusted previews persisted into skills (`auto_evolve.py:321/:401`), no WAL/busy_timeout plus hooks swallowing errors (`storage.py:139`), version quadruple-drift 0.8.0/0.10.0/0.10.0/0.11.0 (`__init__.py:11`, `pyproject.toml:7`, `plugin.yaml:2`, bundled `hermes_curator_evolver/skills/curator-evolution/SKILL.md:4`), `_looks_workflow` two-backtick false positive (`candidates.py:175-184`, F5 - rider on U2), merge-check FileNotFoundError traceback (`skill_audit.py:288-289`, :125), `shell=True` verify with full env (`guarded_apply.py:44-56` - rider on U3's path hardening), semantic `batch_size=1` and rerank-on-500-char-previews (`semantic.py:129/:196/:205` - rider on U8), CI pytest-only with no NUL/ordering coverage (`.github/workflows/ci.yaml`).

### New work packets

U1. NUL byte sanitizer with end-to-end regression
- AC: `storage.py` sanitization removes actual NUL bytes (both the escaped-literal and the byte forms) from tool-result text before persistence, applied at every write path (hooks ingest and backfill import); a regression test plants a NUL-bearing tool result and drives it evidence -> report -> proposal -> `skill_validate` -> guarded apply to completion.
- E: reproducer F1 re-run green (`validator_ok=True`, no perpetual rollback); targeted pytest for storage ingest and backfill import; full suite still green.

U2. Tokenized failure and workflow classification
- AC: `_is_tool_failure` decides on structured signals (JSON `success`/`error` keys, exit codes, exception markers) rather than substrings; `_looks_workflow` requires command-sequence evidence, not two backtick spans; both classifiers covered by an adversarial corpus test (success payloads mentioning "cap"/"capability"/"capture", prose with inline code, single commands).
- E: reproducer F2 re-run shows `type=replay_benchmark is_error=False` for the success payload; F5 re-run shows no `skill_new` for two-backtick prose; corpus test in `tests/`.

U3. Rollback completeness, path validation, and spill retention
- AC: rollback removes or restores every support file recorded in the apply manifest (no orphans); `backup_path`/`target_path` are validated to resolve under the skills directory before any copy; auto-generated `references/curator-evolver-auto-*.md` files get a retention bound (keep most-recent N per skill, N configurable, default small) applied on every auto-run; verify-command execution no longer forwards the full parent environment.
- E: reproducer F3 re-run shows the target rolled back AND no orphan support file; a two-apply scratch test shows the references directory bounded; a tampered-manifest test shows the copy refused; targeted pytest.

U4. Backfill per-session isolation and explicit ordering
- AC: session iteration filters by explicit timestamp comparison (no ordering assumption) and sorts client-side; each session imports inside its own error boundary with per-session error accounting surfaced in the import summary; ordering contract documented next to the SessionDB call.
- E: a synthetic state-DB fixture with oldest-first/shuffled ordering imports the identical session set; a corrupted row yields a counted skip, not an aborted import; targeted pytest.

U5. Byte-based size caps, single-sourced
- AC: one shared bytes-based cap helper replaces `_BUILTIN_HARD_CAP_CHARS` and is used by both guarded_apply and candidates; docs state bytes.
- E: reproducer F4 re-run shows the 180,031-byte CJK file rejected by the builtin gate; targeted pytest for both call sites.

U6. Bootstrap default alignment
- AC: `bootstrap` installs disabled by default and applies nothing unless flags mirror `install-auto`'s opt-ins (`--enable`, explicit `--apply-low-risk` or `proposal_only` default true); printed next-steps tell the operator exactly how to opt in; README quickstart updated to match.
- E: CLI test asserting default bootstrap = plugin installed, disabled, proposal-only; a second test asserting each opt-in flag's effect; README diff.

U7. Hygiene batch (P3 closers)
- AC: verifier cross-checks the proposal's claimed grounding count against report rows; previews persisted into managed blocks are escaped/neutralized (fenced, control characters stripped, length-bounded); evidence DB opens with `journal_mode=WAL`, `busy_timeout`, and a bounded retry on lock; version is single-sourced (one definition consumed by `__init__.py`, `plugin.yaml`, and the bundled skill, plus a test asserting equality); `check_consolidation_capacity` handles missing SKILL.md/read errors gracefully; CI adds lint (ruff), type (mypy), and coverage gates to the existing pytest matrix.
- E: unit tests per item (grounding cross-check rejects an inflated count; a preview containing markdown/ANSI/control characters round-trips inert; a WAL-mode concurrent-writer test); `ruff check` and `mypy` clean; version-equality test fails on an induced drift; CI green with the new gates.

U8. Dedupe scan - near-duplicate detection feeding merge proposals (research survivor 1)
- AC: new `dedupe-scan` command runs pairwise similarity over the skill library using the existing lexical scorer with embeddings as optional acceleration (batch embedding, not `batch_size=1`); merge proposals route through `check_consolidation_capacity` and land in the review queue as reviewable rows - never auto-merged; `--include-archive` mode surfaces dormant near-duplicates for re-home or merge (upstream issue #77264); thresholds configurable.
- E: synthetic library fixture with planted near-duplicates: all found, zero false merges, capacity guard rejects an oversized merge with a named reason; queue rows typed correctly; lexical-only run (no model) produces the same top-k on the fixture.

U9. Staleness report and agentskills.io frontmatter conformance (research survivor 2)
- AC: `report --stale` combines evidence-store last-loaded dates, age-versus-volatility class, and a structural-drift check (commands/paths a skill references still resolvable); applies stamp spec-conformant `metadata` review keys; `skill_validate` enforces the agentskills.io contract (name <=64 lowercase-hyphen, description <=1024, `compatibility` <=500, `metadata` string-map typing) with actionable messages; `audit-skills` namespace collision with `hermes skills audit` resolved or documented.
- E: validator tests over spec edge cases (boundary lengths, bad charset, non-string metadata values); a stale-skill fixture with a gone-command reference is flagged; fresh skills are not.

U10. Missed-trigger detection (research survivor 3)
- AC: `report --missed-triggers` joins tool-failure events against skill-load events plus description matching to rank skills that existed but were never loaded when a matching failure occurred; outputs trigger/description improvement candidates into the review queue.
- E: fixture with a recorded failure matching a loaded-elsewhere skill description yields exactly that candidate; unrelated failures yield none; lexical-only default.

U11. Hub-skill learning via managed-block rebase (research survivor 4)
- AC: opt-in flag permits bounded managed-block learning on hub-installed skills without weakening the provenance gate (block-only, never upstream content); on detected upstream refresh (`.hub/lock.json` version change), the learned block is re-applied onto the new upstream content; conflicts are flagged into the review queue instead of written.
- E: fixture simulating `hermes skills update` (upstream content changes) preserves the learned block byte-identically when compatible and queues a conflict row when not; provenance gate still refuses non-block writes to hub skills.

U12. Upstream trust-posture interop (research survivor 5)
- AC: the write gate honors `security.protected_instruction_files` (plus extra patterns) - never writes those paths; `skills.write_approval: true` detection downgrades auto-apply to proposal-only output with an explanatory log; `status` reads `.usage.json`/native-curator state and a `doctor` check reports mutator conflicts (native curator auto-run, this plugin's timer, SkillClaw proxy in `~/.hermes/config.yaml`).
- E: config-fixture tests for each gate (protected path refused; write_approval -> proposals only; doctor flags a simulated three-mutator setup); documented behavior in README trust section.

U13. Native cron scheduler backend (research survivor 6)
- AC: `install-auto --scheduler cron` registers the daily run as a Hermes cron job with version detection (requires hermes-agent >= v0.21.0; host currently 0.20.6 - feature must no-op with guidance below that); systemd/launchd remains the explicit alternative; uninstall removes the cron registration; Windows becomes installable via this backend.
- E: install/uninstall round-trip against a version-stubbed environment on a scratch Hermes home; detection test for 0.20.6 vs 0.21.0; timer listing shown.

U14. Static HTML report (research survivor 7)
- AC: `report --format html` and `candidates-list --format html` emit a self-contained static file (inline CSS/JS, no network, no daemon) covering evidence timeline, skill health, queue, and apply/version history from existing manifests.
- E: rendered output opens offline (file://, no external requests); JSON and markdown outputs unchanged; an HTML-escaping test over adversarial skill names/previews.

### Decisions

KTD1. Hardening precedes extension: U1-U7 land before any of U8-U14. The write path is the trust boundary every extension reuses; shipping features on a rollback path that orphans files (B3) or a cap that miscounts (B5) compounds risk. (session-settled: conductor-directed - the work order sequences remediation from the assessment before feature work.)
KTD2. Remote policy unchanged: feature branches push to the `fork` remote only, never `origin` or upstream, per the Repository remote section above.
KTD3. Bytes, not characters, for every size cap (U5) - one shared helper, matching `SKILL_MD_HARD_CAP_BYTES`.
KTD4. Model-free default preserved: U8-U14 must produce correct output with lexical-only defaults; embeddings and model drafting stay optional accelerators behind explicit configuration.
KTD5. Coordinate with the native curator rather than duplicate it: hermes-agent v0.21.0 ships its own usage/lifecycle/consolidation curator; this plugin's differentiated surface is the tool-call evidence store, bounded managed blocks, and the guarded apply - U12 (interop) is sequenced before any overlapping feature.
KTD6. Visibility without a daemon: U14 is a static artifact, not a server - no ports, no background process, unlike the proxy+daemon competitor posture.

### Sequencing

U1 -> U2 -> U3 first (the correctness core the original Problem names), then U4 -> U5 -> U6 -> U7 as the second hardening batch; both batches may be split into stewardship-sized change units since surfaces are disjoint. After hardening, U8 -> U12 are the highest-value extension order (dedupe evidence is strongest; interop prevents conflicts with upstream), with U9/U10 next and U13 gated on hermes-agent >= v0.21.0 at the host; U14 any time after U7. The original Acceptance section governs each implementation cycle: feature branch off the default branch, targeted tests for changed surfaces, push to `fork`, no upstream merge.

### Rejected directions (research cycle 1)

- Pre-create similarity gate consulted by native `skill_manage` - no plugin hook exists on skill creation upstream, and an advisory command agents must remember to call is exactly the behavior issue #66180 shows they lack. Superseded by U8.
- Replay-benchmark harness scoring skill updates by re-running tasks - no honest ground truth for "behavior improved" is locally constructible; the feasible core (referenced commands still resolve) is folded into U9's structural-drift check.
- Multi-profile/Bot-Mode evidence aggregation - upstream profile-to-skills-directory contract unverified; revisit after reading profile-routing docs.
- Cross-agent export or marketplace publishing - strategy misfit: the README positions the project as Hermes-native and explicitly "not a skill marketplace".
- Git-backed PR-like review mode - the review queue plus managed blocks already cover review; adds weight without user-demand evidence.
- MCP server exposing the queue - no demand evidence; CLI surface already consumable; widens the security surface.
- `audit-skills` rename as standalone work - cosmetic; folded into U9.
- Assessment P3 fixes as feature candidates - they are U7 hygiene, not roadmap features.

---

## Extension 2026-09-02 - maintenance cycle 2

Provenance: cycle-2 adversarial assessment (`ce-code-review` methodology, 20 findings - 4 P1 / 6 P2 / 10 P3, all reproduced or read from current code; artifact `docs/assessment/2026-09-02-adversarial-repository-assessment.md`, reproducers under `/tmp/assess/ce-assess-76416fd2/`) plus cycle-2 extension research (`ce-ideate`, 5 ranked survivors + 4 evidence corrections from a 16-candidate pool with rejection log; artifact `docs/ideation/2026-09-02-cycle-2-extension-research.md`, E3 reproducer `/tmp/research-070899e1/e3_secret_exposure_repro.py`). Baseline at cycle-2 assess: pytest 174/174 at HEAD `45328db` + uncommitted cycle-1 batch; ruff (no repo config) 65 diagnostics. Roadmap discipline unchanged: pure append, all prior sections preserved byte-identical (pre-image sha256 `79adfbe42fa5f9f25ac2426469327aac40e3f9eb727250c99dd451eb94a904a6`, saved at `/tmp/roadmap-before-cycle2.md`).

### Cycle-1 packet status (verified in working tree this cycle)

- U1-U4 **landed in the uncommitted cycle-1 batch**: U1 NUL sanitizer both forms (`storage.py:79`, tests `test_recorded_tool_results_never_store_nul_bytes`, `test_backfill_import_strips_nul_bytes_from_recorded_tool_results`); U2 structured-signal classification (`candidates.py:210`, capability-word corpus tests); U3 rollback completeness + retention + tamper refusal (`guarded_apply.py:426` `_rollback_support_files`, `prune_auto_reference_files`, tampered-manifest/env-allowlist tests); U4 ordering-independent import + per-session error accounting (backfill tests for shuffled order and counted failures).
- U5, U6, U7 **remain open** (chars cap still `_BUILTIN_HARD_CAP_CHARS`; bootstrap `--enable` still `default=True` at `cli.py:358-361`; no WAL/busy_timeout, version still five-way drift, CI still pytest-only).
- U8-U14 remain planned extensions, unstarted.

### Blocking issues discovered (cycle-2 assessment)

B7. Managed-block writer passes evidence-derived text as the `re.sub` replacement template (`auto_evolve.py:386`): a tool-result preview containing `\1` crashes `auto-run` (exit 1, `re.error: invalid group reference`, no report); `\g<0>` duplicates the entire skill body into the block. Trigger is any skill that already carries a managed block - every run after the first. No test starts from a pre-blocked skill, so the steady-state replace branch has zero coverage. -> U15.
B8. `--max-reference-files` contract is self-contradictory in the just-landed U3 code: CLI help says "0 disables pruning" (`cli.py:242`), `int(values.get(...) or 5)` at `cli.py:803` silently rewrites an explicit 0 to 5, and `prune_auto_reference_files` guards with `keep < 0` (`auto_evolve.py:414`) so keep==0 deletes every auto reference including the one written by the same apply; `tests/test_auto_evolve.py:1106` asserts the delete-all. Same `or`-coercion swallows explicit zeros for `--max-skills`, `--min-evidence`, `--variants` (`cli.py:787,788,800`). -> U16.
B9. Scheduler unit generation injects raw user input: `--schedule` is interpolated into `OnCalendar=` unvalidated (`auto_evolve.py:1386`) - a newline-bearing value writes an arbitrary second `[Service]`/`ExecStart=` section into the user's timer (reproduced); `_systemd_quote` (`auto_evolve.py:190`) escapes only `\` and `"`, never `%`, so systemd specifier expansion rewrites `ExecStart` for paths like `/tmp/weird 100%/skills`. -> U17.
B10. Evidence is silently dropped under write contention: no WAL/busy_timeout/retry (`storage.py:155`) plus a connection per hook call (`hooks.py:13`); with a concurrent writer every hook blocks 5.01s then drops the event (0 of 3 recorded, warning-only). This is cycle-1 U7's third bullet at P1 severity, now corroborated upstream by NousResearch/hermes-agent#101035 (`SQLite busy_timeout=0 causes SQLITE_BUSY crash loop`). -> strengthens U7, not a new packet.
B11. Pipeline integrity cluster: `run_auto_evolve`'s candidate loop has no per-candidate exception boundary (`auto_evolve.py:846`) so one bad skill aborts the whole pass with no report; reference-spill support files are written after verification with no size bound and with `register_support_file_in_manifest`'s return discarded (`auto_evolve.py:1057-1065`); backfill's per-message dedup index collides in ID-less transcripts (`backfill.py:271-272`, 3 calls -> 1 stored). -> U18 and U19.
B12. Two skill-identity schemes: `discover_skill_files` keys on frontmatter `name:` (`auto_evolve.py:280-297`) while `semantic._skill_name` keys on the directory name; when they differ every semantic candidate is dropped (`auto_evolve.py:690`), so `--semantic-candidates`/`--rerank-candidates` silently no-op. -> U19.

### New work packets - cycle-2 remediation

U15. Managed-block replacement safety
- AC: `_apply_managed_block` treats the block as a literal (lambda replacement or escaped template) so no evidence-derived sequence can alter the substitution; previews are neutralized for the block (control characters stripped, plugin markers removed, length-bounded); a second-run regression test starts from a skill that already contains a managed block and drives adversarial previews (`\1`, `\g<0>`, `\n`, embedded auto:end marker) through prepare->apply with no crash and no marker duplication.
- E: cycle-2 reproducers re-run green: `repro_sub_escape2.py` (no re.error, block literal), `repro_m12_no_report.py` (exit 0, report emitted, other candidates intact), `repro_misc2.py` (marker-bearing preview no longer yields `unbalanced-managed-block-markers`); new second-run test in `tests/`.

U16. Numeric-flag contract repair (explicit zeros honored)
- AC: CLI option parsing distinguishes unset from explicit 0 for `--max-reference-files`, `--max-skills`, `--min-evidence`, `--variants`; the documented "0 disables pruning" is implemented end-to-end (keep=0 prunes nothing) and the help, code, and test agree; a test drives each flag through the CLI with 0 and asserts the value reaches the config object unchanged.
- E: `repro_h2_prune_zero.py` re-run shows keep=0 -> no deletions and `cli.py` passes 0 through; the old delete-all assertion at `tests/test_auto_evolve.py:1106` is replaced by a disables-pruning assertion with the contradiction documented in the diff.

U17. Scheduler unit hardening
- AC: `--schedule` is validated against the systemd calendar grammar subset (no newlines, no `]`/`[` directive injection) and rejected with an actionable error; `_systemd_quote`/`_quote_systemd_arg` escape `%` as `%%` in every unit-file argument; generated units are written with a single `ExecStart` and cannot gain sections from any flag value; tests inject a newline-bearing schedule, a `%h` path, and a space-bearing path and assert the unit content.
- E: `repro_h3_systemd.py` re-run shows the injected lines rejected at the CLI (non-zero exit, no file written) and a `%/`-bearing path rendered as `%%` in the unit; `systemd-analyze verify` (when available) accepts the generated units in a scratch XDG_CONFIG_HOME.

U18. Apply-loop resilience
- AC: each candidate applies inside its own error boundary; an unexpected exception becomes a counted skip with the exception class recorded, the loop continues, and the run always emits a report with a summary; support files are written before verification within the same guarded transaction or are verified after write (size-bounded, errors recorded, manifest registration checked); target writes become atomic (temp+rename) so a crash cannot leave a truncated SKILL.md.
- E: a two-skill fixture where the first candidate raises and the second succeeds shows both reflected in one report (`candidates[0].status == "failed:<class>"`, `candidates[1].status == "applied"`); a mid-write interruption test (monkeypatched write) leaves either the old or new full file, never a partial one; targeted pytest.

U19. Skill identity and dedup-key unification
- AC: one function is the single source of skill identity (frontmatter name with directory-name fallback or vice versa - chosen once, documented) consumed by `discover_skill_files`, `semantic._skill_name`, and `_select_candidate_skill_names`; backfill dedup keys on a stable per-call identifier (session id + message index + call index, or the transcript's own call id when present) so ID-less transcripts cannot collide; tests plant `name:` != dir-name skills and a multi-message ID-less transcript.
- E: `repro_misc.py` re-run shows semantic candidates surviving the name mismatch (no silent `fallback` for an eligible skill); `repro_backfill_dedup.py` re-run stores 3 of 3 calls; targeted pytest.

U20. Hygiene batch (cycle-2 P3 closers)
- AC: `summary()` computes the window cutoff once per report; backfill applies the days cutoff before reading transcripts; `_check_evidence_refs` opens evidence DBs read-write never (mode=ro URI); CLI surfaces clean errors with file/line context for merge-check missing paths, missing queue DBs, and malformed JSONL; restore-drill scratch dirs get a retention bound or `--keep` default; `candidates-decide` (U25) may land here or standalone.
- E: unit tests per item (one-cutoff assertion; a fake state DB with old sessions read zero messages; ro-mode assertion via `PRAGMA query_only`; a bad-jsonl fixture error names file and line number); drill retention test.

### New work packets - cycle-2 extensions (research survivors)

U21. Publish-safety: secret scrubbing + guard-scan gate (research survivor 1)
- AC: secret-shaped content is neutralized in previews at every ingest path (hooks and backfill) using the same detection classes as upstream `tools.skills_guard`; the apply gate refuses any update whose resulting skill content scans `dangerous` (import upstream scanner when importable, local regex fallback otherwise), recording `gate:blocked:skills-guard:<finding>`; `report --publish-risks` lists skills whose current content would fail the publish gate, naming plugin-authored evidence lines.
- E: `e3_secret_exposure_repro.py` re-run shows the token neutralized before persistence AND the apply refused (no `dangerous` verdict on the resulting skill); a scan-unavailable fallback test; `report --publish-risks` flags a planted skill and names the offending managed-block line.

U22. Anti-pattern ledger (research survivor 2)
- AC: every verify-failed or rolled-back apply persists a digest (skill name + block hash + failure reason); auto-run suppresses regeneration of an identical block, recording `suppressed-repeat:<n>` instead of re-applying; ledger entries expire when their underlying evidence rows leave the window; `--clear-anti-pattern <skill>` is the escape hatch and is surfaced in `report`.
- E: the cycle-2 marker-loop scenario (`repro_misc2.py` class) runs twice: first run records the failure, second run suppresses with a counted skip and no file write; a ledger-expiry test ages evidence past the window and shows suppression lifted; targeted pytest.

U23. Evidence retention + compaction (research survivor 4)
- AC: `evidence-prune --before <iso> [--keep-aggregates]` deletes raw rows past a retention window while preserving per-skill aggregate counters so reports remain meaningful, then VACUUMs; retention default is configurable and `0` means keep-forever (honoring the U16 contract); `status` reports DB size, row counts, and oldest row.
- E: a fixture DB with rows inside and outside the window prunes exactly the outside set, keeps aggregates, and shrinks on disk; `--keep-aggregates` off drops aggregates too; `status` output includes size/oldest; growth re-measured on this host shows the production DB bounded after a prune (before: 6,675 events / 7.2 MB at cycle-2 research time).

U24. Outcome-linked apply telemetry (research survivor 3)
- AC: each apply manifest records a pre/post cohort delta (error-marked tool events for the skill in equal-length windows before/after the apply timestamp, computed from existing tables, no model); `report --outcomes` ranks applies by delta with cohort sizes printed; a negative delta files a rollback SUGGESTION into the review queue - never auto-rollback; output states the small-cohort caveat explicitly (decision aid, not a benchmark).
- E: a synthetic timeline (3 errors before, 0 after / the reverse) yields the expected signed deltas and exactly one queued suggestion for the negative case; `report --outcomes` renders both cohorts; no auto-mutation of any skill in either case.

U25. `candidates-decide` - close the review loop (research survivor 5)
- AC: `candidates-decide --id N --accept|--reject [--note text] [--format json]` wraps the existing `review_queue.update_status`, emits the updated row, and refuses unknown ids with a clean error; optional provided tool `curator_review_decide` exposes the same operation through the plugin host's `provides_tools` surface; docs show the queue lifecycle end to end (mine -> list -> decide).
- E: a queue fixture with a pending row round-trips accept and reject with notes persisted and `updated_at` set; the CLI refuses a missing queue DB with a clean message (rides U20's error surface); README review section shows the full loop.

### Evidence corrections to standing packets (from cycle-2 research)

- **U13 (native cron): drop the version gate.** The premise "requires hermes-agent >= v0.21.0; host currently 0.20.6 - feature must no-op with guidance below that" is stale: `hermes_cli/cron.py` on THIS v0.20.6 host already implements native cron with `monitor_script`/`monitor_url` ("agent runs only on output change") and `continuity`. U13 is implementable now; monitor-mode maps onto "skip when nothing changed", and the Windows path opens with it.
- **U9: no re-baselining needed.** agentskills.io spec re-fetched 2026-09-02, unchanged (name <=64 lowercase-hyphen, description <=1024, compatibility <=500, `metadata` string-map, `allowed-tools` experimental).
- **U8: grounding intact and strengthened.** NousResearch/hermes-agent#67582/#77264 still open with unchanged comment counts; native consolidation confirmed at source level to be opt-in LLM umbrella-building OFF by default (`agent/curator.py:204-220`), so the deterministic near-duplicate detector remains unowned upstream.
- **U7: severity upgraded, scope unchanged.** Cycle-2 B10 raises the WAL/busy_timeout/retry item to blocking (evidence silently dropped under contention, 0 of 3 events recorded) and upstream #101035 reports the same class; the version-single-sourcing and CI-gate items are unchanged (five-way version drift confirmed at `__init__.py:11` / `pyproject.toml:7` / `plugin.yaml:2` / bundled SKILL.md:4 / README v0.13-vs-v0.14).
- **Upstream drift: none material.** Newest release still v2026.8.31; the three grounding issues unchanged. Standing rejections from cycle 1 remain in force (none overturned; multi-profile aggregation re-examined and upheld - profile/home contract only partially verifiable, demand unevidenced, secret surface would multiply).

### Decisions

KTD7. P1 remediation precedes new extension features (continuing KTD1): U15-U17 land before U21-U25. The managed-block writer, the retention flags, and the scheduler generator are the surfaces every new feature reuses; shipping publish-safety (U21) on a writer that crashes on `\1` (B7) or deletes references on a documented flag (B8) compounds risk.
KTD8. U7 is a cycle-2 blocking item, not optional hygiene: B10's silent evidence loss is the highest-leverage reliability defect (evidence is the product's entire input), and upstream #101035 confirms the class is ecosystem-real. WAL + busy_timeout + bounded retry land before U24, which reads the same tables.
KTD9. Numeric flags must be parse-explicit everywhere: unset and explicit 0 are different values (B8). U16 fixes the four existing flags; U23's retention flag and any future numeric option adopt the same contract by construction.
KTD10. Publish-safety reuses upstream, invents nothing: U21 imports `tools.skills_guard` (already on every Hermes host, model-free) with a local regex fallback - no new scanner, no new dependency, consistent with the model-free default (KTD4).
KTD11. Remote policy unchanged (KTD2): feature branches to `fork` only; this cycle-2 extension is roadmap-only and commits nothing.

### Sequencing

U15 -> U16 -> U17 first (the P1 core: writer safety, flag contract, unit hardening), then U18 -> U19 -> U20 as the second batch, with U7 pulled forward into that batch as blocking (KTD8). U1-U4 are landed and verified; U5 and U6 remain queued ahead of the extensions per KTD1. After remediation: U21 -> U22 (write-path hardening features), U25 any time after U20 (smallest enabler, unblocks the review-queue family including U8/U10/U11 rows), then U23 and U24 last among extensions - U24 depends on U22's ledger for honest suppression accounting. U13's version gate is dropped now; U13 itself stays sequenced after U12 per cycle 1.

### Rejected directions (research cycle 2)

- Inbound skills_guard scan of skill content the plugin only reads - the plugin never executes skill content; upstream already scans at hub install and publish.
- Multi-profile/Bot-Mode evidence aggregation (re-examined) - profile->home contract only partially verifiable (`skill_commands.py` rescan-on-home-change, #88023); user demand still unevidenced; would multiply the secret-bearing surface U21 exists to shrink.
- Evidence DB encryption at rest - local-first threat model; retention (U23) plus ingest scrubbing (U21) address the demonstrated exposure without new key management.
- Writing into native curator state (`.usage.json`/`.curator_state`) - format ownership undocumented upstream; U12's read-only integration remains the right direction.
- `/curator` chat slash command as standalone work - the host exposes no plugin slash registration; the feasible chat surface is a provided tool, folded into U25 as optional.
- Replay-benchmark scoring of applies (re-examined) - unchanged from cycle 1; U24's cohort deltas are a decision aid with printed caveats, not a benchmark, and must stay that way.
- Cycle-2 assessment P3 fixes as feature candidates - they are U20 hygiene, not roadmap features (standing rule).

---

## Extension 2026-09-02 - maintenance cycle 3

Provenance: cycle-3 adversarial assessment (`ce-code-review`, RUN_ID 20260902-075335-6da5e933, attempt 82f9771fbc264672b53841b3cff35448 - 18 findings: 3 current C1-C3 plus 15 pre-existing P1-P15, all re-derived on the current tree with four empirical reproductions R1-R4; artifact `docs/assessment/2026-09-02-adversarial-repository-assessment-pass3.md`) plus cycle-3 extension research (`ce-ideate`, attempt b20d18cb3fc74b02b866cd2f2b5349a0 - 6 survivors, 9 rejections; artifact `docs/ideation/2026-09-02-cycle-3-extension-research.md`). Baseline at cycle-3 assess: pytest 174/174 at HEAD `45328db` + uncommitted cycle-1 batch; ruff 65 errors / 46 fixable. Roadmap discipline unchanged: pure append, all prior sections preserved byte-identical (pre-image sha256 `b61462713ba2b2e2ff111522022814fbf2d1f8196103836cd9d7b87a617c0f90`, saved at `/tmp/roadmap-before-cycle3.md`).

### Completed in cycle 3

- 2026-09-02 `assess` (re-attempt) - tree verified unchanged since cycle-2 assess (find -newer); 18 findings; R1 re.sub replacement injection (IndexError), R2 storage-vs-candidates classifier divergence, R3 --max-reference-files 0 coercion, R4 rerank truncation ordering, all reproduced fresh; README/docs claims verified largely accurate.
- 2026-09-02 `research` - 6 ranked survivors, 9 rejections. Key discovery: upstream ships a default-on skill-write ledger (`tools/skill_ledger.py`, `~/.hermes/skills/.curator_ledger.jsonl`, 16 live rows on this host, import verified from plugin context); issue #100449 (skill-write observability) closed completed 2026-09-02T02:46Z with open follow-up PR #100471; four competitor repos read in depth (all dormant since May 2026); agentskills.io spec unchanged.
- 2026-09-02 `roadmap` - this extension; append-only, all prior sections preserved byte-identical.

### Cycle-2 packet status (verified in working tree this cycle)

- U1-U4 landed in the uncommitted cycle-1 batch; pass-3 assess re-verified NUL stripping, structured-first candidate classification, rollback support-file handling + retention + tamper refusal, and per-session backfill boundaries - regression-free (174/174).
- **U5 status correction (cycle-2 line stale):** hard-cap work is largely present in the working tree - `_MAX_SKILL_CONTENT_CHARS = 100_000` (`auto_evolve.py:50`), `_AUTO_LOADED_SKILL_MAX_CHARS = 12_000` (`:52`), skip-hard-cap strategies (`:486`, `:519`). Residual U5 work is "confirm single-sourcing across guarded_apply/candidates and close", riding the U7 hygiene batch - not a fresh implementation.
- U6, U7 open (`cli.py:358-361` `--enable` default True; zero WAL/busy_timeout in `storage.py` - corroborated by pass-3 P4 and upstream #101035).
- U15-U25 unstarted; U25 confirmed still needed (pass-3 C3: `review_queue.update_status` remains caller-less).

### Blocking issues discovered (cycle-3 assessment)

B13. Reranker reorders only the pre-truncated top-limit embedding slice: `semantic.py:246` truncates to `limit` before the rerank pairs are built at `:250`, so `--rerank-candidates` can never promote a skill the embedder ranked beyond the fold (recall ceiling). The existing test uses a fake backend over fewer candidates than the limit, so the suite cannot see it. -> U26.
B14. Rollback constrains the manifest target only when `--skills-dir` is passed (`cli.py:786`): `guarded_apply.py:499` skips the root check when `allowed_target_roots is None`, contradicting the docstring promise at `:486`; README's CLI reference teaches the unsafe default form. -> U27.
B15. Two error classifiers diverge: `storage._looks_like_error('3 passed, no errors found')` is True (`storage.py:127`) while `candidates._is_tool_failure` on the same string is False - the storage copy corrupts `error_events`, which gate auto-evolve thresholds and U24's outcome cohorts. U2 fixed the candidates side; the storage side was never unified. -> U28.

(Pass-3 C3 - dead `update_status` surface - is already U25. Pass-3 pre-existing P1-P15 map onto U15-U20 per cycle 2 and are unchanged.)

### New work packets - cycle-3 remediation

U26. Rerank oversampling (semantic recall)
- AC: semantic candidate selection oversamples the embedding top-k (e.g. min(5x limit, all candidates)) before rerank pair construction and truncates to `limit` only after rerank; the no-rerank path is byte-identical in behavior.
- E: a fixture where the best skill embeds below the fold but reranks first is selected after the fix (this is pass-3 reproduction R4 turned into a targeted pytest); a greater-than-limit candidate set runs lexical-only unchanged.

U27. Rollback target-root default
- AC: rollback resolves the skills root from the same discovery the apply path uses and constrains `allowed_target_roots` by default; opting out requires a named explicit flag; README rollback examples are correct under the default; a test drives rollback with no `--skills-dir` and asserts the root check fired.
- E: pass-3 C2's scenario (rollback without `--skills-dir` against a manifest targeting outside the skills tree) is refused with a clean error naming the path; U3's tampered-manifest tests still pass.

U28. One error classifier, one source of truth
- AC: storage ingest and candidates ranking consume a single structured-first failure classifier; `storage._looks_like_error` is deleted or delegates to it; keyword corpora live in one place; both call sites are covered by U2's adversarial corpus test extended to the ingest path.
- E: pass-3 reproduction R2 flips (`'3 passed, no errors found'` persists with `is_error=0`); a stored-DB fixture with keyword-bearing success strings yields zero `error_events` rows; full suite green.

### New work packets - cycle-3 extensions (research survivors)

U29. Host-ledger read integration - external-drift attribution and skill-history timeline (research survivor 1)
- AC: `report`/`doctor` read `~/.hermes/skills/.curator_ledger.jsonl` through `tools.skill_ledger.list_entries` when importable (degradation: direct JSONL read, then skip with notice) and attribute every skill write the plugin did not make (actor, action, timestamp, sha256 before/after); a file that changed with no ledger row surfaces as an "unattributed drift" review-queue row; `report --history <skill>` interleaves ledger rows with plugin apply manifests into one timeline; doctor on a fresh host seeds history from existing ledger rows.
- E: a fixture ledger plus plugin manifests renders the merged timeline with plugin and external rows correctly attributed; a drifted file with no ledger row produces exactly one queued row; the import-unavailable degradation path is tested; verified read-only against this host's 16 live rows.

U30. Plugin-apply attribution in the host ledger (research survivor 2)
- AC: `guarded_apply` appends an attribution row via `tools.skill_ledger.append_entry` (action, skill, before/after path+sha256) when importable, recording `skipped` when not; after append, the manifest hash is cross-checked against the ledger entry's after-sha256 (mismatch files a review row, never silent); respects `skills.ledger` disabled by no-oping.
- E: a scratch-home apply produces a ledger row with matching hashes; a monkeypatched hash mismatch files exactly one review row; the import-failure path records skipped and still applies; no write ever touches `.usage.json` or `.curator_state` (KTD13 boundary).

U31. `doctor --host-compat` sweep (research survivor 3)
- AC: doctor probes every host surface the plugin leans on with a per-surface verdict and degradation note: SessionDB read-only API, `tools.skills_guard` importability (U21), `tools.skill_ledger` presence (U29/U30), cron backend availability (U13), plus skill discoverability - the plugin's bundled skill visible to interactive slash discovery (upstream #100403) and no local skill silently gated out by `requires_toolsets` aliasing (#99877); each miss cites the upstream issue number verbatim rather than paraphrasing behavior.
- E: a version-stubbed scratch home yields per-surface verdicts; fixtures reproducing #100403-style invisibility and #99877-style alias gating are reported rather than silent; U12's doctor leg (mutator-conflict check) is absorbed here and its remaining scope reduced accordingly.

U32. Context-budget report (research survivor 4)
- AC: `report --context-budget` computes and ranks per-skill `uses x content_chars` from existing evidence tables plus current file sizes, alongside error rates, with the usage-not-equal-value caveat printed on every render; output feeds U8 dedupe priority ordering; no auto-prune exists anywhere in the path.
- E: a fixture with known usage counts and file sizes yields the expected ranking; the caveat string is asserted; runs lexical-only with no model.

U33. Circuit breaker for unattended runs (research survivor 5; U22 escalation tier)
- AC: N consecutive auto-runs ending in verify-fail/rollback/suppression for the same skill (default 3, configurable) disable the scheduler and file a review-queue row naming skill, streak, and suggested action; streak state persists in the evidence DB across scheduler restarts; re-enabling is an explicit human act (`--clear-anti-pattern`-style); `report` surfaces breaker state.
- E: a synthetic three-failure streak disables the scheduler and queues the row; a restart preserves the streak; clearing re-enables; a healthy run resets the streak; the breaker itself mutates no skill content.

U34. Fleet-library conflict report (research survivor 6; conditional, KTD14)
- AC: `report --skills-dir <shared-library>` audits a `skills.external_dirs` shared library (near-duplicates, conflicting managed blocks, staleness, U21 publish risks) without aggregating any per-profile evidence; output states the blast radius (which profiles see the library, from readable `skills.external_dirs` config).
- E: a shared-library fixture with planted duplicates and conflicts reports all of them and aggregates nothing; gated behind U19 identity unification; ships only per KTD14.

### Evidence corrections to standing packets

- **U5** - status-line correction recorded above; residual is confirm-and-close on the U7 batch.
- **U9** - spec re-fetched, unchanged; add tolerance for unknown-but-valid frontmatter fields (watch: upstream #100056 proposes a non-spec `triggers` field) - conformance must flag, not fail, them.
- **U12** - doctor leg absorbed by U31; protected-path and `write_approval` gates remain U12's core scope.
- **U13** - unchanged from the cycle-2 correction (version gate dropped; native cron present on v0.20.6).
- **U24** - optional cohort ground truth from ledger timestamps once U29 lands.
- Upstream drift otherwise nil: v2026.8.31 still latest; #67582/#77264/#66180 unchanged; #101035 open.

### Rejected directions (research cycle 3)

- Document-to-skill mining (AutoSkill4Doc analog) - outside the evidence-about-usage identity; extraction needs a model against the model-free default; AutoSkill4Doc owns the niche.
- Evidence provider for upstream #101002 goal-loop epic - speculative against an open epic with no shipped surface; the existing `curator_evidence_report` provided tool covers the feasible slice.
- Three-tier progressive loading (SkillForge) - the host owns skill loading; U32 delivers the measurable half instead.
- Q-value/TD(lambda) effectiveness ranking (SkillForge) - U24 territory; RL-flavored ranking conflicts with the model-free default and the replay-benchmark rejection family.
- Multi-profile evidence aggregation (re-examined on #100254 demand evidence) - rejection upheld; only the non-aggregating read-only library audit survives, as U34.
- No standing cycle-1 or cycle-2 rejection is otherwise overturned; the native-state-write rejection is narrowed by decision (KTD13), not overturned.

### Decisions

KTD12. Remediation precedes extension (continuing KTD1/KTD7): U26-U28 land with the cycle-2 remediation batches, before any of U29-U34.
KTD13. Native-state-write rejection narrowed, not overturned: append-only attribution rows via `tools.skill_ledger.append_entry` are permitted (documented, default-on, import verified from plugin context 2026-09-02); the `.usage.json`/`.curator_state` write ban and every other native-state write stand.
KTD14. U34 is demand-gated: ship only on a second independent demand signal (for example #100254 merged with curation commentary, or a user report), or fold as an optional mode of U8; requires U19 first.
KTD15. Remote policy unchanged (KTD2); this cycle-3 extension is roadmap-only and commits nothing.

### Sequencing

U15 -> U16 -> U17 (cycle-2 P1 core) -> U18 -> U19 -> U20 plus U7 (blocking per KTD8), with U26-U28 riding that batch (small, disjoint surfaces; U28 before U24 reads those tables) -> U21 -> U22 -> U33 (U22's escalation tier) -> U29 -> U30 -> U31 (host-integration trio: read the ledger before writing to it, doctor last as it probes what the first two added) -> U25 any time after U20 -> U32 after U8 exists -> U34 conditional per KTD14. U5's residual confirm-and-close rides the U7 hygiene batch.

---

## Extension 2026-09-02 - maintenance cycle 4

Provenance: cycle-4 adversarial assessment pass 4 (`ce-code-review`, run dir `/tmp/compound-engineering-1000/ce-code-review/20260902-085014-4360bd1c/`, attempt `f44a056ccec043c0950be48743c25762`; 27 findings - 18 carried re-derived fresh plus 9 new N1-N9, all inside or triggered by the uncommitted cycle-1 remediation diff; 12/12 reproducers reproduce via `/home/agent/.hermes/conductor-runs/673d15323b9c4580a0e2ed84fa8625fc-assess/repro-adversarial-findings-pass4.sh`; artifact `docs/assessment/2026-09-02-adversarial-repository-assessment-pass4.md`) plus cycle-4 extension research (`ce-ideate`, run dir `/tmp/compound-engineering-1000/ce-ideate/20260902-091847-f3ee7d90/`, attempt `bef3d264d5fd4d76b46e1d02762171c9`; 9 ranked survivors R1-R9 from a ~18-candidate pool, 4 fresh rejections; artifact `docs/ideation/2026-09-02-cycle-4-extension-research.md`). Baseline at cycle-4 assess: pytest 174/174 at HEAD `45328db` + the same 11 uncommitted cycle-1 files (833 insertions, unchanged since); ruff 65 errors / 46 fixable (~19 in the six remediation files). Roadmap discipline unchanged: pure append, all prior sections preserved byte-identical (pre-image sha256 `6fa9a3cd577c91971ba3ca22f3d79595f3a3b988d4b7db15e3b2698d58f22825`, saved at `/tmp/roadmap-before-cycle4.md`).

### Completed in cycle 4

- 2026-09-02 `assess` (pass 4, re-attempt) - adversarial review of the NEW remediation code itself: 9 new findings (N1 tampered-manifest rollback unlink, N2 `--limit` collects before sort, N3 fetch-all before cutoff + bootstrap `limit=None`, N4 keep=0 same-pass pruning, N5 `\u0000` escape survives sanitizer, N6 verifier accepts inflated grounding, N7 `sessions_failed` never printed, N8 new flags undocumented, N9 ~19 new lint diagnostics); 18 carried findings re-derived with fresh anchors; all 12 reproducers reproduce; tree verified unchanged before and after.
- 2026-09-02 `research` - 9 ranked survivors, 4 fresh rejections. Key discoveries: upstream closed #101063 today (rglob vs symlinked skills - this repo still carries the superseded pattern at `auto_evolve.py:310`); live-host quantification of evidence-source pollution (250/754 cron + 34 subagent sessions, 2,524/18,185 tool messages ingested unfiltered while upstream ships `exclude_sources=['cron']`/`exclude_children` semantics and the plugin already stores the `platform` column per row); `search_sessions` has a deterministic newest-first total order and no cutoff parameter; three host surfaces the plugin is provably blind to (`tools/skill_linter`, `.usage.json` sidecar with 100 live entries, `workspace_key` scoping); host rollback writes a pre-rollback safety entry and fails closed.
- 2026-09-02 `roadmap` - this extension; append-only, all prior sections preserved byte-identical.

### Packet status (verified in working tree this cycle)

- U1-U4 landed in the uncommitted cycle-1 batch; pass-4 re-verified all four and found the batch itself defective in three places (B16-B18 below) - the remediation introduced its own bugs on exactly the surfaces it hardened.
- U5 residual is confirm-and-close on the U7 batch (cycle-3 correction stands; hard-cap constants present at `auto_evolve.py:50/:52`).
- U6, U7 open (`cli.py:358-361` `--enable` default True; zero WAL/busy_timeout in `storage.py`, pass-4 P4 reproduced the lock again).
- U8-U34 unstarted; U16 strengthened by N4 (keep=0 deletes the same-pass reference - reproduced); U25 still needed (C3 caller-less surface unchanged); U29/U30 premises unchanged.

### Blocking issues discovered (cycle-4 assessment)

B16. Rollback deletes the restored skill file on a tampered manifest (N1): `_rollback_support_files` (`guarded_apply.py:426-468`) resolves support-file entries under `target.parent` and unlinks hash-matching files, but never excludes the manifest's own target - a manifest whose `support_files` contains `{path: "SKILL.md", sha256: <post-restore hash>}` unlinks the just-restored SKILL.md (reproducer: `removed: ['SKILL.md']`, file gone). The relative-path guard checks only absolute/`..`/containment, not identity with the target. -> U35.
B17. Backfill `--limit` bounds the wrong set and reads every transcript before the cutoff (N2+N3): `_iter_state_sessions` (`backfill.py:175-222`) collects up to `limit` rows in STORAGE pagination order before its client-side newest-first sort - under any non-newest-first driver `--limit N` inspects the oldest N sessions (reproducer: `inspected ['s1','s0']`); full transcripts are fetched for every collected session (`:207-218`) and the days cutoff applied only afterwards in the caller (`:347-435`; reproducer: 5/5 transcripts fetched); bootstrap passes `limit=None` (`cli.py:502`). -> U36.
B18. NUL escapes survive the sanitizer (N5): `_strip_nul_bytes` (`storage.py:71`) removes the raw byte and the `\x00` literal but not the six-character `\u0000` escape; `json.loads` then yields a real NUL (`{"a":"x\u0000y"}` persists verbatim) while literal `\x00` text is mangled. Same perpetual-error-loop class as the original Problem and U1's reason for existing. -> U37.

(N4 strengthens U16 unchanged; N6 inflated-grounding acceptance and N9 lint debt confirm U7's existing verifier-cross-check and ruff/CI ACs are correctly scoped; N7 rides U36's summary AC and U20; N8 rides U7's docs item and U20's clean-error surface. Pass-4 carried findings P1-P15/C1-C3 map onto U15-U20/U26-U28 per cycles 2-3 and are unchanged.)

### New work packets - cycle-4 remediation

U35. Rollback manifest validation + rollback-as-guarded-mutation (B16/N1, C2, research R8)
- AC: support-file entries are validated before any unlink: resolved under the skills root (not merely `target.parent`), never equal to or a symlink-alias of the manifest target SKILL.md, and present in the manifest only if the apply registered them; a rollback that would remove or overwrite a file it did not create is refused with a named reason; every destructive rollback first writes its own pre-rollback safety snapshot (target + touched support files) and fails closed when the snapshot cannot be written - rollbacks are themselves undoable, mirroring the host `hermes curator rollback` contract (`hermes_cli/curator.py:675-722`); rollback of a file modified after the apply requires an explicit flag (closes C2's CLI-default overwrite).
- E: pass-4 N1 reproducer re-run shows the `support_files:[{path:"SKILL.md"}]` manifest refused (`skipped`, reason named) with the restored file present; absolute-path and symlink-alias manifests refused; a failing-snapshot fixture aborts rollback with zero mutations; targeted pytest.

U36. Trusted-order backfill with drift detection (B17/N2+N3+N7, research R3; supersedes the collect-then-sort shape)
- AC: `_iter_state_sessions` pages newest-first trusting the documented `ORDER BY last_active DESC, s.started_at DESC, s.id DESC` contract (`hermes_state.py:13155-13201`), breaks at the first session older than the days cutoff, and asserts observed monotonic non-increase across page boundaries - the current collect-then-sort path survives only as the fallback when the assertion trips; `--limit` bounds sessions AFTER ordering (newest N inspected); bootstrap passes a bounded limit; the import summary prints `sessions_failed` and per-session skips; the ordering contract and the drift fallback are documented at the call site.
- E: pass-4 N2 reproducer (fake driver returning oldest-first) trips the drift check, falls back, and imports the newest set; a newest-first fake with a limit inspects exactly the newest N; N3 reproducer shows transcript fetches stop at the cutoff (fewer than all); a `sessions_failed>0` fixture prints the count; U4's shuffled-order tests remain green as the fallback's tests.

U37. NUL-escape-complete sanitization (B18/N5; closes U1's residual)
- AC: one helper removes every NUL representation that can reach the store - raw byte, `\x00` literal, `\u0000` escape - at both ingest paths (hooks and backfill import), without mangling legitimate text that merely contains the characters `\x00` (strip the escape only when it decodes to NUL in the stored JSON value).
- E: pass-4 N5 reproducer re-run: `{"a":"x\u0000y"}` stored with zero NUL bytes AND literal `\x00` prose preserved unmangled; a stored-JSON fixture round-trips through `json.loads` with zero NUL bytes; U1's end-to-end regression extended with the escape form.

### New work packets - cycle-4 extensions (research survivors)

U38. Source-aware evidence pipeline (R1)
- AC: hooks and backfill tag and by default exclude machine-generated sessions (`platform`/`source` in {cron, subagent}) from evidence ingest, allowlisting human sources (cli, api_server, chat platforms) rather than blocklisting scheduler strings; `--include-sources` is the explicit opt-in; a one-shot re-filter applies to already-stored rows (the column already exists - `storage.py` platform columns, `backfill.py:252` maps `source`); report prints excluded counts.
- E: a fixture state DB mixing cron/subagent/cli imports only the human set by default and all sessions with the flag; a planted stored cron row is re-filtered by the migration; live-host measurement repeated after landing shows cron/subagent rows excluded (baseline recorded this cycle: 250/754 cron + 34 subagent sessions, 2,524/18,185 tool messages).

U39. Symlink-parity skill discovery (R2; ports upstream #101063)
- AC: every skill-discovery site (`auto_evolve.py:310` `rglob("SKILL.md")` and any sibling) walks with `os.walk(followlinks=True)`; relative-path/categorized logic uses the unresolved path for `relative_to()` (upstream fix note 2; applies to the early `resolve()` uses at `guarded_apply.py:71-72` and `skill_sources.py:57/:131/:144`); a symlinked-skill-dir fixture is added to tests.
- E: a symlinked skill dir is discovered identically to a plain dir across report/prune/apply paths; containment checks still refuse escapes; upstream #101063 cited where the pattern is ported.

U40. Host-linter apply gate + `report --lint` (R4; closes the N4 class at the gate)
- AC: guarded apply runs `tools.skill_linter.lint_skill` on the written SKILL.md when importable (degradation: skip with notice) and fails verification on errors; dangling-reference warnings (`_check_reference_links`, `skill_linter.py:262-288`) block or warn on reference-pruning decisions - keep=0 or same-pass pruning must not leave a body reference to a missing file; `report --lint` audits the whole tree with per-skill findings.
- E: an apply whose pruning would orphan a `references/...` link is refused or flagged with the linter's finding text; a lint-clean fixture applies silently; the import-unavailable path is tested; `report --lint` renders a planted dangling reference.

U41. Cron-referenced-skill protection (R6)
- AC: prune/retire decisions read host cron job definitions and treat skills they reference as load-bearing - skip with a named reason in report - mirroring the native curator's `_cron_referenced_skills` (`agent/curator.py:290`); composes with U16's keep=0 contract (protection outranks the retention bound).
- E: a fixture cron job referencing skill X blocks X's reference pruning and retire suggestion with X named; an empty cron set leaves behavior unchanged; targeted pytest.

U42. Workspace-scoped backfill (R9)
- AC: `backfill-sessions --workspace [key]` passes `workspace_key` to `search_sessions` when the host supports it (`hermes_state.py:13158`) and degrades to unscoped with a notice when not; evidence rows record the scope used.
- E: a fake driver asserting the `workspace_key` argument receives it; an unsupported-driver fixture degrades with notice; a two-workspace fixture imports only the scoped workspace's sessions.

### Evidence corrections to standing packets (from cycle-4 research)

- **U7** - N6 (verifier accepted claimed grounding 999 vs 1 actual) and N9 (~19 of 65 ruff diagnostics in the six remediation files) confirm the existing verifier-cross-check and ruff/CI ACs are correctly scoped; no AC change, evidence line added.
- **U12** - scope grows: `status`/`report` also read the `.usage.json` sidecar (live host: 100 entries with `last_used_at`/`patch_count`/`created_by`; native curator's own lifecycle input) and emit a drift line when transcript-mined usage disagrees materially with sidecar ground truth (R5). Read-only per KTD13.
- **U9** - add the host linter's platforms-gating and forbidden-files checks (`skill_linter.py:291-364`) to the conformance watch list.
- **U16** - strengthened by N4 (keep=0 currently deletes the reference written by the same apply - reproduced pass-4); AC unchanged.
- **U29/U30** - premises unchanged: ledger PR #100471 still open, #100449 closed; verified again this cycle.
- **U13** - unchanged (cycle-2 correction stands; v2026.8.31 still latest release).
- Upstream drift otherwise nil: v2026.8.31 latest; #67582/#77264/#66180 unchanged; #101035 open; new upstream issues since cycle-3 contain nothing else curator/skill-relevant beyond #101063 (folded into U39).

### Rejected directions (research cycle 4)

- Optional aux-model review layer - contradicts the model-free default (KTD4); the native curator already owns aux-model review (`agent/curator.py`).
- Evidence-DB stats dashboard - ungrounded observability listicle; U32's context-budget report delivers the measured half.
- Writing `.usage.json`/curator lifecycle state - standing rejection upheld (KTD13); only the read-side drift line survived, folded into U12's correction above.
- Re-proposing cycle-3 survivors 1-6 - cross-referenced as U29-U34; premises unchanged or strengthened, no new evidence overturns anything.

### Decisions

KTD16. Remediation of the landed batch's own defects precedes new extensions (continuing KTD1/KTD7/KTD12): U35-U37 land before U38-U42 - and only after the uncommitted cycle-1 batch itself is committed; building cycle-4 fixes on top of an uncommitted tree risks losing the remediation they repair.
KTD17. U36 supersedes the collect-then-sort backfill shape: the upstream API's ordering is a documented deterministic total order (`hermes_state.py:13155-13201`), so trust-but-verify with a drift fallback replaces both the blanket ordering distrust (U4's original premise, now over-broad) and the fetch-all-before-cutoff cost (N3). U4's shuffled-order tests are retained as the fallback's tests.
KTD18. Source filtering is default-on with an explicit include opt-in (U38): evidence is the product's entire input, and machine-generated sessions (22% of this host's tool messages) are noise by default - opt-in signal for the rare user who wants them. Allowlist human sources; never blocklist scheduler strings (source values are an upstream implementation detail).
KTD19. Port, don't invent (continuing KTD10): U39 ports upstream #101063 verbatim, U40 reuses `tools.skill_linter`, U41 mirrors `_cron_referenced_skills`, U36 cites the host ordering contract, U35 mirrors the host rollback safety-entry contract - every cycle-4 packet has an upstream-provided pattern.
KTD20. Remote policy unchanged (KTD2); this cycle-4 extension is roadmap-only and commits nothing.

### Sequencing

Commit the cycle-1 batch first (its own gate), then U35 -> U36 -> U37 (cycle-4 remediation; U35 first - rollback deletion is the destructive class), pairing with the cycle-2/3 batches where surfaces coincide: U35 shares `guarded_apply.py` with U15 (land together), U36 shares `backfill.py` with U19 (land together), U37 shares `storage.py` with U28 (land together). Then extensions: U38 (evidence quality is the product's input) -> U39 (smallest, correctness) -> U40 (write gate) -> U41 -> U42. Standing order otherwise unchanged: U7 remains blocking ahead of U24 (KTD8); U16 ahead of U23; U26-U28 ride the remediation batch (KTD12); U34 stays demand-gated (KTD14).

---

## Extension 2026-09-02 - maintenance cycle 5

Provenance: cycle-5 adversarial assessment pass 5 (`ce-code-review`, run dir `/tmp/compound-engineering-1000/ce-code-review/20260902-111048-85ee6539/`, attempt `b7800038a84c4198bcf2d7be22cc61f3`; 23 findings - 8 new Q1-Q8 plus 15 carried re-derived fresh, 22 probes with 21 reproduced via `/home/agent/.hermes/conductor-runs/2cc5b112c9694bfaa4a47645f139983a-assess/repro-pass5.py`; artifact `docs/assessment/2026-09-02-adversarial-repository-assessment-pass5.md`) plus cycle-5 extension research (`ce-ideate`, run dir `/tmp/compound-engineering-1000/ce-ideate/20260902-112230-c5e8a1f4/`, attempt `7295512752b44da18c6bd828e61a8622`; 5 ranked survivors from a ~15-candidate pool, 6 fresh rejections; artifact `docs/ideation/2026-09-02-cycle-5-extension-research.md`). Baseline at cycle-5 assess: pytest 184/184 (17 files) at HEAD `45328db` + uncommitted cycle-1 remediation AND the cycle-4 batch (CU-Q..CU-V, 13 files, 1641 insertions, landed since pass 4); ruff 64 errors / 45 fixable (baseline drift 65->63->64, ungated). Roadmap discipline unchanged: pure append, all prior sections preserved byte-identical (pre-image sha256 `0daa376a3099a6223cd20c2dcbb0c71a2121590eab882a5dac3629f0899d42b4`, saved at `/tmp/roadmap-before-cycle5.md`).

### Completed in cycle 5

- 2026-09-02 `assess` (pass 5) - adversarial weight on the six cycle-4 change units, then every carried finding re-derived fresh: 8 new findings (Q1 classifier truth-table, Q2 F821 `Any`, Q3 file-mode drop, Q4 README rollback form stale, Q5 non-atomic safety snapshots, Q6 ~15.75s hook stall under contention, Q7 partial schema never heals, Q8 silent flag rewrites) + 15 carried; fix-verification of the cycle-4 batch's own goals: U15 (re.sub injection) fixed, U35 (tampered-manifest delete) fixed, U16 (keep=0) fixed, U37 (NUL escape) fixed, U27/C2 (unrestricted-rollback opt-in) fixed, U28 unified but defective (Q1).
- 2026-09-02 `research` - 5 ranked survivors, 6 fresh rejections. Key discoveries: upstream state layer split into `hermes_state_{common,schema,search,registry,portability}.py` (facade retained; import surface now a doctor item); #101199 open (exclude cron-source sessions from trigram FTS - 97.5% of one deployment's sessions were cron) and #101191 MERGED (single-flight writer registry - redundant connections fire close-time WAL checkpoints against the live writer, a corruption-incident precursor); `search_sessions` on main now has SQL-level `source_filter`/`exclude_sources`; the host ships a full Skills Hub the plugin has never read (`.hub/lock.json` provenance, quarantine, audit log, install/update/audit verbs); the prompt-index mechanics are pinned (`SKILL_PROMPT_DESC_LIMIT=60`, eager name+description index, lazy bodies - 32/119 skills on this host over budget, worst 535 chars); Agent Skills open spec + `skills-ref` reference validator published; Claude Code listing-budget analysis (least-invoked descriptions dropped first - a ratchet).
- 2026-09-02 `roadmap` - this extension; append-only, all prior sections preserved byte-identical.

### Packet status (verified in working tree this cycle)

- The cycle-4 batch landed uncommitted (13 files, +1641): U15 closed (lambda replacement, `auto_evolve.py:391`), U35 closed (target-identity refusal + pre-rollback safety snapshot; residual Q5 below), U16 closed (explicit zeros honored; residual Q8 warn-on-clamp), U37 closed (value-layer NUL strip, literals preserved), U27/C2 closed (rollback `--allow-any-target` opt-in), U28 partially closed (one classifier now exists at `candidates.py:242`, but Q1 reopens it - see B19).
- U7's sqlite slice landed (WAL/busy_timeout/bounded retry present, `_BUSY_TIMEOUT_MS`, `_write_with_retry` at `storage.py:78/:244`) but its own cost is Q6 (B21), and the version/CI/docs items remain open: version drift persists (`__init__.py:11` 0.8.0 vs `plugin.yaml:2` 0.10.0), ruff 64 errors ungated (Q2's F821 at `cli.py:466` is exactly what the lint gate would catch), README rollback form stale (Q4).
- U6 still open (`--enable default=True` at `cli.py:367`). U36 (backfill ordering/cutoff) NOT landed: N2/N2b/N3 reproduced again this pass, byte-identical behavior. U17, U18, U19, U20, U25, U26 (C1 reproduced again), U29-U34, U38-U42 unstarted.
- Neither the cycle-1 nor the cycle-4 batch is committed (19 dirty/untracked paths) - KTD16's commit-first gate now covers both batches.

### Blocking issues discovered (cycle-5 assessment)

B19. The unified error classifier's truth table is wrong on both sides (Q1; U28 reopened): `looks_like_error` (`candidates.py:97-100,210-241,242`) classifies `{"stdout":"ok","stderr":""}`, `"0 failed, 12 passed"`, and `"exit code 0"` as errors (bare `stderr`/`failed`/`exceeded` keywords; `exit\s+code\s+\d+` matches code 0) and misses `{"returncode":1}`, `{"code":1}`, `{"ok":false}` (structured branch knows only `exit_code`/`error`/`exception`/`success`). This is the same `error_events` cohort corruption U28 was written to close, reopened through the new classifier - and it gates auto-evolve thresholds and U24's outcome cohorts. -> U43.
B20. The guarded-apply atomic-write helpers drop file mode (Q3): apply AND rollback re-create files with process umask (0o640 -> 0o664 reproduced), and the pre-rollback safety snapshot uses plain `write_bytes` (Q5) - the recoverable copy the U35 design leans on can itself be torn. -> U44 (mode and snapshot together).
B21. Hook-path write latency under contention is now worst-case ~15.75s per event (Q6): a fresh connection per `record_*` call (`storage.py:237-241`) times out and retries 3x through the just-landed `_write_with_retry`. Cycle-5 research identified the upstream-endorsed fix pattern (merged #101191: single-flight, per-resolved-path single writer; #101202 recipe: contention-vs-environment errno split). -> U45.
B22. `_schema_ready` probes only `tool_events` (Q7): an interrupted first init leaves `turn_events`/`session_events` missing forever (executescript skipped steady-state). -> U46.
(Q2 F821 rides U7's lint/CI AC with the concrete failing line recorded; Q4 rides U7's docs item and U20's clean-error surface; Q8 rides U16 as a warn-on-clamp residual; carried findings map onto U16-U20/U26-U28/U36/U39 per cycles 2-4 and are unchanged - N6 additionally poisons the very cohort U43 repairs.)

### New work packets - cycle-5 remediation

U43. Error-classifier truth table (B19/Q1; reopens and completes U28)
- AC: `looks_like_error` decides structured-first with an explicit shape table covering the probe corpus: `returncode`/`exit_code`/`code` nonzero -> error, zero -> not error; `ok`/`success` booleans honored; `status`/`error`/`exception` keys honored; bare-keyword fallback matches only failure-bearing phrases (`failed` without a passing count, `exit code <nonzero>`, `traceback`) and never matches success shapes (`"0 failed, 12 passed"`, `"ok"`, empty `stderr` alongside `stdout`); the adversarial corpus from `repro-pass5.py` Q1 probes becomes a permanent test.
- E: all four Q1 probes flip to the correct verdict (success shapes -> `is_error=0`; failure shapes -> caught); a stored-DB fixture with keyword-bearing success strings yields zero `error_events` rows; U2's corpus test extended with these shapes; full suite green.

U44. Mode-preserving atomic writes and atomic safety snapshots (B20/Q3+Q5)
- AC: the atomic write helpers copy the target's existing mode (or an explicit mode arg) onto the temp file before rename for apply, rollback, AND the pre-rollback safety snapshot; `_snapshot_for_safety` switches from plain `write_bytes` to the atomic helper with fsync; no write path in `guarded_apply.py` re-creates a file with bare umask.
- E: pass-5 Q3 reproducer shows 0o640 preserved through apply and rollback; a mid-snapshot interruption test leaves either the full snapshot or none; targeted pytest.

U45. EvidenceStore warm-writer topology + error taxonomy (B21/Q6; lands cycle-5 research survivor S3)
- AC: one cached connection per resolved DB path per process (contextvar/thread-local, single-flight open, `Path.resolve()` key) replaces connect-per-call; connections registered for close-at-exit; `_write_with_retry` splits contention (`busy`/`locked`) from environment errors (fail fast with the real errno, no timeout burn); the deferred-spill queue (queue events on unavailable store, drain next open) is in-scope but optional; hooks never hold a write transaction across turns.
- E: pass-5 Q6 probe re-run shows worst-case hook latency bounded (from ~15.75s to a single busy_timeout) under the same contention fixture; a concurrency test asserts one open per path under a cold burst; the environment-error path returns fast with the errno recorded; targeted pytest.

U46. Schema-readiness probes every table (B22/Q7)
- AC: `_schema_ready` verifies `tool_events`, `turn_events`, AND `session_events` (and any future table list lives in one constant consumed by both init and readiness); an interrupted-init fixture heals on next open.
- E: a DB with `tool_events` present but the other two missing completes init on first write; a fully-initialized DB is untouched; targeted pytest.

### New work packets - cycle-5 extensions (research survivors)

U47. Routing-budget curation (S1; supersedes U32's metric per KTD23)
- AC: `report --routing-budget` lists every skill whose description exceeds the host's `SKILL_PROMPT_DESC_LIMIT` (60; `agent/skill_utils.py:1175`), shows the truncated text the model actually sees (first 57 chars + "..."), flags when the lost tail carried trigger keywords, and correlates truncation with measured invocation counts from the evidence store (with the small-cohort caveat printed); an aggregate line prices the whole index (sum of name + desc[:60] per skills dir); the apply gate warns (never refuses) on description edits that push keywords past char 57; `doctor` reports the probe's availability.
- E: a fixture library with known over-budget descriptions and known usage counts renders the expected rows and caveat; the live host scan (32/119 over budget, worst 535) is the sanity baseline cited in the change unit; lexical-only, no model.

U48. Hub-provenance awareness (S2)
- AC: reports tag hub-installed skills with origin/trust/scan-verdict read from `skills/.hub/lock.json` (import-guarded, tolerate-absent - the file is `"version": 1` shaped and internal); a manifest-hash mismatch on a hub-tracked skill is attributed `hub update` in the U29 timeline instead of `unattributed drift`; `doctor` reports quarantine-dir contents and audit-log tail; read-only throughout (KTD13).
- E: a fixture lock file plus drifted skill yields the attributed row; an absent lock file degrades silently; a quarantine fixture is reported; verified read-only against this host's empty lock (surface shipped default, unused here today).

U49. Agent Skills spec conformance profile (S4; upgrades U9's pin)
- AC: `skill_validate --profile agentskills` (default warn-only) enforces the published spec - `name` 1-64 lowercase/digits/hyphens matching the parent directory, no consecutive hyphens; `description` 1-1024; optional `license`/`compatibility`/`metadata`/`allowed-tools` type-checked but never required; unknown fields (including host `triggers`) are advisories, not failures; output cites `agentskills.io/specification`; no vendoring of `skills-ref` (reimplement the ~6 rules).
- E: spec edge-case fixtures (boundary lengths, bad charset, name != dir, non-string metadata, unknown field) produce the graded verdicts; U9's existing validator tests extended; spec-validity becomes a publish precondition note in U21's report.

U50. Upstream-source staleness report for hub skills (S5; demand-gated per KTD24)
- AC: `report --staleness` (opt-in, network-gated, offline-safe: last-known cached, unknown marked unknown) diffs each lock-file-registered skill's installed hash against its recorded source state and reports behind/current/unverifiable; never auto-updates (the hub's `update` verb owns mutation); requires U48's lock-file read.
- E: a fixture with a behind-source skill reports behind with source cited; an offline run reports unverifiable without erroring; no write path exists in the command.

### Evidence corrections to standing packets (from cycle-5 research)

- **U38** - implementation shortcut now exists: `search_sessions` on upstream main accepts `source_filter`/`exclude_sources` (`hermes_state_search.py:1346-1386`); call the API or mirror the same WHERE clauses; premise strengthened by #101199's measurements (97.5% of a deployment's sessions cron-source; upstream itself excluding cron from its trigram index).
- **U32** - premise corrected and metric superseded: the host does NOT load SKILL.md bodies eagerly - it eager-loads name + description[:57]+"..." (`SKILL_PROMPT_DESC_LIMIT=60`) and lazy-loads bodies via `skill_view`; cost ranking must price the 60-char index (now U47's metric), not file bytes. U32's uses-vs-value ranking intent is preserved inside U47.
- **U9** - pin dropped: target `agentskills.io/specification` + the `skills-ref` reference validator; implemented as U49 (U9's staleness half remains).
- **U31** - three new probes: `hermes_state` facade still exporting the names the plugin imports (state layer split on main - `hermes_state_{common,schema,search,registry,portability}.py`); `.hub/lock.json` + quarantine reachability (feeds U48); `SKILL_PROMPT_DESC_LIMIT`/`is_skill_description_truncated_for_prompt` availability (feeds U47). Doctor must probe the runtime module, never the local checkout (checkout is `v2026.8.27-603`, host newer).
- **U29** - second named writer source: hub `update` (attribution via U48) joins the ledger timeline.
- **U40** - synergy note: the linter's over-budget-description rule (`skill_linter.py:163-169`) is U47's gate-side counterpart; one integration can serve both.
- **U13, U34, standing rejections** - unchanged; release still v2026.8.31 (2026-08-31); no standing rejection overturned.

### Rejected directions (research cycle 5)

- sqlite-vec migration for semantic search - pre-v1 with announced breaking changes; native extension vs the optional-deps posture; the 10^2-10^3 skill working set is fine on the numpy scan.
- Model-assisted description optimization - contradicts the model-free default (KTD4); U47 delivers the measurable half without a model call.
- Hub bundle-shape validation as a standalone packet - real, but a slice of U40's linter integration (port `_referenced_support_paths` there).
- Cron filtering re-proposal - it is U38; the new `source_filter` API and #101199 measurements are recorded as U38's correction above, not a new packet.
- Re-proposing cycle-2/3/4 survivors - cross-referenced as U21-U25/U29-U34/U38-U42; premises unchanged or strengthened.
- Standing cycle-1..4 rejections - none overturned by cycle-5 evidence.

### Decisions

KTD21. Remediation precedes extension (continuing KTD1/KTD7/KTD12/KTD16): U43-U46 land before U47-U50 - and the still-uncommitted cycle-1 + cycle-4 batches are committed first; cycle-5 fixes on top of two uncommitted batches compounds the loss risk KTD16 named.
KTD22. One packet per root cause: U45 merges the assess finding (Q6 hook latency) with research S3 (warm-writer topology) because they share file, mechanism, and the upstream #101191/#101202 recipes; U44 merges Q3 and Q5 for the same reason (one atomic-write helper family in `guarded_apply.py`).
KTD23. U47 supersedes U32's metric (60-char index, lazy bodies) while preserving U32's ranking intent; U32 is closed by absorption, not left open with a stale premise.
KTD24. U50 is demand-gated (KTD14 pattern): ship only on a second independent demand signal (a hub install on a real host, or a user report); requires U48 first.
KTD25. Remote policy unchanged (KTD2); this cycle-5 extension is roadmap-only and commits nothing.

### Sequencing

Commit both uncommitted batches first (KTD21). Then U43 (it repairs the product's entire input signal and everything downstream - U24 cohorts, U28's premise, U47's correlation - reads it) -> U45 (shares `storage.py` with U46; land together) -> U44 (shares `guarded_apply.py` with the U15/U35 surface, already open in the tree) -> U47 -> U48 -> U49. U50 stays demand-gated (KTD24). Standing order otherwise unchanged: U7's remaining items (version single-source, lint/CI gate - Q2's F821 and the 65->64 ruff drift are its evidence - docs) ride the next remediation batch; U36 remains the open backfill defect (N2/N2b/N3 reproduced again this pass); U17/U18/U19/U20/U25/U26 ride the cycle-2/3 batches as sequenced there.

## Extension 2026-09-02 - maintenance cycle 6

Provenance: cycle-6 adversarial assessment pass 6 (attempt `9ce2f967fe58402db266be29f077d742`; fresh pass - no finding carried on trust, all 24 probes re-derived on this tree; 3 new P2s S1-S3 + 7 new P3s S4-S10, plus carried re-derived with fresh line cites; artifacts `docs/assessment/2026-09-02-adversarial-repository-assessment-pass6.md`, `/home/agent/.hermes/conductor-runs/6f5d76c84f52491ba25460c4a6e1a454-assess/{review.md,repro-pass6.py,repro-pass6.json,repro-pass6-fixups.py,repro-pass6-fixups.json}`; methodology disclosure: no ce-* router/skill installed on host - ce-code-review lenses applied in-thread, same as passes 2-5; one early misfired probe appended normal backfill rows to the live host evidence DB, disclosed in the report and left in place) plus cycle-6 extension research (attempt `c592ae8daa9e486ca68355af84dc1725`; 6 ranked survivors from a ~14-candidate pool, 7 fresh rejections; artifacts `docs/ideation/2026-09-02-cycle-6-extension-research.md`, mirrored to `/home/agent/.hermes/conductor-runs/6f5d76c84f52491ba25460c4a6e1a454-research/research.md`). Baseline at cycle-6 assess: pytest 249/249 (31.3s, hermes-agent venv) at HEAD `4350ee2` on `fix/maintenance-cycles-1-5` (`4350ee2` is a workflow-trigger-only empty commit; source identical to `ac9c0ee`); ruff 63 errors / 48 fixable (drift 65->63->64->63, ungated). Roadmap discipline unchanged: pure append, all prior sections preserved byte-identical (pre-image sha256 `7acb640871d750b1abaab1e129df85ed938e7d45711cf9f1e99ca77fbd83b2ab`, saved at `/tmp/roadmap-before-cycle6.md`).

### Completed in cycle 6

- 2026-09-02 `assess` (pass 6) - fresh adversarial pass on the committed cycles-1-5 tree: **every cycle-1-5 fix verified fixed** (Q1 base table, Q3 mode 0o640 preserved through apply AND rollback, Q4 README rollback form, Q5 atomic snapshot, Q6 hook stall bounded at 10.27s measured - residual, N7, N2-class below 10k sessions, P7 schedule injection cleared by design: garbage rejected); 24 probes: 19 reproduced, 3 re-run after harness fixes, 2 tested-and-cleared. New: S1 classifier misses multi-digit failure counts with passing counts (`"10 failed, 2 passed"` -> success, `candidates.py:100` `(?<!0\s)failed`), S2 `{"code":200/201/204}` -> error with `error_events` poisoned 3/3 (`candidates.py:115,258-262`), S3 backfill `metadata_cap` binds in storage order - 10,040-session fake with limit 2 yielded s9999/s9998, newest never fetched, 50 pages (`backfill.py:203-207`); P3s S4-S10 (S5 read paths bypass `_path_lock`; S6 `_extract_skill_name` asymmetry `skill_view` vs `read_file` and event_count inflation, `storage.py:219-229`; S7 docstring "zero->success" contradicts pinned behavior; S8 duplicate frontmatter names silently drop a dir, `auto_evolve.py:399`; S9 bundled SKILL.md `version: 0.11.0` vs 0.10.0 elsewhere - U7b test gap at `tests/test_auto_evolve.py:1238-1246`; S10 raw tracebacks). Carried re-derived: P5/P6 (apply loop plain `write_text` at `auto_evolve.py:1163` inside 1155-1167, `:1143`), P8 (UnicodeDecodeError aborts whole legacy import - newly reproduced), P9 (`:486` count=1), N6 (`verifier.py:26` trusts claimed counts), C1 (`semantic.py:199` truncates before rerank 202-213), C3 (`review_queue.py:173` dead path), P12 (`skill_sources.py:60,209`), P14 (CI pytest-only), P15 (`cli.py:372-377`), cap-unification (32B/26c/53c across `candidates.py`/`guarded_apply.py`/`auto_evolve.py`). No P1s.
- 2026-09-02 `research` - 6 ranked survivors, 7 fresh rejections. Key discoveries: **the bundled-skill sync contract** - runtime `skills_sync.py` keeps manifest v2 `skill_name:origin_hash` (81 live entries) and updates a user copy only while it matches origin; live-reproduced on this host: `evaluating-llms-harness` diverged by one support-file edit (`references/api-evaluation.md` 11085B vs 11114B bundled) and is silently frozen out of all future bundled updates; the plugin reads names only. Upstream drift: #101274 merged / #101300 open / #101226 open (curated edits to synced copies first-class); #101316 (state.db auto-prune 90d + ratio-gated VACUUM recipe); #101266 (cron trigram exclusion -93.9%); #101237 (Skills Index, 977 skills; URL 404-verified twice); native-curator defect cluster #79295/#79311 (clock-vs-usage staleness false positives), #95441 (desktop-only installs never auto-tick), #66648, #97964 (`absorbed_into`), #101341 (revision-identity incident), #101294/#95387 (implicit skill prefetch watch item). Research: SkillProx (2608.07449 - outcome-grounded gates + knowledge-unit demotion), SkillComposer (2606.06079 - improve/merge orthogonal), SkillX (2604.04804 - rejected for scope). New direct competitor `cskwork/skill-curator` (lifecycle UX pattern set); SkillClaw idle since 08-17; agentskills spec unchanged (U49 pin holds).
- 2026-09-02 `roadmap` - this extension; append-only, all prior sections preserved byte-identical.

### Packet status (verified in working tree this cycle)

- Cycles 1-5 are **landed and committed** on `fix/maintenance-cycles-1-5` (`4350ee2`) - KTD16/KTD21's commit gate is discharged; the only uncommitted paths are the two new docs (pass-6 report, cycle-6 research doc), which ride the next commit per convention.
- Cycle-5 remediation batch verified fixed by pass 6: U43 closed at its base truth table (Q1 corpus passes) **but reopened by S1/S2 - see B23**; U44 closed (mode preserved through apply AND rollback, snapshots atomic); U45 closed (10.27s bounded, residual noted - B25 reopens the read side); U46 closed; U36 closed below ~10k sessions **but S3 reopens it at scale - see B24**; U17 closed (schedule garbage rejected, F19 cleared); U7-riders closed (F821 gone, README current) except U7b's test gap (S9 - the single-source equality test does not cover the bundled SKILL.md).
- Test baseline moved 184 -> 249 (+65); ruff 63 errors / 48 fixable, still ungated in CI (P14 - the 65->63 drift across two cycles is the standing evidence).
- Unstarted: U5, U6, U18-U20, U25-U26, U29-U34, U38-U42, U47-U50. P5/P6, P8, P9, N6, C1, C3, P12, P15 remain carried defects with fresh line cites above.

### Blocking issues discovered (cycle-6 assessment)

B23. The error classifier is wrong AGAIN, in two new classes (S1+S2+S4+S7; U43 reopened a second time - the third consecutive cycle a classifier defect is found): multi-digit failure counts paired with passing counts read as success (`"10 failed, 2 passed"`, `"100 failed"`, `"110 failed"` all false at `candidates.py:100` - the `(?<!0\s)failed` lookbehind only guards a bare leading zero); and structured `{"code":200}` (also 201/204/8080 - HTTP success codes stored verbatim by tool wrappers) classifies as error at `candidates.py:115,258-262`, with `record_tool_pass` then appending poisoned `error_events` rows 3/3 in the probe. S4 (a global success phrase anywhere in the payload clears the verdict, `candidates.py:109-112`) and S7 (the module docstring promises "zero -> success" while `tests/test_candidates.py:491` pins the opposite) are the same file's residual family. This poisons the exact cohort U24/U60 must read. -> U51.
B24. Backfill `metadata_cap` binds in storage order, not recency order (S3; U36 reopened at scale): on a 10,040-session store with limit 2 the importer yielded s9999/s9998 (oldest region), never fetched the newest session, walked 50 pages, and logged `sessions_skipped_old=9675` while skipping everything recent (`backfill.py:203-207`). The cycle-5 fix made paging trusted-order; the cap must bind AFTER ordering. -> U52.
B25. EvidenceStore read paths bypass `_path_lock` (S5): `storage.py:291-299`'s docstring promises serialized access but the summary/report readers at `:540/:599/:622` open independent connections (probe: summary() completed in 0.001s while the lock was held by another thread); a reader's `with conn:` block can COMMIT or ROLL BACK another thread's in-flight transaction; and PRAGMA setup runs under the global lock (`:304-330`). -> U53.
B26. Skill attribution is asymmetric and inflates counts (S6): `_extract_skill_name` (`storage.py:219-229`) derives a skill from `read_file` payloads but not from `skill_view` skill lists, so the same lookup attributes differently by tool; two differently-tagged events for one underlying action each increment `skills[].event_count`. -> U54.
B27. Duplicate frontmatter names silently drop a directory (S8; `auto_evolve.py:399`): two skills sharing a `name:` in different dirs collapse to one dict entry with no report, no warning - the same disease as upstream #101341's same-name/different-version profile incident. -> U55 (and it is U59's remediation prerequisite).
B28. Hygiene set (S9+S10+Q6-residual+caps+P14+P15+carried P-series): bundled SKILL.md version 0.11.0 vs 0.10.0 elsewhere with the U7b equality test not covering it; raw tracebacks leak to console (`skill_audit.py:289-290`, corrupt-manifest JSONDecodeError in propose/verify/rollback, bootstrap schedule ValueError); Q6 residual 10.27s; the 32-byte/26-char/53-char cap trio is three different constants for "one line"; CI runs pytest only (ruff 63 ungated); `cli.py:372-377` UX. -> U56.

### New work packets - cycle-6 remediation

U51. Error-classifier truth table, second reopen (B23/S1+S2+S4+S7; completes U43's corpus)
- AC: `looks_like_error` handles paired counts correctly - a failure count >0 paired with any passing count (`"N failed, M passed"`) is an error for ALL N (digit-width-independent, no regex lookbehind tricks); structured shapes treat `code` as process-exit-code semantics EXCEPT when the value is a recognized HTTP/in-band success status (200/201/202/204) or carries an explicit `ok`/`success`/`status` companion; no single success phrase anywhere in a long payload clears an error verdict (phrase scoping restricted to the failing field/line context); the module docstring and `tests/test_candidates.py:491` agree - change one to match the pinned truth, in one commit.
- E: all S1/S2/S4/S7 probes from `repro-pass6.py` flip (liftable verbatim into `tests/test_candidates.py` as the permanent adversarial corpus v2); a `record_tool_pass({"code":200})` fixture yields zero `error_events`; existing 249-test suite green; docstring/test contradiction gone (grep shows one truth).

U52. Backfill cap-in-recency-order + honest accounting (B24/S3; completes U36 at scale)
- AC: `metadata_cap` is applied AFTER trusted-order paging yields the newest `cap` sessions (cap the *result*, never the *scan*), with a monotonicity assertion; `sessions_skipped_old` counts only sessions actually skipped (not pages walked); bootstrap paths share the same ordering guarantee; the 10,040-session fixture becomes a test.
- E: the S3 reproducer (10,040 fake sessions, limit 2) yields the TWO NEWEST sessions (s10039/s10040-equivalents), one page (or bounded pages), and truthful skip counters; sub-10k behavior unchanged (N2/N2b/N3 corpus stays green); targeted pytest.

U53. EvidenceStore read-path concurrency contract (B25/S5)
- AC: either readers acquire the same per-path lock discipline as writers or (preferred) readers open read-only connections (`file:...?mode=ro`) that cannot commit/rollback another thread's transaction; the `storage.py:291-299` docstring is corrected to describe the ACTUAL guarantee; PRAGMA setup moves off the global lock path; no reader ever issues an implicit commit.
- E: the S5 probe re-run - summary() under a held `_path_lock` either blocks briefly or safely completes via a read-only connection, and a concurrent-writer fixture shows the writer's transaction survives (no phantom commit/rollback); targeted pytest.

U54. Symmetric skill attribution (B26/S6)
- AC: `_extract_skill_name` recognizes `skill_view` skill lists on the same terms as `read_file` payloads (one shared extraction entry point); a single underlying lookup surfaced through two differently-tagged events yields ONE attributed skill action (event_count counts actions, not event rows); the asymmetry test from the S6 probe lands in `tests/test_storage.py`.
- E: the S6 reproducer flips (both surface forms attribute; event_count = 1 for the double-tagged case); no regression in the existing attribution tests; targeted pytest.

U55. Duplicate-name collision reporting (B27/S8; prerequisite slice of U59)
- AC: discovery keys on paths and REPORTS frontmatter-name collisions - which directory wins at host load time (read from runtime index behavior, not assumed), the dropped path, and its manifest/eligibility state; nothing is silently dropped; `auto_evolve.py:399`'s dict-collapse goes through an explicit collector.
- E: the S8 fixture (two dirs, same `name:`) produces a collision report with precedence and zero silent drops; targeted pytest; feeds U59's `absorbed_into`/pin vocabulary.

U56. Hygiene batch (B28: S9 version single-source incl. bundled SKILL.md + S10 traceback hygiene + Q6 residual + cap unification + P14 ruff gate + P15)
- AC: the version equality test covers `__init__.py`, `plugin.yaml`, the bundled `skills/curator-evolution/SKILL.md`, AND the result `schema_version` (close the S9 gap); every raw traceback path (`skill_audit.py:289-290`, corrupt-manifest JSONDecodeError in propose/verify/rollback, bootstrap schedule ValueError) is caught and rendered as a one-line actionable error; the one-line cap constant is unified (bytes vs chars resolved and documented) across `candidates.py`/`guarded_apply.py`/`auto_evolve.py`; CI adds a ruff gate at the current 63-error baseline (never rises, ratchets down); Q6's residual 10.27s is measured again and bounded below 10s or documented as acceptable with the fixture cited.
- E: S9/S10 probes flip; `ruff check .` count <= 63 on CI and locally; version test fails loudly if any of the four sources drifts; full suite green at the new baseline.

### New work packets - cycle-6 extensions (research survivors)

U57. Bundled-origin provenance (candidate 1; 85%/Low; extends U48's scope per KTD27)
- AC: source classification parses `skills/.bundled_manifest` v2 origin hashes (import-guarded, tolerate-absent); `report --skills` (inside the existing mode, no new command surface required) emits per bundled skill: `intact` (sync may update; a later hash change is attributed `sync update` in U29's timeline), `curated-diverged` (frozen out of bundled updates - show the three-way diff bundled<->origin<->current using the existing diff plumbing), `bundled-behind` (origin changed under an intact copy); read-only throughout - `reset_bundled_skill()` stays the host's verb, the report may only point at it; `doctor` gains a manifest-reachability probe.
- E: a fixture manifest + diverged tree yields the three states with a per-file divergence walk; this host's live state (81 tracked, 80 intact, 1 support-file-diverged `evaluating-llms-harness`) is the sanity baseline cited in the change unit; an absent manifest degrades silently; no write path exists.

U58. Evidence-anchored staleness reconciliation with the native curator (candidate 2; 75%/Low-Med)
- AC: `report --staleness` (offline, local-only; note: U50's same flag name is hub-SOURCE staleness - merge the two under one flag with two sections or rename now, decide in design) reconciles the native curator's state file (tolerate-absent, never write) with plugin evidence: "marked stale but N attributed events in last D days (false-stale, #79295 class)" vs "no attributed events since seed (true never-used, supports #79311)"; respects `_cron_referenced_skills` (cycle-4 R6's set); `doctor --curator-tick` answers #95441 (native curator ticking on this install? if not, the plugin's scheduler is the only curation path - say so).
- E: fixture state file + evidence rows yields both verdict classes with rows cited; absent state file degrades silently; cron-referenced skills are exempt; no write to host state.

U59. Lifecycle vocabulary: pinned / absorbed_into / collisions (candidate 3; 70%/Med; `adopt` rejected per KTD29)
- AC: per-skill `pinned` state in the review queue (user intent, distinct from `protect_core_skills`'s origin-class list) hard-blocks archive/prune/retire paths; completed consolidations record `absorbed_into` in both manifests and mirror it wherever the host makes it visible (#97964 direction); collision/precedence reporting comes from U55; C3's dead `update_status` path gains a real caller (pin/unpin) or is deleted.
- E: a pinned skill survives an otherwise-qualifying prune in a fixture; post-consolidation manifests carry `absorbed_into` both ways; collision report renders from U55's collector; targeted pytest.

U60. Outcome-delta gate for applies (candidate 4; 72%/Med; hard-depends on U51 - and U24's dependency line now names U51 too)
- AC: each apply records its pre-apply cohort (attributed error rate over the trailing window for that skill, with minimum-N threshold and `insufficient-evidence` as an explicit verdict); the next run computes post-apply `outcome_delta` and attaches it to the candidate/manifest; a candidate whose predecessor's measured cohort regressed beyond threshold is quarantined from auto-apply (human review only) - the outcome-measured upgrade of U22's anti-pattern ledger; N6's claim-vs-report count cross-check lands as the first trivial slice; confounders (model/tool versions) are recorded, not corrected.
- E: a fixture with a regressing predecessor quarantines the successor and prints the delta; a low-N fixture prints `insufficient-evidence` and applies nothing automatically; the N6 cross-check catches a lying verify report in a fixture; no model calls.

U61. Knowledge-unit demotion (candidate 5; 60%/Med-High; most speculative survivor)
- AC: each managed-block bullet carries its generating evidence cohort (bullet->refs map persisted; normalized-bullet-text hashing, merges mark `lineage-lost` and stay eligible); a bullet whose cohort has zero attributed events for `stale_units_days` is DEMOTED - text moved to `references/curator-evolver-demoted-<skill>-<ts>.md` with a one-line pointer - behind the existing apply/verify/rollback machinery; error-preventing content (gate on error-type, not just count) is exempt; docs state honestly this is an evidence-count approximation of SkillProx's leave-one-out utility, not utility measurement.
- E: a fixture block with one stale-cohort bullet demotes exactly that bullet and rollback restores it byte-identically; an error-type-linked bullet is exempt; `stale_units_days` default conservative (>= 90) with the threshold printed; targeted pytest.

U62. Ecosystem duplicate check against the Hermes Skills Index (candidate 6; 55%; demand-gated per KTD28)
- AC: `report --ecosystem` (opt-in, network-gated, offline-safe) - HARD-GATED on the index actually being deployed (`HERMES_INDEX_URL` live, not 404; PR #101237 merged or equivalent); flags curated skills colliding with an indexed skill by normalized name first, content hash second ("you maintain by hand what ClawHub/LobeHub/skills.sh ships (vX)"); feeds consolidation candidates.
- E: a fixture index + colliding skill yields the report with the source cited; offline/404 renders "index unavailable" without erroring; no write path; a one-line re-verify pointer to the gate.

### Evidence corrections to standing packets (from cycle-6 research)

- **U48** - scope broadened (KTD27): hub provenance is one of THREE local provenance sources - `.hub/lock.json` (hub), `.bundled_manifest` origin hashes (bundled, U57), native-curator state (U58's read side). One `SkillSourceInfo` extension, three readers.
- **U29** - third named writer: `sync_skills()` host-upgrade updates (attributable via U57's origin-hash comparison) join hub `update` and human edits in the ledger timeline.
- **U36/U52** - new horizon constraint: upstream #101316 (auto_prune default True, 90-day ended-session retention, ratio-gated VACUUM) caps state.db history once merged; U52's design documents the horizon, and the plugin's evidence store becomes the only >90d record - raising U23's priority, now with #101316's recipe to port instead of inventing one.
- **U45 residual/S5->U53** - #101279 (multi-writer shared-brain deployments, open) shows upstream expects concurrent multi-writer patterns to grow: the read-path concurrency fix matters more, not less.
- **U47** - the Claude Code operator-control pattern (`skillOverrides` name-only/off) has no Hermes equivalent; recorded as a potential UPSTREAM issue, not plugin work; the plugin-side lever is U61's demotion.
- **U31/U13** - three new doctor probes: bundled-manifest reachability + hash parse (feeds U57); native-curator ticking (desktop-only gap, #95441, feeds U58); skills-index URL liveness (feeds U62's gate).
- **U50** - relationship clarified: U50 is hub-SOURCE staleness (network-gated); U58 is host-STATE reconciliation (local). Complementary, not overlapping - but they must not both claim `report --staleness` (decide in U58's design).
- **U24** - dependency line updated: honest cohorts need U51 (the reopened truth table), not the closed U43 base; U60 subsumes U24's measurement intent with an academic design contract (SkillProx 2608.07449).
- **Watch item (no packet)**: #95387 implicit skill prefetch - if mention-driven prefetch lands, `skill_view`-based attribution (S6/U54) loses coverage; re-run U54's evidence if it merges.

### Rejected directions (research cycle 6)

- SkillX-style automated skill-library construction (hierarchical planning/functional/atomic generation) - contradicts the model-free default (KTD4) and the plugin's scope (curating human/hub-provided skills, not synthesizing libraries).
- Porting `cskwork/skill-curator`'s multi-root discovery wholesale - the plugin is Hermes-native; cross-harness roots are a different product (only the collision/precedence reporting pattern survives, in U55).
- `adopt` lifecycle semantics - everything the plugin tracks already has evidence by construction; an adopt gate would guard a population the plugin never acts on (pin/absorbed_into/collision survive, in U59).
- Leave-one-out per-unit utility audits (SkillProx's exact backward gate) - needs an eval harness and task batches the plugin deliberately doesn't have; U61 ships only the evidence-count approximation and says so.
- Index-backed anything before deployment - `HERMES_INDEX_URL` 404s (verified twice); PR unmerged. U62 is written to be unbuildable until that changes.
- Listing-budget knobs in the plugin - host-side settings, not plugin surface; recorded as a potential upstream issue.
- Standing cycle-1..5 rejections - none overturned by cycle-6 evidence; agentskills spec unchanged (U49 pin holds).

### Decisions

KTD26. Remediation precedes extension (continuing KTD21): U51-U56 land before U57-U62. The commit gate that blocked cycle 5 is discharged (cycles 1-5 committed on `fix/maintenance-cycles-1-5`); the two new docs ride the next commit.
KTD27. U57 extends U48's scope rather than duplicating it: provenance is one subsystem with three sources (hub lock, bundled manifest, native-curator state) - build the `SkillSourceInfo` extension once, consume it from both packets.
KTD28. U62 is demand-gated (KTD24 pattern) with a hard technical gate on top: the index must be live (not 404) AND the PR merged or equivalent - re-verify at the next research pass.
KTD29. `adopt` is rejected as a concept (no evidence-free population exists here); `pinned`/`absorbed_into`/collision reporting survive into U55/U59. KTD23-style: no stale-premise packet is left open - U24's measurement intent is absorbed by U60, and U24 closes when U51+U60 land (update its status then, do not delete history).
KTD30. Remote policy unchanged (KTD2); this cycle-6 extension is roadmap-only and commits nothing.

### Sequencing

U51 first - it is the third consecutive cycle a classifier defect tops the board, the reopened truth table poisons every downstream consumer (U24/U60 cohorts, U47's correlation, auto-evolve thresholds), and its corpus is already written in `repro-pass6.py`. Then U52 (same ingest pipeline, disjoint file) -> U53+U54 (both in `storage.py`, land together) -> U55 (opens U59's vocabulary) -> U56 (hygiene, ratchets CI). Extensions follow in research rank order: U57 -> U58 -> U59 -> U60 (needs U51) -> U61 -> U62 (gated, KTD28). Standing order otherwise unchanged: U5/U6/U18-U20/U25-U26/U29-U34/U38-U42/U47-U50 ride the cycles-2..5 batches as sequenced there; the next implement batch should take U51+U52+U53(+U54) as its core - all three are reproduced P2/P3 findings with lift-ready tests.
