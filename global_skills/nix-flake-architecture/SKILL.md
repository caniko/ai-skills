---
name: nix-flake-architecture
description: Modernize Nix flake outputs, input follows, overlays, packages, formatters, checks, dev shells, and NixOS or Home Manager builders. Use when flake output wiring is crowded, inputs drift, overlays are cache-hostile, or package architecture is unclear.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

# Nix Flake Architecture

Load [foundation.md](../nix-ultra/references/foundation.md), then the
relevant profiles:

- [flake-outputs.md](references/flake-outputs.md)
- [inputs.md](references/inputs.md)
- [overlays-packages.md](references/overlays-packages.md)

Keep output names stable, preserve intentional cache-sensitive pins, and use
`--no-update-lock-file` for validation. Do not remove legacy outputs or merge
package sets without checking downstream consumers.

## Solution Placement

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
