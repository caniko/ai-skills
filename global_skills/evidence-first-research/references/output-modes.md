# Research Output Modes

Select one mode only after discovery and any applicable plan audit. Keep the
smallest mode that preserves the evidence needed for the next decision.

## Findings note

Use the nearest established planning-doc location with suffix
`-findings.md` for a small, local investigation. Omit empty optional sections.

```markdown
# <Topic> Findings

## Goal And Trigger
## Root Cause(s)
## Evidence
## Recommended Fix
## Optional Follow-Ups
## Open Decisions
```

## Orientation brief

Use this chat- or file-sized form when the user needs a concise situational
summary before implementation or a decision. Separate facts from assumptions
and make tradeoffs explicit.

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

## Research dossier

Create one durable markdown dossier unless chat-only output is requested.
Prefer `docs/src/planning/<slug>-research.md`, then
`docs/planning/<slug>-research.md`, then the nearest established equivalent.
Omit `Existing Plan Status` when no existing plans are in scope.

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

Every evidence claim must point to a file, command, log, issue, or explicit
user-provided source. State the selected mode and path, key blockers, plan-audit
status, and checks run. If blocked before writing, report the missing-artifact
contract instead of speculative conclusions.
