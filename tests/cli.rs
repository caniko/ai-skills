use std::fs;

use assert_cmd::Command;
use predicates::prelude::*;
use tempfile::tempdir;

fn write_skill(root: &std::path::Path, name: &str, body: &str) {
    let dir = root.join(name);
    fs::create_dir_all(&dir).unwrap();
    fs::write(dir.join("SKILL.md"), body).unwrap();
}

fn write_minimal_config(path: &std::path::Path) {
    fs::write(
        path,
        "[global]\nsources = []\nsync_paths = []\nstale_codex_skill_paths = []\n",
    )
    .unwrap();
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

#[test]
fn project_target_selects_all_configured_projects_and_allows_empty_projects() {
    let tmp = tempdir().unwrap();
    let project_a = tmp.path().join("projects/project-a");
    let project_b = tmp.path().join("projects/project-b");
    write_skill(&project_a.join(".agents/skills"), "alpha", "a");
    fs::create_dir_all(&project_b).unwrap();

    let config = tmp.path().join("skillctl.toml");
    fs::write(
        &config,
        format!(
            r#"
[global]
sources = []
sync_paths = []
stale_codex_skill_paths = []

[[project_source_rules]]
label = "agents"
rel = ".agents/skills"
priority = 1

[[projects]]
name = "project-a"
path = "{}"

[[projects]]
name = "project-b"
path = "{}"
"#,
            project_a.display(),
            project_b.display()
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
            "project",
        ])
        .assert()
        .success();

    assert!(tmp
        .path()
        .join("projects/project-a/alpha/SKILL.md")
        .is_file());
    assert!(tmp
        .path()
        .join("projects/project-b/RECONCILIATION.md")
        .is_file());
}

#[test]
fn project_add_and_remove_update_config() {
    let tmp = tempdir().unwrap();
    let project_root = tmp.path().join("repos/new-project");
    fs::create_dir_all(&project_root).unwrap();

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
            "project",
            "add",
            "new-project",
            project_root.to_str().unwrap(),
        ])
        .assert()
        .success()
        .stdout(predicate::str::contains("added project new-project"));

    let updated = fs::read_to_string(&config).unwrap();
    assert!(updated.contains("[[projects]]"));
    assert!(updated.contains("name = \"new-project\""));
    assert!(updated.contains(&format!("path = \"{}\"", project_root.display())));

    Command::cargo_bin("skillctl")
        .unwrap()
        .args([
            "--config",
            config.to_str().unwrap(),
            "--mirror-root",
            tmp.path().to_str().unwrap(),
            "project",
            "remove",
            "new-project",
        ])
        .assert()
        .success()
        .stdout(predicate::str::contains("removed project new-project"));

    let updated = fs::read_to_string(&config).unwrap();
    assert!(!updated.contains("new-project"));
}

#[test]
fn toml_project_add_and_remove_update_config() {
    let tmp = tempdir().unwrap();
    let project_root = tmp.path().join("repos/toml-project");
    fs::create_dir_all(&project_root).unwrap();

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
            "toml",
            "project",
            "add",
            "toml-project",
            project_root.to_str().unwrap(),
        ])
        .assert()
        .success()
        .stdout(predicate::str::contains("added project toml-project"));

    let updated = fs::read_to_string(&config).unwrap();
    assert!(updated.contains("[[projects]]"));
    assert!(updated.contains("name = \"toml-project\""));

    Command::cargo_bin("skillctl")
        .unwrap()
        .args([
            "--config",
            config.to_str().unwrap(),
            "--mirror-root",
            tmp.path().to_str().unwrap(),
            "toml",
            "projects",
            "remove",
            "toml-project",
        ])
        .assert()
        .success()
        .stdout(predicate::str::contains("removed project toml-project"));

    let updated = fs::read_to_string(&config).unwrap();
    assert!(!updated.contains("toml-project"));
}

#[test]
fn project_add_dry_run_does_not_mutate_config() {
    let tmp = tempdir().unwrap();
    let config = tmp.path().join("skillctl.toml");
    let original = "[global]\nsources = []\nsync_paths = []\nstale_codex_skill_paths = []\n";
    fs::write(&config, original).unwrap();

    Command::cargo_bin("skillctl")
        .unwrap()
        .args([
            "--config",
            config.to_str().unwrap(),
            "--mirror-root",
            tmp.path().to_str().unwrap(),
            "project",
            "add",
            "future-project",
            "/tmp/future-project",
            "--allow-missing",
            "--dry-run",
        ])
        .assert()
        .success()
        .stdout(predicate::str::contains("add project future-project"));

    assert_eq!(fs::read_to_string(&config).unwrap(), original);
}

