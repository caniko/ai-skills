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
canix fleet --help
canix host opencode --help
canix --output json workspace show <project>
canix host profile status atlas-adjacent nomad
```

When `fleet --help` exposes `campaign`, inspect `canix fleet campaign --help`.
The required campaign surface is `import`, `plan`, `status`, `run`, `deliver`,
`checkpoint` and `stop`. Missing commands or an unqualified orchestration library
are concrete producer/consumer release gates. Preserve the current scheduler and
its journal while completing that release chain.

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

Verify the effective session policy before admission. In an existing PR-review
campaign, preserve each registered `PR review` title, `openai/gpt-6.1-sol#xhigh`
model and automatic permissions.
Start native compaction at 180,000 input/cache tokens and keep physical context
below 300,000. Unknown usage requires reconciliation, never a zero-token fallback.

### Native observation and evidence-only delivery

```nu
canix host opencode request nomad GET /api/session/<session>
canix host opencode request nomad GET /api/session/<session>/inbox
canix host opencode request nomad POST /api/session/<session>/prompt --body request.json
```

Persist `request.json` privately before submission. Evidence-only input uses the
existing request ID, `resume: false`, `delivery: "steer"`, exact `text` and
`metadata`. The V2 prompt body has no model field. Reconcile the full inbox
payload and transcript after an ambiguous response; HTTP 404 does not prove that
the inbox rejected the input. Check native `data.status`, `data.host` and
`data.response` independently of Canix's transport success.

Credentials stay host-local. Route an authorized forge operation to its declared
credential host through Canix's typed transport. A cache reader authenticates its
cache, while a private source fetch needs its separate source credential.

```nu
canix host forge github nomad -- api user --jq .login
canix host forge github nomad --stdin-file query.json -- api graphql --input -
```

Use the verified repository and exact full head for a guarded merge. Required
checks, approvals, complete current review and native protection still apply.
Source integration stays with its original owner on scheduler admission; a
transferred Git bundle proves object availability only.

## Sync the host-selected skills

The generic entrypoint belongs in `global_skills/Skillnet.pkl` (schema 2). This
adapter belongs in `host_skills/Skillnet.pkl` (schema 3), with `hosts = List("atlas")`
and real dependency edges to the generic skill and both Canix references.

Consume qualified published Skillnet and ai-skills revisions through Canix's
targeted input updater. Verify `hostSelectionSupport` at the flake root or its
per-system `lib` entry before registering the host manifest. Home Manager sets
`programs.skillnet.host` to the destination hostname; immutable bundles receive
the same explicit host. A build on Atlas must still filter Nomad's bundle as Nomad.

Qualify Can/Dejana × Atlas/Nomad and all four configured agent views. The generic
skill must resolve everywhere; this adapter and its transitive dependencies must
resolve on Atlas and this adapter must be absent on Nomad. Verify source digests,
bundle identities, rendered selectors and the actual active views after rollout.
Retain the full-home owner's acceptance gate before managed activation or any
publication dependent on immutable Nomad hooks.

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
