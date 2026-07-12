---
name: pink-raven-release
description: Release or verify Pink Raven production on runner through canix. Use when the user asks to deploy, release, bump, roll out, or verify Pink Raven/raven.example.com via canix, runner, or the pink-raven flake input.
---

# Pink Raven Release

## Use With Reference

First use `canix-hosted-release-reference`, then apply these Pink Raven defaults.

## Fixed Defaults

- Source repo: `~/canix/canix/projects/repos/owned/gitlab.com/caniko/pink-raven`
- canix repo: `~/canix/canix`
- canix input: `pink-raven`
- Production host: `runner`
- Main service: `pink-raven.service`
- Worker services: `pink-raven-worker.service`, `pink-raven-caption-worker.service`
- Public endpoints:
  - `https://raven.example.com/healthz`
  - `https://raven.example.com/docs/`
  - `https://raven.example.com/docs/index.html`

## Pink Raven Checks

Before updating canix, run release-relevant Pink Raven checks:

```sh
cd ~/canix/canix/projects/repos/owned/gitlab.com/caniko/pink-raven
nix build .#docs --no-link
nix build .#raven --no-link
```

When a change touches version display or docs routing, also run the targeted Rust test that covers the docs version marker if it exists:

```sh
nix develop -c cargo test docs_sidebar_version_matches_package_version
```

Check source state:

```sh
git status --porcelain
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git tag --points-at HEAD
```

## canix Release

From canix:

```sh
cd ~/canix/canix
nix flake update pink-raven
git diff -- flake.lock
nix eval --raw .#nixosConfigurations.runner.config.system.build.toplevel.drvPath
canix rebuild switch runner
```

If personal `canix` lacks `rebuild`, use the admin package:

```sh
nix build .#canix-admin --no-link --print-out-paths
<printed-path>/bin/canix rebuild switch runner
```

Do not use full `nix flake check --no-build` as the only gate when unrelated nomad/home-manager evaluation is already broken; use runner-specific eval for Pink Raven release safety and report unrelated failures separately.

## Production Verification

Verify the release after switching:

```sh
systemctl is-active pink-raven.service pink-raven-worker.service pink-raven-caption-worker.service
systemctl show -p ExecStart pink-raven.service
curl -I --max-time 15 https://raven.example.com/healthz
curl -I --max-time 15 https://raven.example.com/docs/
curl -I --max-time 15 https://raven.example.com/docs/index.html
```

Expected docs behavior for unauthenticated users:

- `/docs/` redirects to `/docs/index.html`.
- `/docs/index.html` redirects to `/login`.

## Service Routing

`raven.example.com` reaches pink-raven through a two-hop proxy chain:

```
Internet → Cloudflare (CNAME raven → example.com, proxied)
  → host-a Caddy :443 (SNI raven.example.com, dial 192.168.178.88:80)
    → runner local Caddy (raven.example.com HTTP → reverse_proxy localhost:3030)
      → pink-raven binary (127.0.0.1:3030)
```

Pink-raven bind on runner: `127.0.0.1:3030`. The gateway proxy on host-a auto-generates routes from the Fleetix service registry (`lib/topology/Services.pkl`, name `"pink-raven"`, `port = 3030`, `targetHost = "runner"`). The local reverse proxy on runner forwards virtual-host-aware requests.

**Dependency note**: raven.example.com depends on host-a's Caddy being healthy. If host-a's Caddy is down (e.g. during a rebuild), raven.example.com returns 502. This is normal — no action needed unless Caddy remains down after the rebuild completes.

**Service restart** (from runner):

```sh
sudo systemctl restart pink-raven
```

## Known Current Blocker Class

`home-manager-can.service` may fail during runner switch if `~/canix/canix/projects/repos/owned/codeberg.org/caniko/ai-skills` is dirty. Do not hide this. If Pink Raven services start and endpoint checks pass, report Pink Raven as deployed while also reporting the host switch nonzero exit and the validation command:

```sh
git -C ~/canix/canix/projects/repos/owned/codeberg.org/caniko/ai-skills status --short --branch
systemctl is-active home-manager-can.service
```
