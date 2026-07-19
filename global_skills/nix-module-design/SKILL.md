---
name: nix-module-design
description: Improve NixOS and Home Manager module architecture, option typing, data boundaries, and integrated or standalone Home Manager behavior. Use when modules mix data with behavior, options are loose, service wiring is duplicated, or host/user boundaries are unclear.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

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

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
