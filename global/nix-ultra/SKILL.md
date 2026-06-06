---
name: nix-ultra
description: Master orchestrator for whole-repository Nix cleanup. Surveys Nix flakes, NixOS modules, Home Manager configs, overlays, packages, secrets, tests, inputs, and style with weighted heuristics, then routes to the nix-* concern skills in correctness, design, polish, and input-gate order. Use when asked to deeply audit, clean up, harden, or make a Nix repository idiomatic.
---

# Nix Ultra - Whole-Repository Improvement Orchestrator

Nix Ultra coordinates the sibling `nix-*` skills. It surveys first, scores concerns, runs the right skills in a stable order, and verifies after every stage. It is general-purpose Nix/NixOS/Home Manager guidance, not a nixpkgs PR workflow; use the existing `nixpkgs-*` skills for nixpkgs pull requests.

Default arguments: path = current repository, `--sensitivity medium`, no `--plan-first`, no `--only`, no `--skip`.

## Phase 0 - Baseline

1. Inspect `git status --short` and preserve unrelated user work.
2. Detect project shape: flake or non-flake, NixOS hosts, Home Manager configs, overlays/packages, secrets system, formatter, checks, CI, and deployment commands.
3. Run only read-only or no-build baseline commands first: `rg --files -g '*.nix'`, formatter check, `nix flake show` or focused `nix eval` if available.
4. If a foundational artifact is missing, stop and report the artifact, why it is required, the producer command, and a validation command.

## Phase 1 - Survey And Score

Score each concern with the routing table below. Exclude `.git`, result symlinks, generated cache directories, `node_modules`, `target`, and vendor trees. For file-size scoring, count `.nix` files: >500 lines scores 3, >300 lines scores 2, <30 lines scores 1.

Sensitivity changes thresholds:

- `low`: threshold x3.
- `medium`: threshold x1.
- `high`: threshold becomes 1.

Honor `--only` and `--skip`. If `--plan-first` is set, print the scored run-list and stop before editing.

## Phase 2 - Staged Execution

Run selected concerns in this order. Within a stage, run higher scores first.

1. Correctness: `nix-eval-failures`, `nix-security-secrets`, `nix-store-purity`.
2. Design: `nix-module-design`, `nix-options-typing`, `nix-data-boundaries`, `nix-flake-architecture`, `nix-overlay-package`, `nix-home-manager`.
3. Polish: `nix-code-reorg`, `nix-dead-code`, `nix-format-style`, `nix-shell-scripts`.
4. Inputs and gates: `nix-input-hygiene`, `nix-test-gates`.

Before invoking a sibling skill, confirm it exists in the available skills list or on disk. If missing, skip it and log `deferred: skill not installed`; do not invent a skill invocation.

After each concern, run formatter and the narrowest eval/build/check that covers the changed area. Do not proceed with a red tree unless the current task is explicitly to diagnose that red state.

## Phase 3 - Convergence

After each full stage, rescore. Re-run quantitative concerns whose score remains above zero and qualitative concerns whose skill reported remaining work. Stop after convergence or three iterations, whichever comes first. At the cap, report deferred work explicitly.

## Phase 4 - Final Gate

Run the strongest affordable validation for the repository:

- Formatter check.
- `nix flake check --no-build --no-update-lock-file --accept-flake-config` when flake-based.
- Focused host evals such as `nix eval .#nixosConfigurations.<host>.config.system.build.toplevel.drvPath --no-update-lock-file --accept-flake-config` for touched NixOS hosts.
- Focused Home Manager/package/check evals for touched outputs.
- Full builds only when needed and affordable.

Report concerns run, skipped, deferred, final scores, validation commands, blockers, and residual risks.

## Routing Table

| Skill | Stage | Preflight score >= threshold | Mode | Eval |
|---|---|---|---|---|
| `nix-eval-failures` | Correctness | `throw` x2, `assert` x2, `or null` x1, `or {}` x1, `mkForce` x2, `types.raw` x2 >= 6 | ScopeLocal | Qualitative |
| `nix-security-secrets` | Correctness | `age.secrets` x3, `sops.secrets` x3, `LoadCredential` x3, `environmentFile` x2, `mode = "0444"` x2, `password` x1, `secret` x1 >= 8 | Connectome | Qualitative |
| `nix-store-purity` | Correctness | `builtins.getFlake` x4, `fetchTarball` x4, `fetchGit` x4, `/home/` x3, `/data/` x3, `path:` x2, `builtins.pathExists` x2 >= 6 | Connectome | Indicative |
| `nix-module-design` | Design | `mkMerge` x2, `mkIf` x1, `mkForce` x3, `imports =` x1, `options.` x2, `disabledModules` x3 >= 10 | Connectome | Qualitative |
| `nix-options-typing` | Design | `mkOption` x2, `types.raw` x4, `types.attrs` x2, `freeformType` x3, `default = config.` x2, `assertions =` x2 >= 8 | ScopeLocal | Qualitative |
| `nix-data-boundaries` | Design | `import ../` x1, `import ../../` x1, `hostsData.` x3, `domain = "` x2, `hostname = "` x1, duplicate literals x2 >= 10 | Connectome | Indicative |
| `nix-flake-architecture` | Design | `perSystem` x2, `flakeModules` x2, `follows` x1, `legacyPackages` x2, `checks` x1, `formatter` x1 >= 8 | Connectome | Qualitative |
| `nix-overlay-package` | Design | `overlays` x3, `overrideAttrs` x3, `callPackage` x2, `mkDerivation` x2, `import nixpkgs` x4 >= 6 | Connectome | Qualitative |
| `nix-home-manager` | Design | `osConfig` x2, `home.packages` x1, `xdg.configFile` x1, `systemd.user` x2, `homeConfigurations` x2, `hostsData` x3 >= 8 | Tiling | Qualitative |
| `nix-code-reorg` | Polish | file-size score >= 3 | Connectome | Quantitative |
| `nix-dead-code` | Polish | `TODO: remove` x3, `deprecated` x2, `disabledModules` x2, `# unused` x2, unreferenced file x3 >= 5 | Tiling | Qualitative |
| `nix-format-style` | Polish | `with pkgs;` x4, `with lib;` x2, package-list broad with x4, dense let blocks x1 >= 6 | ScopeLocal | Quantitative |
| `nix-shell-scripts` | Polish | `writeShellScript` x3, `writeShellApplication` x3, `script =` x1, `preStart` x2, `cat <<` x3, `$(` x1 >= 8 | ScopeLocal | Qualitative |
| `nix-input-hygiene` | Inputs/Gates | `inputs.` x1, `follows` x1, `nixpkgs` x1, `path:` x4, `git+file` x4, `flake = false` x1 >= 10 | Connectome | Indicative |
| `nix-test-gates` | Inputs/Gates | `checks.` x2, `formatter` x2, `pre-commit` x1, `runCommand` x2, `assertRule` x3, `nixosConfigurations` x2 >= 6 | Connectome | Qualitative |

## Notes

Keep changes behavior-preserving unless the user explicitly requests a redesign. Prefer repo conventions over generic taste. Never fabricate missing secrets, lock data, hashes, generated files, or upstream sources.
