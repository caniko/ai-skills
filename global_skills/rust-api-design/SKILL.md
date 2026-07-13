---
name: rust-api-design
description: Improve Rust public API and internal design with idiomatic conversions, typed errors, focused traits, and type-level safety. Use for API, error, trait, or type-safety design work, or when rust-ultra routes design concerns here.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

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

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
