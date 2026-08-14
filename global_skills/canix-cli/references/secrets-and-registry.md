# Canix Secrets and Registries

Load [canix-structure-reference](../../canix-structure-reference/SKILL.md) for
canix/project roots, ownership boundaries, and generated-sidecar rules.

Use canix for agenix edits and registry-backed host/project data:

```sh
canix secret edit age/secrets/root/hosts/thething/hermes_webui_caddy_env.age
canix secret edit --host thething --name hermes_webui_caddy_env
```

Inspect project paths with `canix --output json workspace show <project>` and validate
with `canix workspace check`.

Fleet hosts live in Fleetix Pkl sources and the generated
`lib/generated/topology.nix`; add a host in the Pkl source, import it in
`Topology.aggregated.pkl`, then run:

```sh
nix run .#fleetix-export
```

Keep stable `.nix-results/<name>` links under canix's result commands. Attic
projects, workspace project paths, host facts, and secret paths are
registry-owned; do not hand-edit generated sidecars or encrypted files.