#[test]
fn catalog_generate_creates_docs_and_project_indexes() {
    let tmp = tempdir().unwrap();
    let config = tmp.path().join("skillctl.toml");
    write_minimal_config(&config);
    let catalog_config = tmp.path().join("skillctl.catalog.toml");
    fs::write(
        &catalog_config,
        r#"
[[rules]]
path_prefix = "global/"
scope = "global"
category = "agent-tools"
status = "active"

[[rules]]
path_prefix = "projects/"
scope = "project"
category = "domain-workflow"
status = "active"
"#,
    )
    .unwrap();
    write_skill(
        &tmp.path().join("global"),
        "alpha",
        "---\nname: alpha\ndescription: Alpha skill\n---\n",
    );
    write_skill(
        &tmp.path().join("projects/demo"),
        "beta",
        "---\nname: beta\ndescription: Beta skill\n---\n",
    );

    Command::cargo_bin("skillctl")
        .unwrap()
        .args([
            "--config",
            config.to_str().unwrap(),
            "--catalog-config",
            catalog_config.to_str().unwrap(),
            "--mirror-root",
            tmp.path().to_str().unwrap(),
            "catalog",
            "generate",
        ])
        .assert()
        .success();

    assert!(tmp.path().join("CATALOG.md").is_file());
    assert!(tmp.path().join("ROUTING.md").is_file());
    assert!(tmp.path().join("SKILL_CONFLICTS.md").is_file());
    assert!(tmp.path().join("projects/demo/INDEX.md").is_file());
}

#[test]
fn catalog_lint_rejects_invalid_metadata() {
    let tmp = tempdir().unwrap();
    let config = tmp.path().join("skillctl.toml");
    write_minimal_config(&config);
    let catalog_config = tmp.path().join("skillctl.catalog.toml");
    fs::write(
        &catalog_config,
        r#"
[[rules]]
path_prefix = "global/"
scope = "global"
category = "wrong"
status = "active"
related_skills = ["missing-skill"]
"#,
    )
    .unwrap();
    write_skill(
        &tmp.path().join("global"),
        "alpha",
        "---\nname: alpha\ndescription: Alpha skill\n---\n",
    );

    Command::cargo_bin("skillctl")
        .unwrap()
        .args([
            "--config",
            config.to_str().unwrap(),
            "--catalog-config",
            catalog_config.to_str().unwrap(),
            "--mirror-root",
            tmp.path().to_str().unwrap(),
            "catalog",
            "lint",
        ])
        .assert()
        .failure()
        .stderr(predicate::str::contains("unknown category"))
        .stderr(predicate::str::contains("related skill"));
}

#[test]
fn catalog_show_and_search_use_effective_metadata() {
    let tmp = tempdir().unwrap();
    let config = tmp.path().join("skillctl.toml");
    write_minimal_config(&config);
    let catalog_config = tmp.path().join("skillctl.catalog.toml");
    fs::write(
        &catalog_config,
        r#"
[[rules]]
path_prefix = "global/"
scope = "global"
category = "ci-release"
status = "active"
tags = ["forgejo"]
"#,
    )
    .unwrap();
    write_skill(
        &tmp.path().join("global"),
        "forgejo-ci",
        "---\nname: forgejo-ci\ndescription: Forgejo CI skill\n---\n",
    );

    Command::cargo_bin("skillctl")
        .unwrap()
        .args([
            "--config",
            config.to_str().unwrap(),
            "--catalog-config",
            catalog_config.to_str().unwrap(),
            "--mirror-root",
            tmp.path().to_str().unwrap(),
            "catalog",
            "show",
            "global/forgejo-ci",
        ])
        .assert()
        .success()
        .stdout(predicate::str::contains("category: ci-release"));

    Command::cargo_bin("skillctl")
        .unwrap()
        .args([
            "--config",
            config.to_str().unwrap(),
            "--catalog-config",
            catalog_config.to_str().unwrap(),
            "--mirror-root",
            tmp.path().to_str().unwrap(),
            "catalog",
            "search",
            "forgejo",
        ])
        .assert()
        .success()
        .stdout(predicate::str::contains("global/forgejo-ci"));
}

#[test]
fn grouped_mirror_and_skill_commands_match_legacy_commands() {
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
            "mirror",
            "list",
            "--target",
            "global",
        ])
        .assert()
        .success()
        .stdout(predicate::str::contains("alpha"));

    Command::cargo_bin("skillctl")
        .unwrap()
        .args([
            "--config",
            config.to_str().unwrap(),
            "--mirror-root",
            tmp.path().to_str().unwrap(),
            "skill",
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
