# caniko's AI Skills

This repository is the canonical store for global skills at `ai-skills/global_skills/<name>/`. Per-project skills live in each project's own repository at `<project>/.skills/<name>/`; `~/.claude/skills`, `~/.agents/skills`, `<project>/.claude/skills`, and `<project>/.agents/skills` are generated views, not authored content. The old `<ai-skills>/projects/` tree is obsolete local state and may be removed after validation.

## Layout

```text
global_skills/
  <skill-name>/              # canonical global skills

docs/planning/
  skill-retirement-research.md  # historical audit and provenance
```

Top-level generated catalog files:

- `CATALOG.md`
- `ROUTING.md`
- `SKILL_CONFLICTS.md`

Configuration is centralized per user by Skillnet:

- `$XDG_CONFIG_HOME/skillnet/skillnet.toml` declares this repo root and the project repositories whose `.skills/` directories are canonical.
- `$XDG_CONFIG_HOME/skillnet/skillnet.catalog.toml` declares catalog metadata and taxonomy rules.
- Older checkouts that still contain repository-local config can migrate it with `skillnet config migrate`; the command preserves the configured database and subscription state.

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

Every canonical `SKILL.md`, global or project-local, must place this concise paragraph
immediately after its YAML frontmatter:

```markdown
**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.
```

`graphify` itself is the only exemption because self-invocation would recurse;
its usage and multi-path reference must continue to define the merged
cross-repository graph workflow directly. After adding or changing a skill, run:

```sh
bash scripts/check-graphify-policy.sh
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

Historical planning and audit provenance lives in
[`docs/planning/skill-retirement-research.md`](docs/planning/skill-retirement-research.md).
It is not the active source of truth for the current skill set; inspect the
canonical `global_skills/` stores and generated catalog for that.
