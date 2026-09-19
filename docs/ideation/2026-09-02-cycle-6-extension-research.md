# Cycle-6 Extension Research — evidence-backed candidates beyond the standing roadmap

- **Run:** `6f5d76c84f52491ba25460c4a6e1a454` · phase `research` · attempt `c592ae8daa9e486ca68355af84dc1725`
- **Intent:** `research_repository_extensions`
- **Date:** 2026-09-02 (~14:20Z) · **Repo:** `fix/maintenance-cycles-1-5` @ `4350ee2` (source-identical to `ac9c0ee`; pass-6 assess verified the empty-diff)
- **Skill:** no compound-engineering router / `ce-*` skill is installed on this host (same disclosed deviation as passes 2–6 assess); the `ce-ideate` methodology (grounding → evidence scouting → six-frame generation → critique → basis verification) ran in-thread. Internet access via the **agent-reach router** (Exa MCP for web search, `gh` for GitHub, direct curl for the Hermes docs site) per its host-local routing rules.
- **Prior passes:** `docs/ideation/2026-09-02-cycle-{2,3,4,5}-extension-research.md`. This pass does **not** re-propose their survivors (now roadmap packets U21–U25, U29–U34, U38–U50); it adds a new evidence layer — upstream drift since ~11:25Z including the bundled-skill sync contract, three fresh arXiv frameworks that formalize exactly what this plugin does, a new direct competitor, and new native-curator defect reports — and 6 fresh candidates.

**Method disclosure:** all generation/critique/verification ran in this single pi context (no dispatchable subagents); no independence is claimed for any survivor. Raw pool ~14 candidates. Every `direct:` basis below was verified this run (live host measurement, `gh api`, Exa fetch, or raw runtime source read). One false start corrected mid-run: an initial "curator" search returning 989 upstream results looked like a new discovery but is the **known** native curator (`agent/curator.py`, covered cycle-2 E2 / cycle-4 R6) — only its *new* issue numbers are treated as fresh signal.

---

## What's new since cycle-5 (~11:25Z)

