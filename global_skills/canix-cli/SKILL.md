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

The structure reference defines the snapshot/sidecar distinction and the
fallback when an installed binary lacks `workspace`.

## Build-host invariant

Atlas is the only permitted Nix/Cargo build host. Never run a native aarch64
build on a deployment target, never use a target device as a Nix remote
builder, and never SSH to a target to compile or realize a package. For
aarch64 hosts, invoke the canix Crossbow/rebuild workflow from Atlas; target
SSH is restricted to read-only inspection and post-activation verification.

Load only the reference needed by the task:

- [host-targeting.md](references/host-targeting.md) for fleet routes and SSH;
- [attic.md](references/attic.md) for cache tokens and endpoint modes;
- [secrets-and-registry.md](references/secrets-and-registry.md) for agenix,
  Fleetix sources, generated topology, and result links;
- [extension.md](references/extension.md) when the requested operation is not
  already a subcommand.

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

For code or command changes, run the repository's documented Nix/Cargo check,
then verify the exact subcommand help. Do not claim success when an external
activation or DNS/secret operation was not actually performed.
