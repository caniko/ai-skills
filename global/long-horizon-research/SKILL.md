---
name: long-horizon-research
description: Produce an evidence-backed research dossier for any non-trivial investigation such as audits, pre-design research, and fact-finding before consequential decisions. Use before any work that benefits from a durable, citation-traceable evidence file. Stays domain-agnostic; wrapper skills such as plan-research load this and add domain-specific obligations on top.
---

# Long-Horizon Research

Use this skill to gather and structure durable facts for a consequential investigation. The output is a research dossier, not an implementation plan or decision memo.

## When to use

- Before consequential design, audit, migration, roadmap, broad refactor, or multi-repo cleanup work.
- When the task is not yet researched enough to act on safely.
- When existing docs, plans, or assumptions may be stale and the user wants conclusions based on current evidence.
- When the user asks for "pre research", "research first", "longterm stuff", "investigate this first", or similar.

Do not use this for small single-session tasks or for verifying already executed work. If the work turns out to be small mid-flight, downshift per step 5 instead of forcing the dossier shape.

## Workflow

### 1. Establish the research target

Identify:

- User goal and trigger.
- Target repository, working tree, and any external repositories.
- Whether the work is new, continuing, consolidating existing plans, or auditing existing claims.
- The decision, design, implementation, or audit outcome the research is meant to inform.

### 2. Discover before asking

Inspect available source artifacts before asking questions:

- Planning docs, roadmap pages, TODOs, issue references, and mdBook navigation.
- Source tree layout, manifests, build/test config, CI workflows, release files, generated docs, schemas, and public APIs.
- Recent relevant commits or diffs when they clarify current state.
- Logs, bug reports, transcripts, or external issue links provided by the user.

Use `rg` / `rg --files` first. Prefer objective evidence over planning prose.

### 3. Audit existing plans when present

If existing planning docs are in scope, invoke `plan-progress-review` behavior:

- Extract objective claims and acceptance criteria.
- Verify claims against current source artifacts.
- Classify items as `done`, `partial`, `not-started`, `obsolete`, `blocked`, or `unknown`.
- Carry forward only unfinished, still-relevant work and durable constraints.

Do not copy stale sequencing, old routing, checked boxes without proof, or obsolete assumptions into the new dossier.

### 4. Stop on missing foundational inputs

Never fabricate, synthesize, or silently substitute missing required data. If a foundational input is missing, invalid, contradictory, or cannot be regenerated in the environment, stop and report:

- Missing artifact or source.
- Why it is required for the research.
- Upstream producer that must fix or regenerate it.
- Exact command or workflow to regenerate it.
- Validation command that proves it is fixed.

Use `blocked` for evidence gaps that would change the future work breakdown.

### 5. Right-size before committing to the dossier shape

After steps 1-4 you have enough evidence to judge size. Run this gate **before** writing the dossier. If two or more downshift signals apply, do **not** produce a long-horizon dossier. Write a compact findings note instead.

Downshift signals:

- The canonical fix is one command, one config edit, or one short shell session.
- Candidate next steps collapse to "do the real fix" plus optional polish - the optional items are not load-bearing for the user's stated goal.
- All work targets one repo, one provider, one runtime; no cross-repo coordination, no migration sequencing, no schema/API break.
- Conclusion is "working as designed" / "stale snapshot" / "one rerun" rather than "needs new code or design".
- The user's ask was a triage, audit, or investigation, not "plan this out for me".
- No durable acceptance criteria worth preserving for future work - a brief commit message would carry the same information.

When you downshift, write the report at the same docs location with suffix `-findings.md` instead of `-research.md`. Use this compact shape and stop:

```markdown
# <Topic> Findings

## Goal And Trigger
<What the user wanted and why this investigation exists.>

## Root Cause(s)
<Citations: file:line, command output, commit, log line.>

## Evidence
<Commands run + key artifacts inspected.>

## Recommended Fix
<The single command, edit, or decision that resolves it.>

## Optional Follow-Ups
<Clearly marked optional. Omit the section if there are none.>

## Open Decisions
<Only if a decision blocks the recommended fix.>
```

State explicitly in the response that the work does not need a full dossier and name which downshift signals fired. Skip step 6.

If only one signal fires, continue to step 6 but keep the recommended next steps honest - do not pad with optional work to justify the shape.

### 6. Write the research dossier

Create one durable markdown dossier unless the user explicitly asks for chat-only output.

Location preference:

1. `docs/src/planning/<slug>-research.md` when the repo has mdBook planning docs.
2. `docs/planning/<slug>-research.md` when that planning directory exists.
3. The nearest existing docs/planning equivalent; state the chosen path in the response.

Use this shape:

```markdown
# <Topic> Research Dossier

## Goal And Trigger
<What the user wants and why this research exists.>

## Current Reality
<Evidence-backed state of the repo/system now.>

## Evidence Inventory
<Files, commands, logs, issues, docs, commits, and what each proves.>

## Existing Plan Status
<Only when applicable; status table from plan-progress-review style audit.>

## Work That Should Survive
<Unfinished, still-relevant work and durable constraints.>

## Blockers And Missing Artifacts
<Blocked/unknown items with producer, regeneration command, and validation command.>

## Risks And Constraints
<Compatibility, sequencing, ownership, testing, CI, release, and migration risks.>

## Candidate Next Steps
<Likely next steps, dependencies, sequencing constraints, and parallelism hints.>

## Open Decisions For The User
<Only decisions that materially affect the future work.>
```

Omit `Existing Plan Status` only when there are no existing plans in scope. Keep every evidence claim traceable to a file, command, log, issue, or explicit user-provided source.

## Output standard

In the final response, state:

- Dossier path.
- Key blockers, if any.
- Whether existing plans were audited.
- Commands or checks run for research.

If blocked before writing the dossier, report the missing artifact details from step 4 and do not produce speculative conclusions.

## Anti-patterns

- Do not treat old planning prose as source of truth.
- Do not invent next-step boundaries beyond what current evidence supports.
- Do not pad a single-fix investigation with optional work to justify the long-horizon shape - downshift per step 5.
- Do not bury missing evidence as a caveat when it changes the conclusion or recommended next steps.
- Do not create extra README, quick reference, or process notes inside the skill directory.

## See also

- `plan-research` - planning-tuned wrapper, added separately.
- Domain-grounded research skills - load this base and add their own source and evidence obligations.
