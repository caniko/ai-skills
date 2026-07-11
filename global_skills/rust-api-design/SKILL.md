---
name: rust-api-design
description: Improve Rust public API and internal design with idiomatic conversions, typed errors, focused traits, and type-level safety. Use for API, error, trait, or type-safety design work, or when rust-ultra routes design concerns here.
---

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
