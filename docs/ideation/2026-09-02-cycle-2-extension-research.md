---
date: 2026-09-02
topic: hermes-curator-evolver-cycle-2-extension-research
mode: repo-grounded
run: 589e5a44a79d4dbda45b3af824d14669
phase: research
action: research:research
attempt: 070899e1e4c34ca385cdc12881d345e9
skill: ce-ideate (compound-engineering, installed at /home/agent/.hermes/skills/software-development/compound-engineering/ce-ideate; no dedicated ce-research skill exists — ideate is the narrowest match for "evidence-backed feature and improvement candidates"). Context fence run; OUTPUT_FORMAT=md. Deviation: no subagent primitive in this harness — grounding and ideation ran in one context; no independence claimed. Web probes via agent-reach (Exa) + gh CLI.
---

# Cycle-2 extension research — hermes-curator-evolver

Prior phase input: cycle-2 adversarial assessment (20 findings, 4 P1, artifacts in
`docs/assessment/2026-09-02-adversarial-repository-assessment.md`).
Standing constraints from cycle-1 research (roadmap `.hermes/plans/autonomy-prop_8c5390ffe26640fa.md`,
"Rejected directions"): pre-create similarity gate, replay-benchmark scoring, cross-agent
export/marketplace, git-PR review mode, MCP server for the queue, audit-skills rename,
and assessment-P3-fixes-as-features are **rejected**. Survivors U8–U14 are planned; this
pass looks for candidates **beyond** them and for evidence that **updates** their premises.

## Evidence gathered this phase (all read-only)

### E1. Upstream drift check (NousResearch/hermes-agent, via gh, 2026-09-02 ~07:05 UTC)
- Newest release is still **v2026.8.31** — no release since cycle-1's fetch. Repo active
  (new issues filed within the hour).
- Cycle-1 grounding issues **all still open, unchanged comment counts**:
  #67582 (near-duplicate skill explosion, 6c) · #77264 (archived skills invisible to
  consolidation, 1c) · #66180 (auto-created skills never loaded at task time, 1c).
  → U8/U9/U10 grounding intact; none superseded upstream.
- New upstream issue **#101035** `[P1] SQLite busy_timeout=0 causes SQLITE_BUSY crash loop`
  — the same concurrency class as cycle-2 assess H4; corroborates that busy_timeout/WAL
  hardening is an ecosystem-level need, not a local quirk.

### E2. Upstream source facts (local checkout /home/agent/.hermes/hermes-agent, v0.20.6)
Read directly — stronger than cycle-1's doc-level reading:
- **`hermes_cli/skills_hub.py:1562` `do_publish`**: `hermes skills publish` uploads
  **every file under the skill dir** (`skill_path.rglob("*")`, ~:1606–1611) after a
  self-scan via `tools.skills_guard.scan_skill`; only a `dangerous` verdict blocks it
  (~:1601–1604).
- **`tools/skills_guard.py`** (1,360 lines) is a local, model-free scanner:
  exfiltration / injection / destructive / persistence / network / obfuscation patterns,
  **including credential literals** (`credential_exposure` findings, e.g. GitHub PATs,
  AWS keys).
- **`agent/curator.py`** (2,041 lines): consolidation is an **opt-in, LLM
  umbrella-building pass, OFF by default** (`get_consolidate`, :204–220); the
  deterministic default is only stale/archive transitions (`apply_automatic_transitions`,
  :305). No evidence store, no secret scan, no outcome measurement. → U8's
  deterministic-dedupe differentiator is confirmed at source level, not just docs.
- **`hermes_cli/cron.py`** (843 lines, present at v0.20.6): native cron with
  `monitor_script`/`monitor_url` ("agent runs only on output change", :544–546, :560–561)
  and `continuity`. → **U13's premise is stale**: it gates on "requires hermes-agent
  >= v0.21.0; host currently 0.20.6 must no-op". The capability exists on this host today.
