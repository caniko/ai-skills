---
name: nixpkgs-pr
description: "Create, update, repair, and review pull requests against `NixOS/nixpkgs`: prepare clean branches or worktrees, run targeted local validation, push to a fork, open or fix draft PRs, format the PR body from the nixpkgs template, and review them using the configured `caniko/nixpkgs-review-gha` fork. Use when the user asks to upstream something to nixpkgs, send something to nixpkgs, fix or shepherd a nixpkgs PR, rerun nixpkgs-review-gha, or otherwise publish or update nixpkgs package or module work."
---

# nixpkgs-pr

## Trigger phrases

Use this skill when the user says things like:

- "upstream this to nixpkgs"
- "send this to nixpkgs"
- "nixpkgs ASAP"
- "open a nixpkgs PR"
- "update my nixpkgs PR"
- "fix my nixpkgs PR"
- "shepherd this nixpkgs PR"
- "run nixpkgs-review-gha"
- "rerun nixpkgs-review-gha"

## Workflow

1. Verify scope and repository state first.
   Run `git status -sb`, `git remote -v`, and `gh auth status`.
   Confirm `upstream` points to `NixOS/nixpkgs` and `origin` is the user's fork.
   If the current checkout is dirty or on an unrelated branch, prefer a separate worktree from the latest fetched `upstream/master`.
   If you are repairing an existing PR, fetch the PR metadata and inspect failing upstream CI before making changes.

2. Prepare an isolated branch for the nixpkgs change.
   Fetch `upstream/master`.
   Branch from the fetched upstream tip, not from unrelated local work.
   Keep the change narrowly scoped and stage explicit paths only.

3. Validate locally before publishing.
   Run the most relevant local checks for the touched package or module, usually `nix build .#<attr>` plus a basic smoke test if the output is executable.
   Run `nix fmt <touched-file>` or the repository formatter when formatting is relevant.
   Treat local `nixpkgs-review` as optional supplemental checking only. It does not replace the required GitHub Actions review.

4. Add and validate automatic update definitions.
   For new packages and version bumps with discoverable upstream releases, use `nix-update <attr>` as the default generator for release, hash, and cargo/vendor hash updates whenever a newer release exists.
   Add `nix-update-script` to the package function arguments and define `passthru.updateScript` so the package can be maintained by `maintainers/scripts/update.nix` and nixpkgs-update automation.
   Prefer the standard form for normal GitHub or tag-based sources:

   ```nix
   passthru.updateScript = nix-update-script { };
   ```

   Use `extraArgs` only when the upstream version scheme requires it, such as branch tracking, GitHub-release-only tracking, or a custom version regex.
   Validate the updater before publishing:

   ```bash
   nix eval --impure --expr 'let pkgs = import ./. { config.allowUnfree = true; }; in pkgs.<attr>.updateScript'
   nix-shell maintainers/scripts/update.nix --argstr package <attr>
   ```

   Run the update script from a clean or intentionally staged worktree, inspect any generated diff, and keep only intended package-update changes.
   If the updater cannot run, stop and report the missing source, why it is required, the upstream producer, the exact command or workflow to regenerate it, and the validation command that proves it is fixed.

5. Publish the branch and open the PR.
   Push to `origin` with tracking.
   Open a draft PR against `master` unless the user explicitly asks for ready-for-review.
   Use a standard nixpkgs title such as `pname: old -> new`.
   Always read the nixpkgs PR template before creating or updating the PR body:

   ```bash
   gh api repos/NixOS/nixpkgs/contents/.github/PULL_REQUEST_TEMPLATE.md \
     -H 'Accept: application/vnd.github.raw+json'
   ```

   Write the PR body in two parts:

   - a short human summary of what changed, why it changed, and any review notes
   - the standard nixpkgs template, filled truthfully

   Check only boxes that are already true. If `nixpkgs-review-gha` is still running, leave the `Ran nixpkgs-review` box unchecked and include the run URL in the summary. After the review finishes successfully, update the PR body again and check that box.

6. Review the PR with `caniko/nixpkgs-review-gha`.
   This step is mandatory for this skill. Do not substitute local-only review.
   Read [references/nixpkgs-review-gha.md](references/nixpkgs-review-gha.md) when dispatching the workflow or diagnosing failures.
   Use the configured review repository:

   ```bash
   review_repo="${NIXPKGS_REVIEW_GHA_REPO:-caniko/nixpkgs-review-gha}"
   ```

   Verify that the repo exists and that workflows are available:

   ```bash
   gh repo view "$review_repo" --json nameWithOwner,url,viewerPermission
   gh workflow list -R "$review_repo"
   ```

   If that fails, stop and tell the user to repair or recreate `caniko/nixpkgs-review-gha` from `Defelo/nixpkgs-review-gha` and enable Actions. Do not silently skip the review.

   Dispatch the review workflow with conservative defaults:

   ```bash
   gh workflow run review.yml -R "$review_repo" \
     -f pr="$pr_number" \
     -f x86_64-linux=true \
     -f aarch64-linux=true \
     -f x86_64-darwin=yes_sandbox_relaxed \
     -f aarch64-darwin=yes_sandbox_relaxed \
     -f push-to-cache=true \
     -f upterm=false \
     -f post-result=true \
     -f on-success=nothing
   ```

   After dispatch, capture the run URL and, when useful, monitor it with `gh run list` or `gh run watch`.
   If you had an older review run for the same PR head, cancel it or treat it as stale after pushing the new commit.

7. Close out deliberately.
   If `nixpkgs-review-gha` is still running, report the run URL and current status, and keep the PR body's `Ran nixpkgs-review` box unchecked.
   If it passed, summarize the result and update the PR body so the checklist matches the completed review.
   Default to keeping the PR as draft until the user asks to mark it ready or the surrounding workflow clearly calls for it.

## Failure Modes

- Mixed worktree: move the nixpkgs change to a dedicated worktree or branch before staging.
- Missing review repo or workflow permissions: stop and point the user to the setup steps in the reference file.
- Workflow dispatch 404 or permission error: assume the fork is missing, Actions are disabled, or the user lacks access.
- Stale review run after a new push: cancel it or ignore it, then dispatch a fresh run for the current PR head.
- Failed review run: inspect the GitHub Actions logs, fix the branch, push the update, and rerun the same workflow.
- Unrelated local changes: never `git add -A` unless the user explicitly confirms the whole worktree belongs in scope.
