use camino::Utf8PathBuf;
use clap::{Parser, Subcommand};
use clap_complete::Shell;

#[derive(Debug, Parser)]
#[command(
    name = "skillctl",
    version,
    about = "Reconcile and manage AI skills",
    long_about = "Reconcile AI skill directories from live agent sources into a mirror, edit mirrored skills, and optionally sync the selected mirror state back to live .agents/skills and .claude/skills directories."
)]
pub(super) struct Cli {
    /// Path to the skillctl TOML configuration file.
    #[arg(long, default_value = "skillctl.toml", global = true)]
    pub(super) config: Utf8PathBuf,

    /// Root directory containing the global/ and projects/ mirror directories.
    #[arg(long, default_value = ".", global = true)]
    pub(super) mirror_root: Utf8PathBuf,

    /// Path to the skill catalog metadata configuration file.
    #[arg(long, default_value = "skillctl.catalog.toml", global = true)]
    pub(super) catalog_config: Utf8PathBuf,

    #[command(subcommand)]
    pub(super) command: Command,
}

#[derive(Debug, Subcommand)]
pub(super) enum Command {
    /// Reconcile, sync, and inspect mirror scopes.
    Mirror {
        #[command(subcommand)]
        command: MirrorCommand,
    },
    /// Edit mirrored skill directories.
    Skill {
        #[command(subcommand)]
        command: SkillCommand,
    },
    /// Edit skillctl TOML configuration.
    Toml {
        #[command(subcommand)]
        command: TomlCommand,
    },
    /// Generate, inspect, and validate skill catalog metadata.
    Catalog {
        #[command(subcommand)]
        command: CatalogCommand,
    },
    /// Read live sources and rebuild the selected mirror directories.
    Reconcile {
        /// Target to reconcile: all, global, or project.
        #[arg(long, default_value = "all")]
        target: String,
        /// After rebuilding the mirror, write it back to live .agents and .claude directories.
        #[arg(long)]
        sync: bool,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
    /// Write the current mirror state back to live .agents and .claude directories.
    Sync {
        /// Target to sync: all, global, or project.
        #[arg(long, default_value = "all")]
        target: String,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
    /// Delete a skill from one mirror scope.
    Delete {
        /// Mirror scope: global or a configured project name.
        scope: String,
        /// Skill directory name to delete.
        skill: String,
        /// Write the updated mirror scope back to live directories after editing.
        #[arg(long)]
        sync: bool,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
    /// Rename a skill inside one mirror scope.
    Rename {
        /// Mirror scope: global or a configured project name.
        scope: String,
        /// Existing skill directory name.
        old: String,
        /// New skill directory name.
        new: String,
        /// Replace the destination when it already exists.
        #[arg(long)]
        force: bool,
        /// Write the updated mirror scope back to live directories after editing.
        #[arg(long)]
        sync: bool,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
    /// Move or copy a skill between mirror scopes.
    Move {
        /// Source mirror scope: global or a configured project name.
        from_scope: String,
        /// Skill directory name in the source scope.
        skill: String,
        /// Destination mirror scope: global or a configured project name.
        to_scope: String,
        /// Destination skill name. Defaults to the source skill name.
        #[arg(long = "as")]
        as_name: Option<String>,
        /// Copy the skill instead of moving it.
        #[arg(long)]
        copy: bool,
        /// Replace the destination when it already exists.
        #[arg(long)]
        force: bool,
        /// Write the updated mirror scopes back to live directories after editing.
        #[arg(long)]
        sync: bool,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
    /// Move or copy a project skill into the global mirror scope.
    Globalize {
        /// Configured project name to move from.
        project: String,
        /// Skill directory name in the project mirror.
        skill: String,
        /// Copy the skill instead of moving it.
        #[arg(long)]
        copy: bool,
        /// Replace the global destination when it already exists.
        #[arg(long)]
        force: bool,
        /// Write the updated mirror scopes back to live directories after editing.
        #[arg(long)]
        sync: bool,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
    /// Move or copy a global skill into a project mirror scope.
    Deglobalize {
        /// Skill directory name in the global mirror.
        skill: String,
        /// Configured project name to move to.
        project: String,
        /// Copy the skill instead of moving it.
        #[arg(long)]
        copy: bool,
        /// Replace the project destination when it already exists.
        #[arg(long)]
        force: bool,
        /// Write the updated mirror scopes back to live directories after editing.
        #[arg(long)]
        sync: bool,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
    /// List mirrored skills for the selected target.
    List {
        /// Target to list: all, global, or project.
        #[arg(long, default_value = "all")]
        target: String,
    },
    /// Manage configured project roots.
    Project {
        #[command(subcommand)]
        command: ProjectCommand,
    },
    /// Print configured mirror scopes.
    Targets,
    /// Print configured live source directories for global or project targets.
    Sources {
        /// Source group to show: global or project.
        #[arg(long)]
        target: String,
    },
    /// Generate shell completion scripts.
    Completions {
        /// Shell to generate completions for.
        shell: Shell,
    },
}

#[derive(Debug, Subcommand)]
pub(super) enum MirrorCommand {
    /// Read live sources and rebuild the selected mirror directories.
    Reconcile {
        /// Target to reconcile: all, global, or project.
        #[arg(long, default_value = "all")]
        target: String,
        /// After rebuilding the mirror, write it back to live .agents and .claude directories.
        #[arg(long)]
        sync: bool,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
    /// Write the current mirror state back to live .agents and .claude directories.
    Sync {
        /// Target to sync: all, global, or project.
        #[arg(long, default_value = "all")]
        target: String,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
    /// List mirrored skills for the selected target.
    List {
        /// Target to list: all, global, or project.
        #[arg(long, default_value = "all")]
        target: String,
    },
    /// Print configured mirror scopes.
    Targets,
    /// Print configured live source directories for global or project targets.
    Sources {
        /// Source group to show: global or project.
        #[arg(long)]
        target: String,
    },
}

#[derive(Debug, Subcommand)]
pub(super) enum SkillCommand {
    /// Delete a skill from one mirror scope.
    Delete {
        /// Mirror scope: global or a configured project name.
        scope: String,
        /// Skill directory name to delete.
        skill: String,
        /// Write the updated mirror scope back to live directories after editing.
        #[arg(long)]
        sync: bool,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
    /// Rename a skill inside one mirror scope.
    Rename {
        /// Mirror scope: global or a configured project name.
        scope: String,
        /// Existing skill directory name.
        old: String,
        /// New skill directory name.
        new: String,
        /// Replace the destination when it already exists.
        #[arg(long)]
        force: bool,
        /// Write the updated mirror scope back to live directories after editing.
        #[arg(long)]
        sync: bool,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
    /// Move or copy a skill between mirror scopes.
    Move {
        /// Source mirror scope: global or a configured project name.
        from_scope: String,
        /// Skill directory name in the source scope.
        skill: String,
        /// Destination mirror scope: global or a configured project name.
        to_scope: String,
        /// Destination skill name. Defaults to the source skill name.
        #[arg(long = "as")]
        as_name: Option<String>,
        /// Copy the skill instead of moving it.
        #[arg(long)]
        copy: bool,
        /// Replace the destination when it already exists.
        #[arg(long)]
        force: bool,
        /// Write the updated mirror scopes back to live directories after editing.
        #[arg(long)]
        sync: bool,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
    /// Move or copy a project skill into the global mirror scope.
    Globalize {
        /// Configured project name to move from.
        project: String,
        /// Skill directory name in the project mirror.
        skill: String,
        /// Copy the skill instead of moving it.
        #[arg(long)]
        copy: bool,
        /// Replace the global destination when it already exists.
        #[arg(long)]
        force: bool,
        /// Write the updated mirror scopes back to live directories after editing.
        #[arg(long)]
        sync: bool,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
    /// Move or copy a global skill into a project mirror scope.
    Deglobalize {
        /// Skill directory name in the global mirror.
        skill: String,
        /// Configured project name to move to.
        project: String,
        /// Copy the skill instead of moving it.
        #[arg(long)]
        copy: bool,
        /// Replace the project destination when it already exists.
        #[arg(long)]
        force: bool,
        /// Write the updated mirror scopes back to live directories after editing.
        #[arg(long)]
        sync: bool,
        /// Print planned filesystem changes without mutating files.
        #[arg(long)]
        dry_run: bool,
    },
}

#[derive(Debug, Subcommand)]
pub(super) enum TomlCommand {
    /// Manage [[projects]] entries in skillctl.toml.
    #[command(alias = "projects")]
    Project {
        #[command(subcommand)]
        command: ProjectCommand,
    },
}

#[derive(Debug, Subcommand)]
pub(super) enum ProjectCommand {
    /// List configured projects and their root paths.
    List,
    /// Add a configured project root.
    Add {
        /// Project name used as the mirror scope.
        name: String,
        /// Project repository root path. Relative paths are expanded before writing.
        path: Utf8PathBuf,
        /// Allow adding a project path that does not exist yet.
        #[arg(long)]
        allow_missing: bool,
        /// Print the config change without mutating skillctl.toml.
        #[arg(long)]
        dry_run: bool,
    },
    /// Remove a configured project root.
    Remove {
        /// Project name to remove.
        name: String,
        /// Also delete projects/<name> from the mirror if it exists.
        #[arg(long)]
        prune_mirror: bool,
        /// Print the config change without mutating skillctl.toml.
        #[arg(long)]
        dry_run: bool,
    },
}

#[derive(Debug, Subcommand)]
pub(super) enum CatalogCommand {
    /// Rebuild CATALOG.md, ROUTING.md, SKILL_CONFLICTS.md, and project INDEX.md files.
    Generate,
    /// Validate effective catalog metadata and routing hygiene.
    Lint,
    /// Show catalog metadata for one skill name or qualified scope/name.
    Show {
        /// Skill name, or a qualified name such as global/rust-project-flake.
        skill: String,
    },
    /// Search skill names, descriptions, tags, categories, and projects.
    Search {
        /// Case-insensitive search query.
        query: String,
    },
}
