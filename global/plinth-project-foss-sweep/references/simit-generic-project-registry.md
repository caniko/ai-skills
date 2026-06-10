# Simit Generic Project Registry Extension

## Why This Is Needed

Current simit project discovery is Rust-workspace and simit-feature oriented. The FOSS sweep needs simit to track arbitrary owned repositories, including non-Rust projects and repos that do not yet use simit-managed flake/CI/release features.

Until this extension exists, use simit as the desired canonical registry but do not move repos or rewrite registry paths. Emit a move map and require explicit user approval.

## Required Registry Shape

Add generic project entries alongside existing simit-managed Rust entries:

- canonical path
- project name
- remote URL
- forge host
- forge owner
- forge repository
- ownership classification
- license status and license file
- last git activity date
- project kind, such as `rust`, `nix`, `python`, `javascript`, `go`, `docs`, or `mixed`
- `plinth_project` status: `missing`, `configured`, `built`, `blocked`, or `unknown`
- optional proposed canonical path

Do not overload simit feature statuses for generic FOSS metadata. Keep feature statuses for simit-managed surfaces such as flake, CI, hooks, and packaging.

## Required Commands

The extension should support:

```sh
simit projects discover-git ~/canix/Projects --owned caniko,memorycircuits --since "5 months ago" --dry-run --json
simit projects list --json --kind generic
simit projects scan --prune --kind generic
simit projects move-plan --root ~/canix/Projects/foss/owned --json
```

If command names differ during implementation, preserve these semantics:

- discovery must be dry-run capable
- JSON output must be stable for scripts/agents
- scan must detect missing paths and stale remotes
- move-plan must not move files
- apply-move, if ever added, must require explicit command invocation

## Move Safety Requirements

Before moving a repo:

- `git status --short` is clean or all local changes are understood
- destination path does not exist
- remote URL is recorded in the registry
- current path and destination path are both valid UTF-8
- nested repos are not accidentally moved as part of a parent repo
- registry update and filesystem move are reported as a reversible plan

Use `~/canix/Projects/foss/owned/<repo>` as the default proposed destination for owned FOSS projects unless the user provides a different canonical tree.

## Validation

After adding generic registry support to simit:

```sh
simit projects discover-git ~/canix/Projects --owned caniko,memorycircuits --since "5 months ago" --dry-run --json
simit projects scan --kind generic
simit projects list --kind generic --json
```

Then rerun:

```sh
~/canix/Projects/ai-skills/global/plinth-project-foss-sweep/scripts/discover-recent-owned-foss.sh --dry-run
~/canix/Projects/ai-skills/global/plinth-project-foss-sweep/scripts/plinth-project-sweep.sh --dry-run --limit 3
```
