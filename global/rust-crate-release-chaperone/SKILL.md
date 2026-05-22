---
name: rust-crate-release-chaperone
description: "Chaperone Rust crate releases end to end using simit-managed hooks. Use when Codex should prepare, run, or babysit a Rust crate release; install or verify simit hooks in a repository; run release hooks/checks; fix bugs, lint failures, packaging failures, docs failures, CI workflow failures, Nix failures, cargo-deny/audit failures, or other blockers that arise from release hooks; and repeat validation until the release is ready or a required upstream artifact is missing."
---

# Rust Crate Release Chaperone

## Required Skills

Load these when the work reaches their scope:

- `/home/can/.agents/skills/rust-crate-release-reference/SKILL.md` for common source-integrity, simit infrastructure, changelog, release-bar, validation, blocker-classification, and publish-boundary rules.
- `/home/can/.codex/skills/simit-project-init/SKILL.md` for installing and checking simit-managed flake and CI hooks.
- `/home/can/.agents/skills/rust-crate-release-prep/SKILL.md` only when broader release preparation or component skill routing is needed beyond hook execution.
- `/home/can/.agents/skills/rust-crate-quality-gates/SKILL.md` for strict validation commands.
- `/home/can/.agents/skills/rust-crate-publish-workflow/SKILL.md` when the work reaches final publish sequencing, remote tag push, CI publication orchestration, or post-publish crates.io verification.

## Core Rule

Load `/home/can/.agents/skills/rust-crate-release-reference/SKILL.md` first and apply its shared release rules throughout the chaperone loop.

Own the release-hook feedback loop. Do not stop at the first hook failure when the failure is fixable in the repository. Diagnose it, patch the project, rerun the failed hook or the narrowest equivalent validation, and continue until the release hooks pass or the remaining blocker requires missing upstream input.

Own the full end-to-end release. Once repository-owned failures are fixed and publish prerequisites are satisfied, continue through release commit/tag creation, remote push, CI-triggered publication, and external crates.io verification until the new version is live or a real external blocker prevents it.

## Chaperone Loop

1. Inspect repository state: `Cargo.toml`, `Cargo.lock`, `CHANGELOG*`, `README*`, `LICENSE*`, `src/`, `tests/`, `docs/`, `flake.nix`, `nix/`, CI workflows, remotes, default branch, tags, recent commits, and current git status.
2. Install or refresh simit hooks with `simit init-flake` and `simit init-ci --platform <platform>` unless the repository has an explicit documented policy against one of them. Let `simit init-ci` generate `keys/maintainers.gpg`; if signing trust fails, run `simit release trust status`, then `simit release trust init` or `simit release trust check` before reporting a blocker.
3. Detect whether the repository should reuse the current version instead of bumping it:
   - Use `simit release sync-up` when repository evidence shows the current version is already the intended release and `HEAD` only contains release-repair work for that same version.
   - Require concrete evidence before taking the sync-up path:
     - the current `Cargo.toml` version already has a local tag or is already published for the crate being released;
     - the delta from that version tag to `HEAD` is limited to fixing a failed release, CI/publish breakage, packaging metadata, generated release infrastructure, or similarly non-new release repairs;
     - there is no new user-visible capability, intentional behavior change, new public API/CLI/config surface, or other changelog-worthy release scope beyond repairing the already-tagged version.
   - Validate the "no meaningful change" conclusion from repository facts such as `git diff <version-tag>..HEAD`, changelog state, package metadata, and recent commits. Do not guess.
   - If the evidence is incomplete or mixed, do not silently choose sync-up. Report the missing or conflicting source and continue with the normal bump decision only when repository facts support it.
4. If sync-up does not apply, choose the semver bump from repository-owned changes before release gates:
   - `major` for intentional breaking API/CLI/config behavior changes.
   - `minor` for backward-compatible public features, new commands, new config sources, new generated integration surfaces, or meaningful new capabilities.
   - `patch` for bug fixes, documentation corrections, CI/release repair, dependency-policy repair, or internal cleanup without new public capability.
   - If the current `Cargo.toml` version already exists on crates.io or already has a local tag, bump to the next appropriate version before publish.
