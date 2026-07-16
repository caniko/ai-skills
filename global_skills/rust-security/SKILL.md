---
name: rust-security
description: Audit Rust dependencies and code for security vulnerabilities, unsafe-code soundness, secret handling, command injection, and memory-safety hazards. Use for focused security reviews or when rust-ultra routes safety concerns here.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Rust Security

Load [foundation.md](../rust-ultra/references/foundation.md), then the
relevant profile:

- [security.md](references/security.md) for dependency and application
  security.
- [unsafe-soundness.md](references/unsafe-soundness.md) for unsafe blocks,
  FFI, UB, and `SAFETY` invariants.

Treat unresolved vulnerability findings, unsoundness, secret exposure, and
missing authoritative security input as blockers. Do not weaken a sound unsafe
abstraction merely to remove the `unsafe` keyword.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
