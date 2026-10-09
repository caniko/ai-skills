# Canix Secrets and Registries

Load canix-structure-reference from `.skillnet/deps/canix-structure-reference/SKILL.md`
relative to the assembled **canix-cli package root**, not this reference directory,
for canix/project roots, ownership boundaries, and generated-sidecar rules.
The reference directory may itself be a symlink into the immutable source store.

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
