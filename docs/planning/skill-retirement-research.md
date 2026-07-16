# Skill Retirement Research Dossier

## Goal And Trigger

Identify global skills that are outdated, stale, duplicated, or plausibly low-use, then suggest safe removal or consolidation strategies. The original audit was read-only with respect to skill bodies; it evaluated the working tree, including an existing uncommitted consolidation, against Git `HEAD` (`0577fa86`, 2026-06-22).

## Current Verification (2026-07-14)

- The canonical tree contains 59 global `SKILL.md` files; Skillnet catalogs 155 global and project skills.
- `skillnet catalog lint` passes for all 155 catalogued skills.
- `skillnet doctor` reports no issues, and all configured project views report clean.
- These results supersede the historical counts below. The remainder of this dossier records the evidence and recommendations from the original audit snapshot.

## Historical Snapshot At Original Audit

- The working tree contains 54 global `SKILL.md` files; `HEAD` contains 105.
- The repository is too young for calendar age to prove staleness. Every tracked current skill was introduced between 2026-05-20 and 2026-06-16.
- Skillnet now has a trustworthy PostgreSQL-backed event table and normalized reporting path, but the live table was empty before this implementation. The Claude hook is now installed; Codex, OpenCode, and Crush still lack native emitters in the deployed integration, so their usage remains uncovered rather than zero.
- `skillnet catalog lint` passes for all 165 catalogued global and project skills.
- `skillnet doctor` is clean apart from an informational view-only `sccache-surface` entry. The repository-local Skillnet configuration has been centralized under `$XDG_CONFIG_HOME/skillnet/`.
- The checkout includes the active retirement work, the Rust/Nix stack
  consolidations, and the `evidence-first-research` replacement for the former
  generic research/orientation pair.

## Historical Evidence Inventory

| Evidence | What it establishes |
|---|---|
| `find global_skills -mindepth 2 -maxdepth 2 -name SKILL.md` | 54 current global skills. |
| `git ls-tree -r --name-only HEAD global_skills` | 105 global skills at `HEAD`. |
| `git log --all --follow -- <skill>/SKILL.md` | Current skills are only 25–52 days old; commit count is maintenance activity, not invocation frequency. |
| Cross-skill `rg` reference scan | Composition reachability is a weak low-use proxy only; direct leaf skills need not have inbound references. |
| `skillnet catalog lint` | Catalog metadata and routing hygiene pass for 165 skills. |
| `skillnet doctor` | No errors; one informational canix view-only skill remains. |
| Skillnet migration 004 and `usage` command | Adds normalized harness/source-event metadata, idempotent recording, and catalog-wide zero-filled reports. |
| PostgreSQL `can.public.skill_invocations` | Migration 004 is applied; the table had zero historical rows when queried. |
| `diff` of Codeberg CI skills | `berg-codeberg-ci` and `forgejo-codeberg-ci` have the same trigger and almost identical workflow. |
| `command -v berg`; `command -v fj` | `berg` is absent; `fj` is installed. |
| Comparison with `~/.codex/skills/.system` | `imagegen` is an exact duplicate; `openai-docs`, `plugin-creator`, `skill-creator`, and `skill-installer` shadow system skills. The first two are materially behind the installed system versions. |
| `git diff --name-status` | Existing uncommitted removals and their replacement names. |

## Existing Consolidation Status

| Existing change | Status | Assessment |
|---|---|---|
| `fix-clippy-errors` -> `rust-quality` | Superseded by the Rust domain consolidation | Clippy is now a quality profile; keep the focused behavior under `rust-quality`. |
| `workspace-check` -> `rust-workspace-check` | Implemented, uncommitted | Keep. Removes ambiguous global name and preserves the full workflow. |
| `simit-rust-project-init` split into router + ordinary/release children | Implemented, uncommitted | Keep. The two policies materially differ. |
| Planning/handoff family removal | Implemented, uncommitted | Keep after reference validation. Planning/model/dispatch ownership now belongs to the active harness. |
| `canix-yh-config` removal | Implemented, uncommitted | Keep if all durable canix configuration guidance has landed in `canix-cli`/project-local skills. |
| Plinth visual router and two target-specific skills added | Implemented, uncommitted | Keep; the overlapping `plinth-visual-audit` entry is retired. |

The planning/handoff family currently removed is: `consolidate-plan-sets`, `handoff-to-model`, `multi-phase-plan`, `mvp2prod`, `plan-and-verify`, `plan-handoff`, `plan-research`, and `renew-planning-tree`. The broken `multi-plan-research` link is also removed. These are obsolete under the repository's newly documented harness-owned planning boundary.

