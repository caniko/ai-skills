---
name: gitlab-pages
description: Add GitLab CI wiring for GitLab Pages deployment. Use when a user asks to publish a static site with GitLab Pages, add `.gitlab-ci.yml` Pages deployment, or wire a docs/site build to GitLab Pages on GitLab.com or a self-managed GitLab instance.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# gitlab-pages

## What this does

Adds GitLab CI wiring that builds a static site and publishes it through GitLab Pages.

This skill is for Pages deployment only. It assumes the site build already exists locally, typically as `nix build .#site` for Nix flake projects.

For the generic build → publish model, branch-gating rationale, and the base-URL / subpath pitfall shared with other Pages hosts, see [repo-pages](../repo-pages/SKILL.md). Everything below is the GitLab-specific layer.

## Preconditions

- The project is hosted on GitLab.com or a GitLab instance with Pages enabled.
- The Pages URL is known from project settings or instance conventions. Do not guess if group pages, user pages, unique domains, or custom domains make the final URL ambiguous.
- The site build output is available from a local build command.
- If the project is on a self-managed GitLab instance, Pages must already be enabled by the instance administrators.

## Current GitLab Pages rules

These points are based on GitLab's official Pages docs:

- A Pages deployment is triggered by a job with `pages: true` or a nested `pages:` hash.
- User-defined Pages job names are supported.
- When publishing a non-default directory, use `pages.publish`, not the deprecated top-level `publish`.
- GitLab publishes from a `public/` artifact by default, but `pages.publish` can point to another directory.

## Defaults

- CI file path: `.gitlab-ci.yml`
- Job name: `publish-pages`
- Stage: `deploy`
- Image: `nixos/nix:latest`
- Build command: `nix --extra-experimental-features 'nix-command flakes' build .#site`
- Publish directory: `public/`
- Trigger: default branch only

## Workflow

1. Confirm the exact Pages URL from the project settings or instance policy.
2. Confirm the build command and output directory. For Nix flake sites, default to `nix --extra-experimental-features 'nix-command flakes' build .#site` and `result/`.
3. If the built site is not already emitted into `public/`, copy the deployable output into `public/`.
4. Create or update `.gitlab-ci.yml`.
5. Gate deployment to the default branch unless the repository intentionally publishes from another branch.
6. Validate the build locally when feasible.

## Default template

```yaml
stages:
  - deploy

publish-pages:
  stage: deploy
  image: nixos/nix:latest
  script:
    - nix --extra-experimental-features 'nix-command flakes' build .#site
    - rm -rf public
    - mkdir -p public
    - cp -r result/* public/
  pages:
    publish: public
  rules:
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
```

## Notes

- If the build already writes to `public/`, `pages: true` is enough; keep `pages.publish` only when you need a non-default publish directory or want the path to stay explicit.
- GitLab automatically appends `pages.publish` to `artifacts:paths`; do not duplicate that block unless the repository already has a reason to manage artifacts manually.
- If the deployed site returns `404`, inspect the latest Pages job artifacts and confirm `public/index.html` exists. (See `repo-pages` for the base-URL / subpath pitfall behind most other 404s.)

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
