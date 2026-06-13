---
name: nixpkgs-update-pr
description: "Create and shepherd nixpkgs pull requests that UPDATE an existing package to a newer version: bump version/rev/source hash, refresh language lock or vendor hashes (cargoHash, vendorHash, npmDepsHash), absorb upstream restructures (moved sourceRoot, new build system, Cargo/Go/npm workspace and lockfile changes), validate the rebuild and binaries, push to a fork, open a draft PR with the live template, and run caniko/nixpkgs-review-gha. Use for version bumps, pname old to new changes, unstable-date bumps, `cargoHash`/`vendorHash` out-of-date refreshes, and updates that break because upstream reorganized. For brand-new packages or general PRs use `nixpkgs-init-pr`; for build failures on the current version use `nixpkgs-build-failure-pr`."
---

# nixpkgs-update-pr

Specializes `nixpkgs-init-pr` for the common case of moving an existing package to a newer upstream version. Same branch / publish / review discipline; this skill adds the version-bump mechanics and the restructure-and-lockfile pitfalls that updates routinely hit.

## Shared references

Before publishing or commenting upstream, read the common references in `../nixpkgs-pr-common/references/`:

- `decorum.md` for narrow scope, duplicate checks, and missing-data handling.
- `pr-template.md` before creating or updating a PR body.
- `nixpkgs-review-gha.md` before dispatching or diagnosing GitHub Actions review.

## Workflow

1. Confirm repo state and base.
   Run `git status -sb`, `git remote -v`, `gh auth status`. Confirm `upstream` is `NixOS/nixpkgs` and `origin` is the user's fork.
   If the checkout is dirty or on unrelated work, branch from a freshly fetched `upstream/master` (a separate worktree when the tree must stay untouched). Stage explicit paths only.

2. Pin the new source deliberately.
   Identify the exact rev/tag that contains the desired change — do not assume `HEAD`. For unstable packages, version as `<upstreamVersion>-unstable-YYYY-MM-DD` using the date of the pinned commit.
   When the package fetches from a mirror (e.g. `fetchFromGitLab` while development happens on GitHub, or vice-versa), verify the rev is present on the fetched forge before relying on it (`git ls-remote <forge-url> <rev|HEAD>`).

3. Prefer automation for the bump.
   If the package has — or can reasonably gain — `passthru.updateScript = nix-update-script { };`, bump with `nix-update <attr>` and keep only the intended diff. Validate the updater before publishing:

   ```bash
   nix eval --impure --expr 'let pkgs = import ./. { config.allowUnfree = true; }; in pkgs.<attr>.updateScript'
   nix-shell maintainers/scripts/update.nix --argstr package <attr>
   ```

   Otherwise bump by hand with the fake-hash loop: set each hash (`src` `hash`, then `cargoHash` / `vendorHash` / `npmDepsHash`) to `lib.fakeHash`, build, copy the real `got: sha256-…` back, and repeat for the next hash. Hashes surface in order (source first, then the vendor/deps hash), so expect one rebuild per hash.

4. Absorb upstream restructuring.
   An update is rarely just three new strings. Diff the new tree against the packaging's assumptions and adjust:
   - moved/renamed source dir → `sourceRoot` may be wrong; for a single member of a monorepo/workspace prefer `buildAndTestSubdir` (build) and `cargoRoot`/equivalent over pointing `sourceRoot` *into* the member (its path-dependencies live outside it).
   - changed build system, relocated entrypoints/binaries (recheck `mainProgram`), new runtime/native deps, license or maintainer drift, dropped/renamed features.
   - Drop a now-unused `finalAttrs:`/`rec` wrapper if the field that needed it is gone.

5. Refresh the lock / vendor correctly (see the Rust workspace pitfalls below for the most common trap).

6. Validate before publishing.
   `nix build .#<attr>`, then smoke-test executables in `./result/bin/` (run `--help`/`--version` and any new subcommands the update adds). Run `nix fmt <touched-file>` when formatting applies.
   After committing, run `./ci/nixpkgs-vet.sh master https://github.com/NixOS/nixpkgs.git` (it evaluates committed `HEAD`, not dirty edits).

