---
name: atlas-runner
description: Shared reference for the self-hosted "atlas" Forgejo Actions runner (two labels — `atlas` on the bare `canix-runner:local` image, and `atlas-nix-trusted` on the host-nix `canix-nix-runner:local` image) and the canix Attic cache (`https://attic.candee.baby/canix`). Defines the two runner instances and when to pick each, the bare runner image, the bind-mounted action runtime, the Attic substituter config, runner-online checks, and Codeberg ToU constraints. Not user-invokable on its own; loaded by `forgejo-ci` and `forgejo-atlas-ci`.
---

# atlas runner — shared reference

Shared reference — not user-invokable on its own; loaded by [forgejo-ci](../forgejo-ci/SKILL.md) and [forgejo-atlas-ci](../forgejo-atlas-ci/SKILL.md).

Load [canix-structure-reference](.skillnet/deps/canix-structure-reference/SKILL.md) for
canix path and ownership rules; this reference owns only Atlas runner and
cache facts.

Canonical facts about the self-hosted `atlas` Forgejo Actions runner and the canix Attic cache. There are **two** runner instances on atlas, each backed by its own locally-built OCI image, registered against `https://codeberg.org/` (source: `/data/nvme0/can/canix/root/hosts/atlas/server/build-release/forgejo_runners.nix`).

## Runner selection — two labels

## Fleet build-host invariant

Atlas is the canonical and exclusive build host for fleet releases, including
aarch64 targets. Cross-compile or prepare target closures from Atlas through
canix/Crossbow; never build natively on a target board and never configure a
target host as a Nix remote builder. A target host may be contacted over SSH
only for inspection, activation orchestration owned by canix, and
post-deployment verification.

The runner host advertises **two** labels via two separate Forgejo runner instances. Pick the one that matches what the job does:

| Label | Instance | Image | Use for |
|-------|----------|-------|---------|
| `atlas` | `codeberg` | `canix-runner:local` (bare act image) | JS/composite actions (`actions/checkout`, `actions/cache`) and cargo-in-container jobs that set `container: rust:*`. `/nix/store` is **read-only**. |
| `atlas-nix-trusted` | `nixTrusted` | `canix-nix-runner:local` (host-nix image) | Jobs that run `nix develop` / `nix build` / `nix flake check` and need to **write the host /nix/store** or trigger the host auto-push. Writes go through the **bind-mounted host nix daemon** (`NIX_REMOTE=daemon`); the `/nix/store` bind is still read-only. |

```yaml
# JS actions, or cargo inside a rust:* container:
runs-on: atlas

# nix develop / nix build / nix flake check that writes the store
# or relies on the host post-build-hook auto-push to Attic:
runs-on: atlas-nix-trusted
```

Rule of thumb: if the job touches the Nix store via the host daemon (writes derivations, expects the host auto-push to Attic), it **must** use `atlas-nix-trusted`. Both images bind-mount `/nix/store` **read-only** (`-v /nix/store:/nix/store:ro`); the trusted image's *write* capability comes not from a read-write store bind but from the additionally bind-mounted host nix daemon socket (`/nix/var/nix/daemon-socket/socket`) plus `NIX_REMOTE=daemon`, so writes are routed through the host daemon. The bare `atlas` image has the store read-only and **no** daemon socket. Everything else (JS actions, composite actions, and cargo work that runs inside a `container: rust:*` image where the toolchain is self-contained) uses `atlas`.

For jobs intended for these self-hosted instances, do **not** write
`runs-on: nix`, `runs-on: docker`, or `runs-on: ubuntu-latest`, and do not use
Codeberg hosted tiers as if they were self-hosted labels. The Pages/Codeberg CI
skills may deliberately select `codeberg-tiny`, `codeberg-small`, or
`codeberg-medium`; this reference governs only the `atlas` and
`atlas-nix-trusted` instances.

## What's baked into the `atlas` image

The bare `canix-runner:local` image (label `atlas`) is deliberately minimal — only what `act` needs to drive third-party actions:

- node 24 (for JS-based actions like `actions/checkout`, `actions/cache`)
- git (also required by `actions/checkout`)
- bash, coreutils, curl, tar, gzip, which, CA certs

Language toolchains (rust, python, go, java, nix, …) are **NOT** baked into the image. Each workflow declares the toolchain it needs via `container:` (or `setup-*` actions). This keeps the runner image tiny (~120 MB compressed) and avoids version-pinning conflicts between projects.

If you omit `container:`, the job runs in the bare atlas image (node + git + bash) — fine for pure JS/composite-action workflows, no cargo, no python, no apt.

The `atlas-nix-trusted` instance uses a separate image (`canix-nix-runner:local`) that additionally bakes in `nix` and bind-mounts the host nix daemon, so its jobs can write the host `/nix/store` and trigger the host post-build-hook auto-push. Use it only for the nix-writing jobs described under "Runner selection".

## Action runtime bind-mounted into job containers

Job-level `container:` images hide the bare runner image, but `forgejo-runners.nix` bind-mounts the action runtime into every job container at stable locations. Existing workflow container names stay unchanged, and JavaScript actions still find `node`, `git`, `bash`, `curl`, `tar`, `gzip`, `which`, and CA certs. Do **not** add workflow steps to install Node or replace `actions/checkout` with manual git checkout just because the job uses `container: rust:*`.

## sccache — host-side policy, NOT in CI containers

