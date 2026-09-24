---
date: 2026-09-22
topic: hermes-curator-evolver-extension-research
focus: evidence-backed extension candidates beyond the current roadmap packet set; premise-drift check on upstream, index, competitors, standards
mode: repo-grounded
run: 3ed5d14a80a245f3bb71735d577be08a
phase: research
action: research:research
attempt: 411a6de96305451582a522c68d40ae9a
skill: ce-ideate (compound-engineering @ /home/agent/.config/opencode/node_modules/@fro.bot/systematic/skills/ce-ideate; no ce-research exists — ideate is the narrowest match for "evidence-backed feature and improvement candidates"). Deviation: no subagent primitive in this harness — grounding, generation, and adversarial filtering ran in one context; no independence claimed. External probes via gh CLI (authed codeo1io) + curl; live-host sources read directly at /home/agent/.hermes/hermes-agent (fork checkout b4528e6c98, 2026-09-21). Prior phase input: this run's assess phase (adversarial read of all core modules; baselines pytest 287, venv-ruff 12 w/ binary-skew caveat). Standing constraints honored: roadmap "Rejected directions" (pre-create similarity gate, replay benchmarks, cross-agent export/marketplace, git-PR review mode, MCP server for the queue, audit-skills rename, assessment-P3-fixes-as-features).
---

# Extension research — hermes-curator-evolver (2026-09-22)

> **Integration note (2026-09-24, roadmap KTD46):** this research ran on the run's pre-cycle-7 worktree; its proposed units were renumbered at integration per KTD41 (U77→superseded by main's U79, U78→main's U76/U78, U79→U90, U80→U91, U81→U92, U82→U93, U83→U94; the KTD39 proposal became main's KTD40 — see the roadmap "Integration fold 2026-09-24"). Datum correction: the "98,326 skills on 2026-09-20" figure in E1 belongs to 2026-09-21 per the authoritative cycle-9 ledger.

## Grounding Context (Codebase Context)

Repo: usage-evidence-driven skill curator plugin (hooks.py `on_post_tool_call`/`on_post_llm_call`/`on_session_end`; state-db vs legacy-dir ingest in backfill.py:428-449; evidence store storage.py with WAL-layer hardening at :66-97). This run's worktree is the pre-cycle-7 base; the roadmap packet set in-tree ends at the U55/U56-era planning, with U62 (ecosystem index report) double-gated per KTD28.

## Evidence gathered this phase (all read-only, 2026-09-22 ~09:1x-09:2x UTC)

### E1. Skills Index: live, daily-fresh, accelerating (direct)
- `curl -sI https://hermes-agent.nousresearch.com/docs/api/skills-index.json` → HTTP 301 → `https://nousresearch.github.io/hermes-agent/docs/api/skills-index.json` (Vercel front, GH Pages origin); `curl -sL` body 40,745,623 B, JSON top keys `version/generated_at/skill_count/skills`, **generated_at = 2026-09-22T07:53:16Z (same day), skill_count = 100,496**. Index URL default now lives in `tools/skills_hub_search.py:27` (moved from skills_hub.py:4499 in the older checkout).
- Prior passes: 98,326 skills on 2026-09-20 (KTD28), 977 cited when PR #101237 opened → **+2,170 skills in 2 days**; the deployed index keeps running ahead of the PR.
- `gh api repos/NousResearch/hermes-agent/pulls/101237` → **state=open, merged=false** (1 comment) — the merge half of U62's double gate remains closed TODAY.

