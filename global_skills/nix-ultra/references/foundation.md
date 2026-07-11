# Nix Skill Foundation

Shared rules for every Nix domain skill.

## Discover first

Inspect `git status --short`, `flake.nix`, `flake.lock`, all relevant `.nix`
files, NixOS/Home Manager outputs, overlays/packages, secrets, formatter,
checks, CI, and deployment wrappers. Use `rg --files -g '*.nix'` while
excluding `.git`, result symlinks, generated caches, `node_modules`, `target`,
and vendor trees.

Prefer repository commands and documented wrappers. Use `--no-update-lock-file`
for validation unless input updating is the task. Never fabricate secrets,
hashes, lock data, generated files, missing inputs, or option behavior.

If a required artifact is missing or invalid, stop and report the artifact, why
it is required, its upstream producer, the exact regeneration command, and the
validation command that proves recovery.

## Preserve worktree integrity

Do not reset, discard, or absorb unrelated changes. Keep structural, semantic,
input, and secret changes separately reviewable. Do not move generated
hardware/disk files or secret migrations during a cosmetic reorganization.

## Validation

Run the repository formatter check first, then the narrowest relevant eval:

```sh
nix fmt -- --check
nix eval .#<attr> --no-update-lock-file --accept-flake-config
nix flake check --no-build --no-update-lock-file --accept-flake-config
```

For touched NixOS hosts, evaluate the toplevel drv path. For touched Home
Manager outputs, evaluate an affected `homeConfigurations` attr. Build a
package only when evaluation cannot prove the change and the build is
affordable.

After each change rerun the narrowest failed check, then the relevant broad
gate. Do not continue with a red tree.

## Reporting

Separate facts, edits, skipped checks, assumptions, blockers, and residual
risk. Keep public option/output changes and would-be-breaking changes explicit.
