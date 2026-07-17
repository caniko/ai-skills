---
name: rust-ultra
description: Orchestrate a complete Rust crate/workspace improvement pass. Use for deep audits, hardening, cleanup, or whole-codebase quality work.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Rust Ultra

Use this skill only for whole-codebase work. For a focused request, route to
the smallest domain skill and profile instead of running the full pass.

## Shared contract

Load [foundation.md](references/foundation.md) before discovery. It owns the
common source-integrity, toolchain, dirty-tree, verification, blocker, and
reporting rules. Read [concerns.toml](references/concerns.toml) as the single
source of truth for concern routing, preflight signals, thresholds, stages,
shape gates, and validation modes.

## Workflow

1. Detect the crate/workspace shape, available wrappers, Nix/simit tooling,
   async/runtime use, public library surface, features, unsafe code, and
   release scope.
2. Run the deterministic baseline from `foundation.md`. Stop on a red tree.
3. Evaluate every registry concern and produce a scored run list. Apply `low`
   sensitivity as threshold ×3, `medium` as the recorded threshold, and `high`
   as threshold 1. Respect explicit scope, exclusions, project-shape gates,
   and `--plan-first`.
4. Load the matching domain skill only for concerns that run:
   `rust-correctness`, `rust-security`, `rust-api-design`, `rust-quality`,
   and `rust-dependencies`.
5. Run in registry order: correctness, safety/security, API design, quality,
   then dependencies. Verify after each profile.
6. Re-score after each stage and converge for at most three iterations. Stop
   when quantitative signals are clear and qualitative profiles report no
   remaining work. Log deferred work; never silently cap the pass.
7. Run the final gate from `foundation.md` and report scores, skipped work,
   commits, residual issues, and release follow-ups separately.

## Boundaries

Do not perform crates.io preparation or publication here. Use
`rust-crate-release` for that workflow. Use `rust-project-flake` for project
Nix infrastructure and `rust-workspace-check` for a single-crate workspace
decision.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
