---
name: simit-python-project-init
description: Apply simit initialization to Python uv projects with py-harbor. Use for `simit init flake/ci`, uv projects, generated-file validation, or custom GPU/ML flakes.
---

# Simit Python Project Init

Load [simit-project-init-common](.skillnet/deps/simit-project-init-common/SKILL.md) before
running generators; it owns shared command, blocker, and generated-file rules.

## Purpose

Use `simit` as the canonical initializer for Python uv project flake and CI wiring. Prefer generated output over hand-written substitutes, preserve project-owned py-harbor runtime policy, and stop when required metadata is missing instead of fabricating package names, extras, runners, workflow targets, or flake outputs.

## Discovery

Before running generators:

1. Confirm the project root and VCS state with `pwd` and `git status --short`.
2. Read `pyproject.toml`, `uv.lock`, existing `flake.nix`, `simit.toml`, `nix/*.nix`, and existing CI workflows.
3. If either `pyproject.toml` or `uv.lock` is missing, stop and report:
   - the missing file,
   - why simit Python initialization requires it,
   - the upstream command to regenerate it, usually `uv lock` or `uv sync`,
   - the validation command, usually `test -f pyproject.toml && test -f uv.lock`.
4. Determine the CI platform from repository remotes and existing workflow locations:
   - `.forgejo/workflows/` or Codeberg/Forgejo remote: `--platform forgejo`.
   - `.github/workflows/` or GitHub remote: `--platform github`.
5. Default Python uv CI to `--runtime nix`, because py-harbor flake outputs provide the reproducible app, checks, formatter, and runtime libraries.

## Workflow

1. Preview flake changes:
   ```sh
   simit init flake --print
   ```

2. Apply flake wiring:
   ```sh
   simit init flake
   ```

3. If the project has an existing py-harbor flake with project-specific runtime policy, preserve it. Add or keep `simit.toml` with:
   ```toml
   [flake]
   mode = "custom"
   backend = "py-harbor"
   ```

   Declare expected public outputs under `[flake.expected_outputs]` when the flake is project-owned. Include stable packages, apps, checks, and dev shells that CI or users rely on.

4. If `simit init flake` patched an existing `flake.nix`, optimize the flake only after generated output is valid. Read and follow the shared [flake-modularization routine](.skillnet/deps/simit-project-init-common/references/flake-modularization.md). Keep simit's generated hook files (`nix/treefmt.nix`, `nix/pre-commit.nix`) authoritative unless the user explicitly asks to customize them.

5. Apply CI wiring with the discovered platform:
   ```sh
   simit init ci --platform forgejo --runtime nix
   simit init ci --platform github --runtime nix
   ```

   Add `--runner` only when repository evidence or user configuration requires it. Do not add Rust-only flags such as `--with-nextest`, `--with-msrv`, `--with-audit`, `--with-deny`, or Rust package selectors for Python uv projects.

6. Validate generated output:
   ```sh
   simit init flake --check --diff
   simit init ci --platform <platform> --check --diff
   nix flake check --no-build
   ```

   Then run the narrowest meaningful checks exposed by the flake, for example:

   ```sh
   nix build .#checks.x86_64-linux.flake-eval
   nix build .#checks.x86_64-linux.typecheck
   nix build .#checks.x86_64-linux.offline-tests
   ```

## Existing py-harbor Flakes

When `flake.nix` already exists:

- Do not replace it wholesale unless the user asked for a reset and the current flake has no project-specific outputs to preserve.
- Preserve GPU/ML runtime policy, package outputs, checks, dev shells, apps, docs/site outputs, Python version selection, uv extras, pyproject overrides, runtime libraries, and wrapper environment.
- Keep platform extras from `pyproject.toml` authoritative. Do not silently substitute `cpu`, `nvidia`, `amd`, or `apple` extras.
- Keep py-harbor helpers as the preferred Nix backend: `mkPkgs`, `mkUvDevShell`, `mkUvCheckEnv`, `mkUvAppPackage`, `mkFfmpegCompat`, `mkFfmpegTorchCodecAbiCheck`, and `pythonOverrides.*`.
- Use `git add -N` for newly generated files before `nix flake check --no-build` when the target repository is a Git flake, because Nix cannot see untracked paths.

## Failure Handling

For generator patch failures, missing Git-visible paths, or ambiguous anchors,
follow the shared failure contract in
[simit-project-init-common](.skillnet/deps/simit-project-init-common/SKILL.md). Do not
hand-merge generated output from memory.
