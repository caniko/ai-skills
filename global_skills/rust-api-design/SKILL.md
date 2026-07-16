---
name: rust-api-design
description: Improve Rust public API and internal design with idiomatic conversions, typed errors, focused traits, and type-level safety. Use for API, error, trait, or type-safety design work, or when rust-ultra routes design concerns here.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Rust API Design

Load [foundation.md](../rust-ultra/references/foundation.md), then the
relevant profiles:

- [api-guidelines.md](references/api-guidelines.md)
- [errors.md](references/errors.md)
- [traits.md](references/traits.md)
- [type-safety.md](references/type-safety.md)

Inventory the exported surface before changing it. Mark changes that would
break downstream callers; do not silently apply them. Keep error wording in
the error profile's message section and allocation-only changes in
`rust-quality`'s performance profile.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
