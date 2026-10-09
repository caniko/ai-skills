# caniko's AI Skills

This repository is the canonical store for global skills at `ai-skills/global_skills/<name>/`. Per-project skills live in each project's own repository at `<project>/.skills/<name>/`; `~/.claude/skills`, `~/.agents/skills`, `<project>/.claude/skills`, and `<project>/.agents/skills` are generated views, not authored content.

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

Host-specific entrypoints live under `host_skills/` and are registered through
its external `Skillnet.pkl` (schema 3). Skillnet requires an explicit destination
`host` and intersects host restrictions with existing user grants. The Atlas-only
`atlas-nomad-orchestration` adapter composes the global
`multi-host-agent-orchestration` skill through generated dependency links.
Keeping this source outside the legacy global scan prevents older consumers from
discovering it before the host-capable package and configuration are deployed.

## Authoring

### Greptile review skills

The MIT-licensed `check-pr`, `greploop`, and `cli-review` packages are imported
from `greptileai/skills` at a recorded immutable revision. Each package retains
its license, provenance and upstream references, plus a repository contract for
scoped fixes, revision-bound evidence and hosted-only validation.

- `check-pr`: inspect review feedback, descriptions and CI, then address confirmed issues.
- `greploop`: iterate through current Greptile reviews with a bounded repair loop.
- `cli-review`: explicitly authorized pre-PR CLI review; use hosted review for hosted-only tasks.

These packages do not enable automatic Greptile usage. Honor the operator's
provider policy: when Greptile is excluded, do not request its review or treat
its installation, credits, or score as a prerequisite for unrelated qualification.

Skillnet discovers these packages from `global_skills/` using the existing
canonical-store configuration. Run `skillnet catalog generate`, then
`skillnet view sync --all` to materialize configured consumer views. View sync evaluates
configured Pkl manifests; during a no-local-evaluation pass, defer that step to
the permitted qualification environment. The `Skillnet.pkl` manifest declares
the three entrypoints and their review/Git dependencies. No subscription or second skill store
is required.

`ci/skillnet-composition.yaml` contains the hosted composition gate. Install it
as `.github/workflows/skillnet.yaml` with a workflow-scoped publishing credential.
The gate composes all three skills through published Skillnet and verifies the
entrypoints, repository contracts and transitive dependencies.

The hosted gate uploads `greptile-qualification-skills-<head>` with a portable
archive, provenance and SHA-256 checksums for inspection, **not installation**.
Every event, including protected-branch pushes, records `consumable: false` and
`trust: "qualification-only"`, plus event, ref, protection, source repository and
PR base metadata. A successful candidate-controlled test is not trusted release
authorization. Verify the exact run/source and checksums when auditing evidence;
do not load these artifacts as agent instructions. Consumable publication requires
a separate trusted source/release audit. Keep canonical authored packages in
`global_skills/`; this template does not publish qualified releases.

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

`defaultDependencies` loads `chaosbox-policy` and
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
