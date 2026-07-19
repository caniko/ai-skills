---
name: rust-ultra
description: Orchestrate aggressive Rust workspace modernization with necessary breaking changes and in-repo migration. Use for deep audits, hardening, or whole-codebase quality work.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

# Rust Ultra

Use this skill only for whole-codebase work. For a focused request, route to
the smallest domain skill and profile instead of running the full pass.

## Shared contract

Load [ultra-system-reference](.skillnet/deps/ultra-system-reference/SKILL.md), then
[foundation.md](references/foundation.md), before discovery. The shared ultra
reference owns profile routing, run artifacts, delegation receipts,
convergence, and terminal states. The Rust foundation owns source integrity,
toolchains, dirty-tree handling, technical gates, and blocker reporting.

Treat [concerns.toml](references/concerns.toml) as a profile-granular registry.
Validate it with the shared launcher before surveying the target. Qualitative
profiles always receive a review; their scores prioritize work but never skip
it.

## Change authority

Default to `modernize` mode. A whole-codebase Rust-ultra improvement or fix
request authorizes breaking source, public API, configuration, schema, feature,
and module-layout changes when they materially improve correctness, safety,
cohesion, reuse, or maintainability. Migrate every in-repository caller, test,
fixture, example, and document in the same pass. Record downstream migration
guidance instead of preserving a weaker design solely for compatibility. An
audit or plan-only request remains read-only, but its recommendations use the
same modernize standard.

Use `compatibility` mode only when the user explicitly requests it or a
repository policy names an external compatibility contract. Even then, apply
all non-breaking improvements and record blocked breaking work. Modernize mode
does not authorize publication, deployment, destructive data migration, or
changes unrelated to codebase quality.

## Workflow

### Phase 1: frontier planning

1. Use a frontier-class planner at high effort or greater. Validate the
   registry, detect workspace shape, wrappers, Nix/simit tooling,
   async/runtime use, public surface, features, unsafe code, and release scope.
2. Run the read-only baseline from `foundation.md`. Stop on a red tree unless
   the failure has a source-backed repair path that belongs in the plan.
3. Produce `.ultra-out/survey.initial.json` and initialize the profile ledger.
   Record `modernize` unless the compatibility exception above applies.
4. Load every matching domain skill and perform enough read-only analysis to
   plan every profile. The plan must explicitly cover trait hierarchy and
   boundary analysis, duplicate-behavior/DRY extraction, type cohesion and
   struct granularization, public API migration, correctness, security, and
   dependency work wherever applicable. File splitting alone is never a
   structural plan.
5. Write and validate `.ultra-out/plan.json` using the shared lifecycle
   contract. Freeze its hash before source edits. Stop here only for an audit
   or plan-only request.

### Phase 2: efficient-model build

6. Give the frozen work packages to efficient-model builders. Run correctness,
   security, architecture/API design, quality, then dependencies. Require one
   exact profile disposition in the owning stage receipt; stage receipts must
   collectively cover every profile once. Migrate every in-repository consumer
   of breaking changes.
7. In modernize mode, act on material candidates. Do not mark a threshold-
   triggered oversized file/type, concrete boundary, duplicate cluster, or
   deficient public API `reviewed-clean` with “retain for this pass.” Refactor
   it, prove a documented exceptional shape, or leave it deferred/blocked.
8. Verify changed behavior after each profile, run one full gate per changed
   stage, re-survey, and converge for at most three iterations. Material work
   outside the frozen plan returns `replan-required` to the frontier planner.
9. Write and validate `.ultra-out/build.json` against the integrated source.
   Run the final gate from `foundation.md`, then write source-bound score
   history, stage receipts, `final-validation.json`, and the evidence manifest
   before frontier review.

### Phase 3: same-frontier review

10. Return the plan, build, diff, ledger, receipts, migrations, and gates to
    the exact frontier model identity that planned the run, in an independent
    review context at equal or lower effort. It must check missed architecture,
    trait topology, DRY extraction, giant structs/types, public API quality,
    migration completeness, and every profile obligation.
11. Send in-plan corrections back to the efficient builder; replan material
    scope changes. Repeat until the frontier reviewer approves or records an
    honest non-success verdict.
12. Validate `review.json`, then validate the final ledger with all lifecycle
    artifacts. Report the precise terminal state, profile obligations,
    breaking changes and migration notes, validation, approved exclusions,
    blockers, residual issues, and release follow-ups separately.

## Boundaries

Do not perform crates.io preparation or publication here. Use
`rust-crate-release` for that workflow. Use `rust-project-flake` for project
Nix infrastructure and `rust-workspace-check` for a single-crate workspace
decision.

## Solution Placement

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
