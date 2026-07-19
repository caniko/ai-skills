---
name: rust-fleet-upgrade
description: Audit and align Rust toolchains, dependencies, locks, and MSRV across caniko projects. Use for fleet-wide upgrades or coordinated dependency refreshes.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

# Rust fleet upgrade

Use the registry and the canix CLI as the compact source of truth. Do not scan every repository into the conversation or mutate unrelated dirty work.

## Workflow

1. Read `canix-project-space-reference` and `rust-dependencies` when repository scope or dependency policy is unclear.
2. Start with the machine-readable inventory:

   ```text
   canix workspace rust audit --output json --changes-only
   ```

   Use `--project ID` for a focused pass, `--include-forks` only when fork compatibility is in scope, `--refresh` to update crates.io metadata, and `--offline` when network access is unavailable.

3. Turn the inventory into actions with:

   ```text
   canix workspace rust plan --output json
   ```

   Group compatible updates first. Major-version upgrades are allowed when the newest release is beta, release-candidate, or another clearly maintained prerelease; do not require waiting for a stable tag by policy. The skill decides whether to adopt it from release recency/activity, changelog/API compatibility, MSRV, dependency graph impact, and project validation. Keep an intentional prerelease when it is the best compatible target, and never downgrade it without evidence.

4. Verify before and after each wave:

   ```text
   canix workspace rust verify --output json --project ID
   ```

   Then run the project’s normal `cargo fmt`, `cargo check`, tests, clippy, and Nix/CI checks. Keep the fleet’s primary toolchain on the latest stable reported by the audit; preserve a declared lower MSRV when the project promises one.

5. Apply one clean project at a time. The guarded command is:

   ```text
   canix workspace rust upgrade ID --apply
   ```

   It refuses dirty dependency/toolchain/flake files unless `--allow-dirty` is explicitly justified. Review the diff and lockfile before proceeding to the next project.

## Safety and token efficiency

- Scope from `projects/Workspace.pkl`; active owned projects are the default. Do not edit revoked, personal, upstream, or maintained-fork entries unless the user explicitly includes them.
- Preserve existing edits. If a target is dirty, report the exact files and defer it rather than resetting or overwriting them.
- Prefer JSON plus `--changes-only`, project filters, and cached crates.io metadata. Summarize only shared dependencies, divergent requirements, blockers, and validation results.
- For a prerelease major, record the evidence and label the decision `adopt`, `defer`, or `reject`: adopt active, well-supported releases that pass the project checks; defer releases with unresolved migration or ecosystem gaps; reject releases that are abandoned, incompatible, or unsafe. A beta/RC is not an automatic blocker.
- Do not push, publish, or rewrite generated sidecars without explicit authorization. Record toolchain, dependency, and validation changes in the project’s normal files.

## Solution Placement

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
