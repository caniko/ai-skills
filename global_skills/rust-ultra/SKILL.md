---
name: rust-ultra
description: Orchestrate a complete Rust crate/workspace improvement pass. Use for deep audits, hardening, cleanup, or whole-codebase quality work.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Rust Ultra

Use this skill only for whole-codebase work. For a focused request, route to
the smallest domain skill and profile instead of running the full pass.

## Shared contract

Load [ultra-system-reference](../ultra-system-reference/SKILL.md), then
[foundation.md](references/foundation.md), before discovery. The shared ultra
reference owns profile routing, run artifacts, delegation receipts,
convergence, and terminal states. The Rust foundation owns source integrity,
toolchains, dirty-tree handling, technical gates, and blocker reporting.

Treat [concerns.toml](references/concerns.toml) as a profile-granular registry.
Validate it with the shared launcher before surveying the target. Qualitative
profiles always receive a review; their scores prioritize work but never skip
it.

## Workflow

1. Validate the registry. Detect the crate/workspace shape, available wrappers, Nix/simit tooling,
   async/runtime use, public library surface, features, unsafe code, and
   release scope.
2. Run the deterministic baseline from `foundation.md`. Stop on a red tree.
3. Produce `.ultra-out/survey.initial.json` with the shared survey and
   initialize `.ultra-out/profile-ledger.json`. Apply `low` sensitivity as
   threshold ×3, `medium` as recorded, and `high` as threshold 1. Respect
   explicit scope and approved exclusions. With `--plan-first`, stop only
   after presenting the complete profile ledger and ordered run list.
4. Load the matching domain skill for every applicable profile:
   `rust-correctness`, `rust-security`, `rust-api-design`, `rust-quality`,
   and `rust-dependencies`.
5. Run correctness, security, architecture/API design, quality, then
   dependencies. Require one receipt per profile. In particular, produce the
   trait topology, duplicate-behavior clusters, and type-cohesion dispositions
   required by the structural profile procedures; file splitting is not a
   substitute for type decomposition.
6. Verify changed behavior after each profile and run the relevant full stage
   gate before moving on. A no-change profile still needs analytical evidence.
7. Re-survey after each changed stage and converge for at most three
   iterations. Use `incomplete-convergence-cap` when open work remains at the
   cap.
8. Validate the final ledger with `ultra-system-reference`, then run the final
   gate from `foundation.md`. Report the precise terminal state, profile
   coverage, validation, approved exclusions, blockers, residual issues, and
   release follow-ups separately.

## Boundaries

Do not perform crates.io preparation or publication here. Use
`rust-crate-release` for that workflow. Use `rust-project-flake` for project
Nix infrastructure and `rust-workspace-check` for a single-crate workspace
decision.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
