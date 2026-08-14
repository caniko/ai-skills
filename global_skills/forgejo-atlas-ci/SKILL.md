---
name: forgejo-atlas-ci
description: Generate a Forgejo Actions CI workflow for a project hosted on `codeberg.org` that uses our self-hosted atlas runner (`atlas` for cargo-in-container / JS actions, `atlas-nix-trusted` for nix-store-writing jobs) and/or Codeberg's shared runner tiers (`codeberg-tiny`, `codeberg-small`, `codeberg-medium`). Supports the granular paradigm — routing each CI step (fmt, clippy, test, doc, package) to the appropriate runner tier. Scope is CI only — test, clippy, fmt, lint gates. NOT for Codeberg Pages deployment. For Rust release/publish wiring use `rust-crate-release`.
---

# Codeberg CI on the self-hosted atlas runner

Scope: the **CI** half of a Codeberg project's Forgejo Actions setup — test, clippy, fmt, audit, deny, docs, MSRV. For projects hosted on `codeberg.org`, dispatching to our self-hosted runner registered against Codeberg, not to Codeberg's hosted ones. Rust release/publish workflows live in [rust-crate-release](../rust-crate-release/SKILL.md). NOT for Codeberg Pages deployment — that's the separate [forgejo-pages](../forgejo-pages/SKILL.md) skill.

## Read first

Load [forgejo-ci-common](.skillnet/deps/forgejo-ci-common/SKILL.md) for shared workflow
coverage and trust boundaries. Load the [atlas-runner](.skillnet/deps/atlas-runner/SKILL.md) reference for the bare
`atlas` and host-nix `atlas-nix-trusted` capabilities, mounted action runtime,
cache behavior, runner checks, and Codeberg constraints. Its sccache note
distinguishes host-side availability from container visibility. Also load
[forgejo-ci](../forgejo-ci/SKILL.md) for shared job structure. This skill
documents only the Codeberg-on-atlas CI delta.

## Generate the workflow via simit

For any Rust project, prefer scaffolding CI with [simit](../simit-rust-project-ci-init/SKILL.md). Check the installed capability before selecting optional runner-tier features:

```sh
# from the project root — single atlas runner (backward-compatible)
simit init ci --platform forgejo --runner atlas

# Optional tier splitting is version-dependent. Use it only when the installed
# binary advertises the flags in `simit init ci --help`.
if simit init ci --help | grep -q -- '--granular'; then
  simit init ci --platform forgejo --runtime nix --granular
else
  simit init ci --platform forgejo --runtime nix --runner atlas
fi
```

When supported, `--granular` distributes CI steps across Codeberg runner tiers:

| Step | Runner | Specs |
|---|---|---|
| `cargo fmt --check` | `codeberg-tiny` | 1 CPU, 2G RAM, 2 min limit |
| `cargo clippy` | `codeberg-small` | 2 CPU, 4G RAM, 5 min limit |
| `cargo-deny` / `cargo-audit` | `codeberg-small` | 2 CPU, 4G RAM, 5 min limit |
| `cargo test` | `codeberg-medium` | 4 CPU, 8G RAM, 10 min limit |
| `cargo doc` | `codeberg-small` | 2 CPU, 4G RAM, 5 min limit |
| `cargo package` | `codeberg-medium` | 4 CPU, 8G RAM, 10 min limit |
| `nix flake check` | `atlas-nix-trusted` | Self-hosted, nix store access |

This writes `.forgejo/workflows/ci.yaml`. Release workflows are generated only by
explicit `simit init release` or the release skill; ordinary CI must not create a
publish workflow. To enforce CI drift checks, use
`simit init ci --platform forgejo --runner atlas --check` with the options the
installed binary accepts.

Hand-rolling the yaml is reserved for cases simit cannot express; in that case match the runner/container/checkout shape simit emits so the two stay diff-able.

## Codeberg shared runner tiers

Codeberg offers three shared runner sizes plus lazy variants. The "lazy" suffix (`-lazy`) adds scheduling delay in exchange for better Codeberg infrastructure utilization:

