# Cycle-4 Extension Research — evidence-backed candidates beyond the standing roadmap

- **Run:** `673d15323b9c4580a0e2ed84fa8625fc` · phase `research` · attempt `bef3d264d5fd4d76b46e1d02762171c9`
- **Intent:** `research_repository_extensions`
- **Date:** 2026-09-02 (~09:20Z) · **Repo:** `main` @ `45328db` + 11 uncommitted cycle-1 remediation files
- **Skill:** routed via compound-engineering router → `ce-ideate` (no `ce-research` in the installed roster; matches cycle-2/3 routing). Run scratch: `/tmp/compound-engineering-1000/ce-ideate/20260902-091847-f3ee7d90/`
- **Prior passes:** `docs/ideation/2026-09-02-cycle-{2,3}-extension-research.md` (run `682bd7e4…`). This pass does **not** re-propose their survivors; it adds a new evidence layer and 9 fresh candidates.

**Method disclosure:** grounding, evidence scouting, six-frame generation, and basis verification all ran in this single pi context (no dispatchable subagents available) — no independence is claimed for any survivor. Raw pool ~18 candidates vs the default fleet target ~36–48. Every `direct:` basis below was verified this run (live source read, read-only SQL, or `gh api`).

---

## What's new since cycle-3 (~08:20Z)

1. **Upstream #101063 closed** (2026-09-02T07:31Z): `_find_skill()` used `Path.rglob("SKILL.md")`, which does not follow symlinked skill dirs, while the listing API uses `os.walk(followlinks=True)` — the two paths disagreed on which skills exist. Fix merged: rglob → walk, and categorized lookup keeps the *unresolved* path for `relative_to()` because `resolve()` escapes the skills root. **This repo still has the superseded pattern** (`auto_evolve.py:310`).
2. **Ledger PR #100471 still open** (not merged); its parent observability issue **#100449 is now closed**. v2026.8.31 remains the latest release — no version drift since cycle-3. Otherwise the new-issue stream (08:28–08:53Z) has nothing curator/skill-related beyond #101063/#101073.
3. **Host surfaces the plugin is provably blind to** (grep → 0 hits for `skill_linter|skill_usage|usage.json|workspace_key` in `hermes_curator_evolver/`): a 462-line first-class **skill linter**, a 100-entry **`.usage.json` per-skill lifecycle sidecar**, and **`workspace_key` scoping** on `search_sessions`.
4. **Evidence-source pollution, quantified on the live host**: the default 30-day backfill imports **250 cron sessions (2,524 tool messages) and 34 sub-agent sessions** out of 754 — upstream built `exclude_sources=["cron"]` / `exclude_children` for exactly this inflation, and the plugin filters nothing (`backfill.py:252` stores `source` as `platform` per row but no path reads it).

---

## Ranked candidates

### 1. Source-aware evidence pipeline — exclude cron + subagent children by default
**Axis A1 · Confidence 88% · Complexity Low**

- **Direct evidence:** live `state.db` (read-only): sources = cli 346 / **cron 250** / api_server 124 / **subagent 34**; tool-role messages = cli 6,788 / api_server 8,674 / **cron 2,524** / **subagent 199**. Upstream's `session_count` docstring (`hermes_state.py:13206-13220`) ships `exclude_sources=["cron"]` and `exclude_children` because raw counts are inflated by scheduler sessions and sub-agent/compression children. The plugin's hooks record every session regardless of source, and its evidence schema already carries `platform` per row (`storage.py` tool/turn/session_events; `backfill.py:252` maps `source`→`platform`).
- **Description:** filter `platform IN ('cron','subagent')` out at ingest (hooks + backfill import) by default; `--include-sources cron,subagent` opt-in; a one-shot SQL migration flag to re-filter already-stored rows.
- **Why it matters:** machine-generated usage currently counts as skill-usage evidence (≈22% of tool messages on this host), and any cron job that touches skills creates a daily-regenerating duplicate-evidence loop — the plugin would happily "learn" from its own scheduler.
- **Downsides:** users who genuinely want cron evidence need the opt-out; source strings are an upstream implementation detail (pin by allowlist of known human sources: `cli`, `api_server`, chat platforms).

### 2. Symlink-parity skill scanning — port upstream #101063
**Axis A4 · Confidence 90% · Complexity Low**

