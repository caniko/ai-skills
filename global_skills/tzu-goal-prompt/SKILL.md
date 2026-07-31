---
name: tzu-goal-prompt
description: Create a grounded goal prompt from tzu metadata and optional harness output. Use to seed another planning or implementation run without fabricating missing project context.
---

# Tzu Goal Prompt

Use this skill to turn existing harness evidence into a prompt that a future agent can act on. The goal is to preserve important claims from `tzu` and other harnesses while making their provenance explicit.

## Workflow

1. Locate the project root and `tzu` state.
   - Default SQLite path: `.tzu/state.sqlite` from the current directory.
   - Use `--sqlite <path>` for a non-default database.
   - Use `--state-json <path>` when the caller supplies exported `ProjectState` JSON instead of SQLite.
2. Collect optional external harness output files.
   - Pass each file with `--harness-output <path>`.
   - Do not execute external harness commands from this skill. If output is needed, ask the user or upstream workflow to produce a file first.
3. Generate the prompt with `scripts/tzu_goal_prompt.py`.
   - It always writes the prompt to stdout.
   - Add `--output <path>` to also write a Markdown prompt file.
4. Hand the generated prompt to the next agent or planner as a starting prompt.

## Commands

From a project root with local `tzu` state:

```sh
python3 ~/canix/canix/projects/repos/owned/ai-skills/global_skills/tzu-goal-prompt/scripts/tzu_goal_prompt.py
```

If `python3` is absent, enter the project's documented Python/Nix environment
first; do not substitute an untracked interpreter or rewrite the script.

With explicit state and external harness files:

```sh
python3 ~/canix/canix/projects/repos/owned/ai-skills/global_skills/tzu-goal-prompt/scripts/tzu_goal_prompt.py \
  --state-json /path/to/project-state.json \
  --harness-output /path/to/other-harness.md \
  --output /tmp/tzu-goal-prompt.md
```

Run the script's built-in checks:

```sh
python3 ~/canix/canix/projects/repos/owned/ai-skills/global_skills/tzu-goal-prompt/scripts/tzu_goal_prompt.py --self-test
```

## Output Rules

The generated prompt should include:

- User-visible goal and planner goal when the harness metadata shows a distinct planning goal.
- Harness problem spec claims: domain, project root, constraints, evidence, and acceptance criteria.
- Selected candidate and retained frontier summaries.
- Validation obligations and blockers with producer, regeneration command, and validation command.
- Coding context claims from persisted context snapshots when present.
- External harness-output file content labeled by source path.
- A final instruction that all included harness claims must be verified before consequential changes.

## Blocker Rules

Never fabricate, synthesize, or silently substitute missing required data.

If no readable `tzu` state exists and no explicit state JSON is supplied, stop and report:

- Missing artifact/source.
- Why it is required.
- Upstream producer.
- Exact command or workflow to regenerate it.
- Validation command that proves it is fixed.

If an external harness output file is missing or empty, stop with the same blocker shape. If `tzu` state exists but harness metadata is absent, the generated prompt may include available project state, but it must clearly label harness claims unavailable and include the regeneration command.

## Anti-Patterns

- Running arbitrary external harness commands inside the helper script.
- Treating harness output as verified truth without source labels.
- Dropping obligations, blockers, or validation commands because they are inconvenient.
- Rewriting the generated prompt to sound more certain than the underlying evidence.
