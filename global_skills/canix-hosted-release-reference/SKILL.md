---
name: canix-hosted-release-reference
description: Reusable release workflow for flake-backed projects deployed through canix to NixOS hosts. Use when a project is consumed as a canix flake input and the user asks to release, deploy, bump, verify, or roll a new production version to a named canix host.
---

# Canix Hosted Release Reference

Load [canix-structure-reference](.skillnet/deps/canix-structure-reference/SKILL.md) before
resolving project paths or generated canix consumers.

## Purpose

Release an upstream flake-backed project through canix to a named NixOS host.
Resolve canix-owned source checkouts through the structure reference. This is a
reference skill for project-specific wrappers; combine it with the relevant
project skill and defaults.

## Required Inputs

Resolve these before mutating anything:

- Source repo path and branch/ref canix tracks. For local canix-owned projects,
  use the workspace path, not a guessed sibling checkout.
- canix input name.
- canix repo path, normally `/data/nvme0/can/canix`.
- Target host name as declared in canix, such as `atlas`.
- Service and public endpoint checks that prove the release is live.

If any required source or artifact is missing, stop and report what is missing, why it is required, the upstream producer, the regeneration workflow, and the validation command.

## Release Workflow

1. Preflight the source repo:
   - Run `git status --porcelain`, `git rev-parse --abbrev-ref HEAD`, `git rev-parse HEAD`, and `git tag --points-at HEAD`.
   - Stop on uncommitted source changes unless the user explicitly asks to include them.
   - If semver is part of the release, ensure the package metadata, lockfile, visible version markers, and tag agree.

2. Validate the source project:
   - Run the project’s relevant build/test checks before touching canix.
   - Prefer flake outputs the production package uses, for example `nix build .#docs --no-link` and `nix build .#raven --no-link`.
   - If a required generated artifact is ignored by git but needed by Nix, stage or commit its source, not the generated output, unless the repo intentionally tracks generated output.

3. Update canix:
   - Inspect `/data/nvme0/can/canix/flake.nix` and confirm the input exists.
   - Run `nix flake update <input>` from the canix repo.
   - Check `git diff -- flake.lock`; the target input must move to the intended source commit.
   - Do not revert unrelated dirty canix changes. If unrelated `flake.lock` hunks already exist, report them separately and avoid claiming they belong to this release.

4. Evaluate the target host:
   - Prefer `nix eval --raw .#nixosConfigurations.<host>.config.system.build.toplevel.drvPath`.
   - Use full `nix flake check --no-build` only when it is appropriate for the repo state; if unrelated host evaluation fails, report the failing host and continue only with a host-specific eval for the release target.

5. Switch the host with canix:
   - Prefer the canix CLI over raw `nixos-rebuild`.
   - Current admin command shape is `canix rebuild switch <host>`.
   - `canix rebuild` automatically runs a cargo-check preflight before the nix build. Use `--no-cargo-check` to skip it if needed.
   - Atlas is the sole build host. For aarch64 targets (e.g. `thething`), `canix rebuild switch thething` uses `.#thething-crossbow` and builds from Atlas; never perform a native aarch64 build on the target and never configure the target as a Nix remote builder.
   - Target SSH is limited to read-only service inspection and post-switch verification. Do not run `nix build`, `nix-store -r`, Cargo, or Crossbow compilation on the target.
   - If the installed personal `canix` lacks rebuild commands, build/use the admin package from canix, then run its `bin/canix`.
   - Treat a nonzero switch as important. If the target services started and endpoint checks pass despite an unrelated unit failure, report both facts clearly.

6. Verify production:
   - Confirm relevant units with `systemctl is-active ...` and `systemctl show -p ExecStart <service>`.
   - Confirm the expected package version or store path appears in the running service.
   - Run public endpoint checks with `curl -I` or stronger checks when content matters.
   - Report warnings such as degraded upstream model backends separately from release success.

## Failure Rules

- Never fabricate, synthesize, or silently substitute missing release inputs.
- Never force-push, reset, checkout away, or clean unrelated changes.
- If canix switch fails, include the failing unit, exact reason, and the command that will prove it is fixed.
- If canix already points at the intended source commit and services/endpoints verify, treat the release as current and avoid an unnecessary switch.
