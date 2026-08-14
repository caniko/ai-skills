---
name: codeberg-pages-dns
description: Wire Codeberg Pages custom domains and canix-managed DNS. Use for custom domains, DNS migration, canonical URLs, or deployment-mode checks.
---

# Codeberg Pages DNS

Load [canix-structure-reference](.skillnet/deps/canix-structure-reference/SKILL.md) before
resolving Fleetix or canix-toolbelt checkouts. It owns canix project paths and
the generated-topology boundary; this skill owns Pages deployment-mode and DNS
record decisions.

Use Codeberg's current git-pages model for new deployments. Legacy Pages Server
v2 sites may retain their existing `.domains` workflow only after discovery
classifies them as legacy; never mix the two models silently.

## Discovery

1. Inspect the site repository and canix state before editing:

   ```sh
   git remote -v
   git ls-remote --heads origin pages trunk main master
   rg -n 'git-pages|\.domains|codeberg\.page|base_url|site-url' -S .
   ```

2. Classify the deployment as `legacy-v2`, `git-pages-webhook`, or
   `git-pages-forgejo-action`.
3. Confirm the site output, canonical URL, target repository clone URL, and
   whether both the bare and `www` hostnames are required.
4. If the canix/Fleetix topology cannot represent the deployment mode and its
   authorization records, stop before editing DNS. Do not encode a new site
   using the legacy `<repo>.caniko.codeberg.page` target.

## Current git-pages records

For a Forgejo Actions deployment, configure:

- CNAME for the site hostname to `codeberg.page`;
- TXT at `_git-pages-forge-allowlist.<domain>` containing the repository's
  HTTPS clone URL;
- matching records for `www` when both names are intentionally served;
- the Forgejo action with `site: https://<custom-domain>/` and
  `server: codeberg.page`.

For a webhook deployment, use `_git-pages-repository.<domain>` instead of the
Forgejo allowlist record. The current git-pages server does not require a
`.domains` file; retain one only for an explicitly classified legacy-v2 site.

## canix integration

The durable producer is the Fleetix site model and canix-toolbelt DNS
synthesis, not a hand-written zone record. Until the model carries deployment
mode and authorization records, report the blocker and use the upstream repair
workflow:

```sh
cd /data/nvme0/can/canix/projects/repos/owned/codeberg.org/caniko/fleetix
nix build .#checks.x86_64-linux.fleetix-lib-helpers

cd /data/nvme0/can/canix/projects/repos/owned/codeberg.org/caniko/canix-toolbelt
nix flake check

cd /data/nvme0/can/canix
nix run .#fleetix-export
```

Then validate the generated topology and both CNAME and mode-correct TXT
records before removing any legacy check or record:

```sh
nix build --no-link .#checks.x86_64-linux.dns-codeberg-pages-cnames-match-topology
nix eval .#nixosConfigurations.thething.config.canix-toolbelt.dns.zones.\"tartanoglu.com\".records --json
```

Do not apply DNS while the generated sidecar or topology schema cannot prove
which deployment mode owns the record.

## Site and DNS workflow

1. Update the site's canonical URL and deployment action together.
2. For legacy-v2 only, preserve the existing `.domains` producer and old
   target until that site is explicitly migrated.
3. For current git-pages, add the mode-appropriate CNAME/TXT records through
   canix's generated topology or an approved manual zone entry.
4. Validate locally before applying:

   ```sh
   nix build .#site
   curl -fsSI https://<custom-domain>/
   curl -fsSI https://<custom-domain>/docs/
   ```

5. Plan/apply DNS only through the repository's documented wrapper. If it
   requires operator-held credentials or FIDO confirmation, stop and report the
   exact command for the operator; never simulate success.
6. Verify externally:

   ```sh
   nix shell nixpkgs#bind -c dig @1.1.1.1 +short <custom-domain> CNAME
   nix shell nixpkgs#bind -c dig @1.1.1.1 +short _git-pages-forge-allowlist.<custom-domain> TXT
   curl -fsSI https://<custom-domain>/
   ```

## Safety

- Preserve dirty worktrees and unrelated canix changes.
- Do not globally rewrite legacy `.domains` files or DNS targets without a
  per-site migration classification.
- Remove a manual record only after generated topology proves it replaces the
  same deployment-mode record.
- Treat missing site output, repository identity, topology support, or DNS
  authorization as blockers and report the producer, regeneration command, and
  validation command.

## Related skills

- `forgejo-pages` — build and publish the site.
- `forgejo-docs` / `forgejo-site` — docs-only or combined site composition.
- `canix-cli` — repository-authoritative DNS and secret operations.