- Plugin host surface (`plugin.yaml` + `agent/plugin_llm.py`): plugins declare
  `provides_tools` / `provides_hooks`; no plugin-registered slash commands found —
  chat reachability for new functionality is via `provides_tools` (the plugin already
  ships `curator_evidence_report` that way).

### E3. Live-secret experiment (end-to-end, scratch Hermes home)
Recorded a `skill_manage` result containing `TOKEN=ghp_16C7e42F292c6912E7710c838347Ae178B4a`
×4, ran `auto-run --apply-low-risk --approve-auto-apply`:
- Managed block written with the token **verbatim** ×4 (`SECRET … in SKILL.md: True`);
  `_format_evidence_rows` (auto_evolve.py:323–333) clips previews to 220 chars but scrubs
  nothing. `grep -rn "redact|secret|token|password"` over storage.py + auto_evolve.py: **0 hits**.
- Running upstream's own scanner on the result: **verdict `dangerous`, 4× critical
  `credential_exposure` "GitHub personal access token in skill content"**. An AWS key in
  plain prose also returns `dangerous`.
- Consequence chain: the plugin's verify gate (`skill_validate`) does not detect secrets,
  so the block is applied; `hermes skills publish` then **fails forever** for that skill
  (dangerous verdict), and `hermes skills audit` flags it — the *plugin* becomes the
  author of `dangerous` skills. Conversely the spill file
  (`references/curator-evolver-auto-*.md`, full evidence rows) is uploaded too, since
  publish rglobs the whole skill dir.

### E4. Evidence-store growth (production data, read-only URI, counts only)
`data/evidence.sqlite` on this host: **6,675 tool events + 89 turn events in ~3 days**
(oldest 2026-08-30, newest 2026-09-02T07:03), **7.2 MB**. `grep -rn "DELETE FROM|VACUUM|prune|retention|expire"`
across the package: **0 hits**; README:390 confirms removal "does not delete historical
evidence". Rate ≈ 2,200 events/day → ~800k events/year at this usage, with no retention
path at all. Secret-shaped content already present: **1 of 6,675 rows** matches an
`sk-…` key pattern in `result_preview`/`args_json` (counted, not printed) — i.e. the
E3 exposure path is live, not hypothetical.

### E5. Competitor scan (agent-reach/Exa + gh, beyond cycle-1's SkillClaw)
- **SkillSmith** (github.com/yangforever17/SkillSmith, arXiv 2606.01314, 2026):
  "Skills and tools that co-evolve from their own failures… **validates every change
  before keeping it**… every candidate scored on your data, **kept only if it actually
  improves**. Past failures are remembered as **anti-patterns** so the same mistake
  isn't proposed twice."
- **Auto-Evolution** (github.com/ZhanlinCui/Auto-Evolution-Agent-Skills, v2.0.0,
  Claude Code-compatible): memory-driven pattern detection; dashboard "shows what's
  effective".
- Also surfaced (not yet read in depth): ECNU-ICALK/AutoSkill, ViktorAxelsen/MemSkill,
  dwickyfp/skillforge, aiming-lab/SkillRL (RL-based; different cost class).
- **agentskills.io spec re-fetched 2026-09-02**: unchanged (name ≤64
  lowercase-hyphen, description ≤1024, license, compatibility ≤500, `metadata`
  string-map, `allowed-tools` experimental). U9 needs no spec re-baselining.

## Candidate pool → critique

Generated 16 candidates, critiqued all:

