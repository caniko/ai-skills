---
name: canix-project-space-reference
description: Reference canix workspace identity, Git topology, worktrees, safe mutations, validation, and project assets. Use for inventory, migrations, or coordinated operations.
---

# Canix Project-Space Reference

## Role

This is both a directly invokable workspace skill and a shared reference. When
invoked directly, choose the narrowest safe operation matching the request and
perform or plan it using the contract below. When loaded from a specialized
skill, it owns the common scope, identity, topology, evidence, state, and safety
contract while the caller owns its task-specific procedure.

Load the existing [canix-structure-reference](.skillnet/deps/canix-structure-reference/SKILL.md)
for canix-specific topology, Fleetix ownership, generated sidecars, and
host/deployment rules. This reference adds the whole-project-space boundary and
does not replace that source of truth.

## Scope and canonical roots

Unless the user narrows scope, treat the operating surface as:

| Surface | Canonical location | Authority |
|---|---|---|
| canix parent | `/data/nvme0/can/canix` | Fleet configuration, CLI, and project gitlinks |
| project workspace | `/data/nvme0/can/canix/projects` | Project checkouts, forks, worktrees, personal material, archives |
| workspace catalog | `projects/{owned,forks,upstream,worktrees,...}` | Runtime-discovered project identity and checkout paths |
| observed state | canix workspace scanner output | Git revisions and working-tree state; never a durable registry |
| mutable state | `/data/nvme0/can/ProjectState` | Build, cache, database, dataset, generated, and runtime state |

Read the applicable `AGENTS.md` files before acting. Resolve projects with the
canix workspace scanner/CLI; never guess a checkout from a stale path or add a
second registry.

## Establish the workspace

From the canix checkout, establish the exact target set and save the observed
state before any mutation:

```sh
cd /data/nvme0/can/canix
CANIX_PROJECTS_ROOT=/data/nvme0/can/canix/projects canix workspace check --skip-physical-paths
CANIX_PROJECTS_ROOT=/data/nvme0/can/canix/projects canix workspace check
canix workspace git status --dirty-only
```

Use JSON output for automation:

```sh
canix --output json workspace git status --dirty-only
canix --output json workspace show <project>
```

If the installed CLI lacks a required command, verify the current source
implementation under `cli/src/commands/workspace/` and use the documented
`nix develop -c cargo run --manifest-path cli/Cargo.toml --no-default-features --features admin -- ...`
fallback. Do not revive removed workspace scripts or substitute guessed paths.
Report a missing registry, checkout, command, or sidecar with its owner,
regeneration command, and validation command.


For cross-repository work, query the existing `graphify-out/graph.json` first.
Build or update a merged graph for the exact repository set when it is missing,
stale, or incomplete. Use graph evidence for relationships, but retain Git and
registry metadata as the authority for identity and mutation decisions.

## Project and Git identity

Treat the filesystem as a topology, not a list of names. For each checkout,
record:

- registry ID and current path;
- filesystem kind: canonical repository, maintained fork, upstream clone,
  linked worktree, submodule, personal material, archive, quarantine, or
  generated/state tree;
- `origin` and optional `upstream` remotes, with credentials redacted;
- branch or detached HEAD, exact revision, dirty state, and worktree parent;
- project-specific state path, asset conventions, and path references;
- confidence, blocking evidence, and an explicit `owner_decision`.

Use `git remote -v`, `git status --short`, `git log`, and
`git worktree list --porcelain` as evidence. Group duplicate origins before
proposing deduplication. A `.git` file is not a normal directory: identify its
base repository and registration. Repair an authorized moved worktree only via
the base repository's `git worktree repair`; never delete `.git/worktrees` or
recreate a worktree to hide stale metadata.

Keep `owner_decision = unknown` for ambiguous ownership, fork/upstream status,
archival intent, or deletion intent until the user resolves it. Age, size,
language, directory names such as `old` or `upstream`, and recent activity are
evidence—not authorization.

## Storage and path coupling

Keep source, mutable state, and recovery material distinct:

