---
name: multi-phase-plan
description: Generic shape specification for breaking a non-trivial refactor, migration, or cleanup into a set of standalone markdown phase documents, each self-contained enough that a fresh agent session can pick it up cold. Model-routing and CLI-execution concerns are delegated to flavour skills (`multi-phase-plan-codex`, `multi-phase-plan-claude`, `multi-phase-plan-mixed`). Parallel sub-layer model + CLI dispatch scripts live in `multi-phase-dispatch`. Trigger directly only when the caller is flavour-agnostic; otherwise invoke the matching flavour skill, which loads this one for the shape.
---

# Multi-phase plan document set (generic shape)

Use this skill when the user wants a non-trivial body of work decomposed into a set of standalone phase markdown files, each independently consumable by a fresh agent session. The skill enforces a uniform shape so phases are diffable, parallelisable where possible, and don't entangle context.

This skill is **agent-flavour agnostic**. It defines the phase-doc shape, the workflow, and the high-level sequencing rules. Three concerns are split out:

- **Model selection** — owned by routing skills (`gpt-plan-routing` for Codex / GPT-5.x, `claude-plan-routing` for Claude 4.x).
- **Parallel sub-layer layout + CLI dispatch scripts** — owned by **`multi-phase-dispatch`** (the DRY reference shared by all flavours).
- **Flavour-specific glue** — model picker, callout block format, CLI invocation contract — owned by one of the *flavour skills*:
  - **`multi-phase-plan-codex`** — Codex / GPT-5.x flavour.
  - **`multi-phase-plan-claude`** — Claude flavour (Opus 4.7 / Sonnet 4.6 / Haiku 4.5).
  - **`multi-phase-plan-mixed`** — cross-provider flavour that picks whichever provider/model wins on cost-per-quality per phase or sub-layer.

If a caller invokes this skill directly without picking a flavour, write phase docs with a placeholder `Recommended model: <pending — pick flavour skill>` callout and tell the user to re-run via one of the flavour skills to fill it in.

## When to use

**Decision gate: count the commits.** The predictor for "split into phase docs" is *how many semantic commits the work naturally produces on `trunk`*, not parallelism, not model tiers, not session count. One commit's worth of work → single planning doc (or no doc at all). N commits' worth → N phase docs.

Splitting buys:
- **Bisectable history.** `git bisect` lands on the exact phase that introduced a regression instead of "the refactor".
- **Restart granularity.** If phase 03 blows up mid-execution, `git reset --hard` to the phase-02 commit and redo. With a monolith doc the agent has to figure out where it was.
- **Pre-commit acceptance criteria.** Each phase doc commits to what "done" looks like *before* the diff is written. Forces verification before continuing.
- **Cold-start consumability.** A future agent (or future you) can pick up from phase N without re-reading 1..N-1.

Use this skill when:
- The work naturally produces multiple semantic commits (typically 3–8).
- The user says "break this into phases", "split into multiple files", "one markdown per phase", or names something as "a refactor" / "a migration" / "a cleanup".
- Each commit has its own coherent acceptance criteria and can be validated independently.
- The phases will be executed sequentially with verification between commits, OR concurrently across disjoint files (parallel execution is a bonus, not a requirement).

Don't use this for:
- **Work that lands as a single commit.** A workspace-wide rename, a one-file bug fix, a config tweak — splitting into phases for "rename in crate A", "rename in crate B" is bureaucracy. One planning doc with milestones (or no doc) instead.
- Plans that aren't going to produce trunk commits (just sketch in chat).
- Strategy / discussion / brainstorming — those want prose, not phase files.

### Misleading signals (don't use these as the predictor)

- **"All phases serialise"** — irrelevant. Serial phases still benefit from per-commit bisect + restart + acceptance gates.
- **"All phases use the same model tier"** — irrelevant. Per-phase routing is one motivator for splitting, not the primary one.
- **"It's all one agent session"** — irrelevant. Even one agent, one continuous session, multiple commits → split. The commits will outlive the session.
- **"It's a small change"** — size doesn't matter; commit-count does. A 50-line change across two semantic commits still splits; a 500-line change in one commit doesn't.

## Output shape

A directory under `docs/src/planning/<plan-name>/` containing:

