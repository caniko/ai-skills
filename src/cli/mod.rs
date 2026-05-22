mod args;

use anyhow::Result;
use clap::{CommandFactory, Parser};
use clap_complete::generate;

use crate::commands::Context;
use crate::{catalog, commands};

use args::{
    CatalogCommand, Cli, Command, MirrorCommand, ProjectCommand, SkillCommand, TomlCommand,
};

pub(crate) fn run() -> Result<()> {
    let cli = Cli::parse();
    if let Command::Completions { shell } = cli.command {
        let mut command = Cli::command();
        let name = command.get_name().to_string();
        generate(shell, &mut command, name, &mut std::io::stdout());
        return Ok(());
    }

    let ctx = Context::load(&cli.config, &cli.mirror_root, &cli.catalog_config)?;

    match cli.command {
        Command::Mirror { command } => run_mirror_command(&ctx, command),
        Command::Skill { command } => run_skill_command(&ctx, command),
        Command::Toml { command } => run_toml_command(&ctx, command),
        Command::Catalog { command } => run_catalog_command(&ctx, command),
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
        Command::Project { command } => run_project_command(&ctx, command),
        Command::Targets => commands::targets(&ctx),
        Command::Sources { target } => commands::sources(&ctx, &target),
        Command::Completions { .. } => unreachable!("handled before config loading"),
    }
}

fn run_mirror_command(ctx: &Context, command: MirrorCommand) -> Result<()> {
    match command {
        MirrorCommand::Reconcile {
            target,
            sync,
            dry_run,
        } => commands::reconcile(ctx, &target, sync, dry_run),
        MirrorCommand::Sync { target, dry_run } => commands::sync(ctx, &target, dry_run),
        MirrorCommand::List { target } => commands::list(ctx, &target),
        MirrorCommand::Targets => commands::targets(ctx),
        MirrorCommand::Sources { target } => commands::sources(ctx, &target),
    }
}

fn run_skill_command(ctx: &Context, command: SkillCommand) -> Result<()> {
    match command {
        SkillCommand::Delete {
            scope,
            skill,
            sync,
            dry_run,
        } => commands::delete(ctx, &scope, &skill, sync, dry_run),
        SkillCommand::Rename {
            scope,
            old,
            new,
            force,
            sync,
            dry_run,
        } => commands::rename(ctx, &scope, &old, &new, force, sync, dry_run),
        SkillCommand::Move {
            from_scope,
            skill,
            to_scope,
            as_name,
            copy,
            force,
            sync,
            dry_run,
        } => commands::move_skill(
            ctx,
            &from_scope,
            &skill,
            &to_scope,
            as_name.as_deref(),
            copy,
            force,
            sync,
            dry_run,
        ),
        SkillCommand::Globalize {
            project,
            skill,
            copy,
            force,
            sync,
            dry_run,
        } => commands::move_skill(
            ctx, &project, &skill, "global", None, copy, force, sync, dry_run,
        ),
        SkillCommand::Deglobalize {
            skill,
            project,
            copy,
            force,
            sync,
            dry_run,
        } => commands::move_skill(
            ctx, "global", &skill, &project, None, copy, force, sync, dry_run,
        ),
    }
}

fn run_toml_command(ctx: &Context, command: TomlCommand) -> Result<()> {
    match command {
        TomlCommand::Project { command } => run_project_command(ctx, command),
    }
}

fn run_project_command(ctx: &Context, command: ProjectCommand) -> Result<()> {
    match command {
        ProjectCommand::List => {
            commands::project_list(ctx);
            Ok(())
        }
        ProjectCommand::Add {
            name,
            path,
            allow_missing,
            dry_run,
        } => commands::project_add(ctx, &name, &path, allow_missing, dry_run),
        ProjectCommand::Remove {
            name,
            prune_mirror,
            dry_run,
        } => commands::project_remove(ctx, &name, prune_mirror, dry_run),
    }
}

fn run_catalog_command(ctx: &Context, command: CatalogCommand) -> Result<()> {
    match command {
        CatalogCommand::Generate => catalog::generate(ctx),
        CatalogCommand::Lint => catalog::lint(ctx),
        CatalogCommand::Show { skill } => catalog::show(ctx, &skill),
        CatalogCommand::Search { query } => catalog::search(ctx, &query),
    }
}