7. Search for duplicate PRs.
   Search open and recently closed `NixOS/nixpkgs` PRs by package name and `pname: ` title fragments. Stop and report a substantially similar PR unless the user wants a replacement or follow-up.

8. Publish a draft PR.
   Title `pname: <old> -> <new>` (no trailing period). Link the upstream changelog/compare view and call out anything notable the update brings. Fetch the live PR template, fill it truthfully, and check only boxes backed by completed validation.

9. Run `caniko/nixpkgs-review-gha`.
   Dispatch after the draft PR exists; keep `Ran nixpkgs-review` unchecked and put the run URL in the summary until it passes, then update the body.

## Rust workspace / Cargo.lock pitfalls

These bite specifically on Rust updates where upstream has grown into a Cargo workspace:

- **One member of a workspace.** Build it with `buildAndTestSubdir = "<member-dir>";`. Do not set `sourceRoot` into the member — its `path = "../.."` dependencies resolve relative to the workspace root.
- **`cargoHash`/`fetchCargoVendor` vendors the *entire* workspace lock**, not just your member's closure. If a sibling member pulls a git dependency that the vendor tooling cannot resolve (e.g. `fetch-cargo-vendor-util: Couldn't find manifest for crate <x> inside …/git/<rev>`), or simply drags in heavy unrelated trees (slint, gstreamer), do not fight it — trim the workspace.
- **Trim to the target's closure.** Locally: copy the repo, rewrite the root `Cargo.toml` `members = [ … ]` to just the member plus its transitive *path* dependencies, regenerate the lock (`cargo generate-lockfile`), and confirm `grep 'source = "git+' Cargo.lock` is empty and `cargo build -p <crate> --frozen` succeeds. Commit that small, git-free lock next to the package.
- **`cargoLock.lockFile` is verified against the source tree's lock — it does not silently override it.** With a trimmed lock you must, in `postPatch`, (a) prune `members` the same way and (b) `cp ${./Cargo.lock} Cargo.lock` over the upstream root lock. Otherwise the build fails with `cargoHash … out of date / Cargo.lock is not the same in /build/cargo-vendor-dir` (the diff will be full of the sibling deps you tried to exclude). Keep `[workspace.dependencies]` and `[workspace.package]` intact — members reference them via `.workspace = true`.
- **`cargoHash` reads the source lock *before* `postPatch`**, so you cannot fix vendoring by editing the lock in `postPatch` when using `cargoHash`. For a trimmed lock use `cargoLock.lockFile = ./Cargo.lock;` (resolved at eval time) instead.
- A concise `postPatch` for the trim, robust to the exact member list:

  ```nix
  postPatch = ''
    sed -i '/^members = \[/,/^]/c\members = [ "<member>", "<path-dep-1>", "<path-dep-2>" ]' Cargo.toml
    cp ${./Cargo.lock} Cargo.lock
  '';
  ```

For Go (`vendorHash`) and Node (`npmDepsHash`) updates the analogous trap is simpler: a deps/lockfile change always invalidates the vendor hash — reset it to `lib.fakeHash` and re-derive; never reuse the old one.

## Failure modes

- Mixed worktree: move the update to a dedicated branch/worktree before staging.
- Rev not on the fetched forge yet (mirror lag): wait for sync or switch the fetcher to the authoritative forge in the same PR, noting why.
- `cargoHash`/`vendorHash` out of date after the bump: always re-derive via `lib.fakeHash`; never hand-edit hashes.
- Vendor cannot resolve a sibling git dependency: trim the workspace and commit a git-free lock (above); do not vendor unrelated members.
- Updater (`nix-update`) cannot run or produces an unrelated diff: stop and report per the missing-data contract in `decorum.md`; keep only the intended package-update changes.
- Failed review run: inspect logs, fix the branch, push, and rerun for the current PR head.
