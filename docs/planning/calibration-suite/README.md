# Calibration suite — full surface for `multi-phase-plan`

> **Recommended Codex model for orchestration: GPT 5.5 high**
>
> Builds on the shipped foundation (skillnet 0.3.0 already provides
> the CLI surface, sidecar ingest, Postgres backend, HM module, and
> crates.io publication). This plan adds the **helper surface and
> orchestration** skillnet needs to be a fully self-contained
> calibration loop — the heuristics catalog as a first-class
> concept, evaluation/init/shape-hash helpers, a walkthrough
> orchestrator, documented JSON contracts — then lands the ai-skills
> integration against the cleaner surface. Substantive design
> content lives in phases 01 (catalog model), 06 (SKILL.md rewrite),
> and 04 (walkthrough UX); the rest is mechanical wiring.

## Supersedes

`docs/planning/calibration-loop/` covered the same end-state but
predated the discovery that skillnet 0.3.0 already ships phases
01–04, 07, 08 of that plan. This suite focuses on the remaining
work and adds the helper-command surface that pushes evaluation
into skillnet (so SKILL.md prose stops re-implementing what should
be a CLI call). The prior `docs/planning/calibration-loop/` tree has
been retired; this suite is the active plan and audit trail.

## Scope

Two repositories, two halves:

**skillnet (`~/canix/Projects/skillnet`, published at
`ssh://git@codeberg.org/caniko/skillnet.git`):**

- Heuristics catalog as a first-class concept in code: trigger
  definitions, default thresholds, runtime-mutable thresholds
  table in Postgres, catalog API consumed by every helper.
- Helper commands: `init`, `eval`, `meta-heuristics`,
  `shape-hash`, `heuristics list|show`.
- Documented & SemVer-stable JSON schema for `analyze --format json`;
  formalize the `surprises` `dead-weight:` / `missed-signal:`
  parser (already present, needs spec).
- `walkthrough` orchestrator that runs
  `analyze → propose → decide → export-changelog` in one
  guided session.
- Release 0.4.0 with the above; bump HM module if any new options
  appear; refresh the docs/ mdBook.

**ai-skills (`~/canix/Projects/ai-skills`):**

- `global/multi-phase-plan/SKILL.md` rewrite: drop the 3–8 phase
  cap, add per-phase shape rules, document the heuristics catalog
  (cross-referencing skillnet as source-of-truth for live
  thresholds), document sidecar schema, tag conventions, surprises
  convention, meta-heuristics.
- End-of-plan and end-of-verify hooks (single `skillnet calibration
  init <plan-dir> && skillnet calibration record <plan-dir>` call;
  the catalog evaluation that used to be agent prose is now `eval`).
- `calibrate` mode body delegates to `skillnet calibration
  walkthrough`.
- Flavor wrappers propagated; ai-skills flake consumes published
  skillnet via HM module re-export; legacy Rust sources removed.

## Current state (audited)

- **skillnet 0.3.0** is on user PATH; configured for Postgres
  (`postgres:///can?host=/run/postgresql`); `skillnet calibration
  migrate` succeeded; all 14 calibration subcommands ship.
- **Sidecar** (`src/calibration/sidecar.rs`) matches the planned
  schema at `schema_version = 1` field-for-field.
- **`surprises` parser** in `src/calibration/analyze.rs` already
  handles `dead-weight:` and `missed-signal:` prefixes (verified
  at lines 313–315 and 511+).
- **HM module** (`nix/hm-module.nix`) supports dual backend,
  declarative TOML at `$XDG_CONFIG_HOME/skillnet/`, urlFile for
  secret Postgres URLs.
- **ai-skills** still has the unchanged `multi-phase-plan`
  SKILL.md (3–8 cap, no hooks, no calibrate mode). Git status
  shows old Rust sources are deleted-staged but consumption isn't
  wired yet.

## Design choices locked here

| Decision | Value |
|---|---|
| Catalog source-of-truth | skillnet code (defaults) + Postgres `heuristic_thresholds` table (runtime mutable) |
| Threshold mutation path | `analyze` → `propose` → `decide accept` writes db; `export-changelog` formats human-readable block |
| Backend assumption | Postgres only for this user (`SKILLNET_DATABASE_URL` resolves via HM module); CLI hides backend so plan prose stays backend-agnostic |
| Helper command set | `init`, `eval`, `meta-heuristics`, `shape-hash`, `heuristics list|show` |
| Orchestrator | `skillnet calibration walkthrough` (one command for the calibrate-mode workflow) |
| Sidecar schema bump | Stay at `schema_version = 1` (no breaking changes; add fields only as optional) |
| Crate version after this suite | `0.4.0` |
| Catalog list output | JSON-by-default for tooling; table for humans |
| Calibrate-mode placement | Sister mode in ai-skills' base skill (unchanged) |
| Old `calibration-loop` plan | Retired on verify success of this suite |

## Phase table

