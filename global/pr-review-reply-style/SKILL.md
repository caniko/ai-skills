---
name: pr-review-reply-style
description: Draft concise, human-written pull request review replies after addressing reviewer feedback. Use when replying to inline PR comments, requested changes, or review threads, especially after implementing a code change.
---

# PR Review Reply Style

Use this skill when writing a PR review-thread reply after handling feedback.

## Style

- Keep it short: usually one sentence, two only if test evidence matters.
- Sound like an engineer replying to another engineer, not a status bot.
- Acknowledge the point naturally when useful: "Good call", "Yeah", or "Makes sense".
- State the concrete change in plain language.
- Mention validation only when it is directly relevant and specific.
- Do not over-explain the implementation unless the reviewer asked for rationale.
- Avoid boilerplate such as "Done.", "Implemented as requested", or long summaries.

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
