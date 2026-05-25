---
name: long-horizon-research
description: Prepare evidence-backed pre research before long-term, longterm, or multi-phase plan assembly. Use before `multi-phase-plan-codex`, `multi-phase-plan-claude`, or `multi-phase-plan-mixed` when the user asks for pre research, long-term planning, longterm planning, roadmap planning, a large refactor or migration plan, stale plan consolidation, or "research before we call the multi-phase skill". Produces a durable research dossier and planner handoff; it does not create phase files itself.
---

# Long-Horizon Research

Use this skill to gather and structure the facts that a later multi-phase planning skill needs. The output is a research dossier, not the executable phase plan.

## When to use

- Before a long-horizon plan, roadmap, migration, broad refactor, or multi-repo cleanup.
- Before `multi-phase-plan-codex`, `multi-phase-plan-claude`, or `multi-phase-plan-mixed` when the task is not yet researched enough to decompose safely.
- When existing planning docs may be stale and the user wants the future plan based on current evidence.
- When the user asks for "pre research", "research first", "longterm stuff", or similar before plan assembly.

Do not use this for small single-session tasks or for verifying an already executed phase set. If the work turns out to be single-phase mid-flight, downshift per step 5 instead of forcing the dossier shape.

## Workflow

### 1. Establish the planning target

Identify:

- User goal and trigger.
- Target repository, working tree, and any external repositories.
- Intended downstream planner. Default to `multi-phase-plan-codex` unless the user explicitly asks for Claude or mixed routing.
- Whether the work is new, continuing, or consolidating existing plans.

If the downstream provider matters and the user has not specified it, record the default in the dossier instead of blocking.

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

Do not copy stale phase numbering, old provider routing, checked boxes without proof, or obsolete assumptions into the new dossier.

### 4. Stop on missing foundational inputs

Never fabricate, synthesize, or silently substitute missing required data. If a foundational input is missing, invalid, contradictory, or cannot be regenerated in the environment, stop and report:

- Missing artifact or source.
- Why it is required for the research.
- Upstream producer that must fix or regenerate it.
- Exact command or workflow to regenerate it.
- Validation command that proves it is fixed.

Use `blocked` for evidence gaps that would change the future phase breakdown.

### 5. Right-size before committing to the long-horizon shape

After steps 1-4 you have enough evidence to judge size. Run this gate **before** writing the dossier. If two or more downshift signals apply, do **not** produce a long-horizon dossier and do **not** hand off to a multi-phase planner. Write a compact findings note instead.

Downshift signals:

- The canonical fix is one command, one config edit, or one short shell session.
- Candidate phases collapse to "do the real fix" plus optional polish — the optional items are not load-bearing for the user's stated goal.
- All work targets one repo, one provider, one runtime; no cross-repo coordination, no migration sequencing, no schema/API break.
- Conclusion is "working as designed" / "stale snapshot" / "one rerun" rather than "needs new code or design".
- The user's ask was a triage, audit, or investigation, not "plan this out for me".
- No durable acceptance criteria worth handing to a fresh session — a brief commit message would carry the same information.

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

State explicitly in the response that the work does not need multi-phase decomposition and name which downshift signals fired. Do not name a downstream planner. Skip steps 6-7.

If only one signal fires, continue to step 6 but keep the phase count honest — do not pad with optional phases to justify the shape.

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

## Work That Should Survive Into The Long-Term Plan
<Unfinished, still-relevant work and durable constraints.>

## Blockers And Missing Artifacts
<Blocked/unknown items with producer, regeneration command, and validation command.>

## Risks And Constraints
<Compatibility, sequencing, ownership, testing, CI, release, and migration risks.>

## Candidate Phase Boundaries
<Likely phase slices, dependencies, and parallelism hints without final routing.>

## Open Decisions For The User
<Only decisions that materially affect the future plan.>

## Planner Handoff
<Exact concise prompt/context to feed into the selected multi-phase-plan skill.>
```

Omit `Existing Plan Status` only when there are no existing plans in scope. Keep every evidence claim traceable to a file, command, log, issue, or explicit user-provided source.

### 7. Handoff to multi-phase planning

The dossier's `Planner Handoff` section must name:

- Selected downstream skill (`multi-phase-plan-codex`, `multi-phase-plan-claude`, or `multi-phase-plan-mixed`).
- Dossier path.
- Current-state summary.
- Work that should become phases.
- Known blockers that must remain blockers instead of being planned around.
- Acceptance evidence the future phase set should preserve.

Do not write phase files, route models, or create dispatch scripts in this skill. That belongs to the downstream multi-phase planning skill.

## Output standard

In the final response, state:

- Dossier path.
- Downstream planner selected or defaulted.
- Key blockers, if any.
- Whether existing plans were audited.
- Commands or checks run for research.

If blocked before writing the dossier, report the missing artifact details from step 4 and do not produce a speculative handoff.

## Anti-patterns

- Do not treat old planning prose as source of truth.
- Do not invent phase boundaries beyond what current evidence supports.
- Do not pad a single-fix investigation with optional phases to justify the long-horizon shape — downshift per step 5.
- Do not bury missing evidence as a caveat when it changes the future plan.
- Do not run the multi-phase planning skill from this skill unless the user explicitly asks for the next step after the dossier exists.
- Do not create extra README, quick reference, or process notes inside the skill directory.
