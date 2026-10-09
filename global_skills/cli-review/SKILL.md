---
name: cli-review
description: >
  Run an explicitly authorized Greptile CLI review before opening a PR and
  summarize verified findings. Use hosted PR review for hosted-only tasks.
license: MIT
metadata:
  author: greptileai
  version: "1.0"
allowed-tools: Bash(git:*) Bash(greptile:*) Bash(command:*)
---

# CLI Review

Read [the repository contract](references/repository-contract.md) first. For a
hosted-only task, use the hosted PR review flow instead of running this evaluator.

Run a Greptile review from the local checkout and summarize the findings.

## Instructions

### 1. Confirm repository context

Start from the current repository root:

```bash
git rev-parse --show-toplevel
```

If the command fails, tell the user that the Greptile CLI review must be run from a git repository.

### 2. Check for the Greptile CLI

Check whether `greptile` is installed:

```bash
command -v greptile
```

If it is missing, stop and report the prerequisite. Installation requires explicit
authorization and an operator-approved distribution pinned to a release and
verified against its trusted checksum or signature. Do not install a mutable
latest package or pipe a downloaded installer to a shell. If a verified release
is unavailable, leave the review blocked rather than guessing a version or digest.

After the operator provisions it, re-run `command -v greptile` and inspect the
installed CLI's version/help before using it.

### 3. Ensure authentication

Check the signed-in account:

```bash
greptile whoami
```

If the CLI reports that authentication is missing, run:

```bash
greptile login
```

Wait for the user to complete the login flow before continuing.

### 4. Run the review

The CLI reviews committed changes; uncommitted edits are not uploaded. Require a
clean worktree before either review mode, including staged and untracked files:

```bash
WORKTREE_STATUS=$(git status --porcelain --untracked-files=all) || exit 1
if [ -n "$WORKTREE_STATUS" ]; then
  echo "Uncommitted changes are outside CLI review coverage; stop without altering them." >&2
  printf '%s\n' "$WORKTREE_STATUS" >&2
  exit 1
fi
```

Do not stage, stash, discard or commit the user's work merely to pass this guard.
Select the intended target branch from the task or live PR/MR, not the repository
default. If it or its verified target remote is unknown, stop and ask. Fetch that
remote branch freshly, never resolve a possibly stale local/tracking branch:

```bash
: "${REVIEW_TARGET_REMOTE:?Set the verified target repository remote first}"
: "${REVIEW_TARGET_BRANCH:?Set the intended target branch first}"
git fetch --no-tags "$REVIEW_TARGET_REMOTE" "refs/heads/$REVIEW_TARGET_BRANCH" || exit 1
HEAD_SHA=$(git rev-parse --verify HEAD) || exit 1
BASE_SHA=$(git rev-parse --verify 'FETCH_HEAD^{commit}') || exit 1
REVIEW_BASE=$BASE_SHA
assert_review_revision() {
  local live_base status
  live_base=$(git ls-remote --exit-code "$REVIEW_TARGET_REMOTE" "refs/heads/$REVIEW_TARGET_BRANCH") || return 1
  live_base=${live_base%%[[:space:]]*}
  status=$(git status --porcelain --untracked-files=all) || return 1
  if [ "$live_base" != "$BASE_SHA" ] || [ "$(git rev-parse --verify HEAD)" != "$HEAD_SHA" ] || [ -n "$status" ]; then
    echo "Review head/base/worktree moved; coverage is incomplete. Stop and requalify." >&2
    return 1
  fi
}
assert_review_revision || exit 1
```

Verify the installed CLI supports the documented `--branch` base selector
([official CLI reference](https://www.greptile.com/docs/code-review/greptile-cli#review-options)).
Require support for an immutable Git commit as that selector; if unavailable,
stop rather than fall back to a mutable local branch. Pass the fetched commit to
both output modes. Run `assert_review_revision` again after the review and before
presenting results, including a fresh remote target OID check. A moved target
requires a fresh comparison, not an obsolete coverage claim.

Discover the installed output selectors first; prefer JSON when advertised and
use agent output when JSON is unavailable. Do not mistake authentication/network
or review failures for missing JSON support:

```bash
REVIEW_HELP=$(greptile review --help) || exit 1
case "$REVIEW_HELP" in
  *--json*) greptile review --branch "$REVIEW_BASE" --json || exit 1 ;;
  *--agent*) greptile review --branch "$REVIEW_BASE" --agent || exit 1 ;;
  *) echo "No supported machine-readable review output; stop." >&2; exit 1 ;;
esac
assert_review_revision || exit 1
```

An advertised mode that fails (including a contradictory usage error) remains a
reported CLI failure, not authorization to run a second review. Retain the raw
failure and next action; never hide genuine failures behind the fallback mode.

### 5. Summarize results

Parse JSON output when available and report:

- Review status
- Number of findings
- Highest severity findings first
- Files that need edits
- Coverage: intended base/head, all changed paths, and every path withheld/excluded
  by the CLI's sensitive-file filter, with its exclusion reason
- Suggested next command or fix path

When output is plain text, preserve the same structure as much as possible. Keep the summary concise and focused on actionable findings.

Compare the CLI's disclosed reviewed/withheld file inventory with the committed
diff for the recorded comparison. If the installed output format does not expose
enough coverage information, report coverage as unknown/incomplete, not a complete
zero-finding review. Any withheld path makes full-candidate coverage incomplete.
Never print file contents or secrets to explain the exclusion. Only after the user
explicitly authorizes transmitting each named path and it is verified safe may an
authorized rerun add `--include` for those paths; never automatically override the
filter. Preserve the same `--branch` and source identity on that rerun.
([Sensitive-file behavior](https://www.greptile.com/docs/code-review/greptile-cli#include-a-sensitive-file).)
