# hermes-curator-evolver — Roadmap

> Autonomously maintained by the roadmap sync (reliability-first). Items cite reproducible codebase signals; acceptance is proven by cited evidence.

**Vision**: A reliable, customer-friendly repository advanced by evidence-cited roadmap cycles owned by the autonomy loop

**Pillars**: reliability work outranks customer-experience work; every roadmap item cites reproducible codebase signals; acceptance is proven by cited evidence, never claimed

## Open items

### Refactor 20 high-complexity function(s)
- id: `rm-001` | track: reliability | priority: 90.0 | status: candidate
- signals: reliability.complexity_hot:hermes_curator_evolver/auto_evolve.py::_build_semantic_query, reliability.complexity_hot:hermes_curator_evolver/auto_evolve.py::_select_candidate_skill_names, reliability.complexity_hot:hermes_curator_evolver/auto_evolve.py::_walk_channel_skill_bindings, reliability.complexity_hot:hermes_curator_evolver/auto_evolve.py::install_auto_timer, reliability.complexity_hot:hermes_curator_evolver/auto_evolve.py::run_auto_evolve (+15 more)
- acceptance: Each flagged function is decomposed below the branch threshold with behavior locked by characterization tests
- evidence: ast-based branch-count check passes in CI

### Add test coverage for 2 untested module(s)
- id: `rm-003` | track: reliability | priority: 86.0 | status: candidate
- signals: reliability.no_tests:hermes_curator_evolver/hooks.py, reliability.no_tests:hermes_curator_evolver/tools.py
- acceptance: Every module in ['hermes_curator_evolver/hooks.py', 'hermes_curator_evolver/tools.py'] has a corresponding test file with at least one passing test
- evidence: CI: pytest collects the new test files and they pass

### Refresh stale top-level documentation
- id: `rm-002` | track: reliability | priority: 43.0 | status: candidate
- signals: reliability.stale_doc:README.md
- acceptance: Docs regenerated/updated; staleness detector reports 0 signals
- evidence: inference.stale_docs returns [] for the repo

<!-- managed by hermes-roadmap render; do not edit by hand -->
