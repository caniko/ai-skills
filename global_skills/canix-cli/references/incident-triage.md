# Canix Incident Triage

For a public site down on the fleet (proven on `bekiper.candee.baby`,
2026-09-15). Diagnose from the dependent outward; recover from the
dependency inward.

## Locate each hop in topology before probing it

- Resolve the serving chain from `lib/topology/Services.pkl` (endpoint:
  target host, port, `bind`, `remoteVia`) and `lib/generated/topology.nix`
  (ingress groups, VIP, priorities). Ingress Caddy lives on the public
  ingress holders, not necessarily on the host running the backend.
- Name resolution differs per host: atlas carries `/etc/hosts` overrides
  (e.g. `id.tartanoglu.com` → keepalived VIP to dodge Fritzbox hairpin),
  while public DNS points at the WAN IP. Always check `getent hosts <name>`
  on the host you are diagnosing from, or you will misattribute the 502.
- `bind = "lan"` backends are directly probeable from the LAN
  (`curl http://<lan-ip>:<port>/api/health`); `bind = "loopback"` backends
  are only reachable via their `-http-relay` port with the right `Host`
  header. A fast `000`/refused means nothing listens; a `502` means the
  proxy is up but its upstream is down; a relay timeout with the host
  pingable means the relay/Caddy itself is down.

## Crash-loop drill (`start-limit-hit`)

1. `journalctl -u <unit> -n` first. Repeated identical fatals across
   restarts (and across boots) rule out boot-order races.
2. If the fatal names an upstream (e.g. OIDC discovery 502), test that
   upstream from the same host through the same resolution path before
   touching the crashed service. Restarting the dependent cannot fix a
   dead dependency.
3. Recovery order is dependency order: IdP (`rauthy`) → provision
   (`rauthy-provision`, must exit 0 / `Result=success`) → dependents
   (`bekiper-registry`, …). Verify each hop (`discovery` 200 with the
   expected `issuer`, local `/api/health` 200) before starting the next.

## Rauthy HiQLite cache-WAL panic

Deterministic abort on every start — `hiqlite-wal.../reader.rs:111`,
`SendError` unwrap, right after the `logs_cache` integrity check — means
the cache WAL poisons replay; retries never clear it. The full procedure
lives in canix `docs/src/operations/rauthy-hiqlite.md`; the shape is:

1. Stop `rauthy-provision` and `rauthy` (provision retries otherwise
   restart Rauthy mid-recovery).
2. Back up `/var/lib/private/rauthy` preserving ownership/ACLs/xattrs
   (e.g. `tar --xattrs --acls --numeric-owner`), verify the archive.
3. **Move, never delete**, `data/logs_cache` + `data/state_machine_cache`
   into a timestamped `rescue-cache-*` sibling (precedent:
   `rescue-cache-20260723T0423Z`). Keep the backup and the quarantine.
4. Start `rauthy`, confirm listen + SMTP + discovery; start provision,
   confirm reconciliation; then start dependents.
5. Cost is known up front: all sessions invalidated (fleet-wide re-login),
   manual IP blacklists and failed-login counters lost.

## Report the adjacent damage

An IdP outage fails every OIDC dependent, not just the reported site.
Close an incident note with the still-failed units seen along the way
(e.g. `pink-raven.service`, `foundry-circle.service`) and any anomalies
that need a later look but must not widen the current diff.
