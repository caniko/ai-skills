---
name: rust-security
description: Audit Rust dependencies and code for security vulnerabilities, unsafe-code soundness, secret handling, command injection, and memory-safety hazards. Use for focused security reviews or when rust-ultra routes safety concerns here.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

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

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
