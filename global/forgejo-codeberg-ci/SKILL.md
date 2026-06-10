---
name: forgejo-codeberg-ci
description: "Troubleshoot Codeberg/Forgejo CI using the `forgejo-cli` first. Use when investigating Codeberg Actions or Forgejo workflow runs, publish failures, stuck jobs, tag-triggered releases, missing crates.io publishes, or repository-side CI state on codeberg.org. Prefer `forgejo-cli` for repository targeting and context discovery before falling back to Forgejo Actions pages or API endpoints."
---

# Forgejo Codeberg CI

Use this skill for Codeberg-hosted CI troubleshooting.

## Core Rule

Use `forgejo-cli` first whenever the target is a Codeberg/Forgejo repository. Do not start with ad hoc HTML scraping or generic web search when `forgejo-cli` can establish the repo target or confirm local Codeberg context.

## Workflow

1. Confirm `forgejo-cli` is available:

```sh
command -v forgejo-cli
forgejo-cli --help
```

2. Target the repository with `forgejo-cli` before anything else:

```sh
forgejo-cli repo info
forgejo-cli --owner-repo OWNER/REPO repo info
```

If the current directory is not the target repo, always pass `--owner-repo OWNER/REPO`.

3. Confirm the local Codeberg context with `git remote -v` (cross-check against the `forgejo-cli repo info` target above).

4. Check whether the release or CI trigger actually reached Codeberg:

```sh
git ls-remote --heads origin
git ls-remote --tags origin
```

5. If `forgejo-cli` exposes the needed CI/action capability in the installed version, use it instead of scraping.

6. If the installed `forgejo-cli` does not expose Actions/CI subcommands, keep `forgejo-cli` as the source of repo targeting, then inspect Forgejo Actions state from the matching repository endpoints:

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
