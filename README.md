# caniko's AI Skills

This repository is the canonical store for global skills at `ai-skills/global_skills/<name>/`. Per-project skills live in each project's own repository at `<project>/.skills/<name>/`; `~/.claude/skills`, `~/.agents/skills`, `<project>/.claude/skills`, and `<project>/.agents/skills` are generated views, not authored content. The old `<ai-skills>/projects/` tree is obsolete local state and may be removed after validation.

## Layout

```text
global_skills/
  <skill-name>/              # canonical global skills
```

Catalog files are generated locally when needed:

```sh
skillnet catalog generate
```

Configuration is centralized per user by Skillnet:

- `$XDG_CONFIG_HOME/skillnet/skillnet.toml` declares this repo root and the project repositories whose `.skills/` directories are canonical.
- `$XDG_CONFIG_HOME/skillnet/skillnet.catalog.toml` declares catalog metadata and taxonomy rules.
- Older checkouts that still contain repository-local config can migrate it with `skillnet config migrate`; the command preserves the configured database and subscription state.

`global_skills/` stores global skills as markdown skill packages. The catalog
manifest (`Skillnet.pkl`) and its grants are per-store; generate them locally
with `skillnet catalog generate` when needed.

## Authoring

Author global skills directly in this repository:

```sh
$EDITOR global_skills/<name>/SKILL.md
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

### Cross-repository prerequisite

`defaultDependencies` loads `graphify-policy` and
`solution-placement-policy` for every canonical skill. After adding or changing
a skill, run:

```sh
skillnet catalog lint
```

Then regenerate the relevant views.

## Fresh Host Bootstrap

Clone this repository and every project repository listed in the centralized Skillnet config, then run:

```sh
home-manager switch
```

Home Manager installs `skillnet` and materializes the generated symlink views from the canonical stores.

## Planning

Planning ownership belongs to the active LLM harness. The harness chooses
whether to plan, which model/provider/effort to use, how to dispatch work, and
when to pause or resume it. Skills may provide evidence, domain procedures,
execution checklists, or plan-audit support; they must not route models or
replace the harness's planning loop.

The canonical `global_skills/` stores and Skillnet manifest are the source of
truth for the current skill set. Generate catalog views locally when needed.
