---
name: northstar
description: Create a concise northstar summary for complicated situations before or during implementation planning, especially when the work has many constraints, risks, partial truths, or competing paths.
---

# Northstar

## Purpose

Use this skill to orient complicated work before implementation or while recovering clarity midstream. The output is not a full implementation plan; it is a guiding summary that keeps the goal, facts, uncertainty, and next move visible.

## Workflow

1. Discover the relevant facts before summarizing. Inspect available project state, docs, logs, plans, or prior work when they are available.
2. Separate known facts from assumptions. Do not present guesses as established truth.
3. Preserve the important complexity without producing a wall of text. Prefer compact, high-signal bullets.
4. Tie recommendations back to the goal. Every direction should explain how it helps traverse the situation.
5. Avoid false certainty. Name unresolved risks, missing evidence, and boundaries of what current proof can establish.

## Output Shape

Use these headings exactly unless the user asks for a different format:

- `Northstar`: One sentence stating the guiding objective.
- `Current Reality`: The facts, constraints, and active project state that matter most.
- `Goal State`: What success looks like.
- `Path Through Complexity`: The ordered strategy for moving forward.
- `Risks And Unknowns`: Unresolved facts, blockers, assumptions, or evidence gaps.
- `Guardrails`: Rules that prevent bad shortcuts or misleading conclusions.
- `Immediate Next Move`: The next concrete action.

## Style

- Be concise, direct, and implementation-aware.
- Use factual language over motivational language.
- Mention files, commands, or systems only when they materially clarify the situation.
- Do not invent evidence, silently skip missing inputs, or overclaim what tests/builds prove.
- If the summary will guide later implementation, make the tradeoffs explicit enough that a follow-up plan can build from it.
