---
name: rust-correctness
description: Audit and repair Rust correctness hazards involving async execution, preconditions, panic paths, and unwrap or expect calls. Use for focused hardening work or when rust-ultra routes correctness concerns here.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# Rust Correctness

Load [foundation.md](../rust-ultra/references/foundation.md), then only the
profiles relevant to the request:

- [concurrency.md](references/concurrency.md)
- [fail-fast.md](references/fail-fast.md)
- [panic-paths.md](references/panic-paths.md)
- [unwraps.md](references/unwraps.md)

Keep the profiles separate in analysis: a panic caused by indexing is not an
unwrap audit, and boundary validation is not a replacement for either. Verify
after each profile and preserve valid intentional invariants.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
