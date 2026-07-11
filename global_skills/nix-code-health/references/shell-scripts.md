# Generated Shell Profile

Inventory `writeShellScript`, `writeShellApplication`, hooks, activation
scripts, service `script`, heredocs, and command substitutions. Move static
TOML/JSON/YAML generation to `pkgs.formats`, `builtins.toJSON`, or
`lib.generators` when possible.

For required shell, use strict mode where appropriate, quote variables, use
absolute store paths or `runtimeInputs`, and factor scripts once they exceed a
small inline snippet. Prefer `writeShellApplication` for user-facing commands.
Do not handle secrets in shell when systemd credentials, agenix, sops, or a
service-native credential option fits. Evaluate the generated derivation and
run cheap script-specific checks.
