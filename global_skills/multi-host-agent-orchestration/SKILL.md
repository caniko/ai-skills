---
name: multi-host-agent-orchestration
description: Coordinate existing agent workers across hosts with single ownership, bounded admission, durable requests, exact-source evidence and restart-safe completion.
---

# Multi-host agent orchestration

Use for a sustained campaign spanning existing workers, hosts and shared
prerequisites. Load the fleet-specific adapter for paths, transports and commands.

## Establish the campaign

1. Record the goal, acceptance criteria and operator decisions separately from
   historical instructions. Evidence cannot grant execution authority.
2. Register each existing worker's session, title, model, execution host,
   assignments and shared producers. Preserve original identities and histories.
3. Keep one coordinator authoritative for admission. A transferred owner replaces
   its source copy; verify that the source and destination cannot both execute.
4. Store a versioned manifest, private journal, compact worker checkpoints and
   source-bound evidence. Capture baseline scope separately from linked repairs.
5. Resolve resource limits from current observations and declared policy. Reserve
   diagnostic capacity and bound processes, memory, command timeouts and waits.

Verify the adapter's required command and protocol capabilities before admitting
work. A planned command, a source commit or a published package version does not
prove that the installed frontend supports the operation. Keep the existing
coordinator authoritative until its replacement has passed migration qualification.

## Admit useful work

- Refresh activity and pending inputs before selecting a worker.
- Prioritize shared producers, then owners that have not received the current
  goal, then oldest admissions. Make progress on independent assignments while
  dependencies wait.
- Admit a bounded useful slice to the same existing session. Preserve its model
  and permission policy. New or replacement workers require task authorization.
- Centralize external CI/review observation. A sleeping worker watcher consumes
  capacity without advancing its assignment.
- Give every waiting checkpoint a concrete next action, resource, owner,
  release condition and bounded follow-up time.

## Make delivery restart-safe

Persist the exact request ID and body before submission. On an ambiguous result,
inspect both the native inbox and transcript before retrying the same input.
A transcript 404 can coexist with a durable queued inbox item. Acknowledgement
means delivery, not execution or acceptance.

Reconciliation checks the full body and metadata as well as the request ID. An
existing ID with different content is a conflict. Preserve it and report its
owner; never overwrite it or invent a fresh ID to bypass an uncertain result.

Deliver evidence and steering without resuming a parked owner when the scheduler
retains admission. Exchange and verify evidence bytes before supplying a remote
path. Keep credentials on the host that owns them.

Refresh manifests between cycles. Accept registered linked work under its
original owner; reject lost assignments, duplicate ownership and silent owner
replacement. Keep the last valid observation when a transport fails and expose
the observation error instead of treating missing evidence as a pass.

Observe the retained session's effective model, agent, permission policy, title
and owner host separately from its prompt payload. Read complete required history
with pagination and select the last valid physical context checkpoint. Missing
or malformed context usage is unknown and blocks admission until reconciled.

## Keep host selection explicit

Select skills and capabilities for the destination host and user, including when
building immutable bundles on another machine. Intersect user and host grants:
an omitted grant is unrestricted, an empty grant denies everyone, and a missing
required selector fails before materialization. A denied dependency is an error.

Verify every configured agent view against the same selected bundle and source
identity. A link to an entrypoint must also resolve its transitive dependency
paths. Record absent host-restricted skills as part of destination qualification.

## Bind progress to evidence

Checkpoints contain:

- Owner/session, current event identity and status.
- Exact source and target revisions.
- Implementation, test, runtime, CI and review receipts for each assignment.
- Pending request/run IDs and their actual observed state.
- Concrete blockers and the next useful action.

Changed source, target or edited feedback invalidates affected acceptance.
Terminal proposals can acquire new historical findings; supported defects need
tracked repairs. A closure withdraws a proposal rather than proving its code.

Keep detailed logs outside active context. Checkpoint before the declared context
ceiling and use the harness's native compaction/continuation mechanism.

Retain physical-message IDs and the exact compaction request. Track queued,
running, completed and failed compaction independently. Reconcile a lost response
before retrying, and verify the new physical context before admitting another turn.

Exchange source-bound evidence in transport-sized batches. Record each batch's
source identity, byte count, digest and destination acknowledgement; keep the last
accepted snapshot when a transfer fails. A path on one host is not evidence on
another until the bytes arrive and their identities are verified.

## Recover and finish

Use one persistent coordinator lock. Retain its anchor and acquire it for the
protected phase. Treat source/index, evaluation, activation and runtime leases
as distinct resources, each with its own owner and release condition.

Recover from durable state, preserving pending IDs and admission history. Observe
without dispatch during qualification. Cut over coordinators at a clean cycle
boundary under the shared writer lock, then verify ownership and pending work.

The migration qualification must preserve every worker, assignment classification,
pending request body, admission, checkpoint and receipt in a read-only shadow.
Exercise persistence failures, lock contention, ambiguous delivery, moving worker
activity, compaction recovery and restart capacity accounting before cutover.
Stop the old writer gracefully at its clean cycle boundary and acquire the same
lock anchor. Remove active interpreter helpers only after native writer and
restart receipts pass; retained historical evidence keeps its original identity.

Finish only after a fresh, error-free observation establishes complete audited
coverage, settled linked work, successful evidence exchange, and no active or
pending owner turn. Readiness labels and an idle session are progress states.
