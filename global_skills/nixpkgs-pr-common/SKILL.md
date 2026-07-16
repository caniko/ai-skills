---
name: nixpkgs-pr-common
description: "Shared references for nixpkgs PR skills. Use when another nixpkgs PR skill directs you here, or when you need common nixpkgs contribution decorum, review automation rules, live PR template handling, or caniko/nixpkgs-review-gha workflow instructions."
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# nixpkgs-pr-common

Shared reference — not user-invokable on its own; loaded by
`nixpkgs-init-pr`, `nixpkgs-update-pr`, and `nixpkgs-build-failure-pr`.

## Branch targeting

Default: `master`.  If the `nixpkgs-branch-check` bot flags the PR as a mass
rebuild (labels like `10.rebuild-linux: 2501-5000`), switch the base to
`staging`.  The `nixos-*` and `nixpkgs-*` branches are written to by the
channel release script and must never be used as merge targets.

## References

- Read `references/decorum.md` before writing commit messages, PR summaries, or upstream comments.
- Read `references/pr-template.md` before creating or updating a nixpkgs PR body.
- Read `references/nixpkgs-review-gha.md` before dispatching or diagnosing the external review workflow.
- Write concise, factual prose: no boilerplate, invented claims, or decorative
  formatting. Keep policy language and reviewer replies specific to the patch.

## Review replies

When a reviewer asks for changes, reply showing what changed.

Use standard nixpkgs attrs (`pkgsCross.*`) for any build commands in the PR body, not host-specific paths.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
