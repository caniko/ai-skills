---
name: opencode-permissions
description: Add or diagnose opencode Bash permission rules in canix. Use for permission prompts, command-pattern lists, ignored rules, glob matching, or rendered verification.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# OpenCode Permissions

Permission data is split across `permissions.nix`, `permissions_git.nix`, and
`cli_tools.nix`; `permissions_config.nix` composes and transforms them into
Home Manager's opencode settings. Never edit rendered JSON. Read
[matching.md](references/matching.md) before editing or diagnosing a rule.

## Classify and place rules

1. Check all three data files for an existing pattern and skip rules already
   present.
2. Classify missing patterns:
   - read-only/formatting and repo-local writes: `allow`;
   - recoverable but surprising (`checkout`, `rebase`, `reset`, force push,
     `stash drop`): `ask`;
   - irreversible/system-level (`reset --hard`, `clean`, sudo, disks, service
     restarts): `deny`;
   - bare file paths: reject; do not add a rule.
3. Place the rule in the owning file:
   - Git subcommands, without the `git ` prefix: `permissions_git.nix`;
   - project CLIs (`simit`, `yh`, and similar): `cli_tools.nix`;
   - ordinary commands: `permissions.nix`.
4. Prefer the idempotent CLI for ordinary rules:

   ```sh
   canix opencode permission add bash 'diffstat *' allow
   canix opencode permission add bash 'ssh *' ask
   canix opencode permission add tool webfetch deny
   ```

   Flags match their written position; add a deliberate variant when the
   dangerous flag can appear later in the command.

## Verify

Evaluate the rendered Nix settings and inspect the base rule plus generated
Git/env twins:

```sh
nix eval .#nixosConfigurations.runner.config.home-manager.users.can.programs.opencode.settings.permission.bash --json \
  | jq -r 'to_entries[] | select(.key | test("<cmd>")) | "\(.key) = \(.value)"'
```

Rules take effect only after `canix rebuild switch` and restarting sessions
created before the switch; opencode caches global configuration indefinitely.

Self-SSH denies are generated from `osConfig.networking.hostName`; verify them
in the evaluated output and do not add them to the data files.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
