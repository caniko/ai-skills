---
name: rust-api-design
description: Improve Rust API and internal architecture through conversions, typed errors, trait topology, type safety, and type cohesion. Use for focused design work or rust-ultra profiles.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

# Rust API Design

Load [foundation.md](../rust-ultra/references/foundation.md), then the
relevant profiles:

- [api-guidelines.md](references/api-guidelines.md)
- [errors.md](references/errors.md)
- [traits.md](references/traits.md)
- [type-safety.md](references/type-safety.md)
- [type-cohesion.md](references/type-cohesion.md)

Inventory the exported surface before changing it. In focused or compatibility
mode, mark changes that would break downstream callers. In Rust-ultra
modernize mode, apply materially stronger breaking designs and migrate all
in-repository callers, tests, examples, fixtures, schemas, and docs. Keep error
wording in the error profile's message section and allocation-only changes in
`rust-quality`'s performance profile.

When invoked by `rust-ultra`, return one evidence row for every requested
profile. Internal and binary-only architecture remains in scope even when no
public library API exists.

## Solution Placement

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
