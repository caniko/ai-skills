# Fix Loop Reference

This is an internal shared reference, not a standalone user workflow. The
callable `fix-loop` skill or a domain-specific fix-loop skill loads it and
supplies the exact command that must become green.

## Required contract

Before starting, the invoking skill must define:

- the exact acceptance gate and the command used to rerun it;
- the first-pass diagnostics and focused validation commands;
- what counts as green, including any required post-checks;
- the source and authority boundaries for fixes;
- hard blockers that require an operator, credential, upstream publication, or
  product decision.

If that contract is missing, stop and repair the invoking skill before doing
work. Do not invent a substitute gate.

## Repair loop

1. Inspect the worktree and preserve unrelated dirty changes. Record the
   baseline gate result before editing.
2. Read the complete failure output and identify the earliest causal failure,
   not the final wrapper error.
3. Classify the failure as source/configuration, dependency/upstream,
   generated artifact, tooling/environment, credential/operator input, or
   nondeterministic behavior.
4. Apply one focused fix for one root cause at its highest suitable owner.
   Do not stack speculative edits or weaken the acceptance gate.
5. Run the narrowest relevant validation for the changed owner.
6. Rerun the exact acceptance gate. Any failure resets the loop to the first
   diagnostic step; a specialist handoff does not end the parent loop.
7. Continue until the invoking skill's full success evidence is present.

For cross-repository work, load the workspace ownership reference and invoke
`$graphify` before discovery or edits. Resolve a canonical checkout from the
workspace registry; never edit a read-only store path or guess a project path.

## Integrity rules

- Never replace a required test with a cheaper approximation.
- Never use bypass flags as the final acceptance run.
- Never fabricate secrets, generated files, hashes, package names, or missing
  upstream state.
- Keep fixes and generated artifacts scoped to the current root cause.
- Preserve user changes, credentials, and operator-held prompts.
- Treat a clean process exit as insufficient when the gate defines a stronger
  completion marker or post-activation verification.

## Failure and stop handling

For missing or invalid foundational input, stop and report the exact artifact,
why it is required, its upstream producer, the regeneration or recovery
command, and the validation command that proves recovery.

Do not stop merely because a failure is pre-existing, inconvenient, flaky, or
outside the first suspected subsystem. Reclassify it and continue when the
invoking skill provides an in-scope recovery path.

Stop and return control only when:

- the exact gate and all required post-checks are green;
- a required authority or external coordination is absent;
- every documented environment recovery path is exhausted; or
- the same root cause has resisted three independent fixes and the next step
  requires user judgment about intended behavior.

## Completion report

Report the exact gate result, post-checks, root-cause fixes, focused
validations, remaining blockers (if any), and log/artifact paths. State
explicitly when no reusable lesson was found. If a confirmed reusable lesson
belongs in the invoking skill or a shared reference, update that owner in the
same change set and mention it separately from product/code changes.
