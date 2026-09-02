---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-3-extension-research
focus: cycle-3 evidence-backed extension candidates beyond the U8-U25 roadmap
mode: repo-grounded
run: 682bd7e431e34f7b9efc0c881cde253a
phase: research
action: research:research
attempt: b20d18cb3fc74b02b866cd2f2b5349a0
skill: ce-ideate (narrowest installed match for evidence-backed candidate generation; no ce-research exists). OUTPUT_FORMAT=md (pipeline). Deviation: pi has no subagent primitive - grounding, 6-frame generation, and basis verification ran in one context with disclosure; no independence claimed; raw pool ~15 vs the dispatched-fleet ~36-48 target. Fresh-doc decision: the prior artifact in this dir is cycle-2's provenance for the in-flight batch, so this run appends a new cycle-3 doc rather than mutating it.
---

# Cycle-3 extension research — hermes-curator-evolver

Prior phase input: cycle-3 adversarial assessment (attempt `82f9771fbc264672b53841b3cff35448`, 18 findings, artifact `docs/assessment/2026-09-02-adversarial-repository-assessment-pass3.md`). Standing constraints: the cycle-1 and cycle-2 rejection lists (`.hermes/plans/autonomy-prop_8c5390ffe26640fa.md` lines 121-130, 221-229) and the planned packet set U5-U25. This pass looks for candidates **beyond U8-U25** and for fresh evidence that **updates premises** — it does not re-run cycle-2's checks (release pinning, skills_guard internals, secret-exposure repro) except where premise drift was plausible.

## Grounding Context (Codebase Context)

Everything below was gathered read-only this attempt (2026-09-02, ~08:05-08:20 UTC). Local repo state: HEAD `45328db` + the 11-file uncommitted remediation batch (cycle-1 U1-U4 landed; U15-U25 unstarted — confirmed by pass-3 assess: `review_queue.update_status` still caller-less, `--enable` still `default=True` at `cli.py:358-361`, zero WAL/busy_timeout in `storage.py`).

### E1. Upstream now ships a skill-write ledger — and it is on by default (NEW this cycle)

- `tools/skill_ledger.py` (388 lines) exists on this host's v0.20.6 checkout: appends JSONL entries to `~/.hermes/skills/.curator_ledger.jsonl` (`ledger_path`, line 91) with `{id, ts, actor, action, skill, evidence, before[], after[]}` where before/after carry **path + sha256**; content snapshots via `_store_blob`/`read_blob`/`blobs_dir`; read API `list_entries`/`get_entry`; `ledger_enabled` gates on config `skills.ledger` **default True** (lines 98-101); `derive_actor` distinguishes `user` (CLI) / `curator` (curator walk, background review) / `agent`.
- **Live on this host**: 16 rows, actions `{create, edit, patch, delete}`, all `actor=agent` (sample read, e.g. row 1: create of `hermes-development-delegation` with before/after sha256s).
- Upstream issue **#100449** ("Observability gap: skill file writes with no skill_manage apply event and no agent.log entry") was **closed completed today at 02:46 UTC** — *after* cycle-1 research and *before* cycle-2's 07:05 upstream sweep (which tracked only releases + 3 grounding issues, so this passed unnoticed). The referenced fix PR **#100471** (`fix(skills): ledger write_file and patch hits on live skill trees`, still **open**, head `cursor/oss-buddy-...-100449-44fc`) extends ledger coverage to generic `write_file`/`patch` tool hits on live skill trees and documents the ledger in `website/docs/user-guide/features/{curator,skills}.md`.
- **Verified from plugin context this run**: `from tools.skill_ledger import append_entry, list_entries, ledger_path, ledger_enabled` imports cleanly; the plugin package contains **zero** references to `curator_ledger`/`skill_ledger`; and `guarded_apply.py:315` writes skills via direct `target.write_text` — i.e. **every plugin apply is invisible to the host's ledger/watchdog attribution today**, and conversely the plugin cannot see external writes it could now attribute.

### E2. Fresh upstream user-need signal (issues created since 2026-09-01; release check)

