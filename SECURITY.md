# Security Policy

## Reporting a vulnerability

This repository (codeo1io/hermes-curator-evolver) has issues disabled.
Report suspected vulnerabilities by opening a security advisory:

1. Go to the repository's **Security** tab → **Advisories** → **Report a new vulnerability**,
   or open a draft security advisory directly at
   `https://github.com/codeo1io/hermes-curator-evolver/security/advisories/new`.

If advisories are not enabled at the time you read this, contact a maintainer
through the [codeo1io](https://github.com/codeo1io) GitHub organization (see
the README's Support section); do **not** open a public
issue (issues are disabled) and do **not** post vulnerability details in
public.

Please include: affected commit or release, a minimal reproduction, and the
impact you believe applies. We aim to respond within 7 days.

## Credential handling (roadmap U77)

This project processes session-derived tool results that may contain
credential-shaped strings. The pipeline defense-in-depth, as of maintenance
cycle 9:

- **At ingest** — tool-result previews (`storage._compact`) and serialized
  arguments (`storage._json_dumps`) are scrubbed of credential-shaped
  strings before they are written to the evidence store.
- **At publication** — every embed point that writes evidence previews into
  a `SKILL.md` or a `references/` spill file (`auto_evolve`) re-scrubs the
  preview before writing, so pre-fix rows in an older store cannot leak.
- **At validation** — a `SKILL.md` whose content still contains a
  credential-shaped string fails validation as a named error, so guarded
  apply rolls it back instead of publishing it.
- **Disclosed** — scrub counts appear in `auto-run --format json`
  (`summary.credentials_scrubbed`), backfill summaries
  (`credentials_scrubbed`), and the human CLI output.

Known limitations (honesty disclosure):

- The scrubber is pattern-based (GitHub `ghp_`/`github_pat_`, Anthropic/
  OpenAI `sk-`-family, AWS access keys, Slack tokens, generic
  `token=`/`password=` assignments). A credential in an unusual shape can
  still pass through; treat the pipeline as risk reduction, not a guarantee.
- The repository was public at the time this policy was added. GitHub
  secret scanning and push protection are enabled; a historical doc records
  one synthetic `ghp_`-shaped test token verbatim — it is annotated in place
  (decision KTD39), raises zero secret-scanning alerts, and was never
  issued to a real account.

## Scope

In scope: the Python package `hermes_curator_evolver`, its CLI, the CI
workflows, and the documentation tree. Out of scope: the upstream Hermes
agent host itself, and anything reachable only by an attacker who already
controls your `~/.hermes` directory (the tool operates on trusted local
state by design).
