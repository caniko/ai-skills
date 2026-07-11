# Secrets Profile

Inventory agenix/sops declarations, generated environment files, systemd
credentials, owner/group/mode, and startup ordering. Confirm secret values or
rendered configs never enter `settings`, `environment`, generated TOML/JSON,
or the Nix store.

Prefer service-native credential files, agenix/sops target rendering, or
systemd `LoadCredential` over ad hoc world-readable environment files. Check
dynamic-user ownership and every setup hook that needs pre-start access. A
`0444` mode is an explicit security tradeoff, not a default. Validate the
affected service evaluation and report the upstream rekey/generation workflow
when required material is absent.
