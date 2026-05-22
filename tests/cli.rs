use std::fs;

use assert_cmd::Command;
use predicates::prelude::*;
use tempfile::tempdir;

fn write_skill(root: &std::path::Path, name: &str, body: &str) {
    let dir = root.join(name);
    fs::create_dir_all(&dir).unwrap();
    fs::write(dir.join("SKILL.md"), body).unwrap();
}

#[test]
fn reconcile_without_sync_only_writes_mirror() {
    let tmp = tempdir().unwrap();
    let home_agents = tmp.path().join("home/.agents/skills");
    let home_claude = tmp.path().join("home/.claude/skills");
    let home_codex = tmp.path().join("home/.codex/skills");
    write_skill(&home_agents, "alpha", "a");
    fs::create_dir_all(&home_claude).unwrap();
    fs::create_dir_all(&home_codex).unwrap();

    let config = tmp.path().join("skillctl.toml");
    fs::write(
        &config,
        format!(
            r#"
[global]
sources = [
  {{ label = "agents", path = "{}", priority = 3 }},
  {{ label = "claude", path = "{}", priority = 2 }},
  {{ label = "codex", path = "{}", priority = 1 }},
]
sync_paths = ["{}", "{}"]
stale_codex_skill_paths = ["{}"]
"#,
            home_agents.display(),
            home_claude.display(),
            home_codex.display(),
            home_agents.display(),
            home_claude.display(),
            home_codex.display()
        ),
    )
    .unwrap();

    Command::cargo_bin("skillctl")
        .unwrap()
        .args([
            "--config",
            config.to_str().unwrap(),
            "--mirror-root",
            tmp.path().to_str().unwrap(),
            "reconcile",
            "--target",
            "global",
        ])
        .assert()
        .success();

    assert!(tmp.path().join("global/alpha/SKILL.md").is_file());
    assert!(home_codex.exists());
}

#[test]
fn reconcile_sync_removes_stale_codex_skills() {
    let tmp = tempdir().unwrap();
    let home_agents = tmp.path().join("home/.agents/skills");
    let home_claude = tmp.path().join("home/.claude/skills");
    let home_codex = tmp.path().join("home/.codex/skills");
    write_skill(&home_codex, "alpha", "a");
    fs::create_dir_all(&home_agents).unwrap();
    fs::create_dir_all(&home_claude).unwrap();

    let config = tmp.path().join("skillctl.toml");
    fs::write(
        &config,
        format!(
            r#"
[global]
sources = [
  {{ label = "agents", path = "{}", priority = 3 }},
  {{ label = "claude", path = "{}", priority = 2 }},
  {{ label = "codex", path = "{}", priority = 1 }},
]
sync_paths = ["{}", "{}"]
stale_codex_skill_paths = ["{}"]
"#,
            home_agents.display(),
            home_claude.display(),
            home_codex.display(),
            home_agents.display(),
            home_claude.display(),
            home_codex.display()
        ),
    )
    .unwrap();

    Command::cargo_bin("skillctl")
        .unwrap()
        .args([
            "--config",
            config.to_str().unwrap(),
            "--mirror-root",
            tmp.path().to_str().unwrap(),
            "reconcile",
            "--target",
            "global",
            "--sync",
        ])
        .assert()
        .success();

    assert!(home_agents.join("alpha/SKILL.md").is_file());
    assert!(home_claude.join("alpha/SKILL.md").is_file());
    assert!(!home_codex.exists());
}

#[test]
fn dry_run_does_not_mutate() {
    let tmp = tempdir().unwrap();
    let mirror = tmp.path().join("global");
    write_skill(&mirror, "alpha", "a");
    let config = tmp.path().join("skillctl.toml");
    fs::write(
        &config,
        "[global]\nsources = []\nsync_paths = []\nstale_codex_skill_paths = []\n",
    )
    .unwrap();

    Command::cargo_bin("skillctl")
        .unwrap()
        .args([
            "--config",
            config.to_str().unwrap(),
            "--mirror-root",
            tmp.path().to_str().unwrap(),
            "delete",
            "global",
            "alpha",
            "--dry-run",
        ])
        .assert()
        .success()
        .stdout(predicate::str::contains("delete"));

    assert!(mirror.join("alpha/SKILL.md").is_file());
}