1. **The bundled-skill sync contract is now the plugin's biggest unexploited provenance surface.** Runtime `tools/skills_sync.py` (2,041-line sibling `agent/curator.py` unchanged in role) maintains a v2 manifest `skills/.bundled_manifest` of `skill_name:origin_hash` (live host: **81 entries**); `sync_skills()` **updates a user copy only when it still matches the origin hash** — any user/curator edit freezes the skill out of every future bundled update, silently, with no surface that says so. PRs **#101274** (closed/merged) and **#101300** (open) fix exactly the "curator must be able to edit synced copies" premise (issue **#101226**, open: immutable-source installs synced read-only), and #101226's body names *the curator* as an intended editor of those copies. **Live reproduced on this host:** 80/81 bundled skills intact; exactly one — `mlops/evaluation/evaluating-llms-harness` — diverged, and the divergence is a single support-file edit (`references/api-evaluation.md`, 11085B user vs 11114B bundled; SKILL.md byte-identical; no plugin managed block). That skill will never receive a bundled update again and nothing today reports it. The plugin reads the manifest's **names only** (`skill_sources.py:_read_bundled_manifest_names`); `grep -rn "bundled_skill|diff_bundled|reset_bundled" hermes_curator_evolver/` → 0 source hits.
2. **A centrally generated Hermes Skills Index is landing** — runtime `scripts/build_skills_index.py` + `HermesIndexSource` (`tools/skills_hub.py:4592`) crawl official/clawhub/lobehub/skills.sh/browse.sh/GitHub taps into `website/static/api/skills-index.json`; open PR **#101237** adds nine community repos and cites **977 currently published skills** (including `Panniantong/Agent-Reach` itself). The index URL (`HERMES_INDEX_URL`, `tools/skills_hub.py:4499` → `…/docs/api/skills-index.json`) **404s today** (verified twice) — the surface exists in-tree but is not yet deployed; PR unmerged.
3. **state.db is about to auto-prune** — PR **#101316** (open, body: "the default flips Teknium approved on #54189"): `sessions.auto_prune` default `False→True`, 90-day retention of *ended* sessions, post-prune VACUUM gated on `freelist_count/page_count > 0.25`. Two consequences: the plugin's backfill horizon is capped at ~90d by upstream default, making the plugin's evidence store the only >90d behavioral record (retention value up); and the prune+ratio-gated-VACUUM+throttle recipe is directly portable to `evidence.sqlite` (cycle-2 survivor 4's compaction, still unimplemented).
4. **Cron/trigram exclusion landed as a PR** — **#101266** (open): trigram shadow-table storage **−93.9%** on a synthetic cron-heavy benchmark (1,536,000B → 94,208B, 420→20 indexed docs), canonical transcripts and keyword search preserved. U38's premise (cron is 97.5% of sessions per #101199) now has its upstream implementation; the plugin's direct-SQL reader still needs its own source filter.
5. **Native-curator defect reports with evidence-shaped answers** — new since cycle-5's notes: **#79295** (built-ins seeded before first curator run are *all* marked stale) and **#79311** (re-anchor the never-used clock), **#97243** (overlapping review passes), **#95441** (desktop-only installs never auto-tick `maybe_run_curator` — no curation at all on that install class), **#66648** (surface staleness in status/dashboard), **#97964** (advertise `absorbed_into` in `skill_manage` schema — consolidation state becoming host-visible), **#101341** (kanban skills cannot pin a revision; "name equality is not capability equality", with a live multi-profile same-name/different-version incident table).
6. **Three 2026 arXiv frameworks formalize this plugin's design** (none previously cited in any cycle): **SkillProx** (2608.07449, Aug 2026) — forward stage = diagnosis-driven edits committed **only on an outcome-grounded gate, else rollback+retry, with rejected-edit memory retained as feedback**; backward stage = decompose the skill into auditable knowledge units, **frozen leave-one-out utility audit, validation-gated consolidation/demotion/removal** ("deletion as a dedicated mechanism, not a generic edit"). **SkillComposer** (2606.06079, Jun 2026) — skill evolution decomposes into **create / improve / merge**, and *merge and improve address orthogonal quality dimensions* (generalization vs specification). **SkillX** (2604.04804, Apr 2026, zjunlp) — hierarchical multi-level skill libraries (planning/functional/atomic), iterative refinement from execution feedback, exploratory expansion; +10% when plugged into weaker agents. SkillComposer's related-work also cites the fragility caution: self-generated skills **may provide no average gain** (Li et al. 2026) and utility degrades under realistic retrieval (Liu et al. 2026b).
7. **New direct competitor: `cskwork/skill-curator`** (created 2026-08-04, last push 2026-08-21, 0★ — pre-adoption): "Agent Skills librarian" across Claude Code/Codex/Cursor/Gemini CLI/OpenCode — **multi-root discovery with name-collision + precedence reporting, exact-duplicate detection by package hash, per-skill lifecycle states (active/stale/unmanaged/pinned/protected/invalid/archived), an `adopt` gate (new skills are unmanaged and cannot be pruned until adopted), dry-run-by-default `archive`/`prune` with explicit `--apply`, archive→list→restore round trip, snapshot/rollback, symlink-aware, "no invented usage counts"** (it has no telemetry; this plugin has *real* counts — the differentiator). Existing competitor `AMAP-ML/SkillClaw` still 2,547★ but idle since 2026-08-17; `ComposioHQ/awesome-claude-skills` 74,287★ (cycle-5: 74,270).
8. **Listing-budget mechanics got operator controls** (dev.to/rulestack, 2026-07-27 — the post cycle-5 cited has new detail): `skillOverrides` `"name-only"`/`"off"`, `skillListingBudgetFraction`, `skillListingMaxDescChars`; `/doctor` estimates listing cost; **auto-compaction re-attaches the most recent invocation of each invoked skill (first 5,000 tokens each, 25,000 combined, most-recent-first)**; and the overlap warning — "six overlapping skills make the listing a coin flip" — is the exact failure the plugin's consolidation workstream and pass-6 S8 (duplicate frontmatter names) live inside.
9. **Agent Skills spec unchanged** (agentskills.io/specification re-fetched: name 1–64 lowercase/hyphen/must-match-parent-dir/no `--`, description 1–1024, `license`/`compatibility`/`metadata`/`allowed-tools` optional-experimental) — U49's pin holds; no conformance work invalidated.
10. **Release still v2026.8.31** (2026-08-31); v0.21 planning issue **#101294** packs 31 PRs into 6 story lines — skills-relevant: **#95387 "implicit skill prefetch — load mentioned skills into turn prefetch cache"** (when it lands, skill *mention* becomes a load path distinct from `skill_view`, changing attribution semantics — watch item for U47/S6).

