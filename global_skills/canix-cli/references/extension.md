# Extending Canix

Prefer an existing `canix` subcommand over ad-hoc wrappers. Add a new command
only when the operation is repeatable and canix-specific conventions matter.

Read `/data/nvme0/can/canix/docs/src/design/cli-products.md` before choosing an
implementation owner. Fleetix owns generic topology and configurable deployment
(including the conventional NixOS backend); canix-toolbelt owns reusable
architecture conventions for external adopters; Canix owns fleet-specific data
and policy. Existing specialist libraries keep their engines. Treat this as a
target boundary and check the document's implementation status before using an API.

Fleetix and toolbelt expose library crates published to crates.io through Simit
CI. Consume verified registry versions directly in Cargo and call shared typed
operations in-process. Do not use a Nix source substitution, flake app, or another
frontend executable as a library bridge. Preserve output/role contracts, attempts,
checkpoints, GC roots, the shared host activation lock and remote compatibility.
Migrate Canix and remove duplicated behavior in each published vertical slice.

1. Put shared behavior with the owner above. For remaining Canix adapters, use
   `cli/crates/canix-ops/src/commands/` for hosts/cache/repo operations,
   `canix-commands` for general commands, `canix-workspace-command` for project
   workflows, and `canix-foundation` for Canix-specific shared support.
2. Add a variant to the existing command enum when the noun already exists.
3. Use `crate::fleet::target::Target`, `crate::fleet::hosts`, and `crate::exec`
   instead of re-parsing topology or spawning raw processes.
4. Register the command in the current dispatcher under `cli/src/app/`;
   do not use the removed `cli/src/cli.rs` path.
5. Run focused Cargo checks/tests in the approved project environment and
   treefmt, then `canix <new-command> --help` and compare generated personal/admin
   command schemas. Packaging uses `canix cache binary build .#canix-admin`.

Do not extend canix for one-off investigations, ordinary upstream-tool usage,
or throwaway commands.