5. Apply the chosen release action:
   - For the no-meaningful-change path, run `simit release sync-up` and add `--push` when the workflow requires retargeting the remote tag after local checks pass.
   - Prefer `simit release <major|minor|patch> -m "Release <crate> <version>"` when the worktree is clean enough for simit to own the release commit and tag.
   - If the worktree contains a prepared release candidate with related changes that should ship together, update the version files (`Cargo.toml`, `Cargo.lock` when present), promote `CHANGELOG.md` with `simit changelog release <version>` or the equivalent exact Keep a Changelog edit, run release gates, then commit all release-candidate changes together with a proper release commit message.
   - If the worktree has unrelated or not-yet-committable changes, do not force a release commit. Report the unrelated paths and the exact command sequence to commit once the maintainer confirms they belong in the release.
6. Validate changelog presence and release alignment before running release gates.
   - For sync-up, confirm the current version's release entry already exists and that no new unreleased release notes are being silently skipped.
   - For bump-based releases, confirm the target release version aligns with the promoted changelog entry.
7. Validate hook alignment with simit's check modes, including `simit release trust check` when the generated publish workflow verifies signed tags.
8. Run the generated release checks, preferring project wrappers and Nix checks when present.
9. For each failure, identify whether it is a code bug, test bug, docs bug, changelog bug, metadata/package bug, Nix/hook drift, dependency policy issue, missing tool, missing credential, or missing upstream fact.
10. Fix repository-owned bugs directly. Keep patches scoped to the failure. Do not weaken release hooks, delete checks, relax lints, omit changelog entries, or hide failures unless the user explicitly asks and the tradeoff is reported.
11. Rerun the failed hook/check first, then rerun the full relevant release gate once local failures are cleared.
12. Load `/home/can/.agents/skills/rust-crate-publish-workflow/SKILL.md` for final publish sequencing once local release gates pass or only remote push / CI publish checks remain.
13. Verify CI publish prerequisites from authoritative sources before pushing the release:
   - the repository host is Codeberg/Forgejo and the publish workflow is configured to publish on the repository's release tag convention;
   - `cargo search <crate-name> --limit 1` or the crates.io API confirms whether the target version is already published;
   - the repository remote and default branch are correct for the release push;
   - if repository evidence requires a crates.io owner check, use non-secret read-only commands such as `cargo owner --list <crate-name>` only when they work in the available shell, but do not treat missing local tokens as a reason to publish from the local machine.
14. If the release commit and tag do not exist yet, create them with the structured message rules below. Keep the tag name aligned with the repository convention and the publish workflow.
15. Push the release commit and tag to the canonical remote once validation passes. For this skill, the push is the publication trigger; do not run `cargo publish` from the local shell.
16. Observe the remote publication path:
   - inspect the Forgejo/Codeberg workflow that should publish the crate;
   - wait for the publish job outcome when that evidence is available;
   - if the CI publish fails, diagnose the workflow or repository-owned cause and iterate.
17. Verify publication from an external source:
   - `cargo search <crate-name> --limit 1`,
   - `cargo info <crate-name>` when available, or
   - the crates.io API / package page.
   Continue only until the new version is confirmed live or a propagation/CI/registry blocker is identified.

## Release Commit and Tag Messages

When the chaperone creates the release commit directly, use a structured message:

```text
Release <crate> <version>

Summary:
- <high-signal release change>
- <high-signal release change>

Validation:
- <command that passed>
- <command that passed>
```

When creating a tag, use an annotated tag named exactly like the crate version, matching simit's tag convention, with a structured message:

```text
Release <crate> <version>

Summary:
- <high-signal release change>
- <high-signal release change>

Validation:
- <command that passed>
- <command that passed>
```

Use facts from `CHANGELOG.md` and the validation commands actually run. Do not use empty, generic, or placeholder messages such as `release <version>` unless no richer facts are available, and if no richer facts are available, stop and report the missing release notes source.

## Final Report

Report:

- Hook installation or refresh performed.
- Release action chosen, including whether the chaperone used `simit release sync-up` for a no-meaningful-change repair or a normal semver bump, why that path was chosen, and whether the bump was applied by `simit release` or by direct version/changelog edits due to worktree constraints.
- Commit/tag status, including whether all release-candidate changes were committed and whether a tag was created or intentionally left for the maintainer.
- Push/publish status, including whether the release commit and tag were pushed, which CI workflow was expected to publish the crate, and how crates.io publication was verified.
- Changelog status, including the version checked and any entries added or repaired.
- Release hooks/checks run and their final status.
- Release signing trust-root status, including whether simit generated or checked `keys/maintainers.gpg`.
- Bugs fixed, grouped by affected area.
- Any remaining blockers with the required producer, regeneration workflow, and validation command.
- Whether the new version is confirmed live on crates.io, and if not, the exact external blocker that prevented publication.
