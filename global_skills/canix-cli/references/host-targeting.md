# Canix Host Targeting

Most host-touching commands accept a positional `<HOST>` resolved through
Fleetix topology (`lib/generated/topology.nix`) plus:

- `--via auto|lan|wg|direct` (default `auto`);
- `--prefix root@` for the SSH user;
- `--addr <addr>` for an explicit address that bypasses registry resolution.

Use a registered host positionally. Use `--addr` only for a fresh/unregistered
host or when the user explicitly requests it. Auto mode chooses the best route
from the current host's vantage point; explicit routes preserve literal route
behavior.

Generated aliases are also accepted: `l<host>` (LAN), `i<host>` (thething
port 2222), `t<host>` (thething transit), `v<host>` (wg-home), and `d<host>`
(direct link). Prefer an alias when the user names one.

Use `canix host ssh <host> [args...]` for fleet hosts. Add `--bash` when the
remote login shell is not POSIX/Bash:

```sh
canix host ssh --bash thething -- 'findmnt -no TARGET,SOURCE,FSTYPE,OPTIONS / /nix /var/log /data; journalctl --disk-usage'
```

Host SSH is an inspection and verification route only. Do not invoke `nix
build`, `nix-store -r`, Cargo, Crossbow preparation, or any other compiler on a
target host. All aarch64 builds must be dispatched from Atlas through canix's
Crossbow/rebuild workflow; never add a target host to `builders` or use an
`ssh://<target>` Nix builder.