- **Direct evidence:** `auto_evolve.py:310` `for skill_file in sorted(root.rglob("SKILL.md"))` — the exact pattern upstream just fixed because rglob doesn't follow symlinked skill directories. Upstream's merged fix: `os.walk(str(skills_dir), followlinks=True)` filtering `SKILL.md`, and use the unresolved path for `relative_to()` (its fix note 2 applies to `guarded_apply.py:71-72` and `skill_sources.py:57/:131/:144`, which `resolve()` early).
- **Description:** adopt walk-with-followlinks for every skill-discovery site; add a symlinked-skill fixture to the test suite.
- **Why it matters:** dotfiles-style users (symlinked skill dirs) get those skills silently skipped by report/prune/apply today — invisible under-reporting, the same bug class the desktop UI shipped publicly.

### 3. Trusted-order backfill with drift detection — the *right* fix for N2+N3
**Axis A1 · Confidence 85% · Complexity Low**

- **Direct evidence:** `hermes_state.py:13155-13201`: `search_sessions` computes `last_active` (freshest of heartbeat and last message, `hermes_state_common.py:279-301`) and emits `ORDER BY last_active DESC, s.started_at DESC, s.id DESC LIMIT ? OFFSET ?` — a deterministic three-key total order, newest-first by construction. There is **no cutoff parameter**, so a cutoff cannot be pushed down into SQL.
- **Description:** page newest-first, stop at the first session older than `--days`, and assert observed monotonic non-increase across page boundaries (O(1) check); fall back to the current exhaustive scan only when the assertion trips. Fix bootstrap `limit=None` to the same loop. Print `sessions_failed` while at it (N7).
- **Why it matters:** the pass-4 remediation's fetch-everything posture (N3) pays O(all sessions × transcripts) to defend against an ordering violation the API contract already excludes; trust-but-verify restores O(recent) with a defined fallback. This supersedes the pass-4 fix *shape*, not its intent.

### 4. Host-linter integration as the post-apply gate (and `report --lint`)
**Axis A3 · Confidence 80% · Complexity Low-Med**

