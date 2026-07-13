---
name: simit-rust-project-init
description: Route Rust/Cargo simit initialization requests to the right child skill. Use when Codex is asked to apply, refresh, or validate simit Rust flake or CI wiring but the request may be either ordinary project CI setup or strict crates.io release infrastructure.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# Simit Rust Project Init

## Purpose

This is a compatibility router for Rust simit initialization. Keep the old skill
name usable, then load exactly one child skill for the actual work.

## Routing

Load `../simit-rust-project-ci-init/SKILL.md` when the project is an ordinary
Rust/Cargo project that needs good simit-managed flake or CI wiring, including
flake-integrated Rust tools, services, libraries, binaries, workspaces, custom
flake checks, devShells, packages, apps, modules, or Nix libraries that need CI
but are not being prepared for release publishing.

Load `../simit-rust-crate-release-init/SKILL.md` when the task is release
oriented, including crates.io preparation, explicit `--publish-crates` or
`[ci].publish_crates = true`, publish workflows, release signing, maintainer
trust roots, `keys/maintainers.gpg`, package artifacts, docs.rs readiness,
`cargo package`, or any `rust-crate-*` release-prep skill.

If both paths appear plausible, inspect project files first. Prefer the generic
CI child unless repository evidence or the user request clearly requires release
infrastructure. Do not silently add release signing or publish workflow
requirements to a project that only needs CI.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
