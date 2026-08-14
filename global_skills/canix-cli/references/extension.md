# Extending Canix

Prefer an existing `canix` subcommand over ad-hoc wrappers. Add a new command
only when the operation is repeatable and canix-specific conventions matter.

1. Choose `commands/hosts/` for topology/host work, `commands/cache/` for
   cache/pin operations, or `commands/repo/` for lockfiles, secrets, and repo
   health.
2. Add a variant to the existing command enum when the noun already exists.
3. Use `crate::fleet::target::Target`, `crate::fleet::hosts`, and `crate::exec`
   instead of re-parsing topology or spawning raw processes.
4. Register the command in the current dispatcher under `cli/src/app/mod.rs`;
   do not use the removed `cli/src/cli.rs` path.
5. Validate with `cargo build` or `nix build .#canix`, then
   `canix <new-command> --help`.

Do not extend canix for one-off investigations, ordinary upstream-tool usage,
or throwaway commands.
