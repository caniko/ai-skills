---
name: nixpkgs-build-failure-pr
description: "Create narrowly scoped nixpkgs pull requests that fix package build failures from logs or CI failures. Use when a user provides a failing nix build log, ofborg failure, Hydra failure, local derivation failure, kernel/API breakage, compiler error, dependency build failure, or asks to fix a nixpkgs build failure PR. Requires reproducing or inspecting the failing log, identifying the upstream cause, validating the fixed build, using the live nixpkgs PR template, and reviewing with caniko/nixpkgs-review-gha."
---

# nixpkgs-build-failure-pr

Lineage: this skill specializes the generic evidence-backed research dossier pattern for nixpkgs build failures while preserving its domain-specific diagnose, fix, and validation workflow.

## Shared references

Before publishing or commenting upstream, read the common references in `../nixpkgs-pr-common/references/`:

- Generic research base: [long-horizon-research](../long-horizon-research/SKILL.md) — this skill is a nixpkgs-build-grounded specialization of the generic dossier-producer pattern.
- Sibling research router: [research-routing](../research-routing/SKILL.md).
- `decorum.md` for narrow scope, duplicate checks, and missing-data handling.
- `pr-template.md` before creating or updating a PR body.
- `nixpkgs-review-gha.md` before dispatching or diagnosing GitHub Actions review.

## Workflow

1. Inspect the failure before editing.
   Use the provided log, `nix log <drv>`, CI logs, or `nix build -L` reproduction.
   Record the failing derivation, attr if known, exact compiler/error line, and affected platform/kernel/toolchain.

2. Identify the upstream source of the breakage.
   Search upstream issues/PRs/commits and relevant API or dependency changes.
   Prefer an upstream patch when it applies cleanly.
   If a package needs distro-specific handling, make the condition structural when possible, such as probing headers or features instead of guessing by version.

3. Prepare a clean nixpkgs branch.
   Use a separate worktree from latest `upstream/master` when the current checkout is dirty or unrelated.
   Keep the fix minimal; avoid opportunistic version bumps, refactors, or unrelated metadata changes unless they are required to fix the build.

4. Validate the fix.
   Rebuild the failing attr or exact host/package path that exposed the failure.
   Also run the nearest standard nixpkgs build, for example `nix build .#<attr>`.
   Run `nix fmt <touched-file>` when formatting applies.
   After committing, run `./ci/nixpkgs-vet.sh master https://github.com/NixOS/nixpkgs.git`.

5. Search for duplicate PRs.
   Search open and recently closed `NixOS/nixpkgs` PRs using the package name, failing symbol, and likely title fragment.
   Stop and report a matching PR unless the user explicitly asks for a replacement or follow-up.

6. Publish a draft PR.
   Use a title that names the package and failure, for example `openrazer: fix build with newer hid_report_raw_event API`.
   Fetch the live nixpkgs PR template and fill it truthfully.
   Include upstream links and a concise explanation of why the patch is minimal and appropriate.

7. Run `caniko/nixpkgs-review-gha`.
   Dispatch the review after opening the draft PR.
   Update the PR body only after the review status is known.

## Failure modes

- Cannot reproduce and no usable log exists: stop and request the missing log or derivation path.
- Upstream source cannot be identified: report the uncertainty and keep any workaround clearly scoped and justified.
- The fix needs generated or vendored artifacts that are missing: stop and report the producer, regeneration command, and validation command.
- Review run fails: inspect logs, fix the branch, push, and rerun for the current head.
