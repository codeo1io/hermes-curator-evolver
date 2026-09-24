# Cycle 10 extension research — evidence-backed candidate slate

Date: 2026-09-23 · Run cf968161814b40d7ad4d5760446a4cd6 (research attempt 7da8766493924a79bc90611a6cee1c69) ·
Base under review at research time: a76962c (pre-rebase); all live probes dated 2026-09-23 via
`gh api` + `curl` (agent-reach dev/github routing; no ce-* skill exists on this host — disclosed).

Roadmap cross-reference: units U85–U89 and decisions KTD42–KTD44 live in
`.hermes/plans/autonomy-prop_8c5390ffe26640fa.md` (cycle-10 section). This document is the
evidence record for that slate.

## Candidate slate (ranked)

### R1 — Dependency-aware skill impact analysis, dry-run only (HIGH value, externally demanded)
Source: upstream issue pingchesu/hermes-curator-evolver#12 "Add dependency-aware skill impact
analysis" — OPEN since 2026-05-09, body is a full community-sourced spec (launch-post feedback):
detect `related_skills` frontmatter, co-usage from session evidence, shared tools; `impact
--skill <name> --days 30 --format markdown` CLI; confidence-typed dependency edges
(`explicit_related_skill`, `workflow_reference`, `co_usage`, `shared_tool`); recommended action
per edge (review/no-op/proposal-only); ALL downstream changes proposal-only.
Fit: our evidence store already holds per-session tool_events + skill attribution (co-usage
computable), skill_sources.py holds the source graph, proposals.py the proposal-only channel.
Safety posture unchanged. Suggested unit: new module + CLI subcommand; no cascading writes.
**Disposition: roadmap U87, DEFERRED to cycle-11 as anchor unit (KTD44).**

### R2 — Classifier free-text failure-vocabulary widening (MEDIUM, was net-new post-rebase)
Source: pass-7 assess probe — "ERROR: connection refused", "command exited 1 after retries",
"3 tests failing", "build finished: 3 errors", "request timed out", "permission denied" all
classified as SUCCESS while pinned controls passed; verified gap PERSISTED on live origin/main
27487cd (`grep -c "timed out\|permission denied" = 0` in candidates.py). Exit-status forms
("exited with exit status 1") were covered; the miss was prose vocabulary.
**Disposition: roadmap U86, IMPLEMENTED in cycle-10 batch** — keyword arms (`errors?:` log
prefix outside the `\b(...)\b` group, `exited? N` short form, `timed[-\s_]*out`,
`permission denied`, `failing`), widened count verbs with interposed-noun binding
(`3 tests failing`, `4 validation errors`), count-pattern entry gate (`2 errors`),
symmetric success phrases (`no tests failing`, `no parse errors`), structured
`timed_out`/`permission_denied` statuses. Pinned by tests/test_candidates.py U86 section +
scripts/repro-pass7.py F86 records (corpus 48 → 54).

