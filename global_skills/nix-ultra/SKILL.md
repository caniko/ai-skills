---
name: nix-ultra
description: Orchestrate a complete Nix improvement pass across flakes, NixOS, Home Manager, packages, secrets, and checks. Use for deep audits, hardening, or cleanup.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

# Nix Ultra

Use this skill for whole-repository work. Focused requests should route to the
smallest domain skill and profile.

## Shared contract

Load [ultra-system-reference](.skillnet/deps/ultra-system-reference/SKILL.md), then
[foundation.md](references/foundation.md), before discovery. The shared ultra
reference owns profile routing, run artifacts, delegation receipts,
convergence, and terminal states. The Nix foundation owns source integrity,
dirty-tree handling, evaluation gates, and blocker reporting.

Treat [concerns.toml](references/concerns.toml) as a profile-granular registry.
Validate it with the shared launcher before surveying the target. Qualitative
profiles always receive a review; their scores prioritize work but never skip
it.

## Workflow

### Phase 1: frontier planning

1. Use a frontier-class planner at high effort or greater. Validate the
   registry and detect flake/non-flake shape, NixOS hosts, Home Manager,
   overlays, packages, secrets, checks, formatter, CI, and deployment surfaces.
2. Run the read-only baseline from `foundation.md`. Stop when a foundational
   artifact is missing or evaluation is already red without a source-backed
   repair path.
3. Produce `.ultra-out/survey.initial.json`, initialize the profile ledger,
   load every matching domain skill, and perform enough read-only analysis to
   design work for every profile.
4. Write complete work packages for correctness, security, module
   architecture, flake architecture, code health, and gates. Include output
   compatibility, module/API migrations, evaluation surfaces, deployment risk,
   and validation. Write and validate `.ultra-out/plan.json`; freeze its hash
   before source edits. Stop here only for an audit or plan-only request.

### Phase 2: efficient-model build

5. Give the frozen work packages to efficient-model builders. Run correctness,
   security, module architecture, flake architecture, code health, then gates.
   Require one exact profile disposition in the owning stage receipt; stage
   receipts must collectively cover every profile once. Migrate every
   in-repository consumer.
6. Validate changed evaluation surfaces after every profile; a no-change
   profile still needs analytical evidence. Run one full gate per changed
   stage, re-survey, and converge for at most three iterations. Material work
   outside the frozen plan returns `replan-required` to the frontier planner.
7. Write and validate `.ultra-out/build.json` against the integrated source.
   Run the final gate from `foundation.md`, then write source-bound score
   history, stage receipts, `final-validation.json`, and the evidence manifest
   before frontier review.

### Phase 3: same-frontier review

8. Return the plan, build, diff, ledger, receipts, migrations, and gates to the
   exact frontier model identity that planned the run, in an independent review
   context at equal or lower effort. Review all profile coverage, architecture,
   output preservation or authorized breakage, secrets handling, migration
   completeness, and deployment risk.
9. Send in-plan corrections back to the efficient builder; replan material
   scope changes. Repeat until the frontier reviewer approves or records an
   honest non-success verdict.
10. Validate `review.json`, then validate the final ledger with all lifecycle
    artifacts. Report the precise terminal state, profile coverage, validation,
    approved exclusions, blockers, residual risks, and deployment follow-ups.

## Boundaries

This is general Nix/NixOS/Home Manager guidance. Use `nixpkgs-*` skills for
nixpkgs pull requests and `canix-cli` or project-local deployment skills for
host-specific deployment workflows.

## Solution Placement

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
