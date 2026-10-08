---
name: canix-cli
description: Use canix for fleet deployment, inspection, secrets, Attic cache, media, checks, and repeatable subcommands; avoid shell that bypasses Fleetix or secret conventions.
---

# Canix CLI

Load [canix-structure-reference](.skillnet/deps/canix-structure-reference/SKILL.md) before
crossing canix/project/workspace boundaries. It owns the canonical roots and
registry rules used by this CLI reference.

Use `/data/nvme0/can/canix`'s `canix` command instead of raw
`nixos-rebuild`, `nix flake update`, `attic`, or fleet-host SSH when canix wraps
the operation. The CLI is the source of truth for routing, generated state,
secret ownership, and stable result links.

## Discover the current surface

Do not maintain a copied command catalogue. Ask the installed binary:

```sh
cd /data/nvme0/can/canix
canix --help
canix <group> --help
```

Current groups include rebuild, bootmedia, host, repo, identity, secret,
cache, release, fleet, project, workspace, plinth, and runtime; subcommands
change with the flake. Use the exact installed help for options and names.

Resolve project identity and checkout paths through the workspace commands:

```sh
cd /data/nvme0/can/canix
canix workspace check
canix --output json workspace show <project>
canix workspace cleanup
```

The structure reference defines the snapshot/sidecar distinction, the
build-host invariant, and the fallback when an installed binary lacks
`workspace`.

Load only the reference needed by the task:

- [host-targeting.md](references/host-targeting.md) for fleet routes and SSH;
- [attic.md](references/attic.md) for cache tokens and endpoint modes;
- [secrets-and-registry.md](references/secrets-and-registry.md) for agenix,
  Fleetix sources, generated topology, and result links;
- [extension.md](references/extension.md) when the requested operation is not
  already a subcommand or shared CLI behavior is being extracted. It routes
  generic Fleetix deployment, reusable toolbelt architecture, and Canix policy
  to published Cargo libraries, with explicit migration compatibility gates.

## Safety boundary

Inspect `git status --short` before changing canix or a target repository. Do
not reset, discard, absorb unrelated changes, or bypass operator-held sudo,
FIDO, or secret prompts. If a required host, topology source, generated
sidecar, secret, or command is missing, report the producer, regeneration
command, and validation command instead of guessing.

For deployments and host operations, pass a registered host positionally and
let canix resolve it through Fleetix. Use explicit route/address overrides only
when discovery or the user requires them.

## Validation

Use the narrowest current canix checks first:

```sh
canix repo doctor
canix repo check
canix <changed-group> --help
```

For code or command changes, use focused native language tests in the approved
direnv environment, plus treefmt. Validate Nix packaging through the actual
production output with `canix cache binary build .#<package>`, retaining and
publishing its closure. Nix test-only builds require `--include-tests`;
`canix repo flake-check --plan` never builds, and executing a profile is an
explicit Nix-test request. Use `canix repo direnv status/prepare` to inspect
or warm the existing approved nix-direnv environment; preparation does not
apply environment variables to its parent or approve `.envrc` automatically.

Run the repository's documented focused validation,
then verify the exact subcommand help. Do not claim success when an external
activation or DNS/secret operation was not actually performed.