## Removal And Consolidation Candidates

### Remove now after validation: high confidence

| Skill | Evidence | Strategy |
|---|---|---|
| `berg-codeberg-ci` | Same trigger and near-identical procedure as `forgejo-codeberg-ci`; `berg` is not installed. | Fold its useful “prefer local targeting before web” language into `forgejo-codeberg-ci`, delete it, remove its catalog rule, regenerate catalogs. Restore only if `berg` becomes the canonical client. |
| `plinth-visual-audit` | New `plinth-visual-review` router plus personal/project children now own the same targets. The old skill mixes both workflows and has no inbound composition reference. | Move any unique prerequisite/report schema into the two children or a non-invokable shared reference, then delete the mixed skill. |
| `imagegen` | Its `SKILL.md` is byte-for-byte identical to the installed Codex system skill, and it explicitly calls helpers from the system skill directory. | Delete the global shadow and rely on the system skill. If repository portability is required, automate vendoring with a pinned upstream revision rather than exposing two identical skills. |
| `openai-docs` | Shadows the system skill and is materially behind it: missing current Codex-manual routing, API schema lookup, and newer fallback rules. | Delete the global shadow. Keep local additions only as a small extension skill with a distinct name and trigger; do not fork the upstream name. |
| `plugin-creator` | Shadows a materially newer system skill with changed valid defaults, validation, personal-marketplace behavior, and cache-busting workflow. | Delete the global shadow. Upstream any genuinely local policy into a separately named extension/reference. |
| `skill-installer` | Shadows the system skill and retains the older “restart Codex” behavior; the installed system skill says availability begins next turn. | Delete the global shadow. |
| `skill-creator` | Near-duplicate system shadow; current differences are minor wording/link drift and provide no local specialization. | Delete the global shadow. |

The five system-shadow removals are environment-sensitive. Before deletion, confirm all supported consumers supply the built-ins; otherwise mark the repository copies `compatibility` and exclude them from Codex routing instead of exposing duplicate names.

### Fold into an existing skill: medium confidence

| Skill | Fold target | Rationale and retained content |
|---|---|---|
| `ci-debugging` | `forgejo-codeberg-ci` + `runner` | Its generic `fj` flow belongs in the Codeberg troubleshooter; its runner services, images, daemon socket, timing heuristics, and failure anatomy belong in the runner reference. The present file duplicates both and uses older unit/image assumptions. |
| `rust-crate-rustdoc` | `rust-quality` and `rust-crate-release` | Public rustdoc is a quality profile; strict release docs/package semantics live in the release quality reference. |
| `rust-pr-preflight` | `rust-quality` and `rust-crate-release` | General checks live in `rust-quality`; publish/package/deny/audit gates remain release-only. |
| `forgejo-docs` | Router/recipe over `mdbook-docs` + `forgejo-pages` | It is primarily the composition of those two skills. Reduce it to a short router if automatic multi-skill selection is useful; otherwise document the composition in routing and delete it. |
| `forgejo-site` | Router/recipe over Plinth project site + `mdbook-docs` + `forgejo-pages` | Retain only combined-layout and base-path constraints that are not owned downstream. Its 197-line implementation is too large for an orchestration layer. |
| `host-a-healthcheck` | canix project-local `host-a-status`/`canix-host-status` | Catalog metadata already labels it a reference and points to those project skills. Move unique route/noise knowledge into the project-local owner, then make this a tiny compatibility router for one release before deletion. |

### Keep despite weak usage evidence

Do not remove these solely because they have zero inbound references: `simit-python-project-init`, `immich-provision`, `pink-raven-release`, `opencode-permissions`, `grouped-git-commits`, `pr-review-reply-style`, `tzu-goal-prompt`, and `plinth-project-foss-sweep`. They are leaf entry points with distinct user triggers. Rust leaves are intentionally consolidated into domain profiles by the current Rust-stack migration.

Keep the seven consolidated Nix domain skills composed by `nix-ultra`.
Nix-specific procedures now live as progressive-disclosure profiles; they
remain available without exposing every profile as an independently triggerable
catalog entry. The Rust leaves follow the same pattern, with module layout,
observability, and measured performance folded into `rust-quality` rather than
retaining a separate `rust-code-health` surface.

Do not add a generic cross-language housekeeping skill. The genuinely shared
contract is small (discover first, preserve the worktree, validate narrowly,
and report blockers), while the Rust and Nix procedures, tools, and safety
boundaries differ. A generic trigger would compete with the language-specific
skills without owning an independently executable workflow. Keep the common
contract in each stack's compact foundation reference and keep
`nix-code-health` as the coherent Nix-specific housekeeping entry point.

