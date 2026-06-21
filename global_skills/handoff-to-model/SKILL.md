---
name: handoff-to-model
description: Package survey/analysis results from a complex orchestrator (Nix Ultra, Rust Ultra, or any multi-concern survey) into a self-contained markdown handoff file for execution by a simpler/lighter model. Use when the user says "prepare for handoff", "hand off to a simpler model", "make this executable by [model name]", "export for another model", "create a handoff", or after running a survey/audit orchestrator and wants a different model to execute the plan.
---

# Handoff to Model

## Purpose

Package survey/analysis results into a self-contained markdown handoff file at `/tmp/opencode/<name>-handoff.md` that a simpler model can pick up and execute. This skill does NOT re-survey, re-score, or execute the plan itself — it synthesises existing results into an execution document.

## Input contract

Before producing output, the following must already exist:

- **Survey results** with scored concerns (weighted scores, thresholds, trigger/non-trigger verdicts)
- **Staged execution order** — concerns grouped into stages (Correctness, Design, Polish, Inputs/Gates or equivalent), sorted by score within each stage
- **Baseline info** — repo shape (flake/non-flake, hosts, key systems, file count), git status, formatter state
- **Target model name** — provided by the user or inferred from context (e.g. "deepseek-v4-flash")

If any of these are missing, ask the user before fabricating.

## Output template

Write `/tmp/opencode/<name>-handoff.md` using these exact H2 sections:

```markdown
# <Orchestrator Name> Handoff — <Repo Name> (<Date>)

Target model: **<target-model>**
Source: <source-info>

## Repo Shape
- Canonical path, type, file count, hosts, secrets system, key subsystems

## Pre-existing State
- git status, formatter status, any existing constraints to preserve

## Constraints and Guardrails
- NEVER fabricate secrets, hashes, lock data, generated files, or upstream sources
- Prefer repo conventions over generic taste
- Keep changes behavior-preserving unless redesign is explicitly requested
- List files/paths to skip (vendored, generated, external)

## Execution Order
### Stage 1: <Category>
1. **<concern-name>** (score: N). Top drivers: ...
2. ...
(Repeat per stage)

## Convergence
- Re-score after each full stage; re-run quantitative concerns with score >0 and qualitative concerns whose skill reported remaining work
- Cap at 3 iterations; report deferred work at the cap

## Final Gate
```bash
# exact copy-paste commands for formatter, eval, check, build
```

## Report Format
- Concerns run / skipped / deferred
- Convergence rounds completed
- Final scores (quantitative)
- Validation results
- Blockers and residual risks

## Key Commands Reference
```bash
# useful repo-specific commands
```
```

## Writing rules

- **Preserve constraints from the survey output verbatim.** Do not soften, drop, or reinterpret blocker conditions.
- **Keep guardrails in the handoff.** The simpler model may not infer them from context.
- **Use absolute paths** for the repo root. Do not use `~` or relative paths.
- **Gate commands must be exact copy-paste** — not prose descriptions. Every `$()` and flag must be included.
- **Flag files to skip** explicitly (vendored, generated, external code) in the Constraints section.
- **Target the file under 500 lines.** Omit detailed rationale, scoring methodology, and survey methodology — keep only what the executor needs.
- **Do not include** the survey dump, scoring formulas, or the full orchestrator routing table. The handoff is execution-only.

## Anti-patterns

- Omitting the formatter/gate commands and writing "run the usual checks" instead
- Including survey rationale that the executor does not need
- Writing prose when a copy-paste shell command is needed
- Recommending specific model capabilities (e.g. "you are good at X so...") — the executor model will differ
- Fabricating missing survey data to complete the template
- Using relative paths or `~` for the repo root

## Validation before reporting done

- [ ] Handoff file exists at `/tmp/opencode/<name>-handoff.md`
- [ ] All required H2 sections present (Repo Shape through Key Commands)
- [ ] Gate commands are exact copy-paste with no placeholders
- [ ] No fabricated data (secrets, hashes, lock data, scores not in the survey)
- [ ] Repo root path is absolute
- [ ] File is under 500 lines
- [ ] Files/paths to skip are explicitly listed in Constraints

## Reference

- Upstream producers: orchestrator skills (`nix-ultra`, `rust-ultra`, and any multi-concern survey skill that emits scored execution plans)
- Sibling skill: [plan-handoff](../plan-handoff/SKILL.md) — defines the dossier→planner schema for `multi-phase-plan`. This skill bridges orchestrator survey output → simpler execution model, a different handoff direction.
