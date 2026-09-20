# hermes-curator-evolver — Roadmap

> Autonomously maintained by the roadmap sync (reliability-first). Items cite reproducible codebase signals; acceptance is proven by cited evidence.

**Vision**: A reliable, customer-friendly repository advanced by evidence-cited roadmap cycles owned by the autonomy loop

**Pillars**: reliability work outranks customer-experience work; every roadmap item cites reproducible codebase signals; acceptance is proven by cited evidence, never claimed

## Fleet context

- dependents (changes here affect): (host)
- graph: evidence-derived (imports/refs/deploy surfaces); advisory

## Open items

### Refactor 21 high-complexity function(s)
- id: `rm-001` | track: reliability | priority: 90.0 | status: candidate
- signals: reliability.complexity_hot:*, reliability.complexity_hot:hermes_curator_evolver/auto_evolve.py::_build_semantic_query, reliability.complexity_hot:hermes_curator_evolver/auto_evolve.py::_select_candidate_skill_names, reliability.complexity_hot:hermes_curator_evolver/auto_evolve.py::_walk_channel_skill_bindings, reliability.complexity_hot:hermes_curator_evolver/auto_evolve.py::install_auto_timer (+16 more)
- acceptance: Each flagged function is decomposed below the branch threshold with behavior locked by characterization tests
- evidence: ast-based branch-count check passes in CI

<!-- managed by hermes-roadmap render; do not edit by hand -->