### R3 — U62/KTD28 index-liveness streak: record, do not ungate (process)
Observations (HERMES_INDEX_URL → https://hermes-agent.nousresearch.com/docs/api/skills-index.json):
2026-09-21: 98,326 @ 07:47:22Z (cycle-9 roadmap record) · 2026-09-22: 100,496 (07:53Z) · 2026-09-23: 100,592 (07:54:20Z) — third
consecutive daily-fresh observation; gate-1 streak 3/30 of the proposed 30-day amendment. (Corrected in the
cycle-10 review fix: this doc first recorded the 98,326 datum as 09-20 and the streak as "4th consecutive",
contradicting the landed cycle-9 roadmap ledger — `.hermes/plans/autonomy-prop_8c5390ffe26640fa.md:1406`,
"2026-09-21 was 98,326 @ 07:47:22Z" — and the cycle-10 extension's 3/30 count. The roadmap ledger is
authoritative per KTD38.)
Gate 2 unchanged: hermes-agent PR #101237 (index community skill repos) OPEN/unmerged, last
updated 2026-09-02. **Disposition: ledger extended to 3/30 in the cycle-10 roadmap section;
re-observe ~2026-10-05; ungate only via KTD28 amendment.**

### R4 — Competitor-table refresh (this document)
· hermes-dojo (Yonkoo11, ★174): DORMANT since 2026-06-06 (last commit: MIT license + credits).
· AMAP-ML/SkillClaw ★2,639 "Let Skills Evolve Collectively with Agentic Evolver" (pushed
  2026-08-17) — large, benchmark-driven collective evolution.
· sentient-agi/EvoSkill ★1,219 (2026-08-24); EvoScientist/EvoSkills ★438 (2026-09-01) —
  benchmark packs, not usage-driven.
· Small entrants inside our design center (continuous usage-evidence evolution), all <★20:
  selftune-dev/selftune ★17 (TypeScript skill observability, 2026-09-07); ievo-ai/skills
  (iEvo: capture lessons, patch agents, 2026-09-16); ranjithrajv/wikiskill ★2 (paper companion,
  2026-09-03); Evidune ★3 (outcome-driven, 2026-07-17); okdk7788/skill-evolution ★2
  (GEPA-style, 2026-07-06).
Positioning: the "unoccupied territory" reading is softening — no large occupant in the exact
niche, but 5+ active sub-20★ entrants since June 2026 and one large benchmark-driven collective
(SkillClaw). Moat = Hermes-native host telemetry (`on_skill_lifecycle` hook + skill-usage
telemetry, MRU-first SessionDB) that generic entrants cannot consume.
**Disposition: this document is the refreshed table (roadmap U88).**

### R5 — One-shot-run exclusion/down-weighting in session mining (MEDIUM, needs design probe)
Source: nousresearch/hermes-agent PR #116004 merged 2026-09-19 — one-shot runs stop authoring
skills, loading process skills, spawning reviewer subagents. Implication: one-shot sessions
carry degraded skill-evolution signal from v2026.9.19+ hosts. Next step: confirm whether
state.db session rows expose run mode; if yes, add an ingest filter/down-weight.
**Disposition: research-gated follow-up recorded in the roadmap (next research phase).**

### R6 — Hub-index freshness guard (SMALL)
Index regenerates daily (+2,266 skills in 3 days) and curator binds it (host default URL at
tools/skills_hub_search.py:27, fork b4528e6c98). Guard: compare `generated_at` on fetch; >48h ⇒
warn + serve stale cache explicitly. Cheap robustness for hub-facing surfaces.
**Disposition: roadmap U89, first alternate — pull-in only if batch green + full 3.11/3.12
matrix + ≤40 lines; not pulled in cycle 10.**

## Non-findings / stability notes
· Upstream pingchesu/hermes-curator-evolver: no commits since 2026-08-31 (23 days), no
  releases — no port queue; fork divergence is ours to maintain. Only open issue: #12 (R1).
· Agent Skills spec repo agentskills/agentskills ★25,624: quiet since 2026-08-09 — no spec
  churn; version-under-metadata conformance position stable.
· Host hermes-agent fork checkout unchanged at b4528e6c98 (v2026.9.21 line); upstream releases
  v2026.9.21 / v2026.9.14 / v2026.9.11.
· Skill-install/resolution PRs merged upstream 09-17→09-20 (#116951, #116861, #113167,
  #114991, #117614) are host-side fixes with no curator surface.

## Verify commands
```bash
curl -sL https://hermes-agent.nousresearch.com/docs/api/skills-index.json   # generated_at, skill_count
gh api repos/pingchesu/hermes-curator-evolver/issues/12
gh api repos/nousresearch/hermes-agent/pulls/101237 --jq '{.state,.merged}'
gh api "search/repositories?q=agent+skill+evolution+self-improving&sort=updated"
git -C <repo> show origin/main:hermes_curator_evolver/candidates.py   # U86 arms present
```
