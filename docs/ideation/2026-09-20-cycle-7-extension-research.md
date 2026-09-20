# Cycle-7 extension research — upstream, standards, competitors, dependencies

Date: 2026-09-20 · Research phase of run `78a174fb` (repository-maintenance cycle 7) · Builds on
cycle-6 ideation (2026-09-02) — does not redo it. All upstream facts verified against the live
host checkout at `/home/agent/.hermes/hermes-agent` (git `b7483d5a36`, version 0.21.3, fleet sync
2026-09-20); ecosystem facts gathered via Exa/GitHub (agent-reach) with URLs inline.

## Method & scope

1. Upstream: dated every candidate surface with `git log --reverse -S<symbol>`; swept
   `git log --since=2026-09-02` (cycle-6's cutoff) across the plugin's touchpoints
   (hermes_state, tools/skill_usage.py, agent/curator.py, hermes_cli/plugins.py, hooks.py).
2. Standards: read the Agent Skills open spec (`agentskills/agentskills`, 25.5k★, spec at
   `docs/specification.mdx`).
3. Competitors: EvoSkill (1,211★), MUSE-Autoskill (arXiv 2605.27366), WikiSkill
   (arXiv 2608.27454), skill-swarm-mcp, hermes-agent-self-evolution (5,375★), live skill
   aggregators; benchmarks SkillsBench / SkillLearnBench.
4. Dependencies: live PyPI index for sentence-transformers, PyYAML, ruff, pytest; live venv
   versions on the host.

> Labeling note (added in the roadmap phase): the upstream findings below were first labeled
> U55-U59, which collides with the roadmap's packet-ID namespace (U51-U62 already in use in
> `.hermes/plans/autonomy-prop_8c5390ffe26640fa.md`). They are relabeled **RF-55…RF-59** here;
> roadmap packet IDs remain the only U-namespace (KTD33).

## 1. Upstream (hermes-agent 0.21.3) — new since cycle-6's 2026-09-02 cutoff

### RF-55. `on_skill_lifecycle` hook — authoritative attribution, never mined by any prior cycle

`VALID_HOOKS` (hermes_cli/plugins.py:108-130) includes `on_skill_lifecycle` — "successful skill
lifecycle facts (local skill name visible to plugins)". It fires from `tools/skill_usage.py:434-449`
with `action, skill_name, provenance, task_id, session_id, use_count, reused, reuse_after_patch`.
First appeared f1fd678e44 (2026-07-29). `grep on_skill_lifecycle docs/ideation/` → **0 hits**
(cycles 1-6 never considered it); plugin.yaml provides only post_tool_call / post_llm_call /
on_session_end. This is host-emitted ground truth for the exact problem the plugin heuristically
solves with `_extract_skill_name` on skill_view args (the S6/N2 attribution class).

### RF-56. Host skill-usage sidecar — durable `use_count` predating the plugin

`tools/skill_usage.py` is explicitly "Skill usage telemetry + provenance for the Curator":
`~/.hermes/skills/.usage.json`, keyed by skill name, locked read-modify-write (`.json.lock`),
per-skill `use_count / reused / reuse_after_patch / created_by`, provenance classification
(installed / agent_created / external / local / hub), `is_curation_eligible()` gating (June,
70e1571d89 + 8e223b36ed). Cycle-4 R5 mentioned it once as a usage clock; it was never adopted.
Impact: the N2 starvation (DISTINCT over second-precision timestamps collapsing hook bursts) is
solved structurally by reading a durable monotonic counter instead of counting event rows.

### RF-57. `search_sessions` is MRU-first SQL-side — backfill early termination is provably safe

