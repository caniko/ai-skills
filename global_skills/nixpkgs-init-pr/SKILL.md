---
name: nixpkgs-init-pr
description: "Create and review general nixpkgs PRs: prepare branches, validate, fill the template, and use nixpkgs-review-gha. Route build-log failures to nixpkgs-build-failure-pr."
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# nixpkgs-init-pr

## Shared references

Before publishing or commenting upstream, read the common references in `../nixpkgs-pr-common/references/`:

- `decorum.md` for contribution standards, narrow scope, and duplicate checks.
- `pr-template.md` before creating or updating a PR body.
- `nixpkgs-review-gha.md` before dispatching or diagnosing GitHub Actions review.

## Workflow

1. Verify repository state with `git status -sb`, `git remote -v`, and `gh auth status`.
   Confirm `upstream` is `NixOS/nixpkgs` and `origin` is the user's fork.
   If the checkout is dirty or on unrelated work, create a separate worktree from latest `upstream/master`.

 2. Prepare a narrow branch from the right upstream base.
    Default to `upstream/master`.  If the change is a mass rebuild, use
    `upstream/staging` instead.  See `../nixpkgs-pr-common/SKILL.md` for the
    full branching rules.  The `nixos-*` / `nixpkgs-*` branches are
    channel-script push targets and must never be used as merge targets.
    Use a release branch only for explicit backports.
    Stage explicit paths only and keep unrelated local changes untouched.

3. Implement the package, module, or maintenance change using nixpkgs conventions.
   For new packages, set `strictDeps = true;` and `__structuredAttrs = true;` unless a concrete incompatibility prevents it.
   For discoverable package updates, prefer `nix-update <attr>` and add `passthru.updateScript = nix-update-script { };` so the package is maintainable by `maintainers/scripts/update.nix` and nixpkgs-update automation. Use `extraArgs` only when the version scheme requires it (branch tracking, GitHub-release-only tracking, custom version regex). Validate the updater before publishing, then keep only intended package-update changes from any generated diff:

   ```bash
   nix eval --impure --expr 'let pkgs = import ./. { config.allowUnfree = true; }; in pkgs.<attr>.updateScript'
   nix-shell maintainers/scripts/update.nix --argstr package <attr>
   ```

   If the updater cannot run, stop and report per the missing-data contract in `../nixpkgs-pr-common/references/decorum.md`.

4. Validate before publishing.
   Run the targeted `nix build .#<attr>` or module/test check, plus smoke tests for relevant executables.
   Run `nix fmt <touched-file>` when formatting applies.
   After committing, run `./ci/nixpkgs-vet.sh master https://github.com/NixOS/nixpkgs.git`; this evaluates committed `HEAD`, not dirty edits.

5. Search for duplicate PRs before opening one.
   Search open and recently closed `NixOS/nixpkgs` PRs by package/module name and likely title fragments.
   Stop and report a substantially similar PR unless the user explicitly wants a replacement or follow-up.

6. Publish and open a draft PR.
   Push the branch to `origin`.
   Use a standard title such as `pname: old -> new` or `<module>: <short change>`.
   Fetch the live PR template and fill it truthfully, with a short maintainer-facing summary above it.
   Check only boxes backed by completed validation.

7. Run `caniko/nixpkgs-review-gha`.
   Dispatch the workflow after the draft PR exists.
   If the review is still running, keep the `Ran nixpkgs-review` box unchecked and include the run URL in the PR summary.
   If it passes, update the PR body so the checklist reflects the completed review.

## Failure modes

- Mixed worktree: move the nixpkgs change to a dedicated worktree or branch before staging.
- Missing review repo or workflow permissions: stop and point to `nixpkgs-review-gha.md`.
- Stale review after a new push: ignore or cancel the stale run and dispatch a fresh run for the current PR head.
- Failed review: inspect logs, fix the branch, push the update, and rerun the workflow.
- Missing generated source or updater output: stop and report the missing artifact, upstream producer, regeneration command, and validation command.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