### E2. Upstream release cadence + merged drift since 2026-09-02 (direct, via gh)
- Releases: **v2026.9.21** (published 2026-09-21T18:10Z), v2026.9.14, v2026.9.11 — in-tree research last knew v2026.8.31; upstream moved to ~weekly releases.
- Merged skills-adjacent PRs (gh search `is:pr merged:>2026-09-02 skill`): **#118884** `skill_manage warns when a SKILL.md body outgrows its context budget; batch results carry linter findings`; **#116004** one-shot runs stop authoring skills / loading process skills / spawning reviewer subagents; **#112218** concurrent skill_manage writers no longer lose edits; #113118 hub search finds skills the centralized index has not indexed yet; #116951/#116861/#113167/#114991/#109193 install/registration fixes; #107458 archify in optional-skills catalog.
- Merged sessions-adjacent: **#117684** `hermes sessions set-journal-mode delete|wal` offline conversion (#100896); #113210 mid-turn session-switch refusal; #116986 bulk-archive live-chat guard.
- Standing grounding issues **unchanged, still open** (comment counts static): #67582 near-duplicate explosion (6c) · #77264 archived-skills invisible to consolidation (1c) · #66180 auto-created skills never loaded (1c).

### E3. Live-host source facts (fork checkout b4528e6c98, read directly)
- **`on_skill_lifecycle` hook is live**: `tools/skill_usage.py:468-480` `_emit_skill_lifecycle` → `invoke_hook("on_skill_lifecycle", action, skill_name, provenance=telemetry_provenance(...), task_id, session_id, use_count, reused, reuse_after_patch)` — best-effort, emitted only after an authoritative state change whose write landed (`_mutate_and_emit`). The plugin does NOT consume it (grep over hermes_curator_evolver/ + tests/ = zero hits).
- **MRU-first SQL-side session ordering**: `hermes_state_sessions.py:1112` recursive-CTE candidate selection `ORDER BY COALESCE(s.last_activity_at, s.started_at) DESC, s.started_at DESC, s.id DESC … LIMIT ?` (line drift from the older :1365 citation; semantics intact).
- **Session ancestry edges**: the same CTE walks `compression_parent` edges, `_branched_from` model-config markers, and delegate markers (`hermes_state_sessions.py:1096-1110`) — compaction/branching/delegation fork session ids server-side.
- Plugin store already carries WAL-layer hardening (busy_timeout, journal_size_limit, per-path lock, journal-mode cache, ZFS disk-i/o retry — storage.py:66-97).

