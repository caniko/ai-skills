---
name: workspace-housekeeping
description: Safely clean canix's workspace of repositories, forks, worktrees, archives, quarantine trees, and generated state. Use for projects/ cleanup or Workspace.pkl reconciliation.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Workspace Housekeeping

Load [canix-project-space-reference](../canix-project-space-reference/SKILL.md)
first. It owns the canonical roots, registry, identity evidence, state
classes, path coupling, and safety contract. Read `projects/README.md` and
applicable canix `AGENTS.md` before acting.

## Audit first

1. Establish the exact workspace root, authorized scope, current canix and
   project Git status, remotes, dirty worktrees, and protected exclusions.
2. Validate the registry and physical paths:

   ```sh
   cd ~/canix/canix
   canix workspace check
   canix workspace check --skip-physical-paths
   ```

   Resolve individual entries with `canix --json workspace show <project>`.
   If the installed binary lacks `workspace`, use the current admin CLI from
   `cli/`; never revive deleted workspace scripts or guess paths.
3. Discover cleanup candidates with the dry-run command:

   ```sh
   canix workspace cleanup
   ```

   Use the generic inventory script from the organize-project-workspace skill
   only for evidence the CLI cannot expose, and run it outside the workspace.
4. Inspect generated markers, duplicate origins, path references, worktree
   lists, and `git worktree prune --dry-run --verbose`. A stale worktree is
   repaired or pruned only through its owning base repository after confirming
   that the working directory is absent or preserved by a verified artifact.

## Classify before cleaning

Classify each candidate using Git and registry evidence as source checkout,
maintained fork, upstream reference, linked worktree, project submodule,
personal material, employer recovery material, archive, quarantine, generated
build/dependency state, project data, result, receipt, database, or output.

The cleanup heuristic may remove only verified generated build/dependency
environments and desktop trash. It must not remove tracked files, archives,
quarantine, employer material, personal material, tool-managed worktrees, or
project data. A directory named `target` is not enough evidence: LLVM and
kernel source trees can use that name. Report generated trees owned by another
user as permission blockers; do not invoke elevated deletion implicitly.

## Apply only approved cleanup

Review the dry-run paths and require explicit authorization before applying:

```sh
cd ~/canix/canix
canix workspace cleanup --apply
```

Use `--exclude-prefix` for ordered project groups or deferred repositories.
Never delete `.git/worktrees` metadata directly. Preserve unrelated dirty work
and record the pre-cleanup state before each batch.

After an approved cleanup or path change, validate the manifest and physical
paths, then refresh the observed lock only when revisions intentionally changed:

```sh
canix workspace check
canix workspace lock
nix flake check --no-update-lock-file
```

Edit `projects/Workspace.pkl` for identity, lifecycle, or path changes. Do not
hand-edit `lib/generated/workspace.nix`.

## Handoff

Inspect every changed repository, preserve unrelated work, run focused checks,
and report candidates, protected classes, recovery artifacts, unresolved
exceptions, commands, and validation. Commit or publish only when the user
also requests that specialized operation; then load the workspace-publish
skill and follow its per-repository commit and literal-`push` rules.

## Solution Placement

For durable fixes, prefer generic upstream → Fleetix → standalone flake →
canix-toolbelt → canix. Keep host-specific policy and private fleet data in
canix.
