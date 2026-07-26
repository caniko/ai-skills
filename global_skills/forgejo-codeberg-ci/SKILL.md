---
name: forgejo-codeberg-ci
description: "Troubleshoot Codeberg/Forgejo CI using `fj` first, with git/curl fallback. Use when investigating Forgejo Actions workflow runs on Codeberg, publish failures, stuck jobs, tag-triggered releases, missing crates.io publishes, or repository-side CI state on codeberg.org."
---

# Forgejo Codeberg CI

Use this skill for Codeberg-hosted CI troubleshooting.

## Core Rule

Use `fj` first whenever the target is a Codeberg/Forgejo repository. Do not start with generic web search when `fj`, git, or targeted Codeberg endpoints can establish the repo target or confirm local Codeberg context.

## Workflow

1. Confirm `fj` is available:

```sh
command -v fj
fj --help
```

2. Target the repository with `fj` before anything else:

```sh
fj repo view
fj repo view OWNER/REPO
```

If the current directory is not the target repo, always pass `OWNER/REPO` to
`fj repo view` and the repository option shown by `fj actions --help`.

3. Confirm the local Codeberg context with `git remote -v` (cross-check against the `fj repo view` target above).

4. Check whether the release or CI trigger actually reached Codeberg:

```sh
git ls-remote --heads origin
git ls-remote --tags origin
```

5. Use `fj actions` for CI task operations when possible:

```sh
fj actions -r OWNER/REPO tasks
fj actions -r OWNER/REPO dispatch WORKFLOW_FILE BRANCH_OR_TAG
```

Check the installed `fj actions --help` before using subcommands. If it does
not expose run/job/log detail, use the matching Codeberg Actions pages/API
endpoints below; do not invent `fj actions jobs` or `fj actions logs` syntax.

6. If `fj` does not expose the needed run/job detail, keep `fj` as the source of repo targeting, then inspect Forgejo Actions state from the matching repository endpoints:

```sh
curl -fsSL "https://codeberg.org/OWNER/REPO/actions"
curl -fsSL "https://codeberg.org/OWNER/REPO/actions?workflow=WORKFLOW_FILE"
curl -fsSL "https://codeberg.org/OWNER/REPO/actions/runs/RUN_INDEX"
curl -fsSL "https://codeberg.org/api/v1/repos/OWNER/REPO/tags"
```

7. Prefer run-specific inspection over broad polling. Extract:
- workflow file
- run index
- run status
- current job status
- current step status
- run duration
- tag or branch ref

8. For publish troubleshooting, verify both sides:
- remote CI state on Codeberg
- external publish state on crates.io or the target registry

Example:

```sh
nix develop -c bash -lc 'cargo search CRATE_NAME --limit 5'
curl -fsSL "https://crates.io/api/v1/crates/CRATE_NAME"
```

9. Report the blocker precisely:
- remote trigger missing
- workflow still running
- specific step failed
- remote secret/config issue
- registry propagation delay

Do not guess at CI failure causes when the run is still active.

## Heuristics

- If the Actions list shows a `running` publish workflow, wait on that specific run before declaring failure.
- If the target tag exists remotely but crates.io still returns `404`, the publish path is not complete yet.
- If an unrelated workflow fails, do not attribute that failure to the publish workflow without checking the exact run.
- If the run page exposes structured state in HTML attributes, use that run-specific state instead of parsing the whole page heuristically.

## Report Shape

When closing a Codeberg CI troubleshooting pass, report:

- repository and workflow inspected
- exact run id/index
- current or final run status
- current or failing step
- whether the remote tag/commit exists
- whether the downstream registry reflects the release
- the next action, if any

## Runner Failure Triage

When a run fails or never starts, distinguish repository workflow failures from
the self-hosted runner before changing project code.

List the run and job state first:

```sh
fj actions --help
fj actions -r OWNER/REPO tasks
```

Use the run-specific web/API endpoints from step 6 for jobs and logs when the
installed CLI lacks those operations.

For the runner runner, inspect the matching daemon and image state:

```sh
sudo journalctl -u forgejo-runner-nixTrusted.service --since "10 minutes ago" --no-pager
sudo journalctl -u forgejo-runner-codeberg.service --since "10 minutes ago" --no-pager
sudo podman ps -a | grep -i forgejo
sudo podman images | grep -E 'canix-runner|canix-nix-runner'
```

Failure timing is a heuristic, not proof: failures in the first 10 seconds
usually indicate container/runtime/network infrastructure; 10–60 seconds
usually indicates action setup; later failures usually occur in the workflow
step itself. Confirm the failing step from the run log before classifying it.

Common runner checks:

- JS/composite-action failures: verify `forgejo-runner-act` exists in the
  runner image and that the container can reach Codeberg.
- Nix failures: verify `NIX_REMOTE=daemon` and the host Nix daemon socket
  mount on `nix-runner`.
- Credential failures: inspect the service's systemd credential paths without
  printing secret contents.
- Workspace permission failures: inspect the runner work directory ownership
  and the container workspace mount.

Load [runner](.skillnet/deps/runner/SKILL.md) for canonical labels, images,
mounts, cache behavior, and runner registration facts. Do not infer a fix from
timing alone.
