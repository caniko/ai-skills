---
name: forgejo-ci
description: "Generate Forgejo Actions CI for self-hosted projects: lint, tests, builds, flakes, and Attic publication. Route Codeberg atlas CI to forgejo-atlas-ci and Pages to forgejo-site."
---

# Forgejo CI

Use this skill for self-hosted Forgejo repositories only. Confirm the remote
and runner registration target first; current atlas instances register against
Codeberg, so Codeberg projects use `forgejo-atlas-ci`.

Load [forgejo-ci-common](.skillnet/deps/forgejo-ci-common/SKILL.md) and
[atlas-runner](.skillnet/deps/atlas-runner/SKILL.md) for shared CI and runner facts.

## Workflow

1. Inspect `git remote -v`, existing workflow files, manifests, flake outputs,
   and repository-authoritative test/lint commands.
2. Generate `.forgejo/workflows/` with the installed project generator when it
   covers the requested surface. For Rust, prefer
   `simit init ci --platform forgejo`; check `simit init ci --help` first.
3. Include applicable formatter/lint, typecheck, test, build/package, and
   `nix flake check` jobs. Omit inapplicable stages explicitly.
4. Keep publication separate from pull-request jobs. Read
   [attic-release.md](references/attic-release.md) only when the project must
   publish to canix Attic.
5. For a hand-written Cargo workflow, read
   [rust-template.md](references/rust-template.md) and preserve the project
   MSRV/container contract.

## Self-hosted boundary

- Use only labels advertised by the registered runner.
- Use Forgejo action URLs, not implicit GitHub short names, when the host
  requires full action URIs.
- Do not install the action runtime per workflow when the runner mounts it.
- Do not expose cache, signing, release, or deployment secrets to PR jobs.
- Do not assume sccache is visible inside CI containers.

## Validation

```sh
git diff --check
yamllint .forgejo/workflows/  # when available
simit init ci --platform forgejo --check --diff  # when Simit owns the file
```

Confirm every build target exists and report skipped checks, external operator
steps, and any generator capability gap. Do not claim Attic publication unless
the trusted credential path and protected ref are both configured.
