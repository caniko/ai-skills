---
name: plinth-visual-review
description: Unified router for visual review of Plinth-based project and personal sites using the project and personal Plinth visual review skills.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# Plinth Visual Review

Route to the narrow skill first:

- Project repository with `website/plinth-project.toml`: use `plinth-project-visual-review`.
- canix personal sites for Can or Dejana: use `plinth-personal-visual-review`.

If both apply, run project-site checks first, then canix personal-site target checks. In all cases, use visual-rubric's existing guidance and Plinth's `plinth-site-beauty` preset; missing screenshots, JSON reports, target definitions, or helper exports are blockers.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
