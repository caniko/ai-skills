---
name: rust-quality
description: Improve Rust lint, dead-code hygiene, module organization, public documentation, tests, runtime observability, and measured performance. Use for focused Clippy, cleanup, docs, tests, logging, allocation, or hot-path work, or when rust-ultra routes quality concerns here.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Rust Quality

Load [foundation.md](../rust-ultra/references/foundation.md), then the
relevant profile:

- [clippy.md](references/clippy.md)
- [dead-code.md](references/dead-code.md)
- [module-layout.md](references/module-layout.md)
- [observability.md](references/observability.md)
- [performance.md](references/performance.md)
- [public-docs.md](references/public-docs.md)
- [test-gaps.md](references/test-gaps.md)

Use repository wrappers and preserve behavior. `rust-crate-release` owns
release-only packaging, deny, audit, and publication gates; this skill owns
the reusable code-quality baseline. Do not micro-optimize cold code or add
logging to sensitive or noisy paths. Keep structural and hot-path changes
independently verifiable.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
