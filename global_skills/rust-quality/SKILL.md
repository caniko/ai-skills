---
name: rust-quality
description: Improve Rust linting, dead code, module layout, behavioral reuse, docs, tests, observability, and measured performance. Use for focused work or rust-ultra profiles.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

# Rust Quality

Load [foundation.md](../rust-ultra/references/foundation.md), then the
relevant profile:

- [clippy.md](references/clippy.md)
- [dead-code.md](references/dead-code.md)
- [module-layout.md](references/module-layout.md)
- [duplication.md](references/duplication.md)
- [observability.md](references/observability.md)
- [performance.md](references/performance.md)
- [public-docs.md](references/public-docs.md)
- [test-gaps.md](references/test-gaps.md)

Use repository wrappers and preserve intended domain behavior. In Rust-ultra
modernize mode, do not preserve accidental module/API shape or duplicated
implementation structure. `rust-crate-release` owns
release-only packaging, deny, audit, and publication gates; this skill owns
the reusable code-quality baseline. Do not micro-optimize cold code or add
logging to sensitive or noisy paths. Keep structural and hot-path changes
independently verifiable.

When invoked by `rust-ultra`, return one evidence row for every requested
profile. File layout, behavioral reuse, and type cohesion are distinct reviews;
do not treat a successful file split as proof that responsibilities are sound.

## Solution Placement

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
