---
name: plinth-project-visual-review
description: Review Plinth project sites that use website/plinth-project.toml with plinth-project check/build/dev/audit and visual-rubric reports.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# Plinth Project Visual Review

Use this for project sites with `website/plinth-project.toml`.

## Workflow

1. Validate the config:
   ```bash
   nix develop . -c plinth-project check --config website/plinth-project.toml --json
   ```
2. Build or serve the latest local output:
   ```bash
   nix build .#site --no-link
   nix develop . -c plinth-project dev --config website/plinth-project.toml --port 0
   ```
3. Run the full-site visual gate:
   ```bash
   nix develop . -c plinth-project audit site --config website/plinth-project.toml
   ```
4. Inspect the JSON report and screenshot paths printed by the audit command. Treat missing screenshots, missing report JSON, browser failures, or visual-rubric errors as blockers.

## Review Standard

Use the existing visual-rubric guidance and the `plinth-site-beauty` preset. Do not duplicate or soften the rubric locally. Fail/error verdicts block production unless the user explicitly asks for exploratory review with `--no-fail-on-rubric`.

## Notes

- Prefer explicit `--route` only when the site intentionally needs non-rendered routes; default coverage should be every rendered Plinth page.
- Use `--fake-ai` only for plumbing tests, never for a real production review.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
