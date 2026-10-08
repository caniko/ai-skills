---
name: atlas-nomad-orchestration
description: Coordinate Atlas and Nomad agent campaigns through native Canix commands, preserving existing workers, host-local credentials, admission and exact-source receipts. Atlas only.
---

# Atlas–Nomad orchestration

Load [multi-host-agent-orchestration](.skillnet/deps/multi-host-agent-orchestration/SKILL.md),
[canix-cli](.skillnet/deps/canix-cli/SKILL.md) and
[canix-structure-reference](.skillnet/deps/canix-structure-reference/SKILL.md).
This adapter runs on Atlas; Nomad executes its registered owner sessions locally.

## Discover the native surface

Read installed help before using a new command:

```nu
canix fleet campaign --help
canix host opencode --help
canix --output json workspace show <project>
canix host profile status atlas-adjacent nomad
```

Resolve roots and routes through Canix/Fleetix. The direct Ethernet route is
required for the Atlas→Nomad handoff policy; ordinary host operations retain
their documented route selection. Use the installed qualified CLI rather than
campaign-local Python/JavaScript coordinators.

## Transfer existing work

From a separate Atlas terminal as the session owner:

```nu
canix host opencode handoff <session> --to nomad --dry-run
canix host opencode handoff <session> --to nomad --no-resume
canix host opencode status <session>
```

Select explicit workspaces when the session's registered directory does not
identify its actual project checkouts. Inspect the reported physical roots and
conflicts. Preserve descendants, staged/worktree versions, untracked source and
foreign edits. The canonical Canix checkout remains the activation source.

Let the campaign scheduler admit the imported owner. Atlas histories remain
recovery evidence; their mirrors stay parked while Nomad owns execution. A
running background shell, persistent terminal or pending inbox input requires
the named job/input's documented disposition before handoff can complete.

## Operate the campaign

Import the existing manifest/journal rather than replacing workers. Preview
ownership, pending admissions and capacity with the campaign plan/status commands.
Run one native coordinator under its persistent campaign lock. Use evidence-only
delivery for decisions whose owners remain scheduler-controlled.

Keep models, titles and permission policies with registered sessions. Host
capacity is declared policy informed by current memory/process observations.
Follow dependencies to their source owner; deliver compact capability-specific
receipts instead of starting a second producer repair.

Credentials stay host-local. Route an authorized forge operation to its declared
credential host through Canix's typed transport. A cache reader authenticates its
cache, while a private source fetch needs its separate source credential.

## Preserve qualification and leases

- Use native tests in the project's approved environment and treefmt.
- Use Canix's bounded evaluation commands and retain captured source/derivation
  roots. Release evaluation capacity before Cargo, tests, transport or realization.
- Build actual production outputs through `canix cache binary build`. Publication
  and host activation have distinct receipts and operator decisions.
- Use the shared target activation lease for rebuild/profile/campaign mutations.
  Name the exact resource, owner and release condition on contention.
- Preserve configured identity, signing, contributor metadata and normal hooks.
- Qualify generated behavior in its producer, then consume the exact qualified
  artifact and verify the consumer. Fixtures, packaged clients and deployed
  runtime each require their own evidence.

A source-approved Home Manager change does not establish effective managed
activation. Verify the active generation and immutable hook path before releasing
publication that depends on them.

## Recovery and completion

Inspect existing inbox/request/run IDs after a lost response. Retry exact
persisted payloads; keep evidence exchange independent from owner resumption.
Adopt the existing coordinator journal and lock at a clean cycle boundary, then
verify both hosts' activity and the complete assignment set.

Apply the generic completion criterion, including historical audits, supported
linked repairs, remote evidence acceptance and active/pending owner turns. Retain
concrete external release actions when acceptance is still pending.
