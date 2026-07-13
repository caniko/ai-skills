---
name: pr-review-reply-style
description: Draft concise, human-written pull request review replies after addressing reviewer feedback. Use when replying to inline PR comments, requested changes, or review threads, especially after implementing a code change.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# PR Review Reply Style

Use this skill when writing a PR review-thread reply after handling feedback.

## Style

Use any configured shared human-written style guidance when the consumer
provides it; this repository does not own a separate style skill.

PR-specific additions:

- Acknowledge the point naturally when useful: "Good call", "Yeah", or "Makes sense".

## Shape

Prefer:

```text
Good call, I dropped the extra precheck and let `extract()` returning `Option` handle stale entries directly.
```

With validation:

```text
Good call, I dropped the extra precheck and let `extract()` returning `Option` handle stale entries directly. The focused swarm regression test still passes.
```

If no code change was needed:

```text
Makes sense; I checked this path and left it as-is because ...
```

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
