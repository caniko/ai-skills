mod commands;
mod config;
mod fs_ops;
mod model;
mod reconcile;

use anyhow::Result;
use camino::Utf8PathBuf;
use clap::{CommandFactory, Parser, Subcommand};
use clap_complete::{generate, Shell};

use crate::commands::Context;

#[derive(Debug, Parser)]
#[command(name = "skillctl", version, about = "Reconcile and manage AI skills")]
struct Cli {
    #[arg(long, default_value = "skillctl.toml", global = true)]
    config: Utf8PathBuf,

    #[arg(long, default_value = ".", global = true)]
    mirror_root: Utf8PathBuf,

    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    Reconcile {
        #[arg(long, default_value = "all")]
        target: String,
        #[arg(long)]
        sync: bool,
        #[arg(long)]
        dry_run: bool,
    },
    Sync {
        #[arg(long, default_value = "all")]
        target: String,
        #[arg(long)]
        dry_run: bool,
    },
    Delete {
        scope: String,
        skill: String,
        #[arg(long)]
        sync: bool,
        #[arg(long)]
        dry_run: bool,
    },
    Rename {
        scope: String,
        old: String,
        new: String,
        #[arg(long)]
        force: bool,
        #[arg(long)]
        sync: bool,
        #[arg(long)]
        dry_run: bool,
    },
    Move {
        from_scope: String,
        skill: String,
        to_scope: String,
        #[arg(long = "as")]
        as_name: Option<String>,
        #[arg(long)]
        copy: bool,
        #[arg(long)]
        force: bool,
        #[arg(long)]
        sync: bool,
        #[arg(long)]
        dry_run: bool,
    },
    Globalize {
        project: String,
        skill: String,
        #[arg(long)]
        copy: bool,
        #[arg(long)]
        force: bool,
        #[arg(long)]
        sync: bool,
        #[arg(long)]
        dry_run: bool,
    },
    Deglobalize {
        skill: String,
        project: String,
        #[arg(long)]
        copy: bool,
        #[arg(long)]
        force: bool,
        #[arg(long)]
        sync: bool,
        #[arg(long)]
        dry_run: bool,
    },
    List {
        #[arg(long, default_value = "all")]
        target: String,
    },
    Targets,
    Sources {
        #[arg(long)]
        target: String,
    },
    Completions {
        shell: Shell,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    if let Command::Completions { shell } = cli.command {
        let mut command = Cli::command();
        let name = command.get_name().to_string();
        generate(shell, &mut command, name, &mut std::io::stdout());
        return Ok(());
    }

    let ctx = Context::load(&cli.config, &cli.mirror_root)?;

    match cli.command {
        Command::Reconcile {
            target,
            sync,
            dry_run,
        } => commands::reconcile(&ctx, &target, sync, dry_run),
        Command::Sync { target, dry_run } => commands::sync(&ctx, &target, dry_run),
        Command::Delete {
            scope,
            skill,
            sync,
            dry_run,
        } => commands::delete(&ctx, &scope, &skill, sync, dry_run),
        Command::Rename {
            scope,
            old,
            new,
            force,
            sync,
            dry_run,
        } => commands::rename(&ctx, &scope, &old, &new, force, sync, dry_run),
        Command::Move {
            from_scope,
            skill,
            to_scope,
            as_name,
            copy,
            force,
            sync,
            dry_run,
        } => commands::move_skill(
            &ctx,
            &from_scope,
            &skill,
            &to_scope,
            as_name.as_deref(),
            copy,
            force,
            sync,
            dry_run,
        ),
        Command::Globalize {
            project,
            skill,
            copy,
            force,
            sync,
            dry_run,
        } => commands::move_skill(
            &ctx, &project, &skill, "global", None, copy, force, sync, dry_run,
        ),
        Command::Deglobalize {
            skill,
            project,
            copy,
            force,
            sync,
            dry_run,
        } => commands::move_skill(
            &ctx, "global", &skill, &project, None, copy, force, sync, dry_run,
        ),
        Command::List { target } => commands::list(&ctx, &target),
        Command::Targets => commands::targets(&ctx),
        Command::Sources { target } => commands::sources(&ctx, &target),
        Command::Completions { .. } => unreachable!("handled before config loading"),
    }
}
