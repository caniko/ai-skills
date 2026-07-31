---
name: nix-ultra
description: Orchestrate a complete Nix improvement pass across flakes, NixOS, Home Manager, packages, secrets, and checks. Use for deep audits, hardening, or cleanup.
---

# Nix Ultra

Use this entrypoint for whole-repository Nix work. Focused requests should
load the smallest matching domain skill directly.

## Workflow

1. Let the active harness plan the work and preserve its model/delegation
   ownership. Do not create a second lifecycle or artifact protocol here.
2. Read `references/foundation.md`, inspect the worktree and Nix outputs, and
   load every matching focused skill:
   `nix-correctness`, `nix-security`, `nix-module-design`,
   `nix-flake-architecture`, `nix-code-health`, and `nix-test-gates`.
3. Apply only source-backed changes, migrating in-repository consumers when
   outputs or options change. Stop on missing or invalid inputs.
4. Validate the narrowest affected evaluation after each change, then run the
   repository's documented formatter and flake gates.

Focused skills own their procedures and evidence. This entrypoint only routes
the complete pass and reports unresolved findings, blockers, and validation.

## Boundaries

Use project-local deployment skills for host-specific releases.
