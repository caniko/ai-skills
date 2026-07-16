---
name: nix-ultra
description: Master orchestrator for improving an entire Nix repository, including flakes, NixOS, Home Manager, packages, secrets, and checks. Use when asked to deeply audit, clean up, harden, or make a Nix repository idiomatic.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Nix Ultra

Use this skill for whole-repository work. Focused requests should route to the
smallest domain skill and profile.

## Shared contract

Load [foundation.md](references/foundation.md) before discovery. It owns
source-integrity, dirty-tree, formatter, evaluation, blocker, and reporting
rules. Read [concerns.toml](references/concerns.toml) as the single source of
truth for stages, profiles, preflight signals, thresholds, shape gates, and
validation modes.

## Workflow

1. Detect flake/non-flake shape, NixOS hosts, Home Manager configs, overlays,
   packages, secrets, checks, formatter, CI, and deployment surfaces.
2. Run the read-only baseline from `foundation.md`. Stop when a foundational
   artifact is missing or evaluation is already red without a source-backed
   repair path.
3. Score registry concerns and produce a run list. Apply `low` sensitivity as
   threshold ×3, `medium` as the recorded threshold, and `high` as threshold
   1. Honor `--only`, `--skip`, project-shape gates, and `--plan-first`.
4. Load only the matching domain skills: `nix-correctness`, `nix-security`,
   `nix-module-design`, `nix-flake-architecture`, `nix-code-health`, and
   `nix-test-gates`.
5. Run correctness, security, module architecture, flake architecture, code
   health, then gates. Validate after every profile and never continue with a
   red tree unless diagnosis is the explicit task.
6. Re-score after each stage and converge for at most three iterations. Stop
   when quantitative signals are clear and qualitative profiles report no
   remaining work; report deferred work explicitly at the cap.
7. Run the final gate from `foundation.md` and report concerns, validation,
   blockers, residual risks, and deployment follow-ups.

## Boundaries

This is general Nix/NixOS/Home Manager guidance. Use `nixpkgs-*` skills for
nixpkgs pull requests and `canix-cli` or project-local deployment skills for
host-specific deployment workflows.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
