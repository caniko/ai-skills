---
name: rust-quality
description: Improve Rust lint, dead-code hygiene, module organization, public documentation, tests, runtime observability, and measured performance. Use for focused Clippy, cleanup, docs, tests, logging, allocation, or hot-path work, or when rust-ultra routes quality concerns here.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

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

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
