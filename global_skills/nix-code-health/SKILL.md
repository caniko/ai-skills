---
name: nix-code-health
description: Improve Nix file organization, dead-code hygiene, formatter-neutral style, and generated shell scripts without changing behavior. Use for Nix reorganization, stale module cleanup, idiomatic style, heredoc, hook, or activation-script work.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Nix Code Health

Load [foundation.md](../nix-ultra/references/foundation.md), then the
relevant profiles:

- [module-layout.md](references/module-layout.md)
- [dead-code.md](references/dead-code.md)
- [format-style.md](references/format-style.md)
- [shell-scripts.md](references/shell-scripts.md)

Keep generated hardware/disk files, secret migrations, and operational
comments stable unless the task explicitly includes them. Validate every
structural move with formatter and focused evaluation.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