Keep reference skills such as `runner`, `repo-pages`, and `nixpkgs-pr-common`. Rust release doctrine now lives under `rust-crate-release/references/policy.md` rather than as a separate catalog entry.

## Work That Should Survive

- Preserve the active harness-ownership boundary added to `README.md` and planning/research skills.
- Preserve `rust-workspace-check`; Clippy is now the `rust-quality` profile.
- Preserve the split between ordinary Rust project initialization and strict crates.io release initialization.
- Preserve unique operational facts before folding: runner runner labels/services, docs.rs strict validation, Codeberg base-path rules, and host-a route/noise knowledge.
- Add aliases or one-release compatibility routers when removal changes a commonly used skill name.

## Blockers And Missing Artifacts

### Native coverage for non-Claude harnesses

- **Missing source:** native skill-activation events from deployed Codex, OpenCode, and Crush integrations.
- **Why required:** a zero-filled report is not evidence of non-use unless the harness was observed continuously. Transcript parsing and file-read inference are explicitly disallowed.
- **Upstream producer:** each harness integration, configured through InferNix; Skillnet provides the normalized `usage record` interface.
- **Regeneration/workflow:** add a native adapter that emits `skillnet usage record --harness ... --skill ... --session ... --event-id ...`; enable it through `services.infernix.skillTelemetry.harnesses.<name>` and canix Home Manager wiring.
- **Validation:** run a controlled activation in each harness, verify one PostgreSQL row per event, replay the same source event, and verify the count does not increase.

### Dirty consolidation provenance

- **Missing source:** a commit or plan identifying the owner and intended completion boundary of the existing 55-file worktree change.
- **Why required:** the audit can assess it but should not silently modify or commit another session's consolidation.
- **Upstream producer:** the session or user performing the current consolidation.
- **Recovery workflow:** inspect `git diff --name-status`, `git diff`, and the originating session/plan; then commit the coherent consolidation before starting a second removal wave.
- **Validation:** `git status --short` is clean after the intended commit, followed by `skillnet catalog lint` and `skillnet doctor`.

### Consumer availability for system skills

- **Missing source:** supported-harness matrix proving that every consumer supplies `imagegen`, `openai-docs`, `plugin-creator`, `skill-creator`, and `skill-installer` as built-ins.
- **Why required:** deleting shadows is safe for this Codex installation but might remove functionality from another generated view.
- **Upstream producer:** repository maintainer / Skillnet configuration owner.
- **Validation workflow:** enumerate configured consumers with `skillnet scope`/`skillnet view`, start each supported harness with the global shadows excluded, and verify the five skills remain discoverable from their system source.

## Risks And Constraints

- Low inbound reference count is not low use. Direct leaf skills often have no callers.
- Git commit count measures editing, not activation.
- Duplicate names are worse than duplicated text because skill selection may choose the stale shadow nondeterministically.
- Folding operational skills can create oversized monoliths. Shared facts should become non-invokable references; user-triggered entry points should remain concise routers.
- Generated `CATALOG.md`, `ROUTING.md`, and `SKILL_CONFLICTS.md` must be regenerated after structural changes.
- `skillnet doctor` is clean; the remaining `sccache-surface` message is informational and identifies a view-only skill that can be promoted separately.

## Candidate Next Steps

1. Finish and commit the already-started consolidation; do not mix a second retirement wave into its provenance.
2. Add temporary compatibility routes for renamed skills, then validate no live references remain.
3. Remove `berg-codeberg-ci` and the five Codex system shadows after the consumer matrix check.
4. Fold/delete `plinth-visual-audit`, then consolidate the medium-confidence pairs one pair per commit.
5. Regenerate catalogs and run `skillnet catalog lint` after every structural batch.
6. Keep SynDB generated views synchronized with the canonical Skillnet workflow; they are currently clean, and future `skillnet doctor` errors remain release blockers.
7. Add structured activation telemetry and revisit low-use retirement after a 90-day observation window.

The Rust-stack consolidation is a separate follow-up migration: it reduces the
36 Rust entry points to nine domain/release/workspace skills, keeps detailed
procedures as progressive-disclosure references, and must regenerate catalogs
after the old leaf names are removed.

## Open Decisions For The User

- Whether this repository must support harnesses that do not ship Codex's five system skills.
- Whether compatibility routers should live for one release or names may be removed immediately.
- Whether `forgejo-docs` and `forgejo-site` should remain explicit convenience routers or be represented only as catalog compositions.
