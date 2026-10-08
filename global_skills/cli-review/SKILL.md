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

Prefer JSON output:

```bash
greptile review --json
```

If JSON output is unsupported or fails with a usage error, fall back to:

```bash
greptile review --agent
```

Do not hide the raw command failure if both commands fail. Summarize the failing command and the next action the user needs to take.

### 5. Summarize results

Parse JSON output when available and report:

- Review status
- Number of findings
- Highest severity findings first
- Files that need edits
- Suggested next command or fix path

When output is plain text, preserve the same structure as much as possible. Keep the summary concise and focused on actionable findings.
