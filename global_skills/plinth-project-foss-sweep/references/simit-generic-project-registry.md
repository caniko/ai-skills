# Canix Workspace Registry Contract

## Ownership

Load [canix-structure-reference](../../canix-structure-reference/SKILL.md) for
the canonical roots, registry, snapshot, sidecar, and validation commands.
This reference adds the Plinth/Simit-specific ownership rule below.

Simit remains useful for its own feature inventory (`flake`, `ci`, hooks,
release trust, and packaging), but it does not own canix project locations.
Do not add a second generic project-location registry to simit.

## Required Canix Registry Shape

Keep entries in `projects/Workspace.pkl` with:

- project key and canonical workspace-relative path
- lifecycle and materialization policy
- project kind and access classification
- default branch when it is not `main`

Keep FOSS metadata such as license, remote, recent activity, and
`plinth_project` status in the sweep output or a project-specific report; do
not overload the canix manifest or simit feature statuses with ephemeral scan
results.

## Required Commands

```sh
cd ~/canix/canix
canix workspace check
canix --json workspace show <project>
simit projects scan
simit projects list --json
```

For a manifest change, preserve these semantics:

- the Pkl source is edited, not the generated Nix sidecar
- physical paths and lifecycle values are checked before applying
- observed lock refresh is explicit via `canix workspace lock`
- any move requires explicit command invocation and a reversible plan

## Move Safety Requirements

Before moving a repo:

- parent canix and the affected project `git status --short` are clean or all
  local changes are understood
- destination path does not exist
- remote URL is recorded in the registry
- current path and destination path are both valid UTF-8
- nested repos are not accidentally moved as part of a parent repo
- the Workspace.pkl update and filesystem move are reported as one reversible
  plan

## Validation

After changing the canix workspace registry:

```sh
cd ~/canix/canix
canix workspace check
canix workspace lock
nix flake check --no-update-lock-file
```

Then rerun the read-only Plinth sweep:

```sh
~/canix/canix/projects/repos/owned/codeberg.org/caniko/ai-skills/global_skills/plinth-project-foss-sweep/scripts/discover-recent-owned-foss.sh --dry-run
~/canix/canix/projects/repos/owned/codeberg.org/caniko/ai-skills/global_skills/plinth-project-foss-sweep/scripts/plinth-project-sweep.sh --dry-run --limit 3
```
