---
name: nix-module-design
description: Improve NixOS and Home Manager module architecture, option typing, data boundaries, and integrated or standalone Home Manager behavior. Use when modules mix data with behavior, options are loose, service wiring is duplicated, or host/user boundaries are unclear.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

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

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
