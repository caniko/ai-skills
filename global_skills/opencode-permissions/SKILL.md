---
name: opencode-permissions
description: Add, triage, or diagnose opencode bash permission rules in canix (home/modules/ai/opencode/permissions.nix). Use when the user pastes an opencode "Permission required" prompt or a list of command patterns (e.g. "- git diff *", "- diffstat *"), asks why opencode prompted or denied a command despite the allow list, or wants a command allowed/asked/denied in opencode. Covers rule placement, safety triage, glob matching semantics, and post-edit verification.
---

# opencode-permissions

Permission rules are stored across several Nix files composed by `permissions_config.nix`:

- **`permissions.nix`** — Pure data file (simple attrset `{ bash = {...}; external_directory = {...} }`). This is what the CLI reads/writes. Handles standard system commands. Edit by hand or via `canix opencode permission add`.
- **`permissions_git.nix`** — Pure attrset of git subcommand patterns (without the `git ` prefix). Each pattern is auto-expanded to both `git <cmd>` and `git -C * <cmd>` by `expandGitRules`.
- **`cli_tools.nix`** — Pure attrset of project-specific CLI tools (`vkc`, `bekiper`, `simit`, `yh`, etc.). Same format as `permissions.nix`'s `bash` attrs. Merged directly into bash permissions.
- **`permissions_config.nix`** — Module that imports `permissions.nix`, `permissions_git.nix`, and `cli_tools.nix`, applies transforms (`withEnvPrefixes`, `expandGitRules`, host-aware external_directory merge), and outputs `programs.opencode.settings.permission`. Also **auto-generates hostname-based self-SSH deny rules** (`ssh <hostname> *`, `ssh l<hostname> *`, `ssh v<hostname> *`) from `osConfig.networking.hostName` to prevent SSH-ing into the current host.
- **`permission-helpers.nix`** — `gitPair`, `withEnvPrefixes`, and validation helpers, consumed by `permissions_config.nix`.

All rendered to `~/.config/opencode/opencode.json` by Home Manager. Never edit the JSON — it is a store symlink.

## Matching semantics (non-obvious; read before editing)

- Patterns are **globs only** (`*`, `?`). There is NO regex support: a `/^.../` key is dead weight and never matches anything.
- A compound command is split into sub-commands by tree-sitter (pipes, `&&`, `$(...)`, etc.). Each sub-command's **full source text** is matched against every rule, anchored start-to-end (`"cargo *"` → `^cargo( .*)?$`). A trailing ` *` also matches the bare command with no args.
- Resolution is **last matching rule in alphabetical key order** (Nix sorts JSON keys). `*` (0x2A) sorts before `-`, `/`, and letters, so general-before-specific ordering holds and the most specific match wins. Denies with the same prefix beat allows (`git reset --hard *` deny outsorts `git reset *` ask).
- The permission dialog lists remember-patterns for **all** sub-commands of the compound command — only the segment(s) that evaluated to `ask` actually triggered the prompt. Most pasted patterns therefore already have rules.
- Env-prefixed commands (`FOO=1 cargo test`) cannot match `"cargo *"`. The module's `withEnvPrefixes` helper auto-generates tiered twins (`*=*` allow / `*=**` ask / `*=***` deny) for every rule. **Never hand-write `*=*` rules** — add the base rule and the twin is generated.

## Workflow for a pasted pattern list

1. **Filter to what is missing.** For each pattern, check whether a rule already exists:
   ```sh
   grep -nF '"<pattern>"' home/modules/ai/opencode/permissions.nix
   grep -nF '"<pattern>"' home/modules/ai/opencode/permissions_git.nix
   grep -nF '"<pattern>"' home/modules/ai/opencode/cli_tools.nix
   ```
   For git subcommands, also check `permissions_git.nix` without the `git ` prefix. For project-specific CLIs, check `cli_tools.nix`. Existing patterns were just sibling segments — skip them and tell the user so.

2. **Triage the missing ones:**
   - Read-only or formatter (status, list, view, diff, `diffstat`, plumbing like `rev-parse`, `hash-object`) → `allow`.
   - Repo-local writes already weaker than an existing allow (e.g. `git rm` vs the standing `rm *` allow; `git add`; commit) → `allow`.
   - Recoverable-but-surprising (checkout, rebase, reset, restore, force push, `stash drop`) → `ask`.
   - Irreversible or system-level (`reset --hard`, `clean`, sudo, disk tools, service restarts) → `deny`.
   - **Bare file path as a command** (e.g. `cli/src/foo.rs *`) → do NOT add a rule. It is a malformed model command; `"*" = "ask"` catching it is correct. Tell the user to reject once; the model self-corrects.

3. **Add the rule**:
   - **Project-specific CLI tools** (like `vkc`, `bekiper`, `simit`, `yh`) → add to `cli_tools.nix`.
   - **Git subcommands** → add to `permissions_git.nix` (without `git ` prefix). `expandGitRules` generates both `git <cmd>` and `git -C * <cmd>`.
   - **System commands** → add to `permissions.nix`. Use the CLI or hand-edit:
     ```sh
     canix opencode permission add bash 'diffstat *' allow
     canix opencode permission add bash 'ssh *' ask
     canix opencode permission add tool webfetch deny
     ```
   - Sections are `bash`, `tool`, and `external-dir`; actions are `allow`, `ask`, `deny`.
   - The CLI is idempotent: same-action duplicates are skipped, and an existing rule with a different action is updated.
   - Flags only match in the written position: `"git branch -D *"` does not catch `git branch foo -D`. Add a `"<cmd> * --flag *"` variant when the flag is the dangerous part (see the push force rules).

4. **Verify** the rendered rules:

   ```sh
   nix eval .#nixosConfigurations.runner.config.home-manager.users.can.programs.opencode.settings.permission.bash --json \
     | jq -r 'to_entries[] | select(.key | test("<cmd>")) | "\(.key) = \(.value)"'
   ```

   Expect the base rule, the `git -C *` twin (for gitPair), and the `*=*` env twin, all with the intended action.

5. **Remind the user**: rules take effect only after `canix rebuild switch` AND restarting opencode sessions started before the switch — opencode caches the global config with an infinite TTL.

## Diagnosing "opencode ignored my rule"

opencode logs every evaluation. Find what a command actually matched:

```sh
grep -h "evaluated" ~/.local/share/opencode/log/*.log | grep -E '"action":"(ask|deny)"' | tail -30
```

Each line shows the sub-command (`pattern=...`) and the winning rule (`action={"pattern":...}`). `pattern":"*"` means no rule matched — usually an env prefix, a genuinely missing rule, or a session still running on a pre-switch config (check log timestamps against the last rebuild).

## Self-SSH denial

`permissions_config.nix` auto-generates `ssh <hostname> *`, `ssh l<hostname> *`, and `ssh v<hostname> *` deny rules from `osConfig.networking.hostName`. If you see `ssh <hostname> *` denied on the current host, that's intentional — it prevents SSH-ing into your own machine.

To verify the generated rules for a host:

```sh
nix eval .#nixosConfigurations.<hostname>.config.home-manager.users.can.programs.opencode.settings.permission.bash --json \
  | jq -r 'to_entries[] | select(.key | test("ssh (l|v)?<hostname>")) | "\(.key) = \(.value)"'
```

These rules are not in `permissions.nix` — they're generated at eval time in `permissions_config.nix`. Do not add them to the data files.
