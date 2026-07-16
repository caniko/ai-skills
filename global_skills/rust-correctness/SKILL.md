---
name: rust-correctness
description: Audit and repair Rust correctness hazards involving async execution, preconditions, panic paths, and unwrap or expect calls. Use for focused hardening work or when rust-ultra routes correctness concerns here.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

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

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