- Latest release is still **v2026.8.31** (re-verified). Tracked issues unchanged: #67582 (6c), #77264 (1c), #66180 (1c), #101035 (0c, open).
- **#100403** (open): plugin-registered skills (`ctx.register_skill`) are **omitted from interactive slash-command discovery** — `scan_skill_commands()` walks only project/local/`skills.external_dirs` roots. Direct relevance: the plugin's own bundled `curator-evolution` skill is likely invisible to `/`-invocation on affected hosts.
- **#100254** (open): a real **multi-profile fleet deployment** (1 default + 6 function-specific agents) asks for per-entry include/exclude filtering on `skills.external_dirs` so profiles can share a **central fleet library** while keeping lean per-profile indexes; the issue states `skills.external_dirs` (v0.20.x) already solved the visibility half.
- **#99877** (open): `requires_toolsets` has **no alias normalization** — a skill declaring `files` (natural plural) is *silently gated out forever*; same silent-invisibility class as our assess-P12 (custom skills-dir naming silently disables auto-apply).
- **#100056** (open): proposal for a `triggers` **SKILL.md frontmatter** field for multilingual discovery — a possible upstream divergence from the agentskills.io spec (watch item for U9 conformance).
- **#100715** (open): `--skill <builtin-name>` crashes worker spawn (`Unknown skill(s)`) despite `hermes skills list` showing the name — a third instance of the skill-identity/resolution failure class our U19 fixes locally.
- **#101002 [Epic]** (open): "Evidence-grounded autonomous goal loops" — upstream strategic direction toward *preserving trustworthy evidence across sessions* to close capability gaps end to end. Signals that evidence-grounding is becoming a first-class upstream concern, but no shipped surface to integrate with yet.

### E3. Competitor deep-dive — the four repos cycle-2 surfaced but did not read

All four are **dormant since May 2026** (last pushes 2026-05-10/17/23/30); the active frontier remains SkillSmith + Auto-Evolution (cycle-2's reads). Distinct mechanisms extracted:

- **AutoSkill** (ECNU-ICALK, 570★, arXiv 2603.01145): "**offline extraction from completed data** — existing chats and trajectories can be imported directly for offline skill extraction; there is no need to replay the original interaction"; **versioned skills**; universal SKILL.md format kept "readable, reviewable, manually revisable". Validates the plugin's own model-free offline-mining thesis (backfill) and adds **skill versioning** as an expected property. Also ships AutoSkill4Doc (document→skill) and SkillEvo (replay/eval/mutation/promotion).
- **MemSkill** (569★, arXiv 2602.02474): skills as *meta-memory*; "**periodically mine hard cases** to refine existing skills and propose new ones" — independent corroboration of the hard-case→refinement loop our U22 anti-pattern ledger implements.
- **SkillForge** (1★, zero-deps, 373 tests): tracks execution outcomes (success/latency/tokens), ranks skills by TD(λ) **Q-values**, auto-diagnoses failure patterns, **lifecycle draft→active→deprecated→archived**, and **3-tier progressive loading** (metadata→core→full) to minimize context-window waste.
- **SkillRL** (958★): recursive skill-augmented **RL training** — confirmed out of the plugin's cost class (model-free default); no transferable mechanism.

### E4. Standards and dependencies (re-checks)

- **agentskills.io/specification** re-fetched: same field set (name/description/license/compatibility/metadata/allowed-tools) — U9 baseline intact; #100056 is the only drift pressure visible.
- Runtime deps remain `PyYAML>=6` (+pytest dev) — nothing stale; the zero-dep posture matches SkillForge's positioning and needs no change.

### E5. Local status corrections (working tree, this run)

- U5 is **largely landed in the working tree**, contrary to the roadmap's status line: `auto_evolve.py:50` `_MAX_SKILL_CONTENT_CHARS = 100_000`, `:52` `_AUTO_LOADED_SKILL_MAX_CHARS = 12_000`, skip-hard-cap strategies at `:486/:519` (the roadmap's "_BUILTIN_HARD_CAP_CHARS still" wording is stale).
- U6 (`--enable` default True), U7 (no WAL/busy_timeout — 0 grep hits in storage.py), U20/U25 (dead `update_status`) all still open, matching pass-3 assess.

## Topic Axes

