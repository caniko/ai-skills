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
target host. The sole exception is Canix's restricted Atlas-to-Nomad Nix store
transport, selected explicitly by `canix repo flake-check --offload nomad`;
operators and agents still do not SSH to Nomad to run build commands. All
aarch64 builds must be dispatched from Atlas through canix's Crossbow/rebuild
workflow; never add an aarch64 target to `builders` or use an ad hoc
`ssh://<target>` builder.

## Verify the far end before trusting it

- Run `hostname` first on every new SSH session. If it is not the host you
  targeted, stop: port 22 on a fleet IP is not necessarily that host's sshd
  (observed: `ssh thething` on port 22 landed on atlas presenting a foreign
  key, while the real sshd answers on port 1337 per the `l<host>`/`v<host>`
  aliases). Never run host-modifying commands on an unverified far end.
- A changed-host-key warning is a stop signal, not a prompt to append. Verify
  per port with `ssh-keyscan -t ed25519 -p <port> <addr>` and compare against
  that host's `hostPubkey` in `lib/generated/topology.nix`. Keys are
  per-port/service; a mismatch on one port does not mean the host was rekeyed.
- Do not leave scratch keys in `~/.ssh/known_hosts`. If you append a key to
  test a theory, remove those lines once the real route is established.
- Prefer the preconfigured aliases (`l<host>`, `v<host>`, …) over bare
  `ssh <host>`: they encode the operator-verified port, user, and key policy.
