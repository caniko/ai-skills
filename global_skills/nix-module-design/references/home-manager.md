# Home Manager Profile

Identify standalone, integrated, or dual-mode Home Manager configurations.
Separate user defaults from host overlays, use explicit `osConfig` fallbacks,
and avoid importing user modules directly into host layers unless that is the
documented convention.

Use explicit package provenance, `xdg.configFile`, `home.file`, and user
systemd services consistently. Never write secrets or machine state into the
store. Evaluate an affected `homeConfigurations` output or integrated host.
