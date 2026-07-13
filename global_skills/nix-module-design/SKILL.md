---
name: nix-module-design
description: Improve NixOS and Home Manager module architecture, option typing, data boundaries, and integrated or standalone Home Manager behavior. Use when modules mix data with behavior, options are loose, service wiring is duplicated, or host/user boundaries are unclear.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# Nix Module Architecture

Load [foundation.md](../nix-ultra/references/foundation.md), then the
relevant profiles:

- [module-design.md](references/module-design.md)
- [options-typing.md](references/options-typing.md)
- [data-boundaries.md](references/data-boundaries.md)
- [home-manager.md](references/home-manager.md)

Keep options as the public contract and config as their implementation. Keep
pure data behind an adapter/facade, preserve compatibility unless a breaking
change is explicitly requested, and evaluate at least one affected host or
Home Manager output.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
