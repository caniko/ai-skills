---
name: plinth-visual-review
description: Unified router for visual review of Plinth-based project and personal sites using the project and personal Plinth visual review skills.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Plinth Visual Review

Route to the narrow skill first:

- Project repository with `website/plinth-project.toml`: use `plinth-project-visual-review`.
- canix personal sites for Can or Dejana: use `plinth-personal-visual-review`.

If both apply, run project-site checks first, then canix personal-site target checks. In all cases, use visual-rubric's existing guidance and Plinth's `plinth-site-beauty` preset; missing screenshots, JSON reports, target definitions, or helper exports are blockers.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
