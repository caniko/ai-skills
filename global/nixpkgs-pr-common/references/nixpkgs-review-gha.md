# nixpkgs-review-gha

Use this reference when you need to set up or run the required GitHub Actions review for a nixpkgs PR.

## What it is

`Defelo/nixpkgs-review-gha` runs `nixpkgs-review` in GitHub Actions across:

- `x86_64-linux`
- `aarch64-linux`
- `x86_64-darwin`
- `aarch64-darwin`

It can also post the result back to the nixpkgs pull request when the review repository has a `GH_TOKEN` secret configured.

## Required setup

The expected review repository in this environment is `caniko/nixpkgs-review-gha`.

If that repository does not exist or workflow dispatch fails:

1. Fork `https://github.com/Defelo/nixpkgs-review-gha`.
2. Ensure the fork is named `caniko/nixpkgs-review-gha`.
3. Open the fork's `Actions` tab and enable workflows.
4. If you want automatic comments on reviewed nixpkgs PRs, create a classic personal access token with `public_repo` scope and store it as the `GH_TOKEN` repository secret in the fork.
5. If you want automatic self-updates, create a fine-grained token for the fork with read/write access to Contents and Workflows and store it as `GH_SELF_UPDATE_TOKEN`.

If these prerequisites are not met, stop and tell the user exactly which step is missing. Do not silently replace this review with local `nixpkgs-review`.

## Review workflow inputs

The repository's `review.yml` workflow accepts these inputs:

| Input | Meaning | Good default |
|---|---|---|
| `pr` | nixpkgs pull request number | required |
| `x86_64-linux` | run Linux review on x86_64 | `true` |
| `aarch64-linux` | run Linux review on aarch64 | `true` |
| `x86_64-darwin` | run Darwin review on x86_64 | `yes_sandbox_relaxed` |
| `aarch64-darwin` | run Darwin review on aarch64 | `yes_sandbox_relaxed` |
| `extra-args` | extra `nixpkgs-review` args | empty unless needed |
| `push-to-cache` | push review results to configured cache | `true` |
| `upterm` | start an SSH debug session after review | `false` |
| `post-result` | post a comment back to the nixpkgs PR | `true` |
| `on-success` | automation after a successful review | `nothing` |

Default `on-success` to `nothing`. Only use `mark_as_ready`, `approve`, or `merge` when the user explicitly asks for that automation.

## Dispatch command

Resolve the review repository:

```bash
review_repo="${NIXPKGS_REVIEW_GHA_REPO:-caniko/nixpkgs-review-gha}"
```

Sanity check it:

```bash
gh repo view "$review_repo" --json nameWithOwner,url,viewerPermission
gh workflow list -R "$review_repo"
```

Run the review:

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

Add `-f extra-args='--package <attr>'` only when you intentionally want to narrow or alter the review.

## Finding the run

The workflow run name is `review #<pr-number>` optionally followed by the extra args in parentheses.

Useful commands:

```bash
gh run list -R "$review_repo" --workflow review.yml --limit 10
gh run view -R "$review_repo" <run-id>
gh run watch -R "$review_repo" <run-id> --interval 30
```

If the workflow has `GH_TOKEN` configured and `post-result=true`, it will comment on the nixpkgs PR automatically. Otherwise, use the run summary and logs to report the result manually.

## Interpreting success

Treat the review as passed only when the workflow concludes successfully and the per-system reports do not show failed rebuilds that matter for the user's change.

If the run fails:

1. Open the failing job logs.
2. Identify whether the problem is a real package failure, a sandbox issue, or review repo misconfiguration.
3. Fix the nixpkgs branch or the review repo setup as appropriate.
4. Push the updated nixpkgs branch and rerun the workflow.