| # | Candidate | Verdict |
| --- | --- | --- |
| C1 | Secret-scrub + publish-safety gate at the evidence→skill boundary | **survivor 1** |
| C2 | Evidence retention + compaction command | **survivor 4** |
| C3 | Outcome-linked apply telemetry (keep-only-if-it-helps) | **survivor 3** |
| C4 | Anti-pattern ledger for failed/rejected blocks | **survivor 2** |
| C5 | Inbound skills_guard scan of skills the plugin reads | reject: plugin never executes skill content; upstream already scans at hub install/publish |
| C6 | Multi-profile/Bot-Mode evidence aggregation (cycle-1 revisit) | reject again: profile→home contract now *partially* verifiable (`skill_commands.py` rescan-on-home-change, #88023) but user demand still unevidenced and it multiplies the E3/E4 secret surface |
| C7 | Static HTML dashboard | reject: already U14 |
| C8 | `candidates-decide` CLI (+ optional provided tool) to close the review loop | **survivor 5** (small) |
| C9 | Native-cron scheduler | not a new candidate: **evidence correction to U13** (see below) |
| C10 | agentskills.io conformance | not new: U9 unchanged; spec stable (E5) |
| C11 | Embedding-accelerated dedupe | reject: already U8's optional mode |
| C12 | `doctor` conflict check | reject: already U12 |
| C13 | Evidence DB encryption at rest | reject: local-first threat model; no demand evidence; retention+scrub (C1/C2) address the actual exposure |
| C14 | Diff preview/pinning before apply | reject: dry-run default + backup manifests already cover it; hub `diff`/`list-modified` exist upstream |
| C15 | Write into native curator state (`.usage.json`/`.curator_state`) | reject: format ownership undocumented upstream; read-only integration (U12) is the right direction |
| C16 | `/curator` chat slash command | reject as standalone: host exposes no plugin slash registration (E2); feasible only as a `provides_tools` rider on C8 |

## Survivors (ranked)

### 1. Publish-safety: scrub secrets at the evidence→skill boundary + guard-scan the apply gate
**Evidence:** E3 end-to-end (token verbatim into SKILL.md; upstream scan verdict
`dangerous` 4×critical), E4 (1/6,675 live rows already carries a secret-shaped value),
E2 (`do_publish` rglobs the whole skill dir including `references/` spill files; only
`dangerous` blocks).
**Shape:** (a) neutralize secret-shaped content in previews before persistence
(storage ingest + backfill import), reusing upstream's own detection patterns;
(b) make the plugin's apply gate refuse any update whose resulting skill content
scans `dangerous` — import `tools.skills_guard.scan_skill` when available
(degradation: local regex fallback), exposed as a builtin check alongside
`_run_builtin_cheap_check`; (c) `report --publish-risks` lists skills whose current
content would fail the publish gate, naming the plugin-authored evidence lines.
**Why it wins:** turns a demonstrated poison-the-library path into a gate; makes the
plugin the *first* tool in the chain to know a skill is unpublishable; zero new
dependency (scanner is already on every Hermes host); directly protects U14's
visibility story and every user who ever publishes.

### 2. Anti-pattern ledger — stop re-proposing failed blocks
**Evidence:** SkillSmith's anti-pattern mechanism (E5) is the published competitor
answer; the need is demonstrated locally: cycle-2 assess M6 shows a bad evidence row
regenerating the *identical* failing block on every daily run (permanent
verify-fail→rollback→repeat loop), and H1/M12 show one bad block aborting whole runs.
**Shape:** persist a digest (skill + block hash + failure reason) per verify-failed or
rolled-back apply; auto-run checks candidate blocks against the ledger and records
`suppressed-repeat:<n>` instead of re-applying; ledger rows expire when the underlying
evidence rows age out; surfaced in `report` and reviewable via a `--clear-anti-pattern`
escape hatch.
**Why:** competitor-validated mechanism, model-free, and it converts a confirmed
defect class (repeat loops) into a bounded, observable behavior — a prerequisite for
trusting any of U8–U14 to run unattended.

### 3. Outcome-linked apply telemetry — keep only what helps
**Evidence:** SkillSmith "kept only if it actually improves" and Auto-Evolution's
"shows what's effective" (E5) both treat outcome measurement as core; native curator
has no outcome loop (E2: deterministic transitions only); the plugin already stores
everything needed — `tool_events.is_error` + timestamps + per-apply manifests with
`generated_at` (storage.py schema, guarded_apply manifests).
**Shape:** after each apply, compute a pre/post cohort for that skill (error-marked
tool events involving it, before vs after the apply timestamp, same-length windows);
record `outcome_delta` on the apply manifest; `report --outcomes` ranks applies;
a negative delta files a **rollback suggestion** into the review queue — never
auto-rolls-back. Honest limits stated up front: cohort sizes are small and causal
claims are weak; it is a decision aid, not a benchmark (the replay-benchmark rejection
stands).
**Why:** differentiates the plugin on the axis competitors validate, with data only
this plugin has (local tool-call evidence), while respecting the model-free default
and the standing rejection of benchmark scoring.

### 4. Evidence retention + compaction
**Evidence:** E4 quantified: 6,675 events / 7.2 MB in ~3 days, zero retention code,
README:390 documents evidence outliving the plugin; upstream precedent for curator
pruning exists (`prune_builtins`, archive lifecycle, E2).
**Shape:** `evidence-prune --before <iso> --keep-aggregates` deleting raw rows past a
retention window (default e.g. 90d, configurable, `0` = keep-forever — implemented so
that the documented value actually works, cf. assess H2) while preserving per-skill
aggregate counters so reports/summaries stay meaningful; `VACUUM` after; `status`
reports DB size and oldest row.
**Why:** cheap, unblocks long-lived hosts, reduces the E3/E4 secret-bearing surface,
and pairs naturally with C1.

### 5. `candidates-decide` — close the review loop (small)
**Evidence:** cycle-2 assess T20 (`review_queue.update_status` exists,
review_queue.py:173, with no caller); every U8/U10/U11 survivor lands rows in a queue
that currently cannot be decided from the product; host feasibility via `provides_tools`
(E2), chat-side rider optional.
**Shape:** `candidates-decide --id N --accept|--reject [--note …]` wrapping
`update_status`, plus `--format json`; optional provided tool for chat-side review.
**Why:** the smallest item that makes the entire planned extension family (U8, U10,
U11, and survivors 1–3 above) reachable by a human.

## Evidence corrections to standing roadmap items (not new work packets)

- **U13 (native-cron backend): premise corrected.** Native cron with monitor-mode
  ("runs only on output change") and continuity is present in the **v0.20.6 host
  today** (`hermes_cli/cron.py:544–546`), not only ≥v0.21.0. The version gate and the
  "no-op below 0.21.0" branch can be dropped; monitor-mode semantics map directly onto
  "skip when nothing changed". U13 becomes implementable now and gains a Windows path.
- **U9: no spec re-baselining needed** (agentskills.io unchanged, E5).
- **U8: grounding intact and strengthened** — #67582/#77264 still open (E1); native
  consolidation confirmed opt-in LLM-only at source (E2), so the deterministic
  near-duplicate detector remains unowned upstream.
- **Corroboration for assess H4:** upstream #101035 reports the same
  busy_timeout/SQLITE_BUSY class — WAL/busy_timeout hardening is ecosystem-confirmed,
  not local nitpicking.

## Suggested ordering (for the next prioritize phase)

Survivor 1 (publish-safety) → 2 (anti-pattern ledger) → 4 (retention) → 3 (outcome
telemetry) → 5 (candidates-decide). 1 and 2 harden the unattended write path that
U8–U14 all extend; 3 depends on 2's ledger for honest suppression accounting; 5 can
land any time after the hardening batch. All respect the standing rejections
(no marketplace/export, no MCP surface, no replay benchmarks, model-free defaults).

## Reproduction / verification pointers

- E3: scratch-home script (EvidenceStore + `auto-run --apply-low-risk`) then
  `tools.skills_guard.scan_skill(skill_dir, source="self")` → verdict `dangerous`.
- E4: `sqlite3 "file:data/evidence.sqlite?mode=ro" 'SELECT COUNT(*), MIN(created_at),
  MAX(created_at) FROM tool_events;'`; grep for `DELETE FROM|VACUUM` in
  `hermes_curator_evolver/` → none.
- E1/E5: `gh api repos/NousResearch/hermes-agent/{releases,issues/67582,issues/77264,issues/66180}`;
  `mcporter call exa.web_search_exa`; agentskills.io/specification.
