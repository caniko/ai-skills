---
name: ci-debugging
description: Debug Forgejo CI failures — inspect runner state, read logs, diagnose common failure patterns. Use when a Forgejo Actions run fails, hangs, or never gets picked up and the user wants to find out why.
---

# CI Debugging Skill

Debug Forgejo CI failures — inspect runner state, read logs, diagnose common failure patterns.

## Quick CI Check

```bash
# List recent runs
fj actions -r <owner>/<repo> tasks

# View run info (on Codeberg: run-level summary only)
fj actions -r <owner>/<repo> jobs <run-id>

# View logs (requires forgejo instance with jobs/logs API)
fj actions -r <owner>/<repo> logs <run-id>

# With specific job / attempt
fj actions -r <owner>/<repo> logs <run-id> --job-id <id> --attempt <n>
```

## Runner Diagnostics (runner)

```bash
# Runner daemon logs — shows container creation, step execution, errors
sudo journalctl -u forgejo-runner-nixTrusted.service --since "10 minutes ago" --no-pager
sudo journalctl -u forgejo-runner-codeberg.service --since "10 minutes ago" --no-pager

# Runner work directories
sudo ls -la /var/lib/forgejo-runner/nixTrusted/
sudo ls -la /var/lib/forgejo-runner/codeberg/

# CI containers (created per job, cleaned up after)
sudo podman ps -a | grep -i forgejo

# Check forgejo-runner-act binary (required for Node.js actions)
sudo podman run --rm localhost/canix-nix-runner:local which forgejo-runner-act
sudo podman run --rm localhost/canix-nix-runner:local forgejo-runner-act --version

# Check container can reach Codeberg
sudo podman run --rm localhost/canix-nix-runner:local curl -sI https://codeberg.org | head -5

# Check Nix daemon socket access
sudo podman run --rm -e NIX_REMOTE=daemon -v /nix/var/nix/daemon-socket/socket:/nix/var/nix/daemon-socket/socket localhost/canix-nix-runner:local nix store ping
```

## Debug Workflow Pattern

When CI fails in <10s, the issue is infrastructure (container, runtime, network). Create a multi-job debug workflow to isolate which layer breaks:

```yaml
name: debug-ci
'on':
  push:
    branches: ["debug-ci"]
  workflow_dispatch:

jobs:
  shell-basics:
    runs-on: nix-runner
    steps:
      - run: echo "step 1: shell works"
      - run: id

  nix-access:
    runs-on: nix-runner
    steps:
      - run: nix --version
      - run: nix eval nixpkgs#hello.name

  checkout-node:
    runs-on: nix-runner
    steps:
      - uses: https://code.forgejo.org/actions/checkout@v4

  workspace-node:
    runs-on: nix-runner
    steps:
      - uses: https://code.forgejo.org/actions/checkout@v4
      - run: ls -la
```

Push to the `debug-ci` branch, then watch `fj actions tasks` to see which job succeeds/fails and how long each takes.

## Failure Timing Heuristics

| Time | Likely cause |
|------|-------------|
| 0-10s | Infrastructure failure (container, forgejo-runner-act, network, credentials) |
| 10-60s | Action setup failure (checkout, dependency resolution) |
| 60s+ | Step execution failure (build failure, test failure, nix eval error) |

## Common Failures

### forgejo-runner-act not found
**Symptom**: Jobs with `uses:` actions fail in <5s. Shell-only jobs succeed.
**Fix**: Add `forgejo-runner-act` binary to the container image (`canix-runner` or `canix-nix-runner`).

### Nix daemon socket not accessible
**Symptom**: `nix` commands fail. `nix --version` might work if cached but `nix eval` fails.
**Fix**: Verify `NIX_REMOTE=daemon` env var and `-v /nix/var/nix/daemon-socket/socket:...` mount in runner config.

### Network blocked
**Symptom**: `actions/checkout@v4` or `curl https://codeberg.org` fails from container.
**Fix**: Check podman `--network bridge` config and DNS settings in runner config.

### Credential not found
**Symptom**: Step referencing secrets fails with "not found" or "access denied".
**Fix**: Check `LoadCredential` paths in systemd unit. Credentials go to `/run/credentials/<unit-name>/`.

### Workspace permission denied
**Symptom**: Checkout action fails with permission error on workspace directory.
**Fix**: Ensure `DynamicUser` directory `/var/lib/forgejo-runner/<name>/` has correct ownership.

## Forgejo Actions Anatomy

```
Workflow YAML
    → forgejo-runner daemon parses workflow
    → creates podman container from configured image
    → mounts workspace, bind mounts, env vars
    → for each step:
        - shell step: runs directly in container
        - uses: step: delegates to forgejo-runner-act
            → downloads action from code.forgejo.org
            → executes in container
    → streams logs back via API
    → cleans up container
```

## Relevant Files

- Runner configs: `/nix/store/...-config.yaml` (symlinked from `ConfigFile` in service unit)
- Container images: `localhost/canix-runner:local`, `localhost/canix-nix-runner:local`
- Image tarballs: `/nix/store/...-canix-runner.tar.gz`, `/nix/store/...-canix-nix-runner.tar.gz`
- Image load service: `forgejo-runner-image-load.service`
- Forgejo Actions action runtime: `forgejo-runner-act` (inside containers)
