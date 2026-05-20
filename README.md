# caniko's AI Skills Mirror

Snapshot of all Claude Code and Codex/agents skills found on caniko's machine as of **2026-05-20**.

This is a point-in-time snapshot, not a live sync. Source paths are on the machine at `/home/can/` and `~/canix/Projects/`.

---

## Categories

### Global

| Category | Skills |
|---|---|
| `global/claude` | 20 user-defined + 5 system |
| `global/codex` | 10 user-defined + 5 system |
| `global/agents` | 5 |

### Per-project

| Project | Skills |
|---|---|
| `projects/regicide` | 98 (Claude + Codex + agents, game-dev project) |
| `projects/ai-yolo-nix` | 23 |
| `projects/SynDB` | 15 |
| `projects/SynDB-dep-machete-udeps` | 15 (worktree of SynDB) |
| `projects/syndb-morphometry-rollout` | 15 (.codex-worktree of SynDB) |
| `projects/codex` | 10 (Codex project's own skills) |
| `projects/canix` | 9 |
| `projects/rs-modde` | 7 |
| `projects/mempalace` | 7 (openclaw integration + plugin skills) |
| `projects/fragpipe-mcp` | 4 |
| `projects/goose` | 4 |
| `projects/plinth` | 1 |
| `projects/nix-crossbow` | 1 |
| `projects/rs_bouldy` | 1 |

---

## Layout

```
global/
  claude/          # ~/.claude/skills/
    .system/       # system-reserved skills
  codex/           # ~/.codex/skills/
    .system/
  agents/          # ~/.agents/skills/

projects/
  <project-name>/
    claude/        # .claude/skills/ in repo
    codex/         # .codex/skills/ in repo
    agents/        # .agents/skills/ in repo
    skills/        # skills/ at repo root (fragpipe-mcp)
    codex-plugin/  # .codex-plugin/skills/
    claude-plugin/ # .claude-plugin/skills/
```

---

## Notes on ambiguous files

- **AGENTS.md at repo roots** (e.g., `canix/AGENTS.md`, `SynDB/AGENTS.md`, `regicide/AGENTS.md`): These are project-level agent configuration files, not standalone skills. They were **not** included as skills.
- **`~/.codex/vendor_imports/`**: Contains 38 curated third-party skills. Excluded — these are upstream vendor imports, not caniko's own skills.
- **`~/.codex/.tmp/`**: Temporary plugin workspace. Excluded.
- **SynDB worktrees**: `SynDB-dep-machete-udeps` and `syndb-morphometry-rollout` carry the same skill set as SynDB proper (all three included for completeness).
- **`upstream/mempalace`**: Skills here belong to an upstream project that caniko contributes to; included because they live in caniko's local workspace and contain project-specific skills.
- The `canix-probe-triage` skill references the phrase "private key" in documentation context — not an actual secret credential.

---

Total unique skills (deduplicated by name across all locations): approximately 235 SKILL.md files across all categories.
