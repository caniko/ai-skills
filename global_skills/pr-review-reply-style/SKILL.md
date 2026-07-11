---
name: pr-review-reply-style
description: Draft concise, human-written pull request review replies after addressing reviewer feedback. Use when replying to inline PR comments, requested changes, or review threads, especially after implementing a code change.
---

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
