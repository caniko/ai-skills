---
name: nix-test-gates
description: Strengthen and validate Nix formatter, flake, host, Home Manager, package, activation, and CI checks. Use when Nix cleanup needs durable regression protection or focused evaluation gates.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# Nix Test Gates

Load [foundation.md](../nix-ultra/references/foundation.md) and
[test-gates.md](references/test-gates.md). Prefer cheap checks that explain
the exact violating file or value, then run the focused evals they protect.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
