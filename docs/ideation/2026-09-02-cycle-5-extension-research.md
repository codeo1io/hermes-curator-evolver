# Cycle-5 Extension Research — evidence-backed candidates beyond the standing roadmap

- **Run:** `2cc5b112c9694bfaa4a47645f139983a` · phase `research` · attempt `7295512752b44da18c6bd828e61a8622`
- **Intent:** `research_repository_extensions`
- **Date:** 2026-09-02 (~11:25Z) · **Repo:** `main` @ `45328db` + uncommitted cycle-1 remediation + cycle-4 batch (13 files)
- **Skill:** routed via compound-engineering router → `ce-ideate` (no `ce-research` in the installed roster; matches cycle-2/3/4 routing). Scratch: `/tmp/compound-engineering-1000/ce-ideate/20260902-112230-c5e8a1f4/`
- **Prior passes:** `docs/ideation/2026-09-02-cycle-{2,3,4}-extension-research.md`. This pass does **not** re-propose their survivors; it adds a new evidence layer (upstream drift since ~09:20Z, host prompt-index mechanics, the Skills Hub surface, the Agent Skills open spec, listing-budget discourse) and 5 fresh candidates.

**Method disclosure:** grounding, evidence scouting, six-frame generation, and basis verification all ran in this single pi context (no dispatchable subagents available) — no independence is claimed for any survivor. Raw pool ~15 candidates vs the default fleet target ~36–48. Every `direct:` basis below was verified this run (live source read, live host measurement, `gh api`, or raw fetch of upstream `main`); internet access ran through the agent-reach router (Exa web search + `gh`), per its routing rules.

---

## What's new since cycle-4 (~09:20Z)

1. **Upstream state layer was split** — `hermes_state.py` on `main` is now accompanied by `hermes_state_common.py`, `hermes_state_schema.py`, `hermes_state_search.py`, `hermes_state_registry.py`, `hermes_state_portability.py` (repo root listing via `gh api`). The facade file still exists; whether every name the plugin imports (`SessionDB` et al.) still re-exports from the facade is **not** verified — a doctor-probe item (see corrections).
2. **#101199 (open issue, 11:06Z)**: proposal to exclude cron-source sessions from the trigram FTS index, with deployment measurements — **97.5% of historical sessions were `source='cron'`** (7,465/7,652) and **86% of trigram-covered user+assistant text is cron-source** (~40 MB/week of machine-generated scaffolding). Upstream is converging on exactly the source-filtering premise behind cycle-4's evidence-pipeline candidate.
3. **#101191 (merged 11:07Z)**: cold construction of the shared SessionDB registry is now single-flighted per resolved path and registry keys are canonicalized — root cause: every cold caller opened its own writable connection, and "each loser's teardown then fired a close-time WAL checkpoint against the winner's live writer", the topology logged 7 minutes before corruption incident #4 in #100896.
4. **#101202 (closed, NOT merged, 11:09Z)**: proposed splitting lock errors into contention (`EAGAIN/EWOULDBLOCK/EACCES/EDEADLK` → poll) vs environment (`ESTALE/ENOTSUP/ENOLCK/EIO` → fail fast with the real errno), plus an in-process deferred-recovery retry (60s→1h bounded backoff). Not adopted upstream, but the taxonomy is a sound recipe.
5. **`search_sessions` on `main` now has SQL-level source filtering** — `source_filter` / `exclude_sources` parameters (raw fetch of `hermes_state_search.py:1346-1386`, both the trigram and word-index paths). The implementation shortcut for cycle-4's evidence-pipeline candidate now exists upstream.
6. **The shipped host has a full Skills Hub the plugin has never looked at** — `tools/skills_hub.py` (4,000+ lines): GitHub/optional-skill source adapters, `HubLockFile` provenance at `skills/.hub/lock.json` (per-skill `source, identifier, trust_level, scan_verdict, skill_hash`), a quarantine dir, an audit log, taps, an index cache, and CLI verbs `list/search/install/update/audit` (`hermes_cli/skills_hub.py:1826-1845`); it scans installs through `tools/skills_guard` (`TRUSTED_REPOS`, `content_hash`). Catalog walk notes cite **"ClawHub has 50k+ skills"**. `grep skills_hub|HubLockFile hermes_curator_evolver/` → 0 hits. Live host: `~/.hermes/skills/.hub/` exists, `lock.json` has zero installs, `audit.log` is 0 bytes — the surface is shipped and default, but unused here *today*.
7. **The host's skill→prompt mechanics are now pinned precisely** (installed host, `agent/skill_utils.py`): the system prompt carries an **eager index of every skill's name + description truncated at 60 chars** (`SKILL_PROMPT_DESC_LIMIT = 60`, `:1175`; truncation to 57+"…", `:1195-1201`; probe `is_skill_description_truncated_for_prompt`, `:1203`), while skill **bodies are lazy-loaded** through `skill_view(...)` — `iter_skill_index_files` (`:1207+`) explicitly excludes `references/templates/assets/scripts` support dirs as "progressive-disclosure data". The host's own linter flags over-budget descriptions as "losing routing signal" (`tools/skill_linter.py:163-169`). **Live measurement on this host: 119 `SKILL.md` files, 32 (26%) have descriptions over the 60-char budget** — and the worst offenders are the compound-engineering skills themselves (275–535 chars).
8. **Ecosystem / standards**: the **Agent Skills open spec** is live at `agentskills.io/specification` with a public repo (`agentskills/agentskills`) and a reference validator library (`skills-ref`, also on npm) — frontmatter rules: `name` 1–64 chars, lowercase/digits/hyphens, **must match the parent directory name**, no consecutive hyphens; `description` 1–1024 chars; optional `license`, `compatibility`, `metadata`, `allowed-tools` (experimental). Third-party analysis of Claude Code's listing mechanics (dev.to, 2026): per-entry description cap 1,536 chars, a whole-listing budget of **1% of the model context window**, and on overflow descriptions are dropped **starting with the least-invoked skills — a self-reinforcing ratchet**. Skill-rot discourse ("how do you keep your agent skills from rotting silently?", dev.to 2026) names the exact gap — "Neither [eager preload nor lazy index] has a gardener mode. Nobody removes old skills. Nobody flags duplicates." Bulk adoption is real: curated skill lists at 74k★, single packs shipping 380 skills.
9. **Release unchanged** (v2026.8.31 latest). Local checkout `/home/agent/.hermes/hermes-agent` is at `v2026.8.27-603` — the *installed host*, not the checkout, is the runtime surface the plugin must probe; the skew is itself a doctor consideration.

