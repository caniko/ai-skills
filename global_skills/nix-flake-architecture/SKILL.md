---
name: nix-flake-architecture
description: Modernize Nix flake outputs, input follows, overlays, packages, formatters, checks, dev shells, and NixOS or Home Manager builders. Use when flake output wiring is crowded, inputs drift, overlays are cache-hostile, or package architecture is unclear.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

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

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