| Phase | File | Repo | Depends on | Touches | Can parallel with |
|---|---|---|---|---|---|
| 01 | [01-skillnet-heuristics-catalog.md](./01-skillnet-heuristics-catalog.md) | skillnet | — | `src/calibration/catalog/`, `src/calibration/mod.rs`, `data/multi-phase-plan/schema-pg/*.sql` | 06 |
| 02 | [02-skillnet-helper-commands.md](./02-skillnet-helper-commands.md) | skillnet | 01 | `src/calibration/{init,eval,meta,shape,heuristics_cmd}.rs`, `src/cli/args.rs`, `src/commands/calibration.rs` | 03, 06 |
| 03 | [03-skillnet-analyze-schema-surprises-doc.md](./03-skillnet-analyze-schema-surprises-doc.md) | skillnet | 01 | `src/calibration/analyze.rs` (doc + schema), `docs/src/calibration/json-schema.md` | 02, 06 |
| 04 | [04-skillnet-walkthrough-orchestrator.md](./04-skillnet-walkthrough-orchestrator.md) | skillnet | 02, 03 | `src/calibration/walkthrough.rs`, `src/cli/args.rs`, `src/commands/calibration.rs` | 07 |
| 05 | [05-skillnet-0.4-release.md](./05-skillnet-0.4-release.md) | skillnet | 04 | `Cargo.toml`, `CHANGELOG.md`, `nix/hm-module.nix`, `docs/src/**`, `.forgejo/workflows/*` | — |
| 06 | [06-ai-skills-skill-rewrite.md](./06-ai-skills-skill-rewrite.md) | ai-skills | — | `global/multi-phase-plan/SKILL.md` | 01, 02, 03 |
| 07 | [07-ai-skills-hooks-calibrate-mode.md](./07-ai-skills-hooks-calibrate-mode.md) | ai-skills | 02, 03, 04, 06 | `global/multi-phase-plan/SKILL.md` | — |
| 08 | [08-ai-skills-consumption.md](./08-ai-skills-consumption.md) | ai-skills | 05, 07 | `flake.nix`, `flake.lock`, `global/multi-phase-plan-{codex,claude,mixed}/SKILL.md`, `README.md`, `docs/planning/calibration-loop/` (retire) | — |

## Parallelism layer

**Wave 0**:
- 01 — skillnet heuristics catalog. Foundation; nothing depends on
  external work.
- 06 — ai-skills SKILL.md rewrite. Pure docs in a different repo;
  no code dep. Cross-references the catalog defaults from 01 but
  the *values* can be filled in late.

**Wave 1** (after 01):
- 02 — Helper commands. Consumes catalog API.
- 03 — Analyze JSON schema + surprises spec. Consumes catalog
  trigger names but is mostly doc + minor doc-test additions.
- 02 and 03 in parallel.

**Wave 2** (after 02 + 03):
- 04 — `walkthrough` orchestrator. Needs `analyze --format json`
  schema documented and helper commands stable.
- 07 — ai-skills hooks + calibrate mode. Can start once 02+03
  ship; the calibrate mode references `walkthrough` so cleanest
  to land after 04 too, but doc-level forward-reference is OK.

**Wave 3** (after 04):
- 05 — skillnet 0.4.0 release. Mechanical via
  `rust-crate-release-chaperone`.

**Wave 4** (after 05 + 07):
- 08 — ai-skills consumption. Final flake bump, flavor
  propagation, calibration-loop retirement.

## Serialization points

| File | Phases | Order | Recovery |
|---|---|---|---|
| `skillnet/src/cli/args.rs` | 02, 04 | 02 inserts under `// HELPER COMMANDS`; 04 inserts under `// WALKTHROUGH` | trivial merge |
| `skillnet/src/commands/calibration.rs` | 02, 04 | same | match-arm conflicts only |
| `skillnet/src/calibration/mod.rs` | 01, 02, 04 | 01 first; 02/04 add `pub mod …` lines at end | additive |
| `skillnet/nix/hm-module.nix` | 05 only | n/a | — |
| `ai-skills/global/multi-phase-plan/SKILL.md` | 06 → 07 | 06 rewrites; 07 inserts hooks + calibrate sections | reread post-06 |
| `ai-skills/flake.nix` | 08 only | n/a | — |

## Shared-file lockstep

This plan's heuristic catalog (built in 01, documented in 06) would
itself flag these as triggers if recorded:

- **Shared-file contention**: `skillnet/src/cli/args.rs`,
  `skillnet/src/commands/calibration.rs`, and
  `skillnet/src/calibration/mod.rs` touched by 01, 02, 04.
- **Infra SPOF**: 01 (the catalog API + schema migration) gates
  02, 03, 04, 06's content authority, and 07's hook references.
  Any wrong call here cascades.
- **Long serial chain**: 01 → 02 → 04 → 05 → 08 (depth 5). Every
  downstream phase smoke-tests the prior phase's surface in its
  Acceptance criteria.

