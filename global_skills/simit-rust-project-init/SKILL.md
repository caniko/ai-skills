---
name: simit-rust-project-init
description: Route Rust/Cargo simit initialization to ordinary CI or strict crates.io release setup. Use when the requested flake/CI wiring could be either path.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

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

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
