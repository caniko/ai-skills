---
name: nixpkgs-pr-common
description: "Shared references for nixpkgs PR skills. Use when another nixpkgs PR skill directs you here, or when you need common nixpkgs contribution decorum, review automation rules, live PR template handling, or caniko/nixpkgs-review-gha workflow instructions."
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

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

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
