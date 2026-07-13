---
name: nix-security
description: Audit NixOS and Home Manager secret handling, credential ownership, file modes, environment files, and service startup ordering. Use when secrets may enter the store, become world-readable, or race service startup.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# Nix Security

Load [foundation.md](../nix-ultra/references/foundation.md) and
[secrets.md](references/secrets.md). Treat missing encrypted/rekeyed data as a
blocker; never synthesize it. Inspect both declaration and consuming service.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
