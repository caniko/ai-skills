---
name: forgejo-ci
description: Generate a Forgejo Actions CI implementation with full project coverage (lint, type-check, test, build) and publish Nix build outputs to the self-hosted Attic cache on runner (`https://attic.example.internal/canix`). Use when the user asks for "CI", "set up Forgejo Actions", "add a workflow", or "release to attic" inside a project hosted on the self-hosted Forgejo (`git.example.com`).
---

# Forgejo CI implementation

Use this skill when adding `.forgejo/workflows/*.yml` (or `.gitea/workflows/*.yml`) to a project. The target runner is the self-hosted `runner-example` runner (registered against `https://git.example.com`).

## Inputs to gather first

1. **Project type** — read `flake.nix`, `Cargo.toml`, `pyproject.toml`, `package.json`, `go.mod` etc. Don't guess.
2. **Existing CI** — if `.forgejo/workflows/`, `.gitea/workflows/` or `.github/workflows/` already exist, read them; reuse working steps and only add what's missing.
3. **Nix flake outputs** — list `checks`, `packages`, `devShells`. The CI must exercise every public output.
4. **Test/lint commands** — extract from project files (e.g. `cargo clippy`, `pytest`, `ruff`, `tsc`, `eslint`). Don't invent commands.

## Required job coverage

A complete pipeline contains **all** of:

- `lint` — formatter + linter (e.g. `nix fmt -- --check`, `ruff`, `clippy --all-targets -- -D warnings`).
- `typecheck` — `tsc --noEmit`, `mypy`, `pyright`, etc., when applicable.
- `test` — full unit/integration test suite.
- `build` — `nix build .#<each package>` for every flake package output, or language-native build.
- `flake-check` — `nix flake check --keep-going` (covers `checks.*`).
- `release` (only on tag/main) — push closures to the canix attic cache.

If a stage doesn't apply (e.g. no typechecker), **omit it explicitly** rather than emit an empty stub.

## Runner selection

The runner runner advertises **one** label, `runner`, backed by a single locally-built OCI image (`canix-runner:local` — see [forgejo-runners.nix](../../../..~/canix/Projects/canix/root/hosts/runner/server/forgejo-runners.nix)). Always:

```yaml
runs-on: runner
```

Do **not** write `runs-on: nix`, `runs-on: docker`, or `runs-on: ubuntu-latest` — those labels were retired. Only `runner` matches.

### What's baked into the `runner` image

Deliberately minimal — only what `act` needs to drive third-party actions:

- node 24 (for JS-based actions like `actions/checkout`, `actions/cache`)
- git (also required by `actions/checkout`)
- bash, coreutils, curl, tar, gzip, which, CA certs

Language toolchains (rust, python, go, java, nix, …) are **NOT** in the image. Each workflow declares the toolchain it needs via `container:` (or `setup-*` actions). This keeps the runner image tiny (~120 MB compressed) and avoids version-pinning conflicts between projects.

**Caching is workflow-owned.** The runner enables Forgejo's built-in cache backend (`cache.enabled = true`), so Rust workflows should use `Swatinem/rust-cache@v2` or `actions/cache` explicitly. Runner capacity is pinned to 1, so jobs serialize and workflows should not assume parallel job throughput.

Nix-flake-based jobs get derivation-level caching through the canix Attic substituter at `https://attic.example.internal/canix`; runner pushes build outputs after local builds. Do not depend on host-mounted Rust caches or other runner-local state.

### Picking a `container:` for the job