> **Status: sccache is deployed for host-side Nix builds on atlas, but NOT injected into Forgejo runner containers.**

sccache is active on atlas for Nix builds through the generic
`rs-harbor.lib.mkBuildCachePolicy` and `nixosModules.buildCache` contract.
Atlas selects the build-platform sccache package and derives the versioned
`canix-rust` namespace plus shared cache child from the active build-cache
policy; the sandbox cache is mounted at `/tmp/sccache`. It keeps Garage
credentials in the transport layer and scopes
`XDG_CACHE_HOME` inside sccache and scrubs daemon/S3 variables before each
sandbox compiler invocation. Crossbow cross-Rust derivations use the same
policy from Atlas; the target machine is never a compiler builder.

However, sccache is **NOT** injected into Forgejo runner job containers. The runner images (`canix-runner:local`, `canix-nix-runner:local`) do not include a static sccache binary, and no `RUSTC_WRAPPER` or `SCCACHE_*` env is set in the container environment. Do **not** rely on a compiler cache that the runner containers do not provide.

**What to do in CI workflows instead:** cache via the mechanisms that *are* wired:

- For raw-cargo workflows, use `Swatinem/rust-cache@v2` or `actions/cache@v4` keyed on `Cargo.lock` (the runner enables Forgejo's built-in cache backend via `cache.enabled = true`). This is the canonical caching guidance — see [forgejo-ci](../forgejo-ci/SKILL.md).
- For nix-flake jobs, pull dependencies from the canix Attic substituter (below).

Because sccache is absent from runner containers, do not add `echo RUSTC_WRAPPER=sccache` expecting the runner to supply the binary — there is nothing to wrap to. If you genuinely want a compiler cache in a single workflow, install and configure sccache explicitly within that workflow (and own its backend), but prefer `rust-cache` / Attic.

## Attic substituter config

Wire the canix Attic substituter so dependencies pull from atlas instead of building locally. Reads are anonymous — no token needed for substituter reads:

```yaml
- uses: https://github.com/cachix/install-nix-action@ba0dd844c9180cbf77aa72a116d6fbc515d0e87b # v27
  with:
    extra_nix_config: |
      experimental-features = nix-command flakes
      substituters = https://attic.candee.baby/canix https://cache.nixos.org
      trusted-public-keys = canix:lPzPzKrmYqW5Rxa5r0uQWvCqD3S5nx0h2eCy7XD5JM8= cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=
```

Forgejo Actions requires the full `https://...` URL prefix on non-local actions (e.g. `https://code.forgejo.org/actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4.3.1`).

## Attic token onboarding (push) — defer to canix-cli

Pushing build outputs to the cache needs a project-scoped token. Issue and wire it through the [canix-cli](../canix-cli/SKILL.md) skill, **not** by hand. For projects targeting the `atlas` runner, the user runs (from `/data/nvme0/can/canix`; `atticd-atticadm` needs sudo, so the prompt is human-in-the-loop on their end):

```sh
canix cache token onboard <project> --runner atlas
agenix rekey -a
canix rebuild switch atlas
```

This encrypts the token under
`age/secrets/root/modules/attic_projects/<project>.age` (with hyphens
normalized to underscores), registers it in `lib/attic/Projects.pkl`, and
bind-mounts `/run/canix-attic-tokens/` into job containers as
`$ATTIC_TOKENS_DIR`. Workflows then read the token by path
(`cat "$ATTIC_TOKENS_DIR/<project>"`) and skip any `secrets.ATTIC_TOKEN`.
Token rotation and the deeper registry mechanics live in
[canix-cli](../canix-cli/SKILL.md).

## Verifying the runner is online

Before opening a PR with new workflows, confirm both runner instances are
registered. Current canix names them as systemd services. On atlas:

```sh
sudo systemctl status forgejo-runner-codeberg.service      # label: atlas
sudo systemctl status forgejo-runner-nixTrusted.service    # label: atlas-nix-trusted
sudo systemctl status forgejo-runner-image-load.service    # image loader, when present
sudo podman images | grep -E 'canix-runner|canix-nix-runner'   # confirms both images are in podman's store
```

Then check the Codeberg side under Repo/Org/User Settings → Actions → Runners. Both instances register against `https://codeberg.org/` and report these registration **names**:

- `atlas-codeberg` — advertises the label `atlas`.
- `atlas-codeberg-nix-trusted` — advertises the label `atlas-nix-trusted`.

The **labels** workflows must use are `atlas` and `atlas-nix-trusted` (see "Runner selection"). If an instance isn't listed, or `forgejo-runner-image-load` failed, jobs targeting that label sit pending forever — fix registration / image load first.

## Codeberg ToU hard constraints

When the runner is registered against `codeberg.org`:

- The repository **must be public and under a free/libre license**. CI jobs on private/proprietary repos violate Codeberg ToU even when running on our own hardware, because the runner is registered against the Codeberg instance.
- Don't jam the queue: each of the two runner instances is pinned to `runner.capacity = 1` (`forgejo_runners.nix`). So each instance runs exactly **one** concurrent job — no single label gets 2-way parallelism; jobs targeting the same label serialize. (Two jobs *can* run at once only if one targets `atlas` and the other `atlas-nix-trusted`.) Use `concurrency` groups; gate heavy jobs behind tags.
- No DinD. Image builds must use `buildah` or `podman` against the host's podman socket (already wired via `DOCKER_HOST`).
