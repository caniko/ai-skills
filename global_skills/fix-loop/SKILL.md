---
name: fix-loop
description: Evidence-first retries for failing commands, tests, builds, checks, migrations, and operational verification. Apply focused fixes until the exact gate and post-checks are green.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

# Fix Loop

Use this skill for a bounded, evidence-first retry loop. It applies to local
checks, repository tests, builds, generated artifacts, data jobs, service
verification, and other workflows with a repeatable success gate.

Before using this workflow, read and apply the shared integrity rules in
`.skillnet/deps/fix-loop-ref/SKILL.md`. A domain-specific skill may add stricter
commands, ownership rules, or post-checks; use those requirements in addition
to this workflow.

## Establish the repair contract

Resolve these five items before editing or retrying:

1. **Acceptance gate:** the exact command, API call, query, or observable
   completion marker that must become green.
2. **Diagnostics:** the first-pass command that exposes the complete failure,
   plus the narrow validation command for each likely owner.
3. **Green evidence:** the exit status, output marker, artifact, state change,
   and post-checks that prove success. A zero exit code alone is insufficient
   when the workflow defines stronger evidence.
4. **Authority boundary:** which source, configuration, generated producer,
   dependency, host, or operator owns each possible fix.
5. **Hard blockers:** missing credentials, operator-only actions, unavailable
   upstream publication, required input artifacts, or product decisions that
   Codex cannot safely supply.

Take the contract from the user request and authoritative local sources in
this order: a domain skill or runbook, repository instructions, CI/workflow
definitions, task/build scripts, package or flake definitions, then project
documentation. If sources disagree, report the conflict and follow the
highest-authority source rather than guessing.

If the user supplies an exact failing command, use it as the acceptance gate
unless an authoritative source explicitly defines a stronger gate. If no exact
gate can be established, stop before edits and report:

- the missing command or completion artifact;
- why it is required;
- the upstream producer or owner that must define or create it;
- the exact regeneration or recovery workflow, if one is documented; and
- the validation command that proves the input is usable.

Never replace a missing gate with a convenient approximation such as a cheap
unit test, a bypassed check, or a guessed health probe.

## Run the loop

### 1. Capture the baseline

- Read all applicable `AGENTS.md` and task-specific instructions.
- Inspect the worktree, branch, target, credentials boundary, and relevant
  generated/state directories. Preserve unrelated dirty changes.
- Run the exact acceptance gate once before editing. Capture its complete
  output and exit status; retain the log or artifact path when the project
  provides one.
- If the gate cannot start because a foundational input is missing or invalid,
  classify that blocker and report its producer and recovery command before
  attempting code changes.

For cross-repository work, invoke `$graphify` before discovery, planning, or
edits. Query an existing graph first; build or update the graph for the exact
repository set when it is missing or stale. Resolve canonical checkouts from
the workspace registry before mutating them.

### 2. Diagnose the earliest cause

Read the complete failure output, not only the final wrapper error. Identify
the earliest causal failure and classify it as one of:

- source or configuration;
- dependency or upstream state;
- generated artifact or stale producer output;
- tooling or environment;
- credential, operator input, or external authority; or
- nondeterministic behavior.

For transient failures, first confirm that an unchanged retry is safe and
meaningful. Record each attempt. Do not use repeated retries to conceal a
deterministic failure, and do not call a failure flaky without evidence.

### 3. Apply one focused repair

Fix one root cause at its highest suitable owner. Prefer, in order, the
authoritative upstream source, shared producer, project source/configuration,
then the consumer. Regenerate derived files through their documented producer
and validate the result; do not hand-edit generated output as the durable fix.

Do not stack speculative edits, broaden the change to unrelated cleanup, lower
assertions, disable checks, fabricate fixtures or secrets, or add bypass flags
to the final acceptance run. Do not perform deploys, destructive operations,
publication, or operator-held actions unless the request and local authority
explicitly include them.

### 4. Validate narrowly, then rerun the gate

- Run the narrowest focused validation for the changed owner.
- Re-run the exact acceptance gate with the same required environment and
  completion criteria.
- If it fails, treat that result as a fresh diagnostic cycle. Read the new
  complete output and select the next earliest causal root cause.
- Continue until the exact gate and every required post-check are green, or a
  documented stop condition is reached.

An unchanged retry is appropriate only for a demonstrated transient failure
when it is safe, in scope, and the gate itself is still the required check.
When repeated attempts expose nondeterminism, collect reproducible evidence
and fix the race, environment, or dependency at its owner rather than
declaring success from one lucky pass.

## Handle blockers without fabricating recovery

Stop and return control when a required authority or external state is absent,
or when every documented recovery path is exhausted. Name the exact blocker,
the evidence, the responsible producer/operator, the command or workflow that
must be run, and the validation that proves recovery.

Do not stop merely because a failure is pre-existing, inconvenient, slow, or
outside the first suspected subsystem. Reclassify it and continue whenever the
contract provides an in-scope recovery path. Stop after the same root cause has
resisted three independent fixes and the next action requires a user decision
about intended behavior.

## Report completion

Report all of the following in the handoff:

- exact acceptance gate, baseline result, final result, and post-checks;
- root cause and focused fix for each loop iteration;
- focused validation commands and their results;
- changed files or external state, with log/artifact paths;
- remaining blockers and required operator or upstream action; and
- whether a reusable lesson was found. If one belongs in this skill, a
  domain-specific skill, or the shared contract, update that owner in the same
  change set and identify it separately from product/code changes.

## Solution Placement

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