```text
projects/
├── owned/<service>/<repo>
├── forks/<service>/<repo>
├── upstream/<service>/<repo>
├── worktrees/<base-repo>/<purpose>
├── personal/<domain>/            # protected unless explicitly in scope
├── experiments/
└── archives/<kind>/              # protected unless explicitly approved
ProjectState/
├── caches/  build/  databases/  datasets/  generated/
```

Measure `target`, `node_modules`, `.venv`, `.direnv`, databases, datasets,
receipts, results, and generated outputs separately from source. Never remove
them merely because they look disposable; tracked files, reproducibility
fixtures, evidence, and project-owned runtime data outrank naming heuristics.
Protect personal, quarantine, access-revoked employer, archives, and
tool-managed worktree trees by default.

Search configuration, scripts, flakes, `direnv`, CI, editor settings, service
definitions, and documentation for absolute workspace paths, sibling-project
paths, local flake inputs, and generated checkout paths. Keep path and state
references as blockers until the affected project is validated after a move.

For inventories and migration dossiers, use these registry fields at minimum:

```text
id current_path proposed_path kind lifecycle namespace origin_remote
upstream_remote base_repository branch_or_head dirty_state state_path
archive_artifact confidence blocking_evidence owner_decision
```

## Mutation boundaries

Default to read-only discovery. Never move, rename, delete, reset, clean,
checkout, fetch, rewrite, prune, amend, rebase, force-push, or overwrite a
project asset unless the calling request explicitly authorizes that operation.
Preserve pre-existing dirty, staged, untracked, and ignored-but-tracked work.

Before any authorized mutation, save status, branch/HEAD, remotes, worktree
registries, and the exact selected paths. Require a destination that does not
already exist, a rollback artifact or preserved source, and focused validation.
Mutate the canonical project or skill source, not generated sidecars or
materialized views. Validate the scanner's project identity, path references,
worktree registration, and project checks afterward.

For a cross-repository commit/publish operation, process child repositories
before the canix parent, keep child commits separate from parent gitlink
updates, and treat publication as a distinct authorization. A literal `push`
keyword is required by the workspace-publish skill; never infer push authority
from a general request to commit or clean up.

## Project-wide visual assets

Asset generation is an explicit opt-in operation, separate from inventory,
cleanup, migration, and publication. When the user asks for an asset for each
project:

1. Resolve the selected registry entries first. Default to active source
   projects; exclude personal material, archives, upstream references,
   generated/state trees, and protected or ambiguous entries unless named.
2. Inspect each repository's `AGENTS.md`, existing brand assets, native SVG or
   icon conventions, and intended asset destination. Do not overwrite an
   existing asset without explicit replacement authorization.
3. For new raster logos or visual concepts, load/use the `imagegen` skill and
   the built-in `image_gen` tool by default. Issue one generation call per
   distinct project/logo; keep a shared art direction while deriving identity
   from verified project metadata. Use the `logo-brand` prompt taxonomy and
   require no watermark, no invented claims, and exact text only when needed.
4. Save selected project-bound outputs inside the owning checkout at its
   established asset path, or pause on a materially ambiguous destination.
   Keep a manifest mapping project ID, prompt/spec, output path, and validation
   result. Do not leave the only copy in the Codex image cache.
5. Inspect every output and validate dimensions, format, alpha/background
   expectations, text accuracy, and repository references before a commit.

If the user explicitly requests the text-to-image API, CLI, model, or provider
path, follow `imagegen`'s explicit CLI fallback rules and report missing
credentials or unavailable API access. Never invent an endpoint or silently
switch models. For an existing repo-native vector/logo system, edit or extend
that system instead of introducing an unrelated raster logo.

For a direct request such as “generate a logo for every active project,” use
the sequence above as the operation: resolve the active registry set, exclude
protected or ambiguous entries, inspect destinations, issue one image
generation call per project, and return the asset manifest plus validation
results. Do not interpret “every project” as permission to write into
archives, personal material, upstream-only checkouts, or generated state.

## Evidence and handoff

Every report or implementation handoff must distinguish facts, inferences,
candidates, blockers, and user decisions. Include commands run, inventory or
dossier paths, exact changed projects, validation results, skipped checks and
why, and whether any migration, deletion, commit, push, or asset generation
actually occurred. Unknown foundational inputs must name their producer,
regeneration command, and validation command.
