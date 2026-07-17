---
name: repo-pages
description: Shared reference for repository-hosted Pages publishing (Codeberg Pages, GitLab Pages, and similar). Defines the build → publish model, branch gating, URL-matching pitfalls, and preconditions common to host-specific Pages skills. Not user-invokable on its own; loaded by `forgejo-pages`, `gitlab-pages`, and other Pages wiring skills.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# repo-pages

## What this is

A shared reference skill describing the publishing model used by repository-hosted Pages services (Codeberg Pages, GitLab Pages, and similar). Host-specific Pages skills (`forgejo-pages`, `gitlab-pages`, ...) load this skill for the generic model and add their own preconditions, runner choices, action URIs, and URL conventions on top.

This skill does not produce a workflow on its own. Always invoke a host-specific Pages skill, which references this one.

## The build → publish model

A Pages deployment is a CI job that:

1. Builds a static site locally with a project-defined build command.
2. Hands the built output directory to the host's Pages publishing mechanism.
3. Makes that output available at a public URL controlled by the host.

The split between "build" and "publish" matters: the build is project-specific (often `nix build .#site` for Nix flake projects), while the publish step is host-specific.

## Common preconditions

- The site build output is available from a local build command. Validate locally when feasible before wiring CI.
- The final public Pages URL is known unambiguously from project settings or host conventions. Do not guess when group/user/subpath/custom-domain rules make the final URL ambiguous.
- The repository or project meets the host's eligibility rules (visibility, licensing, Pages-enabled state). Host-specific skills enumerate these.

## Branch gating

Limit Pages deployment to the repository's default branch unless the repository intentionally publishes from another branch. This prevents draft branches from publishing unfinished content. Use `main` by default; use `master` only when the target repository actually uses it.

## Build output and publish directory

The publish directory the host uploads must contain exactly what should appear at the public URL root. Common patterns:

- The build emits to `result/` (Nix flake builds via `nix build`).
- The host expects a specific directory (e.g. GitLab Pages historically reads `public/`).
- Bridge the gap by copying or pointing the host's "publish" input at the build output directory.

When the final public URL uses a project subpath (for example `https://<owner>.<host>/<repo>/`), the site's own base URL or `site-url` must match that subpath, or relative links and assets will 404. This is a frequent post-deploy failure.

## Default workflow shape

1. Confirm the project name and the exact final Pages URL from host settings.
2. Confirm the build command and output directory. For Nix flake sites, default to `nix build .#site` and `result/`.
3. Wire a single CI job that runs the build and hands the output to the host's Pages publish step.
4. Gate the job to the default branch.
5. Validate the build locally when feasible.

## Diagnostics

- If the deployed site returns `404` at the expected URL, inspect the publish job's output/artifacts and confirm an `index.html` exists at the root of what was uploaded.
- If pages load but assets and links 404, the site's base URL likely does not match the final Pages subpath.

## Notes for host-specific skills

A host-specific Pages skill should layer on top of this skill and define:

- The exact workflow/CI file path the host uses (e.g. `.forgejo/workflows/pages.yaml`, `.gitlab-ci.yml`).
- The runner or image to use, with any host-imposed limits.
- The action or publish mechanism (e.g. `https://codeberg.org/git-pages/action@2b24bbb7ff943d3c8fe1df91326adec66daea6dd # v2.2.0`, GitLab's `pages:` keyword).
- The final URL convention (user pages, project pages, group pages, custom domains).
- The token or auth mechanism (e.g. `${{ forge.token }}`).
- Host-specific eligibility rules (public + free/libre license for Codeberg Pages; Pages enabled by admins for self-managed GitLab; etc.).

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
