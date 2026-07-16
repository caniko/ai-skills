---
name: pr-review-reply-style
description: Draft concise, human-written pull request review replies after addressing reviewer feedback. Use when replying to inline PR comments, requested changes, or review threads, especially after implementing a code change.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# PR Review Reply Style

Use this skill when writing a PR review-thread reply after handling feedback.

## Style

Load and apply [`$write-human-style`](../write-human-style/SKILL.md) before
drafting. It owns the general voice, clarity, concision, and anti-boilerplate
rules. This skill adds only review-thread behavior.

PR-specific additions:

- Reply to the reviewer's specific point rather than summarizing the whole PR.
- Acknowledge the point naturally when useful: "Good call", "Yeah", or "Makes
  sense". Do not force the same opener into every thread.
- State the concrete change in the past tense, then mention focused validation
  when it adds confidence.
- If no code change was needed, give the reason and the evidence without
  sounding defensive.
- Do not add reflexive thanks, a formal sign-off, or a generic "resolved" note.

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

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