---

## Topic axes

- **A1** Host-surface leverage (new upstream surfaces the plugin is blind to)
- **A2** Evidence quality, trust, and store reliability
- **A3** Skill lifecycle: routing effectiveness, provenance, staleness
- **A4** Standards and ecosystem conformance (Agent Skills spec, hub interop)
- **A5** User-need and competitor signal (listing budgets, rot, bulk adoption)

## Ranked candidates (survivors)

### 1. Routing-budget curation — measure and protect the 60-char description index
**Axis A3/A5 · Confidence 82% · Complexity Low**

- **Direct evidence:** host truncates every skill's description to 57+"…" for the eager system-prompt index (`agent/skill_utils.py:1175-1203`); the host linter calls over-budget descriptions a routing loss (`tools/skill_linter.py:163-169`); **32 of 119 skills on this host (26%) exceed the budget, including the highest-value compound-engineering skills (275–535 chars)**; the plugin has zero references to any of this (`grep SKILL_PROMPT_DESC_LIMIT|extract_skill_description hermes_curator_evolver/` → 0).
- **Description:** `report --routing-budget` lists every skill whose description truncates, what the model actually sees (first 57 chars), and whether the lost tail carried trigger keywords; an evidence-linked column answers "does a truncated description correlate with lower measured invocation?" — the question nobody else can answer, because only this plugin holds per-skill invocation history. A guard slice rejects or flags apply-gate description edits that push the trigger keywords past char 57.
- **Why it matters:** the ecosystem analysis shows description budget is the *routing* signal (CC drops least-invoked descriptions first — a ratchet; Hermes has no drop mechanism, so it pays `name+60c` for every skill forever — with 380-skill packs that is ~25 KB of index in every prompt). This is also an **evidence-based correction** to cycle-3's context-budget candidate, whose "Hermes loads SKILL.md whole" premise is wrong (bodies are lazy; the index is 60c).
- **Downsides:** truncation ≠ death (skills remain invocable by name; the model often reads the body via `skill_view`); the correlation study needs enough usage history per skill; keyword-primacy is a heuristic, not a guarantee.
- **Folds in:** aggregate index-cost view (all skills × name+60c) previously sketched under cycle-3 idea 4.