### E4. Competitors & ecosystem (external, gh — 2026-09-22)
- `Yonkoo11/hermes-dojo` ★174, **idle since 2026-06-06** (direct competitor, no movement in 3.5 months).
- `sentient-agi/EvoSkill` ★1214, pushed 2026-08-24 (active); `Akshay2695/muse_autoskill` ★38 idle since 2026-06-13; `NousResearch/hermes-agent-self-evolution` ★5386 idle since 2026-06-17.
- Fresh entrants: `EvoScientist/EvoSkills` ★436 (pushed 09-01), `ZJU-REAL/EvoSkill-GUI` ★17 (pushed 09-17), **`kitze/skillbox` ★226 created 2026-09-17 — "self-hosted, versioned skills library for AI agents, MCP, scoped clients"** (5-day traction), `cskwork/skill-curator` ★0 active 09-07.
- Volume explosion at the collection layer (ASu-skills ★5005 topical collections etc.) + index growth E1 → hand-maintained collision risk grows daily.
- Continuous usage-evidence-driven evolution (the curator's design center) remains unoccupied: every active competitor is benchmark/trajectory-driven or idle.

### E5. Standards
- `agentskills/agentskills` (spec repo): last push **2026-08-09**, latest commits are client-showcase additions (OpenClaw #492; "add hermes-agent" #491). **U49's pin (version under `metadata`, spec body unchanged) re-verified and holds**; bonus fact: upstream hermes-agent is now formally listed as an Agent Skills client.

## Ranked Ideas (survivors)

### 1. Consume `on_skill_lifecycle` for native attribution
**Description:** Add an `on_skill_lifecycle` handler to the plugin's hook surface (hooks.py currently: on_post_tool_call/on_post_llm_call/on_session_end only) and ingest its telemetry (action, skill_name, provenance, task_id, session_id, use_count, reused, reuse_after_patch) as first-class evidence rows, demoting transcript inference to a fallback for pre-hook history.
**Warrant:** `direct:` live host emits it at `tools/skill_usage.py:468-480`, best-effort only after authoritative state changes; plugin grep for `on_skill_lifecycle` = 0 hits; upstream #116004 additionally stops one-shot runs from authoring/loading process skills, which makes inferred attribution noisier exactly where the hook stays authoritative.
**Rationale:** kills the attribution-inference error class (the curator's core signal), self-dating and dedup-able by (task_id, session_id), and free — the host already pays for it.
**Downsides:** needs dedupe against inferred rows for the overlap window; hook is best-effort (misses are possible, ordering not guaranteed).
**Confidence:** 90% · **Complexity:** Medium · **Status:** Unexplored

### 2. Compression-aware evidence linking
**Description:** When ingesting from the state db, walk the host's ancestry edges (compression_parent, `_branched_from`, delegate markers — `hermes_state_sessions.py:1096-1110`) and link evidence rows to the canonical (root) session so usage attribution survives history compaction, branch, and delegation.
**Warrant:** `direct:` the host's own session queries resolve recency through exactly this recursive CTE; the plugin keys evidence by raw session_id (storage.py schema), so every compaction event silently forks the attribution history of a long-lived working session.
**Rationale:** long sessions are precisely where usage evidence accumulates; without linking, the curator's strongest signals get fragmented by host-side housekeeping the plugin never sees.
**Downsides:** ancestry walk adds ingest complexity; delegate sub-trees need a policy (attribute to root vs delegate).
**Confidence:** 80% · **Complexity:** Medium-High · **Status:** Unexplored

### 3. MRU early-terminate probing for the state-db branch
**Description:** In backfill's state-db branch (mutually exclusive with the dir scan, backfill.py:443-449), replace full enumeration with probe-then-early-terminate: page sessions MRU-first via the SQL-side `ORDER BY COALESCE(last_activity_at, started_at) DESC … LIMIT ?` and stop at the first page fully covered by prior ingests.
**Warrant:** `direct:` ordering+LIMIT confirmed at `hermes_state_sessions.py:1112` in the live checkout; the plugin binds to that SessionDB class (MRU-first, SQL-side, LIMIT/OFFSET-capable). The legacy-dir branch already MRU-sorts by mtime (backfill.py:149-150) — this closes the asymmetry.
**Rationale:** backfill cost on a busy host scales with history depth, not with new evidence; MRU termination makes incremental ingest O(new sessions).
**Downsides:** clock-boundary correctness needs a watermark + overlap re-probe; MRU order must be re-verified per host version (it drifted :1365→:1112 already).
**Confidence:** 85% · **Complexity:** Medium · **Status:** Unexplored

### 4. Relax U62's double gate to sustained-liveness
**Description:** KTD28 gates the ecosystem-collision report (`report --ecosystem`) on BOTH index liveness and PR #101237 merge. Evidence now shows the deployed index is independently operated and daily-fresh; propose re-gating on a 30-day daily-generation streak alone (or an explicit override check), leaving the PR-merge condition as a notice, not a gate.
**Warrant:** `direct:` this run — URL live (200 via 301→nousresearch.github.io), generated 2026-09-22T07:53:16Z, 100,496 skills, 40.7 MB; PR #101237 verified open/unmerged via gh the same morning; prior pass had 98,326 on 09-20 (+2,170/2 days).
**Rationale:** the report's value grows with index volume (collision risk compounds daily), and the merge half of the gate has been the only closed half for 20 days while deployment ran ahead.
**Downsides:** index schema is unversioned-by-contract (top keys version/generated_at/skill_count/skills observed); 40 MB payload needs streamed/windowed fetch discipline; a stewardship decision (KTD amendment), not just code.
**Confidence:** 75% · **Complexity:** Low (decision) + Medium (report impl per U62 AC) · **Status:** Unexplored

### 5. Derive skill-size caps from the host's context-budget signal
**Description:** Replace/augment the plugin's self-imposed caps (`_MAX_SKILL_CONTENT_CHARS`/`_AUTO_LOADED_SKILL_MAX_CHARS`, auto_evolve.py:53/55) with the host's budget verdict: upstream skill_manage now warns when a SKILL.md body outgrows its context budget and batch results carry linter findings (PR #118884, merged).
**Warrant:** `direct:` gh-verified merge; the host budget is the one that actually governs whether a curated skill loads — two independent budgets will diverge.
**Rationale:** a curator that trims to its own cap can still ship a skill the host refuses to auto-load (the exact failure mode of upstream #66180, still open).
**Downsides:** budget value is host-version-dependent; needs a fallback for hosts without the verdict surface.
**Confidence:** 70% · **Complexity:** Low-Medium · **Status:** Unexplored

### 6. Local versioned snapshots of curated skills (skillbox-interop posture)
**Description:** Give each promote/demote a lightweight local version trail (content-addressed snapshots under the existing store; optional skillbox-compatible manifest export) so restore drills and rollbacks operate on immutable points, not live files.
**Warrant:** `external:` kitze/skillbox gained ★226 in 5 days (created 2026-09-17) on "self-hosted, versioned skills library" — demand signal for versioned skill state; `direct:` this repo's restore_drill currently lacks a reaping story for drill scratch dirs and restore lacks the N1 manifest-path hardening rollback has (this run's assess).
**Rationale:** versioning is the missing primitive under both restore drills and the audit trail; staying local honors the rejected cross-agent export/marketplace direction.
**Downsides:** storage growth needs pruning; skillbox compatibility is speculative until its manifest stabilizes (5 days old).
**Confidence:** 55% · **Complexity:** Medium · **Status:** Unexplored

## Rejection Summary

| # | Idea | Reason Rejected |
|---|------|-----------------|
| 1 | Journal-mode/WAL interop with new `hermes sessions set-journal-mode` | Already covered in-tree: storage.py:66-97 has the WAL layer (busy_timeout, journal_size_limit, per-path lock); upstream #117684 is host-side conversion, no plugin action warranted |
| 2 | Near-duplicate creation blocking (upstream #67582 demand) | Rejected direction: pre-create similarity gate; consolidation among owned skills stays the lane |
| 3 | MCP surface for the review queue | Rejected direction (roadmap); skillbox's MCP usage does not reopen it |
| 4 | Cross-agent export / marketplace distribution | Rejected direction; skillbox traction noted but out of scope |
| 5 | Hub-search fallback for unindexed skills | Folded into idea 4 as an implementation detail (#113118), not a standalone candidate |
| 6 | Standalone one-shot-run telemetry handling | Folded into idea 1 (hook stays authoritative where one-shops go silent, #116004) |
| 7 | Pin ruff in CI | Real but already-seeded maintenance (#5442), below the ideation bar / already tracked |
| 8 | Refresh-only items (standing issues #67582/#77264/#66180; agentskills spec pin) | Premise refreshes, not candidates — reported in Grounding (E2/E5) |

## Sources

Internet (2026-09-22 ~09:15-09:30 UTC, gh CLI authed as codeo1io + curl): `repos/NousResearch/hermes-agent/pulls/101237` (open/unmerged); releases v2026.9.21/.9.14/.9.11; PR searches `merged:>2026-09-02 skill|sessions` (#118884, #117684, #116004, #112218, #113118, …); issues #67582/#77264/#66180 (states+comments); repo stats Yonkoo11/hermes-dojo, cskwork/skill-curator, sentient-agi/EvoSkill, Akshay2695/muse_autoskill, NousResearch/hermes-agent-self-evolution, EvoScientist/EvoSkills, ZJU-REAL/EvoSkill-GUI, kitze/skillbox; agentskills/agentskills commits (last push 2026-08-09); `https://hermes-agent.nousresearch.com/docs/api/skills-index.json` (301 → nousresearch.github.io; generated_at 2026-09-22T07:53:16.198683+00:00; skill_count 100,496; 40,745,623 B; fetched to /tmp/sidx.json). Local live host: /home/agent/.hermes/hermes-agent @ b4528e6c98 (2026-09-21) — tools/skill_usage.py:455-485, tools/skills_hub_search.py:27, hermes_state_sessions.py:1096-1116. Repo tree (this worktree): backfill.py:70,149-150,428-449; hooks.py:25-80; storage.py:66-97; auto_evolve.py:53/55.
