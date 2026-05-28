---
name: mvp2prod
description: Transform a local MVP Rust project into a publication-ready state and push it to a target git repository. Bootstraps licenses, metadata, README, CHANGELOG, and runs AI-powered quality passes.
argument-hint: <mvp-dir> --repo <url> [--branch <branch>] [--init-repo]
---

# MVP to Production — Publication Bootstrapping

You are transforming a local MVP (minimum viable product) Rust project into a publication-ready state and publishing it to a target git repository. This is a two-phase process: deterministic scripted bootstrapping followed by AI-powered content and quality passes.

---

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `<mvp-dir>` | yes | — | Path to the local MVP project directory |
| `--repo <url>` | yes | — | Target git repository URL (SSH or HTTPS) |
| `--branch <branch>` | no | `"trunk"` | Branch to publish to |
| `--init-repo` | no | `false` | Initialize target repo if it doesn't exist |

---

## Phase 0: Validation and Repo Setup

1. Validate that `<mvp-dir>` exists and contains a Rust project (`Cargo.toml`)
2. Test connectivity to target repo with `git ls-remote`
3. Either clone the existing repo or initialize a new one (if `--init-repo`)
4. Create work directory at `/tmp/yh-mvp2prod-{repo_name}`
5. Checkout or create the target branch
6. Clean the work directory (preserve `.git`) and copy MVP contents

---

## Phase 1: Scripted Bootstrapping (Deterministic)

Automated file creation and metadata setup — no AI involved:

1. **Licenses**: Create `LICENSE-MIT` and `LICENSE-APACHE` if missing (MIT OR Apache-2.0, crates.io standard)
2. **Cargo.toml license**: Set `license = "MIT OR Apache-2.0"` field
3. **Cargo.toml metadata**: Inject `repository`, `homepage`, `readme` fields (SSH URLs auto-converted to HTTPS)
4. **.gitignore**: Ensure `/target` entry exists
5. **CHANGELOG.md**: Create skeleton with `[Unreleased]` section
6. **Formatting**: Run `cargo fmt` (best-effort)
7. **Commit**: `feat: publish MVP to production`

---

## Phase 2: AI Agent Tasks (Daemon-Managed)

An auto-generated todo file runs through the standard daemon pipeline:

### Task 1: `bootstrap`
- Complete `Cargo.toml` metadata: `description`, `keywords`, `categories`, `authors`
- Write comprehensive `README.md` with installation, usage, and examples
- Fill `CHANGELOG.md` `[Unreleased]` section with actual features from the codebase
- Replace any placeholder URLs with the canonical repository URL

### Task 2: `housekeep` (depends on bootstrap)
- Gates: `cargo test`, `cargo clippy --all-targets -- -D warnings`
- Final validation: run tests, fix clippy warnings, verify licenses and metadata
- Remove TODO comments and dead code

### Fix rules (auto-executed after every task)
- `fmt` — cargo fmt with style commit
- `clippy-fix` — cargo clippy --fix, escalates to full clippy routine on warnings
- `check` — cargo check --all-targets

### Interleave
- `cleanup` session fires at end of pipeline

---

## Phase 3: Push

Push the completed branch to the remote:
```
git push -u origin <branch>
```

Uses interactive push to allow credential prompts if needed.

---

## Output

On success:
```
Published MVP to <repo_url> on branch '<branch>'.
Working copy: /tmp/yh-mvp2prod-{repo_name}
```

The working directory contains the fully bootstrapped project with all commits pushed to the target repository.

---

## Design Decisions

- **Dual license** (MIT OR Apache-2.0): crates.io community standard
- **SSH → HTTPS conversion**: crates.io requires HTTPS URLs for `repository`/`homepage`
- **Scripted then AI**: Phase 1 is deterministic and idempotent; Phase 2 uses AI for content that requires understanding the codebase
- **Symlink preservation**: MVP copy preserves symlinks (Unix-specific)
- **No Docker in Phase 1**: Pure host-side file operations; only Phase 2 uses container tasks

For simit-managed crates.io release readiness, see `../rust-crate-release-prep/SKILL.md`.