- A1 Host-integration surfaces (ledger, plugin skill discovery, cron, provides_tools)
- A2 Evidence quality and lifecycle (beyond U21-U24)
- A3 Multi-host/fleet operator needs
- A4 Skill lifecycle mechanics competitors validate (versioning, promotion, hard-case mining)
- A5 Standards and conformance drift

## Ranked Ideas

1. **Host-ledger read integration — external-drift attribution and a unified skill-history timeline**
   - **Description:** `doctor`/`report --external-changes` reads `~/.hermes/skills/.curator_ledger.jsonl` via `tools.skill_ledger.list_entries` and attributes every skill write the plugin did not make (actor, action, timestamp, sha256 before/after); unattributable content drift (file changed, no ledger row) becomes a review-queue row instead of a silent surprise. Fold in a `report --history <skill>` view that interleaves upstream ledger entries with the plugin's own apply manifests into one timeline, and seeds fresh installs with immediate skill history (16 rows already exist on this host) instead of waiting days for evidence.
   - **Axis:** A1.
   - **Basis:** `direct:` `tools/skill_ledger.py:91` path + default-on gate (lines 98-101) + `list_entries` read API, verified importable from plugin context this run; upstream #100449 body describes exactly this failure at a live deployment (16 drifted files, watchdog flagged, "could not be attributed to any session"); open PR #100471 extends coverage further.
   - **Rationale:** turns the plugin from blind to external skill writes into the one place a Hermes user can ask "who changed my skills and when"; upgrades U12's read-only integration from abstract conflict check to a concrete, documented, default-on surface. AutoSkill's "versioned skills" expectation (E3) lands here almost for free.
   - **Downsides:** ledger coverage is incomplete by design (terminal/editor/MCP writes stay unlogged per #100471 body) — the report must say "unattributed" rather than "no one"; PR #100471 not merged yet means tool-mediated writes may be missing on current hosts.
   - **Confidence:** 80% · **Complexity:** Medium.

2. **Attribute plugin applies in the host ledger (write-side integration)**
   - **Description:** `guarded_apply` calls `tools.skill_ledger.append_entry(action=..., skill=..., before/after=...)` when importable (record skipped if not), so every plugin apply appears in the host's own ledger, watchdog correlation, and `agent.log` grep surface; manifest hash cross-checked against the ledger entry's after-sha256 to detect write/record divergence.
   - **Axis:** A1.
   - **Basis:** `direct:` import of `append_entry` verified working this run; `guarded_apply.py:315` writes via `write_text` (bypasses the ledger); plugin has 0 ledger references. `reasoned:` upstream #100449/#100471 establishes that the ledger is the sanctioned attribution surface for skill writes — the plugin writing skills without recording there recreates, for plugin applies, the exact observability hole upstream just closed.
   - **Rationale:** this is an **evidence-based correction to a standing rejection**: cycle-2 rejected "writing into native curator state" on the premise "format ownership undocumented upstream" — the ledger is now a documented (website docs in #100471), default-on, importable API with a stable JSONL shape. The rejection should be re-decided narrowly: append-only attribution rows, never `.usage.json`/`.curator_state`.
   - **Downsides:** consumes upstream API surface that could change (needs the same import-guard/degradation posture as U21's skills_guard import); double bookkeeping (plugin manifests + ledger) must stay reconcilable.
   - **Confidence:** 75% · **Complexity:** Medium.

3. **`doctor --host-compat`: a compatibility and visibility sweep for every host surface the plugin leans on**
   - **Description:** one doctor pass probes each host dependency with a per-surface verdict: SessionDB read-only API reachable, `tools.skills_guard` importable (U21), `tools.skill_ledger` present (ideas 1-2), cron backend available (U13), and — new — **skill discoverability**: is the plugin's bundled skill visible to interactive slash discovery on this host (#100403), and do any local skills carry `requires_toolsets` values that silently gate them out (#99877)? Each miss prints the degradation the plugin already handles plus the upstream issue reference.
   - **Axis:** A1/A5.
   - **Basis:** `direct:` #100403 (plugin skills omitted from `scan_skill_commands()`), #99877 (alias gate silently hides skills), assess-P12 (skills-dir naming silently disables auto-apply); `reasoned:` U13's version-gate premise rotted silently between cycles — a probe surface is the systematic cure for premise rot, and it converts three silent-invisibility bug classes (two upstream, one local) into one observable check.
   - **Rationale:** cheapest trust-builder for unattended operation; every planned packet (U21-U25) imports or reads a host surface, so the sweep compounds; gives launch-day users a one-command "will this work here" answer.
   - **Downsides:** surface list must be maintained as packets land; upstream bug workarounds embedded in doctor output can go stale (cite issue numbers, don't paraphrase behavior).
   - **Confidence:** 78% · **Complexity:** Medium.

4. **Context-budget report: rank skills by evidence-measured context cost**
   - **Description:** `report --context-budget` computes per-skill `uses × content_chars` from the existing evidence store (tool_events usage + current file sizes), and reports which skills consume the most context per unit of demonstrated value (uses, error rates) — a pruning/priority input for U8 dedupe and U23 retention, and an objective answer to "is this skill worth its bytes".
   - **Axis:** A2/A4.
   - **Basis:** `external:` SkillForge's core thesis that skills should be "tracked, ranked, diagnosed … through real-world usage data" with 3-tier progressive loading existing specifically to "minimize context window waste" (E3); `direct:` the plugin already stores every ingredient (usage events, `is_error`, file sizes; `storage.py` schema, `report` machinery) — the metric is a join, no model, no new capture.
   - **Rationale:** Hermes loads SKILL.md whole, so per-skill bytes are real context cost on every load; nobody — host or competitor — can compute this *from local evidence* the way this plugin can. Differentiates on the plugin's unique asset while feeding existing packets (U8 priority ordering, U24 value framing).
   - **Downsides:** usage≠value (a rarely-used skill may be critical); report must print the caveat, not a score alone; AutoSkill/SkillForge treat ranking as core while we deliberately keep it advisory (model-free, no auto-prune).
   - **Confidence:** 70% · **Complexity:** Low.

5. **Circuit breaker for unattended scheduler runs**
   - **Description:** when N consecutive auto-runs end in verify-failure/rollback/suppression for the same skill (or M runs produce zero successful applies), the scheduler **disables itself** and files a review-queue entry naming the skill, the streak, and the suggested next action; re-enable is an explicit human `--clear-anti-pattern`-style act.
   - **Axis:** A2.
   - **Basis:** `direct:` the cycle-2 repeat-loop scenario (bad evidence row regenerating the identical failing block daily, M6/U22) is a *permanent* loop today — U22 suppresses identical blocks but nothing stops a drifting generator; `reasoned:` every long-running automation discipline (breakers, dead-man switches) distinguishes "bounded retry" from "alert a human" precisely because unattended loops without a stop condition consume trust and compute forever.
   - **Rationale:** converts the worst unattended failure mode from silent daily churn to a loud, safe stop; complements (and can be folded into) U22 as its escalation tier rather than competing with it.
   - **Downsides:** threshold tuning (too eager disables on noisy weeks); must survive scheduler restarts (streak state persisted in the evidence DB, not memory).
   - **Confidence:** 72% · **Complexity:** Low.

6. **Fleet-library conflict report (read-only, non-aggregating)**
   - **Description:** `report --skills-dir <shared-library>` mode that audits a central `skills.external_dirs` library the way it audits a private tree — near-duplicates, conflicting managed blocks, staleness, unpublishable content (U21) — explicitly **without** aggregating evidence across profiles; per-profile evidence stays local, the library is just a directory of skills.
   - **Axis:** A3.
   - **Basis:** `direct:` upstream #100254 documents a real 1+6-profile fleet sharing a central library and asking for curation-side filtering — the first concrete demand evidence in this problem space (cycle-1/2 rejected multi-profile work as "demand unevidenced"); `reasoned:` the plugin's audits are already directory-scoped (`--skills-dir`), so a shared library is the same object with higher blast radius, and conflict detection there is the same code path with the stakes printed.
   - **Rationale:** narrowly reopens a rejected direction on new evidence while honoring every ground of the original rejection (no evidence aggregation across profiles, no secret-surface growth — a report reads skill files it can already read).
   - **Downsides:** demand is one issue; the asker wants upstream filtering, not a plugin — this is a "watch demand, ship the cheap report" bet, the weakest survivor here; plugin currently assumes single-tree identity (U19 first).
   - **Confidence:** 55% · **Complexity:** Medium.

## Rejection Summary

- **Document→skill mining (AutoSkill4Doc analog)** — scope expansion beyond the plugin's identity (evidence about *usage*, not about documents); extraction needs a model, conflicting with the model-free default; AutoSkill4Doc already owns the niche.
- **Evidence provider for upstream #101002 goal-loop epic** — speculative against an open epic with no shipped surface; the feasible slice (chat-side evidence query) is already covered by the existing `curator_evidence_report` provided tool.
- **3-tier progressive loading (SkillForge)** — the host owns skill loading; the plugin cannot change it (scope), and idea 4 delivers the measurable half instead.
- **Q-value / TD(λ) effectiveness ranking (SkillForge)** — overlaps U24 outcome telemetry; RL-flavored ranking contradicts the model-free default and the replay-benchmark rejection family.
- **Standalone skill-history timeline / hash cross-check / backfill-from-ledger** — folded into ideas 1-2 (duplicates a stronger, unified candidate).
- **Multi-profile evidence aggregation (re-examined on #100254 evidence)** — rejection **upheld**: the issue asks for upstream include/exclude filtering, not cross-profile evidence aggregation; only the non-aggregating read-only report shape survived (idea 6).
- **Inbound skills_guard scan, marketplace/export, MCP surface, git-PR mode, replay benchmarks, `/curator` slash command** — standing cycle-1/2 rejections; no new evidence this pass overturns any of them.
- **In-thread run degradation (disclosure, not rejection):** grounding, generation (6 frames), and basis verification all ran in this one context — no independent corroboration is claimed for any survivor; raw pool ~15 candidates vs the dispatched-fleet target of ~36-48; verifier freshness absent by construction.

## Evidence corrections to standing roadmap items

- **U12 (read-only integration): premise strengthened and made concrete** — the surface to read is now `tools/skill_ledger` (default-on, importable, documented in #100471's website-docs diff). Idea 1 operationalizes it; the prioritization phase may want to fold U12 into it.
- **Cycle-2 rejection "writing into native curator state": premise partially stale** — "format ownership undocumented upstream" no longer holds for the *ledger* specifically (documented JSONL + importable API). Recommend re-deciding narrowly for append-only attribution rows (idea 2); the `.usage.json`/`.curator_state` ban stands.
- **U5 status line stale** — hard-cap work is largely present in the working tree (`auto_evolve.py:50/:52/:486/:519`); roadmap wording ("chars cap still `_BUILTIN_HARD_CAP_CHARS`") should be updated when the batch lands.
- **U9** — spec unchanged; add a watch note for upstream frontmatter divergence (`triggers`, #100056): conformance should tolerate unknown frontmatter fields rather than fail.
- **U24 (optional enhancement)** — ledger timestamps give cohort windows an independent ground truth beyond the plugin's own tables.
- **Upstream drift otherwise nil** — v2026.8.31 still latest; #67582/#77264/#66180 unchanged; #101035 open with no comments.

## Verification pointers (all read-only, reproducible)

- Ledger: `python3 -c "from tools.skill_ledger import list_entries; ..."` (import verified this run); `head ~/.hermes/skills/.curator_ledger.jsonl`; gate default in `tools/skill_ledger.py:98-101`.
- Plugin blindness: `grep -rn "curator_ledger\|skill_ledger" hermes_curator_evolver/` → 0; `hermes_curator_evolver/guarded_apply.py:315` (`target.write_text`).
- Upstream: `gh api repos/NousResearch/hermes-agent/{releases,issues/100449,issues/100449/events,pulls/100471}`; issue search `repo:NousResearch/hermes-agent is:issue created:>=2026-09-01 skill` (29 hits; the relevant ones quoted above).
- Competitors: `gh api repos/{ECNU-ICALK/AutoSkill,ViktorAxelsen/MemSkill,dwickyfp/skillforge,aiming-lab/SkillRL}/{,readme}` (star/push dates and feature text quoted above).
- Standards/deps: `curl agentskills.io/specification`; `pyproject.toml` dependencies block.