- One file per phase: `NN-<slug>.md` where `NN` is two-digit ordinal (`01`, `02`, …) and `<slug>` is `kebab-case`.
- Each file is fully standalone — no "see the overview doc first" preamble, no shared context that lives only in chat.
- Optionally a top-level `README.md` or index entry in `docs/src/SUMMARY.md` so the mdBook (if used) surfaces them.

The `docs/src/planning/<plan-name>/` location is the convention; adjust per project layout. If the project doesn't use mdBook, drop the SUMMARY hookup.

The parallel sub-layer extension (nesting `sub-NN-<slug>.md` files inside a phase directory and emitting a sibling `run-NN-<slug>.sh` script) is owned by **`multi-phase-dispatch`** and consumed by every flavour. Each flavour skill plugs in its own CLI invocation contract — the layout is shared.

## Required structure per phase file

Every phase file must contain, in this order:

```markdown
# Phase <letter or number> — <Imperative title>

> **Recommended model: <flavour skill fills this in>**
>
> <One paragraph rationale produced by the flavour skill: complexity,
> role in plan, what would happen if a smaller model ran this.>

## Working tree

<Explicit cwd for the agent running this phase. If it's the same
repo as the parent project, say so. If it's an external repo
(steampipe, fragpipe, etc.), give the absolute path.>

## Goal

<One paragraph stating exactly what success looks like. Outcome-
focused, not action-focused.>

## Why this matters now

<Why-this-phase-exists context: the originating symptom (paste the
relevant log line / warning / failure mode), the cost of deferring,
and how it fits into the broader plan.>

## Out of scope

<Bullet list. Be explicit about what NOT to do — phase docs that
miss this section invite scope creep.>

## Plan

<Numbered steps. Each step is concrete enough to execute without
asking clarifying questions. Include commands where applicable.>

## Acceptance criteria

<Checkbox list of objectively verifiable conditions. "Tests pass" is
not enough; name the specific test target. "Build is clean" is not
enough; name the warning count expected.>

## Files likely touched

<Per-file list with paths. If multiple repos are involved, group by
repo with explicit working tree.>

## Pitfalls

<Failure modes the agent is likely to hit. For each: symptom, cause,
recovery. Pre-mortem the work so the agent isn't reactively
patching.>

## Reference

<Links: to the originating diagnosis (chat transcript, issue,
investigation doc), to related phases in this set, to upstream docs.>
```