## Whole-set acceptance criteria

- [ ] `skillnet calibration heuristics list --format json` returns
      the canonical catalog with default thresholds, source
      (default or db override), and section/category metadata.
- [ ] `skillnet calibration init <plan-dir>` writes a valid
      `.calibration.json` from a plan README + phase files.
- [ ] `skillnet calibration eval <plan-dir>` returns trigger rows
      matching what `record` would persist.
- [ ] `skillnet calibration meta-heuristics <plan-dir>` returns
      the firing meta-heuristics as JSON.
- [ ] `skillnet calibration shape-hash <plan-dir>` returns a
      deterministic hash for the same plan inputs across runs.
- [ ] `skillnet calibration analyze --format json` output is
      documented under `docs/src/calibration/json-schema.md` with
      a SemVer commitment; `analyze.rs` has a corresponding doc
      test.
- [ ] `skillnet calibration walkthrough` runs end-to-end
      (analyze → interactive propose → decide → export-changelog)
      with `--non-interactive` mode for scripted use.
- [ ] `skillnet --version` reports `0.4.0`; the crate is
      published; HM module accepts any new options without
      breaking existing configs.
- [ ] `ai-skills/global/multi-phase-plan/SKILL.md` has the
      per-phase shape rules, heuristics catalog (with cross-
      reference to `skillnet calibration heuristics list`),
      meta-heuristics, sidecar schema, tag conventions, surprises
      convention, the end-of-plan + end-of-verify hooks, the
      calibrate mode delegating to `walkthrough`, and the
      changelog footer.
- [ ] Three flavor wrappers list `plan`/`verify`/`calibrate`.
- [ ] `ai-skills/flake.nix` has `inputs.skillnet` pointing at
      Codeberg and re-exports the HM module.
- [ ] `docs/planning/calibration-loop/` is git-rm'd (retired).
- [ ] Round-trip smoke: write this plan's sidecar via `init`,
      `record`, `verify`, observe rows in Postgres
      `calibration` schema.
- [ ] `cargo test`, `cargo clippy --all-targets -- -D warnings`,
      `cargo fmt --check`, `nix flake check` clean in both repos.

## Global constraints

- The Postgres backend is what this user runs. Helper commands
  must not assume backend; they all go through skillnet's existing
  `Db` abstraction (which already picks `db_postgres.rs` vs
  `db.rs`).
- Heuristics catalog defaults ship in code; runtime overrides
  live in a `heuristic_thresholds` table seeded on migrate.
  Changing a threshold via the calibration loop updates the
  table; new installs see the defaults.
- The skill body never writes Postgres directly. All ingest goes
  through `skillnet calibration <verb>`.
- Helper commands are part of the public CLI surface from 0.4.0;
  additions later are non-breaking, removals are breaking.
- `analyze --format json` schema is SemVer-stable from 0.4.0.
  Changes require a major bump.

## Routing summary

| Phase | Repo | Layout | Model | Blocking? |
|---|---|---|---|---|
| 01 | skillnet | flat | 5.5 high | yes (foundation) |
| 02 | skillnet | flat | 5.5 medium | yes (gates 04, 07) |
| 03 | skillnet | flat | 5.5 medium | yes (gates 04, 07) |
| 04 | skillnet | flat | 5.5 medium | yes (gates 05) |
| 05 | skillnet | flat | 5.5 medium | yes (gates 08) |
| 06 | ai-skills | flat | 5.5 high | no (parallel) |
| 07 | ai-skills | flat | 5.5 medium | yes (gates 08) |
| 08 | ai-skills | flat | 5.5 medium | no (final) |

No `max` phases. Phase 05 (crate publish, non-reversible) is the
closest; mitigated by `rust-crate-release-chaperone`.

## Skills available to leverage

Per the existing `ai-skills` catalog:

- 05 release: `rust-crate-release-chaperone`,
  `rust-crate-release-prep`, `rust-crate-publish-workflow`,
  `rust-crate-quality-gates`, `rust-crate-forgejo-release-ci`,
  `berg-codeberg-ci`.
- 05 docs refresh: `mdbook-docs`, `rust-crate-forgejo-docs`.
- 03 schema docs: `mdbook-docs` for the JSON schema page if it
  lands inside the existing `docs/` mdBook.
- 08 cleanup of `calibration-loop/`: `retire-docs-planning`.

## Reference

- Originating audit: skillnet 0.3.0 ships phases 01–04, 07, 08 of
  the prior `calibration-loop` plan; this suite covers the
  remaining ai-skills work plus the helper surface that pushes
  evaluation into skillnet.
- Sister (superseded) plan: `docs/planning/calibration-loop/`.
- Skillnet repo: `ssh://git@codeberg.org/caniko/skillnet.git`,
  local at `~/canix/Projects/skillnet`.
- Ai-skills repo: `~/canix/Projects/ai-skills`.
- Live skillnet docs: `skillnet --help`, `skillnet calibration
  --help`.