- **Direct evidence:** upstream `tools/skill_linter.py` (462 lines, importable + CLI): `lint_skill(path)`, `format_findings`, `has_errors`; checks include `_check_reference_links` (`:262-288`), which flags body references to `references/|templates|/assets/` paths that don't exist on disk as WARNING `dangling-reference`. Plugin grep for `skill_linter` → 0 hits.
- **Description:** after every guarded apply, run `lint_skill` on the written SKILL.md and fail verification on errors (warn on dangling-reference — which is exactly the artifact N4's keep=0 pruning produces); add `report --lint` for a whole-tree pass. Delete plugin-side validation where it duplicates the linter instead of growing a parallel one.
- **Why it matters:** closes the N4 class (pruning referenced files to zero) with the host's own maintained checker; keeps the plugin's "don't reimplement the host" posture.

### 5. Read the `.usage.json` sidecar as an independent per-skill ground truth
**Axis A3 · Confidence 75% · Complexity Low**

- **Direct evidence:** live `~/.hermes/skills/.usage.json` (verified this run): 100 entries keyed by skill name with `created_at`, `created_by`, `last_used_at`, `last_viewed_at`, `patch_count`, `last_patched_at`, `last_reused_patch_generation`, `archived_at`. `tools/skill_usage.py` (1,393 lines) documents the sidecar-not-frontmatter design; counters are bumped by skill_view/skill_manage; the native curator reads it for lifecycle. Plugin grep → 0 hits.
- **Description:** report/verify read (never write) the sidecar; emit a drift line when transcript-mined usage disagrees materially with `last_used_at`/`patch_count`.
- **Why it matters:** a second evidence clock, free, host-maintained — the drift line doubles as a correctness alarm for the plugin's own miner. Strictly read-only, honoring the standing rejection of writing into native state (which cycle-3 already narrowed only for ledger attribution rows).

### 6. Cron-referenced-skill protection before prune/retire
**Axis A2 · Confidence 72% · Complexity Low-Med**

- **Direct evidence:** `agent/curator.py:290` `_cron_referenced_skills()` — the native curator refuses lifecycle transitions for skills referenced by cron jobs. The plugin prunes/retires on its own reference counts alone (`auto_evolve.py:1054-1066`, where N4 showed keep=0 pruning a same-pass reference).
- **Description:** before any prune/retire decision, collect skills referenced by host cron job definitions and treat them as load-bearing (skip + report why).
- **Why it matters:** upstream has already encoded "scheduler references are load-bearing" as policy; the plugin's prune path currently has no equivalent and can delete the backing file of an automated job.

### 7. Port the host's sqlite hardening slice to the evidence DB (informs P4 fix)
**Axis A5 · Confidence 82% · Complexity Low**

- **Direct evidence:** `hermes_state.py:640-1200` — `resolve_journal_mode()` (canonical `database.journal_mode` config, default WAL), WAL-with-DELETE-fallback for filesystems where the pragma raises, `journal_size_limit` (`:941`), bounded WAL read pool (`_read_ctx`, `:4968`) so readers never convoy behind the writer, upstream issue #68545. Pass-4 P4 reproduced `database is locked` on the plugin's evidence DB under concurrent hooks+timer.
- **Description:** adopt the WAL + busy_timeout + journal_size_limit slice (not the whole layer) in `storage.py`.
- **Why it matters:** the fix is a pattern port of a proven in-tree recipe, not new design.

### 8. Rollback-as-guarded-mutation (narrows N1/C2)
**Axis A2 · Confidence 70% · Complexity Med**

- **Direct evidence:** host `hermes curator rollback <id>` writes a *pre-rollback safety ledger entry first and fails closed when that fails* (`hermes_cli/curator.py:675-722`) — rollbacks are themselves undoable. Pass-4 N1 showed the plugin's rollback deleting a restored SKILL.md when the manifest is tampered; C2 showed CLI-default rollback overwriting user edits.
- **Description:** give the plugin's rollback the same contract: a safety snapshot entry before any unlink/overwrite, refuse on snapshot failure, and require confirmation for destructive rollback of files modified after the apply. Pairs with cycle-3 ideas 1–2 (host-ledger read/write), not a replacement.

### 9. `workspace_key`-scoped backfill (`--workspace`)
**Axis A4 · Confidence 60% · Complexity Low**

- **Direct evidence:** `search_sessions(workspace_key=...)` exists (`hermes_state.py:13158`, git-root-else-cwd semantics) — built so `/resume`'s "last" means last *in this workspace*. The plugin imports all workspaces mixed together.
- **Description:** `backfill-sessions --workspace [key]` opt-in scoping.
- **Downsides:** opt-in only until demand shows up; cross-workspace evidence is arguably the point for shared skills.

### Also noted (fold into prioritize)
- **Config parity:** read upstream curator config keys (`stale_after_days`, `archive_after_days`, pinned set) so plugin thresholds and host lifecycle decisions never disagree — natural companion to survivors 5–6.
- **Carried fixes, not features:** pass-4 N5–N9 tails (NUL sanitizer regex, verifier grounding ratio, lint debt) remain remediation work, not roadmap items.

---

## Rejections this pass (beyond all standing cycle-1/2/3 rejections)

- **Optional aux-model review layer** (flip the model-free constraint, mirroring upstream's background review) — contradicts the plugin's model-free identity; upstream already owns that surface.
- **Evidence-DB stats dashboard** — generic observability listicle, no grounding evidence.
- **Writing `.usage.json`/curator lifecycle state** — standing rejection upheld (read-only survivor 5 is the honored slice).
- **Re-proposing cycle-3 survivors 1–6** (host-ledger read integration, ledger write-side, `doctor --host-compat`, context-budget report, circuit breaker, fleet-library report) — cross-referenced; their premises are unchanged or strengthened (ledger PR still open).

## Corrections to the standing roadmap

- **U12 (read-only host integration): strengthened twice over** — the readable surface now includes the skill linter and `.usage.json` sidecar besides the ledger; prioritize may want to fold U12 into survivors 4+5.
- **U9 (spec conformance):** linter's `_check_platforms_gating`/forbidden-files checks are additional conformance surfaces to mirror, not just frontmatter.
- **N2/N3 (pass-4):** survivor 3 supersedes the fetch-everything remediation shape with evidence about the API's real ordering contract.
- **Upstream drift otherwise nil** — v2026.8.31 latest; #67582/#77264/#66180 unchanged.

## Verification pointers (all read-only, reproducible)

- Source mix / tool messages: read-only sqlite over `~/.hermes/state.db` (`SELECT source, COUNT(*) FROM sessions GROUP BY 1`; `messages` join on `role='tool'`).
- Ordering contract: `hermes_state.py:13155-13201` + `hermes_state_common.py:279-301`.
- Symlink fix: `gh api repos/NousResearch/hermes-agent/issues/101063`; plugin side `auto_evolve.py:310`, `guarded_apply.py:71-72`.
- Linter/sidecar: `python3 -c "import sys; sys.path.insert(0,'/home/agent/.hermes/hermes-agent'); from tools.skill_linter import lint_skill"`; `jq 'length' ~/.hermes/skills/.usage.json`.
- Blindness: `grep -rn "skill_linter\|usage.json\|workspace_key" hermes_curator_evolver/` → 0.
