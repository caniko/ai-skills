---
name: evidence-first-research
description: Produce evidence-backed research for consequential investigations, audits, pre-design work, and difficult implementation decisions, selecting a compact findings note, concise orientation brief, or durable citation-traceable dossier after discovery. Use when work needs current facts before action, existing plans or assumptions may be stale, or the user asks to investigate, research first, orient a complex situation, or prepare a research handoff.
---

# Evidence-First Research

Use this skill to establish what is true before consequential design, implementation, migration, audit, roadmap, or cleanup work. Research is an input to later planning and execution; it is not a plan, model-selection procedure, dispatcher, or implementation workflow.

## Workflow

### 1. Establish the research target

Identify the user’s goal and trigger, target repository or system, relevant external repositories, whether the work is new or continuing, and the decision or implementation outcome the research must inform.

### 2. Discover before asking

Inspect available source artifacts before requesting information:

- planning docs, roadmaps, TODOs, issues, and navigation;
- source layout, manifests, build/test configuration, CI, release files, schemas, and public APIs;
- recent relevant commits or diffs;
- logs, bug reports, transcripts, and external links supplied by the user.

Use `rg` / `rg --files` first. Prefer objective current evidence over planning prose. Record the commands and artifacts that support each material claim.

### 3. Audit existing plans when applicable

When plans, phase docs, roadmaps, migration checklists, or planning directories are in scope, load [`plan-progress-review`](../plan-progress-review/SKILL.md) and apply its claim extraction, source verification, and status classification. Carry forward only unfinished, still-relevant work and durable constraints. Do not copy stale sequencing or checked boxes without proof.

### 4. Stop on missing foundational inputs

Never fabricate, synthesize, or silently substitute missing required data. If a foundational artifact is missing, invalid, contradictory, or cannot be regenerated, stop and report:

- the missing artifact or source;
- why it is required;
- the upstream producer that must fix or regenerate it;
- the exact regeneration command or workflow;
- the validation command that proves it is fixed.

Use `blocked` when the evidence gap would change the future work breakdown.

### 5. Choose the smallest honest output

After discovery and plan audit, select one output mode. Do not force a dossier onto a small investigation.

Choose **findings note** when at least two of these signals apply:

- the canonical fix is one command, one configuration edit, or one short shell session;
- candidate next steps collapse to the real fix plus non-load-bearing polish;
- all work targets one repository, provider, and runtime with no migration sequencing, schema/API break, or cross-repository coordination;
- the conclusion is “working as designed”, “stale snapshot”, or “one rerun”;
- there are no durable acceptance criteria worth preserving.

Choose **orientation brief** when the user needs a concise, evidence-backed situational summary before implementation or a decision, and the complexity is primarily competing constraints, partial truths, risks, or paths—not a request for a durable research record.

Otherwise choose **research dossier**. If only one downshift signal applies, keep the dossier concise and do not pad it with optional work.

## Output modes

### Findings note

Write at the nearest established planning-doc location with suffix `-findings.md`:

```markdown
# <Topic> Findings

## Goal And Trigger
## Root Cause(s)
## Evidence
## Recommended Fix
## Optional Follow-Ups
## Open Decisions
```

Omit empty optional sections. Cite files and lines, command output, commits, logs, or explicit user-provided sources.

### Orientation brief

Use these headings exactly unless the user requests another format:

```markdown
# <Topic> Orientation Brief

## Northstar
## Current Reality
## Goal State
## Path Through Complexity
## Risks And Unknowns
## Guardrails
## Immediate Next Move
```

Keep it compact and implementation-aware. Separate facts from assumptions, tie each direction to the goal, name uncertainty, and make tradeoffs explicit enough for a later plan. This mode is not a substitute for evidence collection.

### Research dossier

Create one durable markdown dossier unless the user explicitly requests chat-only output. Prefer locations in this order:

1. `docs/src/planning/<slug>-research.md` when the repository has mdBook planning docs;
2. `docs/planning/<slug>-research.md` when that planning directory exists;
3. the nearest established docs/planning equivalent.

Use this shape:

```markdown
# <Topic> Research Dossier

## Goal And Trigger
## Current Reality
## Evidence Inventory
## Existing Plan Status
## Work That Should Survive
## Blockers And Missing Artifacts
## Risks And Constraints
## Candidate Next Steps
## Open Decisions For The User
```

Omit `Existing Plan Status` when no existing plans are in scope. Keep every evidence claim traceable to a file, command, log, issue, or explicit user-provided source.

## Output standard

State the selected output mode and path (when a file was written), key blockers, whether existing plans were audited, and the commands or checks run. If blocked before writing, report the missing-artifact details and do not produce speculative conclusions.

## Guardrails

- Do not treat old planning prose as source of truth.
- Do not invent next-step boundaries beyond current evidence.
- Do not hide evidence gaps as caveats when they change the conclusion or work breakdown.
- Do not create README, quick-reference, changelog, or process-note files inside this skill directory.
- Keep planning, provider/model routing, dispatch, and execution with the active harness.

## See also

- Domain-grounded research skills add their own required sources, commands, and validation gates.
- [`research-routing`](../research-routing/SKILL.md) provides recommendation-only routing when the correct specialist is unclear.