| Label | Arch | CPU | RAM | Runtime limit | Use for |
|---|---|---|---|---|---|
| `codeberg-tiny` | amd64 | 1 | 2G | 2 min | `cargo fmt --check`, quick validation |
| `codeberg-small` | amd64 | 2 | 4G | 5 min | `cargo clippy`, `cargo-deny`, `cargo-audit`, `cargo doc` |
| `codeberg-medium` | amd64 | 4 | 8G | 10 min | `cargo test`, `cargo nextest`, `cargo package` |
| `codeberg-tiny-lazy` | amd64 | 1 | 2G | 2 min | Non-urgent fmt, delayed scheduling |
| `codeberg-small-lazy` | amd64 | 2 | 4G | 5 min | Non-urgent clippy, delayed scheduling |
| `codeberg-medium-lazy` | amd64 | 4 | 8G | 10 min | Non-urgent tests, delayed scheduling |

Jobs that exceed the runtime limit are terminated. The granular preset above already accounts for these limits — `cargo test` goes to `codeberg-medium` (10 min) while `cargo fmt` goes to `codeberg-tiny` (2 min).

## Picking a `container:` for the job

- **Rust**: follow the image rendered by the installed Simit version. Current
  Rust 1.85 fixtures use `rust:1.85-bookworm`; do not invent a `trixie` tag for
  an MSRV unless the image exists and the generator emits it.
- **Nix**: `container: nixos/nix:latest`, or skip `container:` and install nix into the bare atlas image via `cachix/install-nix-action`.
- **Python / Go / Node-other-version**: use the official `python:`, `golang:`, `node:` images, or the bare atlas image plus `actions/setup-python` / `setup-go` / `setup-node`.

## Codeberg-specific action sources

Codeberg mirrors common actions at `code.forgejo.org/actions/`. Always use the full URL form:

```yaml
- uses: https://code.forgejo.org/actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4.3.1
- uses: https://code.forgejo.org/actions/cache@0057852bfaa89a56745cba8c7296529d2fc39830 # v4.3.0
```

GitHub-hosted actions also work via `https://github.com/<owner>/<repo>@<ref>` but pull from ghcr/github at runtime — prefer the Forgejo mirror for stability.

simit's generated CI yaml does its own bare-image checkout (manual `git init` + fetch) because the Alpine Rust container lacks the JS runtime the actions need — leave that block alone if you regenerate.

## Attic substituters for CI test jobs

CI test jobs that drive `nix` (`--runtime nix`, or hand-written nix workflows) should pull from our attic so flake-check is fast. CI is **read-only** against the cache — reads are anonymous, no token needed; the substituter config block is in [atlas-runner](.skillnet/deps/atlas-runner/SKILL.md). Cache **push** and the `canix cache token onboard --runner atlas` token flow are owned by [rust-crate-release](../rust-crate-release/SKILL.md); don't wire `ATTIC_TOKEN` here.

## Workflow examples

Read [workflow-examples.md](references/workflow-examples.md) only when a
hand-written workflow is unavoidable.

## Anti-patterns

See [atlas-runner](.skillnet/deps/atlas-runner/SKILL.md) for shared runner anti-patterns
(no per-workflow action-runtime install, no private-repo Actions, no DinD, and
no assumption that sccache is visible inside CI containers). Codeberg-specific:

- **Don't use `codeberg-medium` as a panic button** when atlas is down — if our runner is down, fix it. But DO use Codeberg runners deliberately when the granular paradigm calls for it.
- **Don't beat the runtime limit** — a full `cargo test --all-features` on a large crate can exceed the 2 min `codeberg-tiny` or 5 min `codeberg-small` limit. The granular preset puts test on `codeberg-medium` (10 min) for that reason. Verify wall-clock times per project.
- **Don't hand-roll checkout** with `git init`/`git fetch` outside simit's generated block; use `https://code.forgejo.org/actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4.3.1`.
- **Don't hand-roll CI yaml** when `simit init ci --platform forgejo` covers the project. Regenerate instead of patching by hand. Use tier-splitting flags only when `simit init ci --help` exposes them.
- **Don't put publish/release jobs in the ordinary CI workflow**. Tag-triggered
  Rust publication belongs to the workflow generated by `simit init release`,
  owned by [rust-crate-release](../rust-crate-release/SKILL.md).
- **Don't wire `ATTIC_TOKEN` or `CRATES_IO_API_TOKEN` here** — CI is read-only against the cache and never publishes. Token flow lives in the release skill.
