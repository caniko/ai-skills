---
name: yeehaw
description: Execute, inspect, or resume harness-created phase plan directories through the yh MCP phases tools. Use when the user wants to run a phase plan in the current repository, asks for `/yeehaw run`, `/yeehaw show`, or `/yeehaw status`, or after the active harness writes a phase doc set under `docs/src/planning/PLAN-NAME/`.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# Yeehaw phase executor

Do not auto-invoke this from another skill. Suggest `/yeehaw run`; wait for the user to ask for execution.

## How to use

1. Resolve the plan directory. If the user did not pass one, use the most recent phase plan directory in the current repository, usually `docs/src/planning/<plan-name>/`.
2. Call `phases_show` with `{ "plan_dir": "<absolute or repo-relative path>" }`.
3. If `phases_show` returns an error, stop and tell the user the directory is not a valid phase doc set.
4. For `/yeehaw show`, summarize the returned `phases` and `dag_edges`.
5. For `/yeehaw status`, call `phases_status` and summarize `lock`, active signals, and checkpoints.
6. For `/yeehaw run`, call `phases_run` only after `phases_show` succeeds. Pass `resume: true` when continuing a prior run. Pass `strict: true` only if the user explicitly asks for strict failure semantics.
7. While `phases_run` is active, surface MCP progress messages as phases start, complete, pause, or fail.
8. When `phases_run` returns, interpret `status` and `exit_code` exactly as below.

## Exit-code handling

- `status: completed`, `exit_code: 0`: report the completed phase ids and the lock file path.
- `status: needs_human`, `exit_code: 2`: stop. Prompt the user with `active_checkpoint.question` and include `active_checkpoint.suggested_resolution` when present.
- `status: impossible`, `exit_code: 3`: stop. Surface the returned `message`, failed phase ids, and the lock file path.
- `status: expansion_pending`, `exit_code: 4`: tell the user an expansion proposal was staged. Offer to inspect `active_checkpoint.proposal_path` or re-run `/yeehaw run` to apply pending proposals.

## Anti-patterns

- Do not retry blindly on `needs_human`; always surface the checkpoint to the user.
- Do not run `phases_run` on a directory that `phases_show` has not accepted.
- Do not skip a human checkpoint by passing `strict: true` unless the user asked for strict mode.
- Do not claim progress streaming is authoritative; the final `phases_run` return value is the source of truth.
- Do not run two `phases_run` calls against the same plan directory at the same time.

## Test plan

Manual smoke steps:

1. Have the active harness write a small phase plan in a repository that has the yee-haw MCP server configured.
2. Run `/yeehaw show <plan-dir>` and confirm the phase DAG is listed.
3. Run `/yeehaw run <plan-dir>` and confirm phase progress appears and the final response includes `status`, `exit_code`, and `lock_file`.
4. Re-run `/yeehaw status <plan-dir>` and confirm it reflects the lock file written by the run.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
