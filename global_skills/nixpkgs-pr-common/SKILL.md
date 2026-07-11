---
name: nixpkgs-pr-common
description: "Shared references for nixpkgs PR skills. Use when another nixpkgs PR skill directs you here, or when you need common nixpkgs contribution decorum, review automation rules, live PR template handling, or caniko/nixpkgs-review-gha workflow instructions."
---

# nixpkgs-pr-common

Shared reference — not user-invokable on its own; loaded by `nixpkgs-init-pr` and `nixpkgs-build-failure-pr`.

## Branch targeting

Default: `master`.  If the `nixpkgs-branch-check` bot flags the PR as a mass
rebuild (labels like `10.rebuild-linux: 2501-5000`), switch the base to
`staging`.  The `nixos-*` and `nixpkgs-*` branches are written to by the
channel release script and must never be used as merge targets.

## References

- Read `references/decorum.md` before writing commit messages, PR summaries, or upstream comments.
- Read `references/pr-template.md` before creating or updating a nixpkgs PR body.
- Read `references/nixpkgs-review-gha.md` before dispatching or diagnosing the external review workflow.
- Read the `human-written-like` skill for the generic style guide (no boilerplate, no emoji, no clause-separator dashes, sound like an engineer).

## Review replies

When a reviewer asks for changes, reply showing what changed.

Use standard nixpkgs attrs (`pkgsCross.*`) for any build commands in the PR body, not host-specific paths.
