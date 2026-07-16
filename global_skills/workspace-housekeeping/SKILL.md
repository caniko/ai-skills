---
name: workspace-housekeeping
description: Audit, classify, and safely clean canix's owned project workspace containing Git repositories, forks, linked worktrees, personal material, archives, quarantine trees, and generated state. Use when Codex is asked to tidy the canix `projects/` tree, remove old or disposable files, reconcile `projects/Workspace.pkl`, prune stale worktree metadata, or establish a repeatable maintenance workflow.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Workspace Housekeeping

Load [canix-structure-reference](../canix-structure-reference/SKILL.md) first;
it owns the canonical roots, registry, and source-of-truth boundaries.

Use this skill for the canix-owned project workspace. Treat source, state,
archives, and recovery material as different classes; never decide that a
checkout is old or removable from its name or mtime alone.

Read `projects/README.md` and applicable canix `AGENTS.md` before acting.

## Audit first

1. Establish the exact workspace root, applicable `AGENTS.md` instructions,
   current canix and project Git status, remotes, dirty worktrees, and
   user-authorized scope.
2. Validate the canix-owned registry and physical paths:

   ```sh
   cd ~/canix/canix
   canix workspace check
   canix workspace check --skip-physical-paths
   ```

   Use `canix --json workspace show <project>` to resolve an individual
   checkout. If the installed binary does not expose `workspace`, build/use
   the current admin CLI from `cli/`; do not revive the deleted
   `projects/tools/workspace*` scripts.

3. Use the canix cleanup command for candidate discovery; it is dry-run by
   default:

   ```sh
   cd ~/canix/canix
   canix workspace cleanup
   ```

   The generic inventory script is a fallback for evidence that the CLI does
   not expose, and must run outside the workspace checkout:

   ```sh
   /home/can/.codex/skills/organize-project-workspace/scripts/inventory_workspace.sh \
     ~/canix/canix/projects /tmp/projects-housekeeping-live --sizes
   ```

4. Inspect `git-repositories.tsv`, `worktrees.tsv`,
   `generated-markers.tsv`, duplicate origins, path references, and
   `git-worktree-lists.txt`. Use `git worktree prune --dry-run --verbose`
   before any metadata prune.
5. Preserve dirty source and untracked personal data. Treat `archives/`,
   `local/` quarantine, access-revoked employer material, `.codex-worktrees/`,
   and tool-managed `.claude/worktrees/` as protected unless the user
   explicitly expands scope.

## Classify before cleaning

Use evidence-backed classes:

- source checkout, maintained fork, upstream reference, linked worktree, or
  project-owned submodule;
- personal material, employer recovery material, archive, or quarantine;
- generated build/dependency state (`target` with `CACHEDIR.TAG` or
  `.rustc_info.json`, `node_modules`, `.venv`, `.direnv`);
- project data, datasets, results, receipts, databases, or outputs, which need
  project-specific review and are not routine disposable state.

Do not remove directories merely because they are named `target`; LLVM and
kernel source trees use that name for real files. Do not remove archives or
quarantine trees while performing routine generated-state cleanup.
Protect any candidate containing tracked files; repository history outranks
the generated-state naming heuristic. Report generated trees owned by another
user as permission blockers and do not invoke elevated deletion implicitly.

## Apply the approved cleanup

Keep the canix cleanup command dry-run by default and review its printed paths:

```sh
cd ~/canix/canix
canix workspace cleanup
```

Apply only after explicit user authorization and after recording dirty state:

```sh
cd ~/canix/canix
canix workspace cleanup --apply
```

Use `--exclude-prefix` to honor ordered project groups or temporarily defer a
repository. Remove stale linked-worktree metadata only through the owning base
repository's Git command, never by deleting `.git/worktrees` directories.
Before pruning, confirm that every reported working directory is absent or
already preserved by a verified bundle or archive.

## Keep the registry truthful

The workspace manifest is the source of organizational truth and the lock file
is an observed snapshot. After an approved cleanup or path change, validate
that manifest and lock paths exist, then refresh the lock snapshot only when
the observed revisions intentionally changed:

```sh
cd ~/canix/canix
canix workspace check
canix workspace lock
nix flake check --no-update-lock-file
```

Do not use the removed `./tools/workspace` commands or treat the generated
`lib/generated/workspace.nix` sidecar as an editable source. If a project path
or lifecycle needs changing, update `projects/Workspace.pkl`, then validate
the sidecar/evaluation through the canix flake's documented generation checks.

Keep historical migration documents intact, but update operational path
references when the canonical layout changes. Record deletion candidates,
protected classes, recovery bundles, and unresolved exceptions in the
workspace dossier; do not hide them in a commit message.

## Commit and hand off

Inspect all changed repositories after cleanup. Group changes by coherent
purpose, preserve unrelated pre-existing dirty work, run focused validation,
and push only repositories with an authorized configured remote. Keep private
tax data and access-revoked employer trees out of commits. If a user requests
an ordering such as ai-skills, skillnet, and canix last, defer those paths and
validate them as the final group.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
