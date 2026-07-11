---
name: workspace-housekeeping
description: Audit, classify, and safely clean mixed project workspaces containing Git repositories, forks, upstream clones, linked worktrees, personal material, archives, quarantine trees, and generated state. Use when Codex is asked to tidy a Projects directory, remove old or disposable files, reconcile a workspace registry, prune stale worktree metadata, or establish a repeatable long-term maintenance workflow.
---

# Workspace Housekeeping

Use this skill for filesystem and Git-topology cleanup. Treat source, state,
archives, and recovery material as different classes; never decide that a
checkout is old or removable from its name or mtime alone.

## Audit first

1. Establish the exact workspace root, applicable `AGENTS.md` instructions,
   current Git status, remotes, dirty worktrees, and user-authorized scope.
2. Run the read-only inventory script outside the workspace checkout:

   ```sh
   /home/can/.codex/skills/organize-project-workspace/scripts/inventory_workspace.sh \
     ~/canix/Projects /tmp/projects-housekeeping-live --sizes
   ```

3. Inspect `git-repositories.tsv`, `worktrees.tsv`,
   `generated-markers.tsv`, duplicate origins, path references, and
   `git-worktree-lists.txt`. Use `git worktree prune --dry-run --verbose`
   before any metadata prune.
4. Preserve dirty source and untracked personal data. Treat `archives/`,
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

Keep the cleanup command dry-run by default and review its printed paths:

```sh
./tools/workspace cleanup
```

Apply only after explicit user authorization and after recording dirty state:

```sh
./tools/workspace cleanup --apply
```

Use `--exclude-prefix` to honor ordered project groups or temporarily defer a
repository. Remove stale linked-worktree metadata only through the owning base
repository's Git command, never by deleting `.git/worktrees` directories.
Before pruning, confirm that every reported working directory is absent or
already preserved by a verified bundle or archive.

## Keep the registry truthful

The workspace manifest is the source of organizational truth and the lock file
is an observed snapshot. After path normalization or cleanup, validate that
manifest and lock paths exist, then refresh the lock snapshot:

```sh
./tools/workspace check
./tools/workspace lock
pkl eval -f json Workspace.pkl >/dev/null
jq empty Workspace.lock.json
nix flake check . --no-update-lock-file
```

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