## Topic axes

- **A1** Host-surface leverage (bundled-sync contract, skills index, native-curator state)
- **A2** Evidence quality, retention, and store lifecycle
- **A3** Skill lifecycle: provenance, staleness, consolidation, revision identity
- **A4** Research-validated evolution mechanics (outcome gates, unit demotion)
- **A5** User-need and competitor signal (native-curator bugs, skill-curator UX, revision pinning)

## Ranked candidates (survivors)

### 1. Bundled-origin provenance — read `.bundled_manifest` origin hashes; report frozen-out skills and attribute sync writes
**Axis A1/A3 · Confidence 85% · Complexity Low**

- **Direct evidence:** manifest v2 `skill_name:origin_hash` shipped and live (81 entries, `tools/skills_sync.py:8,91,160-235`); the sync contract updates a user copy **only while it matches the origin hash** (`:883-897`); #101226/#101274/#101300 make curated edits to synced copies a first-class supported scenario; **live reproduced:** `evaluating-llms-harness` diverged by one support-file edit (11085B vs 11114B) → permanently frozen out of bundled updates, invisible; plugin currently reads names only (`skill_sources.py`).
- **Description:** extend the plugin's source classification to parse origin hashes; `report --bundled-drift` emits three states per bundled skill — `intact` (sync may update; a later hash change is *attributed* as a sync update in the drift timeline), `curated-diverged` (frozen out; show the three-way diff bundled↔origin↔current, reusing the existing reference-spillover diff plumbing), and `bundled-behind` (origin changed under an intact copy → expect a sync update on next host upgrade). Never mutates — `reset_bundled_skill()` stays the host's verb; the report can *point* at it.
- **Why it matters:** every host upgrade rewrites up to 81 skill trees the plugin may have manifests for; without origin hashes those writes are the unattributed external-drift class (U29's timeline needs a named writer), and every curator edit silently forfeits upstream fixes — the exact failure live on this host today. Cheapest first-mover integration: the file is local, versioned (`version`-less but shape-stable since v2), and already half-read by the plugin.
- **Downsides:** manifest format is internal (import-guard + tolerate-absent, the established posture); `_dir_hash` spans the whole skill dir, so the plugin can't say *which* file diverged without its own per-file walk (do the walk in the report, not the classifier); zero divergence on fresh installs means the report is boring until the first real edit — ship it inside the existing `report --skills` mode.
- **Folds in:** the third writer source for U29's ledger timeline (hub update was #2, per cycle-5); a `doctor` probe for manifest reachability (extends U31's list).

### 2. Evidence-anchored staleness reconciliation with the native curator
**Axis A1/A3/A5 · Confidence 75% · Complexity Low-Medium**