`hermes_state.SessionDB.search_sessions` executes `ORDER BY last_active DESC, s.started_at DESC,
s.id DESC LIMIT ? OFFSET ?` (read from the installed module). The plugin's full-pagination +
client-sort design (backfill.py:171-189 docstring: "host pagination order must not be trusted as
recency order… a hostile or oldest-first host storage would truncate imports") predates knowing
this. A monotonicity probe on the first page (fall back to full scan when it fails) preserves the
hostile-store property while making the real host O(limit) instead of O(store). Note:
`after/before` bounds landed 2026-09-19 (e450795829) **only for `search_messages`**, not
`search_sessions` — so SQL-side cutoff pushdown is not available; MRU early-stop is.

### RF-58. Canonical sqlite layer + WAL hardening — the plugin's storage alignment gap

Since cycle-6: 576accd92b (2026-09-12) consolidated 12 hand-rolled sqlite stacks into
`hermes_cli/sqlite_util.py:open_db` ("plugin DBs use the WAL fallback"), fixing the #69567 fd-leak
class (`with conn:` commits but never closes). Companion hardening: 939a2f64b4 (duplicate writer
handles), 274fd56dca / 75e155ab09 (WAL lock guards), d8dcdfd620 (**refuse WAL on cross-VM
filesystems — virtiofs/9p — before corruption**), 9b6dcad91d (mkstemp-published files stay 0600),
3ef8b384a9 (one atomic-write utility for 24 writers). The plugin's EvidenceStore has a WAL→DELETE
fallback (storage.py:257-294) but forces WAL unconditionally otherwise, caches connections
in-process (the N8 warm-cache masking), and hand-rolls atomic writes — each of which the host has
now defined canonical semantics for. Local filesystems here are ext2/3 (checked via `stat -f`),
so the cross-VM case is latent portability, not a live bug.

### RF-59. Skill-system churn touching the plugin's sources model

Since cycle-6: 2e786d901b (skill loads named in live activity), 945eca9aaa (skill success/guard
result consumers), b67441309c (contracts: model/tools/skills stay optional), c8e155dcbf
(`${HERMES_SKILL_DIR}` templating in skill text, agent/skill_preprocessing.py). Staged SKILL.md
content could adopt the token instead of hardcoded paths; skill_sources should classify
`HERMES_SKILL_DIR`-resolved dirs (P12's custom-dir/SOURCE_UNKNOWN class).

## 2. Open-standard conformance (Agent Skills spec)

The spec (agentskills.io, originally Anthropic, 25.5k★, pushed 2026-08-09) requires frontmatter
`name` + `description`; optional fields are `license`, `compatibility` (≤500 chars),
`metadata` (arbitrary string→string map), `allowed-tools`. **There is no top-level `version`
field** — the spec's own versioning example is `metadata: { version: "1.0" }`
(specification.mdx:34-36, 55-58, 162-164). The plugin's bundled skill uses top-level
`version: 0.11.0` (`hermes_curator_evolver/skills/curator-evolution/SKILL.md:4` — full tree path; the pre-review draft's short form failed the commit-gate citation check) — readable by the plugin but invisible to
spec-conformant consumers; this also feeds the S9 version-drift finding (0.11.0 vs 0.10.0
fallbacks elsewhere). Candidate: dual-read (top-level + metadata.version) on ingest, write both on
staging, plus an `audit-skills --spec-check` conformance mode validating curated skills against
the open spec (bundled references layout, name/description presence, compatibility ≤500).

## 3. Competing approaches & positioning

- **EvoSkill** (sentient-agi, 1,211★, Apache-2.0, active 2026-09-19; arXiv 2603.02766): GEPA-style
  joint skill+prompt mutations evaluated on **held-out benchmarks**; supports Claude Code, Codex,
  OpenCode, OpenHands, Goose, Harbor. Its feature table lists two capabilities as open research
  directions (🛠️): **"Evolution without a benchmark"** — citing
  `NousResearch/hermes-agent-self-evolution` — and **"Continuous evolution: improving skills from
  regular usage"**. Those two are exactly this plugin's design center (evidence from real sessions,
  no benchmark harness). Roadmap implication: the curator's differentiation is the thing the
  leading competitor hasn't shipped; making it measurable (outcome deltas) is the defensible moat.
- **hermes-agent-self-evolution** (NousResearch, 5,375★, updated 2026-09-20): DSPy + GEPA
  optimization of skills/prompts/code for the same host. Sibling, not rival: natural integration —
  curator supplies usage evidence + safety gating, self-evolution supplies optimizer. A roadmap
  integration note ("evidence export for optimizers") is cheap to write now.
- **MUSE-Autoskill** (arXiv 2605.27366, under review): unified lifecycle creation/memory/
  management/**evaluation**; reports outperforming **Hermes**, Codex, and Claude Code on
  SkillsBench/SkillLearnBench, and self-created skills beating human-authored ones on covered
  tasks (85.24% vs 81.17%). Defensive pressure is explicit — Hermes is a named baseline. The
  transferable leg is *evaluation*: per-skill testability is what the plugin's verifier lacks.
- **WikiSkill** (arXiv 2608.27454): separates raw experience / accumulated knowledge (wiki) /
  executable skills; ablation shows persistent knowledge accumulation is critical, and evolved
  skills transfer across models (other-model-evolved skills can beat self-evolved). Maps onto the
  plugin's evidence store / managed-bullet knowledge / SKILL.md triad; supports cycle-6 candidate
  5 (knowledge demotion to references/) and multi-model attribution.
- **skill-swarm-mcp** (ancrz, 2026-02): MCP server for skill discovery/install — BM25F + 7 signals,
  5-dimension trust engine, usage tracker with "dead skill detection", 5 registries. Shows the
  pattern of serving skill metadata to arbitrary agents over MCP; the host ships an MCP server
  surface (hermes_cli/web_server_mcp.py), so the curator could expose read-only `skill_health` /
  `proposal_review` tools.
- **Skill aggregators are live at scale** (demand gate for cycle-6 candidate 6): anbeime/skill
  (10k+ GitHub skills auto-aggregated, updated daily), K-Dense scientific-agent-skills (165 skills,
  190k users), ClawHub (50k+, via host hub). The cycle-6 duplicate-check candidate was gated "on
  index deployment"; multiple indices now exist.

## 4. Benchmarks (verifier's missing empirical leg)

Public and current: **benchflow-ai/SkillsBench** (+ HF dataset `benchflow/skillsbench`) and
**SkillLearnBench** (cxcscmu, COLM'26). Enables an optional `verify --replay` mode: run a
candidate's skill instructions against held-out tasks to produce the measured outcome-delta
cycle-6 candidate 4 currently can only approximate from error cohorts. Costly; demand-gate it.

## 5. Dependencies (live PyPI, 2026-09-20)

- sentence-transformers 6.1.0 latest; plugin pins `>=3` (pyproject.toml:40) — compatible, but
  semantic.py (CrossEncoder rerank path) is untested against the 6.x line; a CI leg or tox env
  pinning `sentence-transformers~=6.1` would close the drift.
- ruff 0.16.8 vs installed 0.16.3; pytest 9.1.1 current (suite passes under it); PyYAML: live
  venv has **6.0.3** (the 5.4.1 seen earlier came from an ambient python, not the host venv —
  no conflict; plugin's `>=6` floor is satisfied everywhere it runs).

## Ranked candidates (evidence-backed)

1. **Authoritative attribution: subscribe `on_skill_lifecycle` + read `.usage.json`** (RF-55/RF-56).
   Fixes the S6/N2 class structurally — durable counters and host-emitted names instead of
   DISTINCT-over-seconds and arg-sniffing. Fallback path keeps pre-0.21 hosts working.
2. **Backfill early termination on host MRU ordering** (RF-57) — resolves N6 with a
   monotonicity-probe + fallback design; upstream SQL is read-verified.
3. **Storage alignment with host canonical sqlite semantics** (RF-58) — lazy-import
   `hermes_cli.sqlite_util.open_db` where available, vendor fallback otherwise; adopt cross-VM WAL
   refusal and fd-hygiene; addresses N8's masking class and the whole corruption surface.
4. **Spec-conformant frontmatter + `audit-skills --spec-check`** (§2) — dual-read version fields,
   validate name/description/compatibility rules; directly reduces S9 drift.
5. **Outcome measurement positioning** (EvoSkill/MUSE, §3-4) — roadmap: own the
   continuous/benchmark-free evolution niche; optional SkillsBench replay harness behind a
   demand gate; evidence-export seam for hermes-agent-self-evolution.
6. **MCP exposure of curator health/review** (skill-swarm pattern; host has the surface).
7. **Ecosystem duplicate check — demand gate met** (cycle-6 candidate 6): indices live.
8. **Deps drift closure**: ST 6.x CI leg, ruff 0.16.8 bump.

## Standing rejections — status check

Cycle-2's "write into native curator state" rejection stands for `.usage.json` (host-owned
sidecar); read-only consumption (candidate 1) is the same boundary cycle-3 drew for the ledger.
No re-decision needed.

## Verification pointers

- `grep -rn "on_skill_lifecycle" <host>/hermes_cli/plugins.py tools/skill_usage.py` → hook + emitters.
- `python -c "import hermes_state, inspect; src=inspect.getsource(hermes_state.SessionDB.search_sessions)"` → MRU ORDER BY.
- `cd <host> && git log --since=2026-09-02 --oneline -- hermes_state* tools/skill_usage.py` → RF-57/RF-58 commits.
- Spec: https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx (frontmatter table).
- EvoSkill README feature table: https://github.com/sentient-agi/EvoSkill (open-direction rows).
- Benchmarks: https://github.com/benchflow-ai/SkillsBench · https://github.com/cxcscmu/SkillLearnBench.
