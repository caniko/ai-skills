# OpenCode Permission Matching

Read this before diagnosing a rule. Patterns are globs (`*`, `?`), not regex.
Compound commands are split by tree-sitter and each sub-command's full source
is matched start-to-end. A trailing ` *` also matches the bare command.

Rules resolve by the last matching key in alphabetical order; general `*`
rules sort before specific prefixes, and a same-prefix deny beats allow. The
dialog may list every sub-command even when only one segment prompted.

`FOO=1 cargo test` does not match `cargo *` directly. `withEnvPrefixes` creates
the `*=*`, `*=**`, and `*=***` twins; never hand-write those generated rules.
Git rules are expanded to both `git <cmd>` and `git -C * <cmd>`.

Bare file paths are malformed model commands; do not add a rule for them.

To inspect a winning rule:

```sh
grep -h "evaluated" ~/.local/share/opencode/log/*.log \
  | grep -E '"action":"(ask|deny)"' | tail -30
```

`pattern:"*"` usually means an env prefix, missing rule, or stale session
configuration. `permissions_config.nix` also generates hostname-based self-SSH
denies; those rules do not belong in the data files.
