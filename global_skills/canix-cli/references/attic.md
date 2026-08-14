# Canix Attic Operations

Use the canix CLI as the operator-facing interface. Do not shell out to
`attic login`, issue tokens over SSH, paste tokens into repositories, or print
secret plaintext. Keep sudo and FIDO prompts visible to the operator.

## Identify the cache first

There are two different recovery paths:

- The primary fleet cache (`canix`) uses the operator JWT and the cache signing
  key. Diagnose it with `canix cache health`; repair an expired JWT or declared
  public-key drift with `canix cache recover` (use `--apply` only when the
  reported drift is intended).
- A named private project cache, such as `harbor-macos-sdk`, uses a
  registry-backed project token. A 401 from that cache is not fixed by
  `canix cache recover`.

Start with:

```sh
cd /data/nvme0/can/canix
canix cache health
nix show-config | rg '^(substituters|netrc-file|trusted-public-keys)'
```

Record the failing cache URL and project name. Never weaken a netrc mode or
copy its password into diagnostic output. A root-owned 0600 netrc is expected
to be unreadable to the invoking user. Do not use an unprivileged direct-store
probe as proof of cache authentication: the real rebuild daemon owns the
credential file. Use the cargo preflight dry-run or the ordinary guarded
rebuild as the daemon-context probe. `canix cache health` reports whether its
effective configuration can be independently checked.

```sh
canix repo check --host <host>
```

## Private project token workflow

For an existing registry entry, use the guarded activation flow. Its dry run
shows the planned secret, rekey, rebuild, and cache-auth bootstrap steps:

```sh
canix cache token list
canix cache token activate <project> --consumer <host> --dry-run
canix cache token activate <project> --consumer <host>
```

Activation is the normal path for a consumer host. It rekeys the age secret,
deploys the host, and verifies the private cache authentication. The final
rebuild gate must be the ordinary command, without `--no-token-check`:

```sh
canix rebuild switch <host>
```

Use `--no-token-check` only for explicitly documented diagnosis or bootstrap;
it is not evidence that the cache problem is solved.

## Registering or rotating a project

The canonical project registry is `lib/attic/Projects.pkl`. Register or
onboard through canix, then regenerate the checked-in sidecar if the command
changed the Pkl source:

```sh
canix cache token register <project> --consumer <host>
# or, for a new CI consumer:
canix cache token onboard <project> --runner <host>
nix run .#pkl-to-nix -- lib/attic/Projects.pkl lib/generated/attic-projects.nix
agenix rekey -a
canix rebuild switch <host>
```

For rotation:

```sh
canix cache token refresh <project>
canix cache token activate <project> --consumer <host>
```

`refresh` requires an interactive sudo prompt. The refreshed encrypted source
must be at exactly:

```text
age/secrets/root/modules/attic_projects/<name-with-hyphens-replaced-by-underscores>.age
```

This is the path resolved by `secrets.atticProject` in
`flake/_shared/config_lib.nix` and consumed by the NixOS modules. The old
`age/secrets/attic_projects/` path is legacy and must not become a durable
source of truth.

If refresh reports the legacy path, or the canonical ciphertext remains
unchanged, suspect a stale installed canix binary or an old token workflow.
Do not silently deploy the wrong file. Inspect the producer and source paths:

```sh
rg -n 'SECRET_DIR|secret_path|atticProject' cli/src flake/_shared/config_lib.nix
git status --short -- age/secrets age/rekeyed
```

Fix the producer/binary first, preserve the old ciphertext if a migration is
needed, then run `nix run .#agenix -- rekey -a`. Never decrypt or display the
token to diagnose a path mismatch.

## FIDO and deployment failures

`agenix rekey` and token refresh may require a Nitrokey/YubiKey touch. Keep the
hardware present and retry the prompt with `y`; never choose a dummy identity
or bypass the FIDO prompt. Repeated `libfido2` errors are a real blocker:
report the exact command, error, missing key, and validation command rather
than claiming the rotation completed.

If `atticd` itself fails during activation, read its journal before diagnosing
the Nix cache as an authentication problem:

```sh
systemctl status atticd.service --no-pager -l
journalctl -u atticd.service -b --no-pager -n 80
```

For the local PostgreSQL peer-auth setup, Attic needs both an explicit database
role and a parseable URL authority. The working shape is:

```text
postgresql://atticd@localhost/atticd?host=/run/postgresql
```

The shorthand `postgresql:///atticd?host=/run/postgresql` may make Attic try
the role `anonymous` or fail URL parsing. Keep the `atticd` role declared with
`services.postgresql.ensureUsers` and `ensureDBOwnership`; do not respond by
disabling unrelated service sandboxing or by creating a dummy database role.
Validate the rendered URL before retrying activation:

```sh
nix eval --json '.#nixosConfigurations.atlas.config.services.atticd.settings.database.url'
```

If activation completed but Nix still receives 401, check the rendered
configuration and daemon reload without exposing the secret:

```sh
nix show-config | rg '^(netrc-file|substituters)'
nix eval --json '.#nixosConfigurations.<host>.config.age.secrets' --apply builtins.attrNames
canix cache health
```

The NixOS module must declare the project token, render a mode-0600 netrc for
the cache's loopback and canonical endpoints, and restart `nix-daemon` after
activation. If those facts are absent, repair the upstream module/secret
declaration before retrying deployment.

## Completion evidence

For a primary-cache repair, rerun `canix cache health` and confirm all cache
checks pass. For a private project-cache repair, confirm the named cache no
longer returns 401, then run:

```sh
canix rebuild switch <host>
canix rebuild status <host>
canix host healthcheck <host>
```

Do not call a rebuild complete while the exact guarded `canix rebuild switch`
gate still fails, even if a dry run or a build without the token check passes.

## Endpoint modes

Registry-backed cache endpoints use `dns` (default HTTPS), `lan` (server LAN),
and `loopback` (atlas itself). Direct P2P links use an explicit
`canix.caches.atticBaseUrl`. Consult `canix cache --help` and the current Nix
module before adding or changing an endpoint mode.
