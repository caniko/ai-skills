---
name: forgejo-ci-common
description: Shared non-invokable Forgejo CI contract for repository discovery, job coverage, trust boundaries, runner selection, and validation. Load from a host-specific Forgejo CI skill.
---

# Forgejo CI Common

Load this reference before generating a Forgejo workflow. Keep host-specific
URLs, runner labels, and publication policy in the invoking skill.

## Discovery

Inspect remotes, workflow directories, manifests, flake outputs, existing CI,
and documented test/lint commands. Derive commands from the project; never
invent an empty job or a package target.

Complete applicable pipelines cover formatter/lint, type checking, tests,
build/package outputs, and flake checks. Omit inapplicable stages explicitly.
Use concurrency cancellation for repeated pushes and keep release/publication
jobs separate from untrusted pull-request jobs.

## Trust and runner boundary

Do not expose cache, release, deployment, or signing credentials to pull
requests. Cache reads may be public; cache pushes and publication require a
trusted runner and a protected branch/tag. Load `atlas-runner` for the current
self-hosted labels, image capabilities, mounts, cache, and service facts.

Use the exact action URI supported by the host. Do not bootstrap an action
runtime or hand-roll checkout when the configured runner/generator supplies it.

## Validation

Before reporting completion, confirm workflow syntax, every referenced package
or check exists, every `runs-on` label is supported, and the generated workflow
matches the installed generator's `--check --diff` output. Report skipped gates,
external operator steps, and any unavailable CLI capability.