- **Rust**: prefer `container: rust:<MSRV>-trixie` (Debian 13, glibc 2.41) when the version is available. **Trixie tags only exist for rust 1.93 and newer** — for older MSRV pins, fall back to `rust:<MSRV>-bookworm` (Debian 12, glibc 2.36). Avoid `*-alpine` (musl edge cases; glibc isn't a size cost given the toolchain cache).
- **Nix**: `container: nixos/nix:latest`, or skip `container:` and install nix into the bare runner image via `cachix/install-nix-action` (see Nix setup pattern below).
- **Python / Go / Node-other-version**: use the official `python:`, `golang:`, `node:` images, or the bare runner image plus `actions/setup-python` / `setup-go` / `setup-node`.

If you omit `container:`, the job runs in the bare runner image (node + git + bash) — fine for pure JS/composite-action workflows, no cargo, no python, no apt.

## Nix setup pattern

For Nix-based projects, install Nix once per job using `cachix/install-nix-action` (works on Forgejo Actions) and wire the canix cache as a substituter so dependencies pull from runner instead of building locally:

```yaml
- uses: https://code.forgejo.org/actions/checkout@v4
- uses: https://github.com/cachix/install-nix-action@v27
  with:
    extra_nix_config: |
      experimental-features = nix-command flakes
      substituters = https://attic.example.internal/canix https://cache.nixos.org
      trusted-public-keys = canix:uqr0nD3I0mfj9BYfZgTZHMaDKfI2yCTtSA5JGTWKUeg= cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=
```

Note the `https://...` URL prefix on actions — Forgejo Actions requires the full URL for non-local actions.

## Rust workflow template (recommended defaults)

For raw-cargo Rust workflows, use `Swatinem/rust-cache@v2` for registry, git, and target caching keyed by `Cargo.lock` plus `rustc -V`; use `cargo-binstall` so cargo tools install from prebuilt binaries in seconds; and use `cargo-nextest` for faster test execution and clearer failures than `cargo test`.

```yaml
jobs:
  test:
    runs-on: runner
    container: rust:<MSRV>-trixie   # or -bookworm for < 1.93
    steps:
      - uses: https://code.forgejo.org/actions/checkout@v4

      - uses: https://github.com/Swatinem/rust-cache@v2
        with:
          # Default key is fine for single-job workflows; for multi-job
          # workflows pin a shared key so all jobs share the same cache.
          shared-key: ${{ github.workflow }}
          # cache-on-failure keeps the warm cache populated even when a
          # downstream step fails, which is common while iterating in CI.
          cache-on-failure: true

      - name: Install cargo-binstall
        run: |
          curl -L --proto '=https' --tlsv1.2 -sSf \
            https://raw.githubusercontent.com/cargo-bins/cargo-binstall/main/install-from-binstall-release.sh \
            | bash

      - name: Install cargo tools
        run: |
          cargo binstall -y --no-confirm \
            cargo-nextest \
            cargo-audit \
            cargo-deny

      - name: Test
        run: cargo nextest run --all-features

      - name: Clippy
        run: cargo clippy --all-targets --all-features -- --deny warnings

      - name: Audit
        run: cargo audit

      - name: Deny
        run: cargo deny check

      - name: Doc
        run: cargo doc --no-deps --all-features
```

## Attic release pattern

To publish build outputs back to the canix cache:

1. **Issue + wire the token via the [canix-cli](../canix-cli/SKILL.md) skill, not by hand.** From `~/canix/Projects/canix`, the user runs (sudo prompts on their end — human-in-the-loop):
   ```sh
   canix attic onboard <project> --runner runner
   agenix rekey -a
   canix deploy switch runner
   ```
   This puts the encrypted token under `age/secrets/attic-projects/<project>.age`, registers it in `lib/attic-projects.json`, and on the runner host bind-mounts `/run/canix-attic-tokens/` into job containers as `$ATTIC_TOKENS_DIR`. Workflows then read the token by path and skip `secrets.ATTIC_TOKEN` entirely:
   ```yaml
   - name: Push to attic
     run: |
       nix profile install nixpkgs#attic-client
       attic login canix https://attic.example.internal "$(cat "$ATTIC_TOKENS_DIR/<project>")"
       attic push canix $(cat paths.txt)
   ```
2. **Legacy fallback** — only when the project is *not* on our self-hosted runner: add a repo CI secret `ATTIC_TOKEN`. Use the snippet below; substitute the snippet above otherwise.

```yaml
release:
  needs: [lint, test, build, flake-check]
  if: github.ref == 'refs/heads/trunk' || startsWith(github.ref, 'refs/tags/')
  runs-on: runner
  steps:
    - uses: https://code.forgejo.org/actions/checkout@v4
    - uses: https://github.com/cachix/install-nix-action@v27
      with:
        extra_nix_config: |
          experimental-features = nix-command flakes
          substituters = https://attic.example.internal/canix https://cache.nixos.org
          trusted-public-keys = canix:uqr0nD3I0mfj9BYfZgTZHMaDKfI2yCTtSA5JGTWKUeg= cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=
    - name: Build all packages
      run: |
        nix build --print-out-paths --no-link \
          $(nix flake show --json | jq -r '.packages."x86_64-linux" | keys[] | "\(".\#" + .)"') \
          > paths.txt
    - name: Push to attic
      env:
        ATTIC_TOKEN: ${{ secrets.ATTIC_TOKEN }}
      run: |
        nix profile install nixpkgs#attic-client
        attic login canix https://attic.example.internal "$ATTIC_TOKEN"
        attic push canix $(cat paths.txt)
```

## Workflow file conventions

- Place workflows in `.forgejo/workflows/` (Forgejo's preferred path; `.gitea/workflows/` also works).
- One file per concern: `ci.yml` (lint/test/build/flake-check on every push and PR), `release.yml` (publish on tag/trunk).
- Use `concurrency` groups to cancel in-progress runs on new pushes:
  ```yaml
  concurrency:
    group: ${{ github.workflow }}-${{ github.ref }}
    cancel-in-progress: true
  ```

## Validation before reporting done

1. `yamllint .forgejo/workflows/` (if available) or at least visually verify YAML.
2. Confirm every `runs-on:` value is `runner` (the only label the runner advertises).
3. Confirm every `nix build` target actually exists in the flake.
4. Tell the user explicitly which token path applies:
   - On self-hosted runner (default): *"Run `canix attic onboard <project> --runner runner` from the canix repo, then `agenix rekey -a && canix deploy switch runner`. Sudo will prompt on your end. The release job reads `$ATTIC_TOKENS_DIR/<project>` automatically — no per-repo CI secret needed."*
   - Legacy / external runner: *"Add the `ATTIC_TOKEN` repo secret; issue it with `canix attic register <project>` (the printed token goes into the repo settings)."*

## Anti-patterns to avoid

- Don't use `actions/checkout@v4` without the `https://code.forgejo.org/` prefix — it will fail to resolve on Forgejo.
- Don't push to the cache from PR jobs (untrusted code with secret access). Gate `release` on trunk/tags only.
- Don't `nix-collect-garbage` inside the runner — the runner reuses container caches, GC defeats the point.
- Don't add a matrix over OSes; the only available runner OS is the act-latest image.