For **high-risk** phases (anything routed to the flavour's top tier — `GPT 5.5 max`, Opus 4.7 at high thinking budget, etc.), add:

```markdown
## Risk profile

<Enumerated list of what can go wrong. Sets the mental model the
agent enters with.>

## Strategy

<For multi-step changes that span multiple commits: lay out the
commit ladder explicitly with revert costs.>

## Rollback drill

<Concrete commands to practice rollback before the destructive
commit. Include a time SLA.>

## Failure modes and recoveries

<F1, F2, …  Each with symptom / cause / recovery, written so the
agent has a runbook.>
```

## Workflow

1. **Take inventory.** List every concrete action the work entails. Group related actions into candidate phases. Aim for 3–8 phases — fewer means the breakdown isn't pulling weight; more means individual phases are probably too small.

2. **Identify dependencies.** Draw an explicit dependency table:

   ```
   Phase | Depends on  | Touches files       | Can parallel with
   A     | —           | crate/foo/          | B, C
   B     | —           | crate/bar/          | A, C
   C     | —           | vendor/baz/         | A, B
   D     | —           | repo/X/flake.nix    | A, B, C
   E     | D           | repo/X/flake.nix    | —
   ```

   Phases that touch disjoint files can run in parallel. Phases that touch the same file must serialise — flag this explicitly in each affected phase's "Working tree" or "Plan" section so the agent doesn't have to discover the conflict mid-execution.

3. **Route each phase through the flavour skill's routing skill.** For each phase, evaluate:
   - **Task complexity**: trivial / moderate / complex / frontier.
   - **Role in plan**: leaf / sub-agent / orchestrator / top-level planner.

   The flavour skill (`multi-phase-plan-codex` or `multi-phase-plan-claude`) names the routing skill to use and the exact format of the "Recommended model" callout block. Match the recommendation to the phase's complexity × role coordinates — don't inflate.

4. **Write each phase file** following the required structure above. Self-contained. Include the originating evidence (a log paste, a transcript excerpt, an issue reference) so the agent isn't guessing at why the phase exists.

5. **Wire into SUMMARY** if the project uses mdBook (`docs/src/SUMMARY.md`). One line per phase under a "Plan: <plan-name>" section.

6. **Provide a routing summary** in the chat reply alongside the file creation:

   | Phase | File | Model | Tier rationale | Blocking? |
   |---|---|---|---|---|

   Plus a parallelism matrix showing which phases can run concurrently and which serialise.

7. **Hand off any flavour-specific extensions** — the flavour skill may add run scripts, sub-layer directories, or CLI dispatch bundles after the base shape is written.

## Sequencing and parallelism guidance

Default each phase to "independent unless flagged". Explicit constraints belong in the phase doc, not in tribal knowledge.

| Constraint | How to communicate |
|---|---|
| File-level conflict (same file touched) | Note in both phases' "Plan" section: "<Phase X> must land first; pull/rebase before starting". |
| Logical dependency (later phase consumes earlier phase's output) | First sentence of the later phase's "Working tree" section names the prerequisite phase. |
| Repo-level conflict (both phases push to same repo's main branch) | Recommend sequential execution AND have the later phase note "pull steampipe/main before starting — see Phase D". |
| Verification gating (later phase needs earlier phase's smoke run to be green) | In the later phase's "Acceptance criteria" preamble, list the prerequisite phase's green run as a precondition. |

## What goes in the chat reply

After writing the files, the chat reply should include:

1. The directory location (`docs/src/planning/<plan-name>/`) with a count of files written.
2. The routing summary table (phase × model × blocking-status).
3. The parallelism matrix or note "all phases are independent" / "phases X and Y must serialise".
4. Any setup the user needs to run (e.g., `mdbook build`, `git add docs/src/SUMMARY.md`).
5. A concrete next-step suggestion: "ready to start with phase A" or "phase A is the only blocker — others can fan out".
6. Any flavour-specific dispatch instructions (the flavour skill adds these).
7. When yee-haw execution is appropriate, add: "Run `/yeehaw run` to execute this plan set in yeehaw."

Don't recap the contents of each phase file in chat. The files are the artifact; the chat reply is the dispatch.

## Anti-patterns to avoid

- **"Overview" or "index" file that the per-phase files depend on.** Defeats standalone-ness. The phase files must each be readable cold.
- **Cross-references between phase files for actual content.** Cross-references for *context* are fine ("Phase D must land first — see [04-…](./04-…)"). Cross-references that hide a step ("see Phase A for the build command") force the agent to read both files. Inline the step.
- **Conditional phases ("only do this if X").** If a phase's existence is conditional, write the decision criterion as its own initial step inside the phase, not as a wrapping "do we need this?" guard.
- **Generic acceptance criteria.** "Tests pass" / "builds cleanly" / "no regressions" are not acceptance criteria. Name specific test targets, warning counts, log-line presence/absence.
- **Routing every phase to the top tier.** Both routing skills explicitly warn against this: it multiplies cost with diminishing returns. Use low/medium tiers aggressively for mechanical phases; reserve the top tier for genuinely frontier-complex work.
- **Pre-mortem section missing on high-risk phases.** If you've routed a phase to the top tier, you owe the agent a failure-modes-and-recoveries section. Without it, the agent has to discover the failure modes the hard way.
- **Splitting one-commit work into phases.** If steps 1–5 of the plan are all going to land as a single commit (because they only make sense together — e.g. a rename across files, or a struct migration that breaks the build until all sites are updated), don't split. One planning doc with a numbered milestone list. Splitting buys nothing because there's no bisect target, no restart point, no per-step acceptance gate to enforce.

## Reference

- Parallel sub-layer model + CLI dispatch scripts (DRY): `multi-phase-dispatch`.
- Flavour skill (Codex / GPT-5.x): `multi-phase-plan-codex` — pins `gpt-plan-routing` and the Codex CLI invocation contract.
- Flavour skill (Claude): `multi-phase-plan-claude` — pins `claude-plan-routing` and the Claude CLI invocation contract.
- Flavour skill (mixed): `multi-phase-plan-mixed` — picks per-step across both providers for cost-per-quality efficiency; dispatch script switches CLI per sub-layer.
- mdBook conventions for project docs: `docs/src/SUMMARY.md`.
