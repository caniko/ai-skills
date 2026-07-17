---
name: simit-dependent-fixes
description: Use Workspace.pkl and simit's feature registry to repair downstream projects affected by simit changes, release regressions, generated CI/flake drift, or command layouts.
metadata:
  short-description: Fix simit downstream projects via the registry
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Simit Dependent Fixes

Load [canix-structure-reference](../canix-structure-reference/SKILL.md) when
working from canix; it owns project scope and checkout paths. This skill owns
the Simit-dependent repair loop.

## Purpose

This skill is a domain-grounded research specialist (simit ecosystem); see the Reference section for its place in the research family.

Use `simit projects` as the inventory for downstream Rust projects that have
simit-managed files or simit feature usage. When operating from canix, the
project universe and checkout paths come from the canix-owned workspace
registry; simit is not the location authority. Fix affected
dependents directly, but first decide whether the root
cause belongs in simit itself. If generated output is wrong, brittle, noisy,
or missing migration coverage, fix simit and add a regression before touching
many downstream repositories.

## Command Resolution

Prefer the newest installed `simit`:

```sh
simit --version
simit projects --help
```

If a simit checkout is available and the task is about unreleased simit changes,
use it explicitly without changing the downstream project:

```sh
cargo run --manifest-path ~/canix/canix/projects/repos/owned/codeberg.org/caniko/simit/Cargo.toml -- projects list --json
```

Current command shape is grouped:

```sh
simit init flake --check --diff
simit init ci --platform forgejo --check --diff
simit release trust check
simit projects list --json
```

If an older downstream project still references `init-flake` or `init-ci`,
regenerate with current simit rather than preserving obsolete command spelling.

## Registry Workflow

1. Validate canix's workspace registry, then refresh or inspect simit's feature
   registry:
   ```sh
   cd ~/canix/canix
   canix workspace check
   simit projects scan
   simit projects list --json
   ```

   The fleet sweep is mandatory before reporting. Enumerate every applicable
   canix project path from `projects/Workspace.pkl`, then correlate it with
   `simit projects list --json`, including projects whose feature is `absent`
   because hand-rolled workflows can carry the same regression. Skip only
   ephemeral `/tmp/*` scratch entries and manifest entries that are archived,
   personal, or explicitly non-Rust unless the user names them. Check every
   applicable project under the registered roots and report one verdict for
   each; never stop at the first failing dependent.

2. If the Simit feature registry is sparse or the user names a filesystem area,
   discover within the canix-owned workspace:
   ```sh
   simit projects discover ~/canix/canix/projects/repos/owned
   simit projects discover ~/canix/canix/projects/repos/owned --json
   ```

   Do not add a second location registry in Simit; update
   `projects/Workspace.pkl` when project ownership or paths change.

   Use `--include-empty` only when intentionally registering bare Rust projects
   for future simit adoption. Default discovery should skip non-simit projects.

3. Select affected projects by evidence, not by guessing:
   - managed `ci`, `flake`, `changelog`, `release_trust`, or packaging features
   - generated workflows containing obsolete commands
   - release workflows or docs using the wrong crates.io secret name
     (`CRATES_IO_API_TOKEN` is the repository secret; export it to
     `CARGO_REGISTRY_TOKEN` only as Cargo's runtime environment variable)
   - check failures from `simit init ... --check --diff`
   - user-reported CI or release failures after a simit release

4. For each selected project, enter the repo and check ownership state:
   ```sh
   git status --short
   git remote -v
   ```

   Do not overwrite unrelated local changes. If existing changes touch files
   you must edit, read them and work with them.

## Downstream Repair Loop

For each dependent:

1. Run the relevant simit checks before editing:
   ```sh
   simit init flake --check --diff
   simit release trust check
   simit init ci --platform <forgejo|github> --check --diff
   ```

2. Regenerate only the managed surface that drifted:
   ```sh
   simit init flake
   simit init ci --platform <forgejo|github> [same justified options]
   simit release trust init
   ```

   Preserve project-specific options such as `--runner`, `--windows-runner`,
   `--runtime nix`, release artifact flags, package manager flags, and strict
   checks when the existing workflow or project config shows they are intended.

3. Validate locally with the narrowest meaningful gates:
   ```sh
   simit init flake --check --diff
   simit release trust check
   simit init ci --platform <platform> --check --diff
   nix flake check --no-build
   cargo test --all-features
   ```

   Add project-specific checks when CI, docs, packaging, or release workflows
   are the affected surface.

4. If the repo is on Codeberg/Forgejo and release CI is involved, use the
   Codeberg/Forgejo CI skill or `fj` before guessing at remote state.

## When To Fix Simit First

Stop downstream patching and inspect simit itself when any of these are true:

- two or more dependents need the same manual edit to generated files
- `simit init ... --check` fails on files generated by current simit
- generated workflows require user config even though equivalent CLI overrides
  were supplied
- discovery reports generic Rust projects as simit-managed by accident
- discovery errors on skipped projects that should not need Cargo metadata
- generated CI uses obsolete simit commands or loses runner/platform flags
- the repair needs hand-editing generated files that simit should own

In the simit repo, add a focused regression test for the downstream failure,
fix the generator/discovery/check behavior, and run:

```sh
cargo fmt --all -- --check
cargo test --all-features
cargo clippy --all-targets --all-features -- --deny warnings
cargo package --list
```

After releasing or using the fixed simit checkout, return to the registry and
regenerate downstream projects with the fixed command.

## Reporting

Close with:

- simit version or checkout used
- canix workspace scope and registry query/discovery scope (summarize the
  `Workspace.pkl` entries and `simit projects list` output that drove the
  sweep)
- **per-project verdict for every applicable non-scratch canix workspace entry**
  — `affected`, `clean`, or `skipped (<reason>)`; include its Simit feature
  status when present.
  An omission is a bug; if a project was not checked, say so explicitly with
  the reason. Ephemeral `/tmp/*` paths may be collapsed into a single line.
- projects changed and validation per project
- simit fixes made, if any
- remaining remote CI or publish state, if checked

## Reference

- Generic research base: [evidence-first-research](../evidence-first-research/SKILL.md) — this skill is a simit-grounded specialization of the generic evidence-first research pattern. Use the base directly for non-simit research.
- Sibling research router: [research-routing](../research-routing/SKILL.md) — picks the right research specialist when the request is ambiguous between simit and other domains.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
