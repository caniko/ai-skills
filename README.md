# caniko's AI Skills Mirror

Snapshot of all Claude Code and Codex/agents skills found on caniko's machine as of **2026-05-22**.

This is a point-in-time snapshot, not a live sync. Source paths are on the machine at `/home/can/` and `~/canix/Projects/`.

---

## Categories

### Global

| Category | Skills |
|---|---|
| `global` | 51 reconciled skills |

### Per-project

| Project | Skills |
|---|---|
| `projects/regicide` | 36 (reconciled unique skills, game-dev project) |
| `projects/ai-yolo-nix` | 21 |
| `projects/SynDB` | 15 |
| `projects/codex` | 10 (Codex project's own skills) |
| `projects/canix` | 9 |
| `projects/rs-modde` | 7 |
| `projects/fragpipe-mcp` | 4 |
| `projects/goose` | 4 |
| `projects/CourseOfLife` | 1 |
| `projects/plinth` | 1 |
| `projects/nix-crossbow` | 1 |
| `projects/rs_bouldy` | 1 |

---

## Layout

```
global/
  <skill-name>/    # reconciled global skills from ~/.agents, ~/.claude, ~/.codex

projects/
  <project-name>/
    <skill-name>/  # reconciled project skills from supported source dirs
```

## CLI

`skillctl` is the Rust CLI for reconciling and managing the mirror. Configuration lives in `skillctl.toml`.

When direnv is enabled for this repository, `skillctl` is available directly from the dev shell:

```sh
direnv allow
skillctl --help
```

Without direnv, run it through Nix:

```sh
nix run .# -- reconcile --target all
nix run .# -- reconcile --target all --sync
nix run .# -- sync --target all
nix run .# -- list --target global
nix run .# -- targets
```

The same functionality is also available through grouped command families:

```sh
skillctl mirror reconcile --target all
skillctl mirror sync --target all
skillctl mirror sync --all
skillctl mirror list --target global
skillctl skill delete global skill-name
skillctl toml project list
```

### Concepts

`skillctl` separates the checked-in mirror from live agent directories:

- `global/` is the reconciled global skill mirror.
- `projects/<name>/` is the reconciled project skill mirror for a configured project.
- Live global sources come from `~/.agents/skills`, `~/.claude/skills`, and `~/.codex/skills`.
- Live project sources are configured per project and can include `.agents/skills`, `.claude/skills`, `.codex/skills`, root `skills`, plugin skill directories, and extra paths.

Mirror edits are local by default. Commands mutate `global/` or `projects/<name>/` unless `--sync` is passed or `skillctl sync` is run.

Sync writes selected mirror skills back to live `.agents/skills` and `.claude/skills`, removes stale `.codex/skills`, and removes `.codex` only when it becomes empty. Existing non-skill Codex configuration is preserved.

### Targets And Scopes

Commands that accept `--target` use:

- `all`: global plus every configured project.
- `global`: only the global mirror and global live sources.
- `project`: every configured project mirror and project live sources.

Commands that accept a positional `scope` use either `global` or a configured project name. Use `skillctl targets` to print valid scopes.

Configured project roots are managed in `skillctl.toml` with the `toml project` command group:

```sh
skillctl toml project list
skillctl toml project add CourseOfLife ~/canix/Projects/CourseOfLife
skillctl toml project remove CourseOfLife
skillctl toml project remove CourseOfLife --prune-mirror
```

`toml project add` writes a new `[[projects]]` entry to `skillctl.toml`. The project path must exist unless `--allow-missing` is passed. `toml project remove` removes the config entry only by default; `--prune-mirror` also deletes `projects/<name>` from the checked-in mirror if present. The legacy `skillctl project ...` form remains available as a compatibility alias.

### Reconcile And Sync

Reconcile reads live sources first and rebuilds the selected mirror directories using newest-wins collision resolution:

```sh
skillctl reconcile --target all
skillctl reconcile --target global
skillctl reconcile --target project --dry-run
skillctl mirror reconcile --target all
```

Pass `--sync` to also write the reconciled mirror back to live `.agents` and `.claude` directories:

```sh
skillctl reconcile --target all --sync
```

Sync skips live-source discovery and writes the current mirror state back to live directories:

```sh
skillctl sync --target all
skillctl sync --target global --dry-run
skillctl mirror sync --all
skillctl mirror sync --target global --dry-run
```

### Edit Commands

Skill edit commands mutate the mirror by default. Pass `--sync` to also write the result back to live `.agents/skills` and `.claude/skills`.

```sh
skillctl delete global skill-name
skillctl rename global old-name new-name
skillctl move project-a skill-name project-b --as new-name
skillctl globalize project-name skill-name
skillctl deglobalize skill-name project-name
skillctl skill move project-a skill-name project-b --as new-name
```

`rename`, `move`, `globalize`, and `deglobalize` refuse to overwrite an existing destination unless `--force` is passed. `move`, `globalize`, and `deglobalize` move by default; pass `--copy` to preserve the source skill.

### Discovery Helpers

```sh
skillctl list --target all
skillctl list --target global
skillctl targets
skillctl sources --target global
skillctl sources --target project
skillctl mirror targets
skillctl mirror sources --target project
```

### Catalog

`skillctl.catalog.toml` defines taxonomy rules for mirrored skills without moving skill directories. It supplies effective `category`, `scope`, `status`, tags, related skills, and duplicate-name notes used by catalog linting and generated browsing docs.

```sh
skillctl catalog lint
skillctl catalog generate
skillctl catalog show global/rust-project-flake
skillctl catalog search forgejo
```

`catalog generate` rebuilds:

- `CATALOG.md`: skills grouped by global category and project.
- `ROUTING.md`: routing guide for overlapping families such as `fix-loop-*`, `yh-*`, Rust release, Forgejo/Codeberg, ETL/figure layout, and code review.
- `SKILL_CONFLICTS.md`: duplicate-name and overlap report.
- `projects/<name>/INDEX.md`: per-project skill indexes.

### Shell Completions

Generate shell completions:

```sh
skillctl completions bash
skillctl completions zsh
skillctl completions fish
skillctl completions elvish
skillctl completions powershell
```

`scripts/reconcile-skills.nu` is retained as a compatibility wrapper for:

```sh
nix run .# -- reconcile --target all --sync
```

---

## Notes on ambiguous files

- **AGENTS.md at repo roots** (e.g., `canix/AGENTS.md`, `SynDB/AGENTS.md`, `regicide/AGENTS.md`): These are project-level agent configuration files, not standalone skills. They were **not** included as skills.
- **`~/.codex/vendor_imports/`**: Contains 38 curated third-party skills. Excluded — these are upstream vendor imports, not caniko's own skills.
- **`~/.codex/.tmp/`**: Temporary plugin workspace. Excluded.
- The `canix-probe-triage` skill references the phrase "private key" in documentation context — not an actual secret credential.
- **Reconciliation**: `global/` and each `projects/<project-name>/` directory are generated by `skillctl`. The CLI reads all available live sources first, including `.agents/skills`, `.claude/skills`, `.codex/skills`, root `skills`, plugin skill directories, and configured project-specific extras. It then writes the reconciled set back to `.agents/skills` and `.claude/skills` when `--sync` is passed, and removes only stale `.codex/skills` copies. Empty project `.codex` directories are removed; non-skill Codex configuration is preserved. Claude/Codex `.system/*` skills are flattened into normal global skills. On collisions, the source tree with the newest file mtime wins. Exact newest-time ties are accepted only when the tied directory contents are identical.

---

Total mirrored `SKILL.md` files across all categories: 161. Unique skill directory names across all locations: 156.
