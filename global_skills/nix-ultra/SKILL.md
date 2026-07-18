---
name: nix-ultra
description: Orchestrate a complete Nix improvement pass across flakes, NixOS, Home Manager, packages, secrets, and checks. Use for deep audits, hardening, or cleanup.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Nix Ultra

Use this skill for whole-repository work. Focused requests should route to the
smallest domain skill and profile.

## Shared contract

Load [ultra-system-reference](../ultra-system-reference/SKILL.md), then
[foundation.md](references/foundation.md), before discovery. The shared ultra
reference owns profile routing, run artifacts, delegation receipts,
convergence, and terminal states. The Nix foundation owns source integrity,
dirty-tree handling, evaluation gates, and blocker reporting.

Treat [concerns.toml](references/concerns.toml) as a profile-granular registry.
Validate it with the shared launcher before surveying the target. Qualitative
profiles always receive a review; their scores prioritize work but never skip
it.

## Workflow

1. Validate the registry. Detect flake/non-flake shape, NixOS hosts, Home Manager configs, overlays,
   packages, secrets, checks, formatter, CI, and deployment surfaces.
2. Run the read-only baseline from `foundation.md`. Stop when a foundational
   artifact is missing or evaluation is already red without a source-backed
   repair path.
3. Produce `.ultra-out/survey.initial.json` with the shared survey and
   initialize `.ultra-out/profile-ledger.json`. Apply `low` sensitivity as
   threshold ×3, `medium` as recorded, and `high` as threshold 1. Honor
   approved exclusions and shape gates. With `--plan-first`, stop only after
   presenting the complete profile ledger and ordered run list.
4. Load the matching domain skill for every applicable profile:
   `nix-correctness`, `nix-security`,
   `nix-module-design`, `nix-flake-architecture`, `nix-code-health`, and
   `nix-test-gates`.
5. Run correctness, security, module architecture, flake architecture, code
   health, then gates. Require one receipt per profile. Validate changed
   evaluation surfaces after every profile; a no-change profile still needs
   analytical evidence.
6. Re-survey after each changed stage and converge for at most three
   iterations. Use `incomplete-convergence-cap` when open work remains at the
   cap.
7. Validate the final ledger with `ultra-system-reference`, then run the final
   gate from `foundation.md`. Report the precise terminal state, profile
   coverage, validation, approved exclusions, blockers, residual risks, and
   deployment follow-ups.

## Boundaries

This is general Nix/NixOS/Home Manager guidance. Use `nixpkgs-*` skills for
nixpkgs pull requests and `canix-cli` or project-local deployment skills for
host-specific deployment workflows.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
