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

Deliver evidence and steering without resuming a parked owner when the scheduler
retains admission. Exchange and verify evidence bytes before supplying a remote
path. Keep credentials on the host that owns them.

Refresh manifests between cycles. Accept registered linked work under its
original owner; reject lost assignments, duplicate ownership and silent owner
replacement. Keep the last valid observation when a transport fails and expose
the observation error instead of treating missing evidence as a pass.

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

## Recover and finish

Use one persistent coordinator lock. Retain its anchor and acquire it for the
protected phase. Treat source/index, evaluation, activation and runtime leases
as distinct resources, each with its own owner and release condition.

Recover from durable state, preserving pending IDs and admission history. Observe
without dispatch during qualification. Cut over coordinators at a clean cycle
boundary under the shared writer lock, then verify ownership and pending work.

Finish only after a fresh, error-free observation establishes complete audited
coverage, settled linked work, successful evidence exchange, and no active or
pending owner turn. Readiness labels and an idle session are progress states.