### 2. Hub-provenance awareness — read `.hub/lock.json`, detect hub-update clobbers, probe quarantine
**Axis A1/A3 · Confidence 75% · Complexity Low-Medium**

- **Direct evidence:** `HubLockFile` (`tools/skills_hub.py:4008-4024`) tracks provenance in `skills/.hub/lock.json` with per-skill `source`, `identifier`, `trust_level`, `scan_verdict`, `skill_hash`; hub CLI exposes `install/update/audit` (`hermes_cli/skills_hub.py:1826-1845`); the hub quarantines unsafe installs and writes an audit log; `grep skills_hub|HubLockFile hermes_curator_evolver/` → 0 hits; live host has the `.hub` dir shipped but an empty lock file (the surface precedes adoption — cheap first-mover integration).
- **Description:** reports tag hub-installed skills with origin/trust/scan verdict read from the lock file; `doctor` reports quarantine contents and audit-log tail; and — the real prize — when a hub `update` rewrites a skill the plugin has a manifest for, the manifest-hash mismatch is *attributed* ("hub update at T") instead of surfacing as unattributed external drift (this slots directly into cycle-3's ledger-timeline candidate as a second writer source).
- **Why it matters:** the hub is the host's sanctioned bulk-adoption path (50k+ catalog); every hub install is a skill the plugin's curation model currently cannot distinguish from a hand-written one, and every hub update is a managed-block clobber the plugin will misread.
- **Downsides:** lock-file shape is an internal API (version field `"version": 1` is the only stability promise — import-guard + tolerate-absent, same posture as the ledger integration); zero hub installs on this host today means the read path is unexercised until a user installs one (ship behind the existing `--skills-dir` report mode).

### 3. EvidenceStore connection topology — one warm writer per process, contention-vs-environment retry split
**Axis A2 · Confidence 78% · Complexity Medium**

- **Direct evidence:** `EvidenceStore.connect()` opens a **fresh `sqlite3.connect` on every call** (`storage.py:237-241`), and `record_tool_call`/`record_turn`/`record_session_end` (`:310/:347/:378`) each pay it plus two PRAGMAs and a journal-mode apply — the exact "redundant-writer topology" upstream diagnosed in merged **#101191** as firing close-time WAL checkpoints against the live writer ("5 live SessionDB handles" logged 7 minutes before corruption incident #4). This is also the amplifier behind pass-5 finding Q6 (worst-case ~15.75s hook stall under contention).
- **Description:** cache one connection per resolved DB path per process (contextvar/thread-local; single-flight the open; canonicalize the key with `Path.resolve()` exactly as #101191 did), and split `_write_with_retry`'s error handling into the taxonomy from #101202: busy/locked/EAGAIN-family → bounded retry; `ENOLCK/ESTALE/EIO`-family → fail fast with the real errno instead of burning timeouts (cite: #101202 closed unmerged — the taxonomy is a recipe, not upstream law).
- **Why it matters:** turns the plugin's worst unattended failure mode (hook latency under contention) from per-event connection storms into a single warm path, and imports an upstream-endorsed corruption-prevention pattern the evidence store currently violates by construction.
- **Downsides:** a cached connection changes lifecycle assumptions (hooks must never hold a write txn across turns); needs the same close-at-exit hygiene upstream added; #101202's errno split is unverified against the plugin's actual failure distribution (log first, split second).
- **Folds in:** the deferred-spill idea (queue events when the store is unavailable, drain later) — that is #101202's deferred-recovery retry applied to evidence rows.

### 4. Agent Skills spec conformance profile in `skill_validate`
**Axis A4 · Confidence 72% · Complexity Low**

- **Direct evidence:** the open spec is published and versioned in a public repo with a reference validator (`agentskills/agentskills`, `skills-ref` on npm; `agentskills.io/specification`); its frontmatter rules are concrete (name 1–64, lowercase/digits/hyphens, **must match the parent dir**, no `--`; description 1–1024; optional `license`/`compatibility`/`metadata`/`allowed-tools`); the plugin's validator checks name/description *presence* only (`skill_validate.py:61-75`).
- **Description:** a `--profile agentskills` mode (default: warn-only) enforcing the spec's name/description rules, flagging `name != parent-dir` and spec-unknown-but-harmless fields as advisories, and never failing on fields the spec marks optional or the host adds (`triggers`, per upstream #100056) — tolerance is the point.
- **Why it matters:** spec-valid skills are portable into the 74k★ ecosystem and the hub's install path; being the tool that *certifies* portability is cheap differentiation, and it upgrades the standing U9 "watch frontmatter divergence" note from a watch item to a pinned conformance target.
- **Downsides:** the spec has an experimental field (`allowed-tools`) — pin by published date and cite the URL in output, don't hard-fail; avoid vendoring `skills-ref` (JS) — reimplement the ~6 rules.
- **Folds in:** spec-validity as a publish precondition inside the standing publish-safety packet (cycle-2 survivor 1).

### 5. Upstream-source staleness report for hub-installed skills ("gardener mode")
**Axis A3/A5 · Confidence 55% · Complexity Medium**

- **External evidence:** the rot discourse names the failure precisely — a skill is "80% valid, step 4 rotted, nobody flags it" and the file-vs-v2 dilemma has no good answer; the rot post's own answer (skills as versioned documents in a semantic store) is what this plugin's manifests already approximate locally.
- **Direct evidence:** the hub lock file records each skill's `source` + `identifier` + `skill_hash`, and the hub already solves GitHub auth (`GitHubAuth` in `tools/skills_hub.py`) — a read-only "is my installed skill behind its source?" check has every ingredient.
- **Description:** `report --staleness` (opt-in, network-gated, offline-safe: last-known result cached, unknown marked unknown) diffs the installed hash against the source's current state for lock-file-registered skills only, and reports "behind / current / unverifiable" — never auto-updates (hub `update` owns that).
- **Why it matters:** it is the first curation answer to the rot post's "which of my 70 skills are stale" question that does not require the user to have written the skill.
- **Downsides:** zero hub installs on this host today — pure watch-item demand; GitHub rate limits and private-source auth make "unverifiable" the common case unless hub auth is reused; deliberately stays out of the update business to avoid competing with the hub.

## Rejections this pass (beyond all standing cycle-1..4 rejections)

- **sqlite-vec migration for semantic search** — pre-v1 upstream ("expect breaking changes"), a native extension vs the plugin's optional-deps posture, and the working set is 10²–10³ skills where the numpy scan is already fine. Revisit only if a cross-library fleet report lands (cycle-3 idea 6 territory).
- **Multi-model / LLM-assisted description optimization** — contradicts the model-free default; the measurable half (S1's correlation report) delivers the value without a model call.
- **Hub bundle-shape validation at the apply gate** (port of `_referenced_support_paths`, `skills_hub.py:202`) — real, but it is a slice of the standing host-linter integration (cycle-4 survivor 4); fold there, don't double-track.
- **Ingest-side cron filtering as a *new* candidate** — it is cycle-4 survivor 1; what is new (SQL `source_filter` params, #101199's 97.5% measurement) is recorded below as an implementation shortcut and premise upgrade, not a re-proposal.
- **Skill marketplace / export, MCP surface, git-PR mode, replay benchmarks, `/curator` command, document→skill mining, Q-value ranking** — standing rejections; no new evidence this pass overturns any of them.
- **In-thread run degradation (disclosure, not rejection):** grounding, generation, critique, and verification ran in this one context — no independent corroboration is claimed for any survivor; raw pool ~15 candidates vs the dispatched-fleet target ~36–48.

## Corrections to the standing roadmap

- **Evidence pipeline (cycle-4 survivor 1) — implementation shortcut now exists:** `search_sessions` on upstream `main` accepts `source_filter`/`exclude_sources` (`hermes_state_search.py:1346-1386`); either call the API or mirror the same WHERE clauses in the plugin's direct-SQL reader. Premise strengthened by #101199's deployment measurements (97.5% cron sessions; 86% of trigram-covered text cron-source) and by upstream itself moving to exclude cron from its trigram index.
- **Context-budget candidate (cycle-3 idea 4) — premise corrected:** Hermes does **not** load SKILL.md bodies eagerly; it eager-loads `name + description[0:57]+"…"` and lazy-loads bodies via `skill_view`. Context-cost math must price the 60-char index, not file bytes; survivor 1 absorbs the corrected metric.
- **U9 (spec conformance) — pin dropped:** target `agentskills.io/specification` + `skills-ref`; tolerance for unknown frontmatter fields is now spec-mandated behavior (`metadata`, `allowed-tools`), not just defensive posture.
- **doctor --host-compat (cycle-3 idea 3) — three new probes:** (a) `hermes_state` facade still exporting the names the plugin imports (state layer split, see What's-new #1); (b) `.hub/lock.json` + quarantine reachability; (c) `SKILL_PROMPT_DESC_LIMIT`/`is_skill_description_truncated_for_prompt` availability for S1. Also: the local checkout at `/home/agent/.hermes/hermes-agent` is `v2026.8.27-603` while the installed host is newer — doctor should probe the *runtime* module, never the checkout.
- **Ledger timeline (cycle-3 idea 1) — second writer source:** hub `update` is now a named external writer the timeline can attribute via the lock file and audit log (survivor 2).

## Verification pointers (all read-only, reproducible)

```bash
# host prompt-index mechanics + live measurement
grep -n "SKILL_PROMPT_DESC_LIMIT" -A 28 /home/agent/.hermes/hermes-agent/agent/skill_utils.py | head -40   # :1175-1203
sed -n '155,175p' /home/agent/.hermes/hermes-agent/tools/skill_linter.py                                    # truncation rule
python3 - <<'EOF'   # 32/119 over budget (recursive scan, YAML frontmatter)
import re,pathlib,yaml
s=pathlib.Path.home()/'.hermes/skills'; n=t=0
for md in s.rglob('SKILL.md'):
    m=re.match(r'^---\n(.*?)\n---',md.read_text(errors='ignore'),re.S)
    if not m: continue
    try: fm=yaml.safe_load(m.group(1)) or {}
    except Exception: continue
    d=str(fm.get('description') or '').strip()
    if d: n+=1; t+=len(d)>60
print(n,"descriptions;",t,"over 60 chars")
EOF
# hub surface
sed -n '4008,4024p' /home/agent/.hermes/hermes-agent/tools/skills_hub.py        # HubLockFile
grep -n '"install"\|"update"\|"audit"\|action ==' /home/agent/.hermes/hermes-agent/hermes_cli/skills_hub.py | head
grep -rn "skills_hub\|HubLockFile\|SKILL_PROMPT_DESC_LIMIT" /work/projects/hermes-curator-evolver/hermes_curator_evolver/ | wc -l   # 0
cat ~/.hermes/skills/.hub/lock.json 2>/dev/null; wc -l ~/.hermes/skills/.curator_ledger.jsonl                  # empty lock; 16 rows
# plugin store topology
sed -n '237,241p' /work/projects/hermes-curator-evolver/hermes_curator_evolver/storage.py                     # connect-per-call
# upstream drift
gh api repos/NousResearch/hermes-agent/issues/101199 --jq '.title,.state'      # cron/FTS exclusion, open
gh api repos/NousResearch/hermes-agent/pulls/101191 --jq '.merged,.merged_at'  # true, 2026-09-02T11:07:21Z
gh api repos/NousResearch/hermes-agent/pulls/101202 --jq '.merged'             # false (recipe, not law)
curl -s https://raw.githubusercontent.com/NousResearch/hermes-agent/main/hermes_state_search.py | sed -n '1346,1386p'
gh api repos/NousResearch/hermes-agent/releases/latest --jq '.tag_name'        # v2026.8.31
# standards / ecosystem
curl -sL https://agentskills.io/specification | grep -c "allowed-tools"         # spec fields
gh api repos/agentskills/agentskills/contents --jq '.[].name' | head -5         # repo + skills-ref
```

Sources (internet, via agent-reach/Exa + gh): agentskills.io/specification; github.com/agentskills/agentskills (+ npm `skills-ref`); dev.to/rulestack "Too many Claude Code skills? How the listing budget decides which descriptions Claude sees" (per-entry 1536-char cap, 1%-of-context listing budget, least-invoked-dropped-first); dev.to/klymentiev "How do you keep your AI agent skills from rotting silently?" (gardener-mode gap); ComposioHQ/awesome-claude-skills ★74,270 and alirezarezvani/claude-skills (380 skills) as bulk-adoption signal.
