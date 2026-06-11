# caniko's AI Skills

This repository is the canonical store for global skills at `ai-skills/global/<name>/`. Per-project skills live in each project's own repository at `<project>/.skills/<name>/`; `~/.claude/skills`, `~/.agents/skills`, `<project>/.claude/skills`, and `<project>/.agents/skills` are generated views, not authored content. The old `<ai-skills>/projects/` tree is obsolete local state and may be removed after validation.

## Layout

```text
global/
  <skill-name>/              # canonical global skills

docs/planning/
  mirror-canonical-store/    # Option B migration plan set
```

Top-level generated catalog files:

- `CATALOG.md`
- `ROUTING.md`
- `SKILL_CONFLICTS.md`

Configuration:

- `skillnet.toml` declares this repo root and the project repositories whose `.skills/` directories are canonical.
- `skillnet.catalog.toml` declares catalog metadata and taxonomy rules.

## Authoring

Author global skills directly in this repository:

```sh
$EDITOR global/<name>/SKILL.md
skillnet view sync
```

`skillnet view sync` regenerates the global consumer views. It is also auto-invoked by `skill new`, `skill rename`, and `skill delete`.

Author per-project skills inside the owning project repository:

```sh
cd <project>
$EDITOR .skills/<name>/SKILL.md
skillnet project sync --name <project>
```

`skillnet project sync` regenerates that project's in-repo working copy and consumer views from `.skills`.

## Fresh Host Bootstrap

Clone this repository and every project repository listed in `skillnet.toml`, then run:

```sh
home-manager switch
```

Home Manager installs `skillnet` and materializes the generated symlink views from the canonical stores.

## Planning

The migration plan and research dossiers live in:

- `docs/planning/mirror-canonical-store/`
- `docs/planning/mirror-canonical-store-research.md`
- `docs/planning/reconciliation-anomalies-research.md`

These documents describe the Option B move away from mirrored per-project content and toward per-repo canonical `.skills/` stores.
