# Shared Flake Modularization Routine

Use this reference whenever a skill creates, uplifts, or optimizes a project
`flake.nix` and modularization is appropriate. Keep this routine DRY by
linking here instead of copying it into other skills.

## When To Modularize

Modularize after generator output is correct, not before.

Use modules when at least one is true:

- `flake.nix` is hard to scan, typically over about 120 lines.
- A derivation, dev shell, CI support package, formatter config, or site/docs
  package is large enough to hide the output structure.
- The same dependency lists, package arguments, or shell inputs are repeated.
- Future generated updates should be easy to review.

Keep a compact single-file flake when the project has only trivial packages and
no repeated logic.

## Required Shape

Keep `flake.nix` as the entrypoint and move implementation details into `nix/`:

```text
flake.nix
nix/
  packages.nix
  checks.nix
  dev-shells.nix
  treefmt.nix
  pre-commit.nix
```

Use only the files that the project needs. Prefer descriptive module names for
domain-specific outputs, for example `nix/site.nix`, `nix/docs.nix`,
`nix/rust.nix`, or `nix/cross.nix`.

## Boundary Rules

`flake.nix` should keep:

- `description`;
- `inputs`;
- the `outputs = inputs @ { ... }:` boundary;
- system iteration, if present;
- high-level assembly of `packages`, `checks`, `devShells`, `formatter`,
  `apps`, and overlays.

`nix/*.nix` modules should hold derivations and build logic, repeated
dependency lists, dev shells, checks, formatter/hooks, and site/docs packages.
Pass dependencies explicitly; avoid implicit globals in imported modules.

Good module signature:

```nix
{
  pkgs,
  lib,
  craneLib ? null,
  self ? null,
  ...
}: {
  # outputs
}
```

Good import style:

```nix
let
  packages = import ./nix/packages.nix {
    inherit pkgs lib craneLib;
    src = ./.;
  };
in {
  packages = packages // {
    default = packages.my-package;
  };
}
```

## Preservation Rules

Preserve behavior first:

- Keep existing output names stable.
- Keep Simit-managed `nix/treefmt.nix` and `nix/pre-commit.nix` compatible
  with `simit init flake --check`.
- Do not move generated hook files unless the generator already uses that path.
- Do not delete packages, checks, shells, overlays, or apps because they look
  unused.
- Do not change pins, follows relationships, or builders unless the active task
  requires it.

## Refactor Order

1. Run the generator or make the functional flake change first.
2. Validate evaluation before splitting when feasible:
   ```sh
   nix flake check --no-build
   ```
3. Move one concern at a time into `nix/<concern>.nix`.
4. Re-evaluate after each meaningful split if the flake is complex.
5. Run final validation:
   ```sh
   nix flake show
   nix flake check --no-build
   ```
6. Run `nix build` when the project has a clear default package or check.

## Stop Conditions

Stop and report instead of guessing when a module needs missing source files, a
package version/binary/workspace input cannot be derived, custom outputs are
ambiguous, or `simit init flake --check --diff` fails after modularization.

Report the blocker, upstream artifact or producer, regeneration/inspection
command, and validation command that proves the fix.
