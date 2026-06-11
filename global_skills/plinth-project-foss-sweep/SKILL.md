---
name: plinth-project-foss-sweep
description: Inventory owned FOSS repositories worked on recently and apply or refresh Plinth project-site configs with `plinth-project`. Use when Codex is asked to sweep recent FOSS projects, create or update `website/plinth-project.toml`, validate/build project websites, organize owned project locations, or use simit's project registry as the canonical location source for Plinth project sites.
---

# Plinth Project FOSS Sweep

## Purpose

Apply `plinth-project` consistently across owned FOSS repositories while keeping repository locations auditable through simit. Default to dry-run discovery and explicit blockers; do not fabricate missing metadata.

## Core Rules

- Treat simit as the desired source of truth for project locations, but do not move repos or rewrite registry paths until simit supports generic FOSS entries and the user explicitly approves the move plan.
- Target owned FOSS only by default: recent git activity, user-owned remote namespace, public forge remote, and a license file.
- Exclude `upstream/`, `worktrees/`, `assesments/`, scratch/temp repos, vendored nested repos, and obvious third-party forks unless the user explicitly names them.
- Stop on missing foundational metadata. Report the missing artifact, why it is required, the upstream command/workflow to create it, and the validation command.
- Preserve existing `website/plinth-project.toml`; only fill missing generated-safe fields after reading the repo.

## Discovery Workflow

1. Inspect simit's current registry:
   ```sh
   simit projects scan
   simit projects list --json
   ```

   If `simit` is unavailable, use the local checkout without modifying target projects:
   ```sh
   cargo run --manifest-path ~/canix/Projects/simit/Cargo.toml -- projects list --json
   ```

2. Discover recent owned FOSS candidates:
   ```sh
   ~/canix/Projects/ai-skills/global/plinth-project-foss-sweep/scripts/discover-recent-owned-foss.sh \
     --root ~/canix/Projects \
     --since 5-months \
     --dry-run
   ```

3. Classify every candidate:
   - `target`: owned namespace, recent activity, non-excluded path, public forge remote, license file.
   - `needs-user-review`: owned/recent but no license, ambiguous remote, nested third-party repo, or unclear FOSS status.
   - `skip`: excluded path, stale, non-owned remote, worktree/upstream/assessment/scratch.

4. Read [references/simit-generic-project-registry.md](references/simit-generic-project-registry.md) when the user asks to reorganize paths or register non-Rust/non-simit-managed projects.

## Apply Workflow

Use the sweep script for broad runs:

```sh
~/canix/Projects/ai-skills/global/plinth-project-foss-sweep/scripts/plinth-project-sweep.sh \
  --root ~/canix/Projects \
  --since 5-months \
  --dry-run
```

For each `target` repo:

1. Check `git status --short`. Do not overwrite unrelated local changes.
2. Inspect `README*`, license/COPYING, remotes, package manifests, existing `website/plinth-project.toml`, and generated output.
3. If config is missing, create `website/plinth-project.toml` from real repo metadata only.
4. If config exists, preserve authored content and refresh only missing generated-safe fields.
5. Validate:
   ```sh
   plinth-project check --config website/plinth-project.toml
   plinth-project build --config website/plinth-project.toml
   ```

Use `--apply` on the script only after reviewing dry-run output. `--dry-run` is the default behavior.

## Reorganization Workflow

- Generate a proposed move map into `~/canix/Projects/foss/owned/<repo>` for targets that are not already co-located.
- Do not execute moves in this skill until the user explicitly asks for implementation.
- Before any future move, require: clean or understood git status, no duplicate destination, remote URL recorded, simit generic registry support available, and a reversible move plan.

## Reporting

Report:

- simit command/version or local checkout used
- discovery root, since cutoff, and owned namespace filter
- per-project verdict: `updated`, `already-current`, `blocked`, `skipped`, or `needs-user-review`
- exact blocker details and validation commands
- proposed simit registry updates and move map
- validation commands run and their results

## Resources

- `scripts/discover-recent-owned-foss.sh`: dry-run inventory and classifier.
- `scripts/plinth-project-sweep.sh`: dry-run/apply loop for `website/plinth-project.toml`, `plinth-project check`, and `plinth-project build`.
- `references/simit-generic-project-registry.md`: required simit extension plan before generic project moves.