- **Direct evidence:** native curator staleness is clock-based (`DEFAULT_STALE_AFTER_DAYS=30`, `apply_automatic_transitions`, `agent/curator.py:72,305`); open bugs **#79295** (all pre-first-run built-ins marked stale) and **#79311** (re-anchor never-used clocks) are install-clock-vs-usage-clock confusions; **#95441** desktop-only installs never auto-tick; **#66648** demands staleness visibility. The plugin's `tool_events.skill_name` history (and `.usage.json`, cycle-4 R5) is precisely the missing usage clock.
- **Description:** `report --staleness` (offline, local-only) reconciles the native curator's state file with plugin evidence: "marked stale but **N attributed events in the last D days** (rows e1..eN — false-stale, #79295 class)" vs "no attributed events since seed → true never-used (supports #79311's re-anchor intent)". A `doctor --curator-tick` probe answers #95441: if the native curator never ticks on this install, report that the plugin's scheduler is the only curation path and raise its visibility in output.
- **Why it matters:** it converts two open upstream defects into this plugin's home-field advantage — only this plugin holds the usage evidence to adjudicate clock-based staleness; and the desktop-only gap is a positioning fact for every future README/demo.
- **Downsides:** native curator state-file shape is internal (tolerate-absent, never write it); "attributed events" inherit every classifier defect (hard dependency on the U43 residual S1/S2/S4 fixes); staleness≠uselessness for cron-referenced skills (already protected upstream via `_cron_referenced_skills` — respect it by reading the same set, cycle-4 R6's packet).
- **Folds in:** U50 stays a separate, network-gated *source* staleness check (hub origin); this is *host-state* reconciliation — complementary, not overlapping.

### 3. Lifecycle vocabulary for the review queue — `adopted` / `pinned` / `absorbed_into`, with collision+precedence reporting
**Axis A3/A5 · Confidence 70% · Complexity Medium**

- **Direct evidence:** `cskwork/skill-curator` (new competitor) proves the UX pattern set — unmanaged-until-`adopt` (nothing new can be pruned), `pin`/`unpin`, dry-run-by-default archive with `--apply`, **exact-duplicate detection by package hash and name-collision/precedence reporting across roots**; upstream **#97964** is making `absorbed_into` host-visible in `skill_manage`; upstream **#101341** documents the live incident class of same-name/different-version skills across profiles; pass-6 **S8** reproduced the plugin silently dropping one of two same-frontmatter-name skills.
- **Description:** (a) fix S8's silent drop by keying discovery on paths and *reporting* frontmatter-name collisions with precedence (which dir wins at load time, per the host's own index rules); (b) add `pinned` per-skill state to the review queue (distinct from `protect_core_skills`' builtin list: user intent, not origin class) that hard-blocks archive/prune/retire paths; (c) when a consolidation (merge-check) completes, record `absorbed_into` in both manifests and mirror it wherever the host makes it visible.
- **Why it matters:** the competitor's entire lifecycle UX is now table stakes; upstream is standardizing the exact vocabulary (`absorbed_into`); and the same-name collision class is no longer theoretical — it has an upstream incident table (#101341) and a reproduced plugin-side defect (S8).
- **Downsides:** duplicating the host's lifecycle verbs risks drift (write only plugin-side state; mirror, don't own); "precedence" is host-index-order semantics and must be read from runtime behavior, not assumed; `adopt` semantics map awkwardly onto evidence-mining (everything the plugin tracks already has evidence by definition) — adopt is likely **rejected as a concept**, kept only the pin/collision/absorbed parts.
- **Folds in:** U24's outcome cohorts (pinned rows are excluded from cohort math); C3's dead `update_status` gains a real caller.

### 4. Outcome-delta gate — measure whether an applied skill actually changed the error cohort
**Axis A4/A2 · Confidence 72% · Complexity Medium**

