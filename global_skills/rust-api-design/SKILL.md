---
name: rust-api-design
description: Improve Rust API and internal architecture through conversions, typed errors, trait topology, type safety, and type cohesion. Use for focused design work or rust-ultra profiles.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Rust API Design

Load [foundation.md](../rust-ultra/references/foundation.md), then the
relevant profiles:

- [api-guidelines.md](references/api-guidelines.md)
- [errors.md](references/errors.md)
- [traits.md](references/traits.md)
- [type-safety.md](references/type-safety.md)
- [type-cohesion.md](references/type-cohesion.md)

Inventory the exported surface before changing it. Mark changes that would
break downstream callers; do not silently apply them. Keep error wording in
the error profile's message section and allocation-only changes in
`rust-quality`'s performance profile.

When invoked by `rust-ultra`, return one evidence row for every requested
profile. Internal and binary-only architecture remains in scope even when no
public library API exists.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
