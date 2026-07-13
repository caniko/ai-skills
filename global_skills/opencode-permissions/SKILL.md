---
name: opencode-permissions
description: Add, triage, or diagnose opencode Bash permission rules in canix. Use for “Permission required” prompts, pasted command-pattern lists, ignored allow/ask/deny rules, glob matching questions, or rendered permission verification.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

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

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