- **Direct evidence:** SkillProx's forward stage commits only on an **outcome-grounded performance gate** and **retains rejected edits as feedback** (2608.07449); SkillComposer shows improve and merge are separately measurable dimensions (2606.06079); the fragility literature (Li 2026: self-generated skills may provide *no average gain*) makes unmeasured auto-evolution a liability. Plugin today: `verify_command` is syntactic validation; **N6** (carried): the verifier never cross-checks claimed vs report counts; auto-evolve applies and never looks back — the exact "unverified forward update" SkillProx's gate exists to prevent.
- **Description:** model-free slice using data the store already has: after each apply, record the pre-apply cohort (attributed error rate over the trailing window for that skill); on the next run, compute the post-apply cohort and attach `outcome_delta` to the candidate/manifest. Policy: a candidate whose *predecessor's* measured cohort regressed beyond a threshold is quarantined from auto-apply (human review only) — the outcome-measured upgrade of cycle-2 survivor 2's anti-pattern ledger ("stop re-proposing failed blocks").
- **Why it matters:** it is the only mechanism on any roadmap (host, competitor, or this plugin) that answers "did the curated edit help?" from *real* session evidence rather than benchmarks — the plugin's structural differentiator, now with an academic design contract to cite.
- **Downsides:** cohort deltas are noisy at small N (require a minimum event count before any verdict, report `insufficient-evidence` otherwise); confounded by everything else that changed (model swaps, tool versions — record them in the manifest for later stratification); hard dependency on S1/S2/S4 classifier fixes and on S6 attribution (garbage in, regression out); leave-one-out auditing (SkillProx's backward gate) needs an eval harness this plugin deliberately doesn't have — do **not** promise it.
- **Folds in:** N6's grounding cross-check becomes the trivial first slice (claim vs report count) inside the same gate.

### 5. Knowledge-unit demotion — prune stale managed-block bullets into `references/` instead of accumulating
**Axis A4/A3 · Confidence 60% · Complexity Medium-High**

- **Direct evidence:** SkillProx's backward stage: decompose the accumulated skill into auditable units, estimate per-unit utility, then **validation-gated consolidation, demotion, or removal** — explicitly because append-only skill text is the unregulated-growth failure; the plugin's managed block is already an auditable-unit boundary whose bullets are generated from specific evidence cohorts (evidence_refs in manifests), and its current growth policy is append-only (only `references/` spill files are pruned via `max_reference_files`); the rot discourse (cycle-5) and the listing-budget/overlap analysis (1,536-char entries, 1%-of-context listing, "six overlapping skills = coin flip") price every hot-path byte.
- **Description:** tag each managed-block bullet with its generating cohort (manifest already carries evidence refs; persist the bullet→refs map); when a bullet's cohort has had **zero attributed events for `stale_units_days`**, demote it — move the text to `references/curator-evolver-demoted-<skill>-<ts>.md`, leave a one-line pointer — behind the existing apply/verify/rollback machinery. Nothing is deleted; rollback restores.
- **Why it matters:** it closes the loop the rot posts demand (step-4-rot has an owner) using only evidence the plugin already stores; demotion-not-deletion is both SkillProx-validated and consistent with the plugin's reversibility posture.
- **Downsides:** bullet-level cohort attribution requires stable bullet identity across rewrites (hash the normalized bullet text; merges break lineage — accept and mark `lineage-lost`); zero-events is weaker than SkillProx's leave-one-out utility (say so in docs); risk of demoting content that prevents rare-but-catastrophic errors (gate on error-type, not just count); complexity is real — this is the most speculative survivor.
- **Folds in:** U47's budget metric (demotion is the write-side lever for the read-side budget report); U3's reference pruning already establishes the references/ lifecycle.

### 6. Ecosystem-index duplicate check (demand-gated on index deployment)
**Axis A1/A3 · Confidence 55% · Complexity Low once index is live**

- **Direct evidence:** `HermesIndexSource` + `HERMES_INDEX_URL` shipped in runtime (`tools/skills_hub.py:4499,4592`); PR #101237 (open) cites 977 published skills across 7+ source classes; the public URL **404s today** (verified twice this run); `cskwork/skill-curator` validates duplicate-detection demand (exact-dup by package hash locally).
- **Description:** when (and only when) the index is deployed and reachable: `report --ecosystem` (opt-in, network-gated, offline-safe) flags curated skills whose normalized name or content hash collides with an indexed skill — "you are maintaining by hand what ClawHub/LobeHub/skills.sh already ships (vX)" — feeding the consolidation workstream with ecosystem-level merge candidates.
- **Why it matters:** 977-skill ecosystems make same-shape collisions the default condition, not the edge case (#101341's incident is the same disease at profile scope); being the tool that notices "this hand-curated skill duplicates a maintained upstream one" is cheap differentiation on data only it can see.
- **Downsides:** index not live (hard gate — do not build against an unmerged PR); content-hash equivalence across ecosystems is fuzzy (name+description similarity first, hash exact-match second); KTD14-style demand gate applies (second independent signal, e.g. an actual index deployment or a user report).

## Rejections this pass (beyond all standing cycle-1..5 rejections)

- **SkillX-style automated skill-library construction** (hierarchical planning/functional/atomic generation, exploratory expansion) — contradicts the model-free default (KTD4) and the plugin's scope (curating human/hub-provided skills, not synthesizing libraries). Evidence archived for the day an opt-in model-assisted mode exists.
- **Porting `skill-curator`'s multi-root discovery wholesale** — the plugin is Hermes-native; cross-harness roots are a different product. Only the collision/precedence *reporting* pattern survives (candidate 3a).
- **`adopt` lifecycle semantics** — everything the plugin tracks already has evidence by construction; an adopt gate would guard against a population the plugin never acts on. Kept: pin, collision, absorbed_into (candidate 3).
- **Leave-one-out per-unit utility audits** (SkillProx's exact backward gate) — requires an eval harness and task batches the plugin deliberately doesn't have; candidate 5 ships only the evidence-count approximation and says so.
- **Index-backed anything before deployment** — URL 404 (verified); PR unmerged. Candidate 6 is written to be unbuildable until that changes.
- **Listing-budget knobs (`skillOverrides`, budget fraction) in the plugin** — those are Claude Code settings; the Hermes-side equivalent (if any) belongs upstream. Recorded as a potential upstream issue, not plugin work.
- **Standing rejections** (marketplace/export, MCP surface, git-PR mode, replay benchmarks, `/curator` command, document→skill mining, Q-value ranking, model-assisted description optimization, sqlite-vec) — no new evidence overturns any of them.

## Corrections to the standing roadmap

- **U48 (hub provenance) — broaden to a three-source provenance model:** `.hub/lock.json` (hub installs), `.bundled_manifest` origin hashes (bundled, candidate 1), native-curator state (candidate 2's read-side). One `SkillSourceInfo` extension, three readers.
- **U29 (ledger timeline) — third named writer:** `sync_skills()` updates (attributable via candidate 1's origin-hash comparison), joining hub `update` and human edits.
- **U36 / pass-6 S3 (backfill ordering) — new horizon constraint:** #101316's default 90-day auto-prune of ended sessions caps state.db history; U36's design must document the horizon, and the plugin's evidence store becomes the only long-horizon record — raising the priority of cycle-2 survivor 4's retention policy (now with #101316's ratio-gated-VACUUM recipe to port instead of inventing one).
- **U45 residual / pass-6 S5 (read-path locking):** #101279 (multi-writer shared-brain deployments, open) shows upstream expects concurrent multi-writer patterns to grow — S5's fix matters more, not less.
- **U47 (routing budget):** the CC operator-control pattern (`name-only` demotion) has no Hermes equivalent — candidate as an *upstream* issue; the plugin-side lever is candidate 5's demotion.
- **U31/U13 (doctor) — three new probes:** bundled-manifest reachability + hash-parse; native-curator ticking (desktop-only gap, #95441); skills-index URL liveness (for candidate 6's gate).
- **Watch item (no packet):** #95387 implicit skill prefetch — if mention-driven prefetch lands, `skill_view`-based attribution (pass-6 S6) loses coverage; re-run S6's evidence if it merges.

## Verification pointers (all read-only, reproducible)

```bash
# bundled-sync contract + live divergence (candidate 1's core evidence)
grep -n "origin_hash\|user-modified\|safe to update" /home/agent/.hermes/hermes-agent/tools/skills_sync.py | head
python3 - <<'EOF'   # 81 tracked; 80 intact; evaluating-llms-harness diverged by one support file
import sys, pathlib
sys.path.insert(0, "/home/agent/.hermes/hermes-agent")
from tools.skills_sync import _get_bundled_dir, _dir_hash, _read_manifest, _discover_bundled_skills, _compute_relative_dest
bdir=_get_bundled_dir(); man=_read_manifest(); disc=dict(_discover_bundled_skills(bdir))
for name,origin in man.items():
    if name not in disc: continue
    dest=pathlib.Path.home()/".hermes/skills"/_compute_relative_dest(disc[name],bdir)
    if _dir_hash(disc[name])!=origin or _dir_hash(dest)!=origin: print("diverged:",name)
EOF
diff /home/agent/.hermes/hermes-agent/skills/mlops/evaluation/evaluating-llms-harness/references/api-evaluation.md \
     /home/agent/.hermes/skills/mlops/evaluation/evaluating-llms-harness/references/api-evaluation.md | head -5
grep -rn "bundled_skill\|diff_bundled\|reset_bundled" /work/projects/hermes-curator-evolver/hermes_curator_evolver/ | wc -l   # 0
# skills index (surface exists, deployment 404s)
grep -n "HERMES_INDEX_URL\|class HermesIndexSource" /home/agent/.hermes/hermes-agent/tools/skills_hub.py
curl -sI https://hermes-agent.nousresearch.com/docs/api/skills-index.json | head -1            # 404
# upstream drift
gh api repos/NousResearch/hermes-agent/pulls/101316 --jq '.title,.merged'    # auto-prune 90d, open
gh api repos/NousResearch/hermes-agent/pulls/101266 --jq '.title,.merged'    # cron trigram -93.9%, open
gh api repos/NousResearch/hermes-agent/pulls/101237 --jq '.title,.merged'    # index +9 repos, 977 skills, open
gh api repos/NousResearch/hermes-agent/issues/101226 --jq '.title'           # bundled sync read-only bug
gh api "search/issues?q=repo:NousResearch/hermes-agent+curator+in:title+state:open" --jq '.items[0:6][]|.title'
gh api repos/NousResearch/hermes-agent/issues/101341 --jq '.title'           # revision pinning incident
# native curator staleness mechanics
grep -n "DEFAULT_STALE_AFTER_DAYS\|def apply_automatic_transitions" /home/agent/.hermes/hermes-agent/agent/curator.py
# competitor + ecosystem
gh api repos/cskwork/skill-curator --jq '.created_at,.pushed_at,.stargazers_count'
gh api repos/AMAP-ML/SkillClaw --jq '.stargazers_count,.pushed_at'
gh api repos/ComposioHQ/awesome-claude-skills --jq '.stargazers_count'      # 74287
# research + standards (via agent-reach Exa / direct)
#   arXiv 2608.07449 SkillProx; 2606.06079 SkillComposer; 2604.04804 SkillX
#   agentskills.io/specification re-fetched — unchanged vs cycle-5 pin (U49 holds)
#   dev.to/rulestack listing-budget post — skillOverrides/name-only, 5k/25k re-attachment budgets
```

Sources (internet, via agent-reach router: Exa MCP + `gh` + direct curl): NousResearch/hermes-agent PRs #101237/#101266/#101316/#101274/#101300 and issues #101226/#101341/#79295/#79311/#97243/#95441/#66648/#97964/#101294/#95387 (gh api, 2026-09-02 ~14:0xZ); runtime sources `/home/agent/.hermes/hermes-agent/{tools/skills_sync.py,tools/skills_hub.py,scripts/build_skills_index.py,agent/curator.py}` (live host read); arXiv 2608.07449 (SkillProx), 2606.06079 (SkillComposer), 2604.04804 (SkillX) via Exa; github.com/cskwork/skill-curator via Exa + gh; agentskills.io/specification via Exa; dev.to/rulestack listing-budget article via Exa.
