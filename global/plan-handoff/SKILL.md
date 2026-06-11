---
name: plan-handoff
description: Shared reference skill defining the Planner Handoff schema that upstream producers (long-horizon-research wrappers, consolidate-plan-sets, plan-progress-review) emit and the downstream planner skill (multi-phase-plan) consumes. Not user-invokable on its own; loaded by other skills.
---

# Plan handoff (shared Planner Handoff schema reference)

## Purpose

This skill defines the minimal `## Planner Handoff` contract between upstream dossier producers and the downstream multi-phase planner consumer. This shared reference skill owns one cross-skill contract while producer and consumer skills own their local workflows. Not user-invokable on its own.

## Schema (required fields)

Every `## Planner Handoff` section must include exactly these required fields, using H3 subheadings with the names shown here:

- **Dossier path** — string; absolute or repo-relative path to the dossier file the handoff sits in.
- **Current-state summary** — paragraph; the planner's starting picture.
- **Routing constraints** — the carter routing constraints the plan should honor, with rationale: `none` (route across all enabled providers), a provider restriction (`--provider claude|codex|opencode`), and/or `--budget` when cost is the binding constraint.
- **Work that should become phases** — bulleted list; one bullet per candidate phase slice.
- **Known blockers** — bulleted list; producer-asserted blockers the planner must preserve, not plan around.
- **Acceptance evidence to preserve** — bulleted list; verifiable claims the produced phase set must protect.

## Schema (optional fields)

Producers may include these fields when the evidence supports them. Consumers must tolerate their absence.

- **Candidate phase boundaries** — fuller dependency table when the producer has enough evidence.
- **Risks and constraints** — narrative section covering material compatibility, sequencing, ownership, testing, CI, release, migration, or policy constraints.
- **Open decisions for the user** — material user decisions surfaced by the producer.

## Section format

Use a literal H2 heading named `## Planner Handoff`, followed by H3 subheadings for every required field. Optional fields, when present, also use H3 subheadings. Keep the content plain Markdown: paragraphs and bullets only.

Minimal template:

```markdown
## Planner Handoff

### Dossier path

<absolute or repo-relative path to this dossier>

### Current-state summary

<one paragraph summarizing the planner's starting picture>

### Routing constraints

<`none`, or carter flags such as `--provider claude` / `--budget`, with reasoning>

### Work that should become phases

- <candidate phase slice>
- <candidate phase slice>

### Known blockers

- <blocker the planner must preserve>

### Acceptance evidence to preserve

- <verifiable claim or evidence requirement the phase set must protect>
```

Optional fields, if emitted, appear after the required fields:

```markdown
### Candidate phase boundaries

<dependency table or structured bullets when evidence supports them>

### Risks and constraints

<narrative constraints>

### Open decisions for the user

- <material decision>
```

## Consumer parse rules

Downstream planner skills must parse `## Planner Handoff` by H3 subheading name. If any required field is missing, empty, filled only with placeholder text, or structurally wrong for its field type, the planner must stop and ask for the missing required content. It must not fabricate, infer, or silently substitute a required field from the user's free-text prompt.

Required fields have these precedence rules:

- `Dossier path`, `Current-state summary`, `Work that should become phases`, `Known blockers`, and `Acceptance evidence to preserve` override competing free-text prompt context unless the user explicitly says the dossier is stale or superseded.
- `Known blockers` are hard constraints. Preserve them as blockers in the generated phase set; do not turn them into implementation phases unless the user explicitly supplies the missing upstream artifact or decision.
- `Routing constraints` are advisory routing input for the carter calls. If the user's free-text request names different constraints, the consumer should state the mismatch and follow the user, continuing only when the mismatch is intentional.
- Optional fields are advisory. Consult them when present; ignore them when absent.

## Producer obligations

Every required field must contain literal, evidence-backed content. `TBD`, `TODO`, empty bullets, copied placeholders, or a heading with no body are contract violations. If a producer cannot fill a required field without fabricating data, it must stop and report the missing artifact or decision, why it is required, the upstream producer to fix it, the exact command or workflow to regenerate it, and the validation command that proves it is fixed.

Producers should omit optional fields when evidence is insufficient. Absence is valid for optional fields; padding is not.

## Anti-patterns

- Copying the template verbatim without replacing placeholders.
- Producing the section as prose without H3 subheadings.
- Renaming required fields or changing their heading level.
- Adding empty optional sections to imply evidence that is not present.
- Treating `Known blockers` as work to schedule around instead of constraints to preserve.
- Expanding the required schema beyond the six fields in this contract.

## Reference

- Current producer skills:
  - **`long-horizon-research`**.
  - **`consolidate-plan-sets`**.
  - **`plan-progress-review`**.
- Downstream consumer skill: **`multi-phase-plan`** (routing via the `carter` CLI).
