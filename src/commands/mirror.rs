use anyhow::Result;

use super::Context;
use crate::reconcile as reconcile_ops;

pub fn reconcile(ctx: &Context, target: &str, sync: bool, dry_run: bool) -> Result<()> {
    for target in ctx.selected_targets(target)? {
        reconcile_ops::reconcile_target(&target, sync, dry_run)?;
    }
    Ok(())
}

pub fn sync(ctx: &Context, target: &str, dry_run: bool) -> Result<()> {
    for target in ctx.selected_targets(target)? {
        if dry_run {
            println!("# sync {}", target.name);
            println!("from: {}", target.mirror_path);
            println!(
                "to: {}",
                target
                    .sync_paths
                    .iter()
                    .map(|p| p.as_str())
                    .collect::<Vec<_>>()
                    .join(", ")
            );
            continue;
        }
        reconcile_ops::sync_target(&target)?;
        println!("synced {}", target.name);
    }
    Ok(())
}

pub fn list(ctx: &Context, target: &str) -> Result<()> {
    for target in ctx.selected_targets(target)? {
        println!("# {}", target.name);
        for skill in reconcile_ops::mirror_skill_dirs(&target.mirror_path)? {
            println!("{}", skill.file_name().unwrap_or_default());
        }
    }
    Ok(())
}

pub fn targets(ctx: &Context) -> Result<()> {
    for target in ctx.all_targets()? {
        println!("{}", target.name);
    }
    Ok(())
}

pub fn sources(ctx: &Context, target: &str) -> Result<()> {
    for target in ctx.selected_targets(target)? {
        println!("# {}", target.name);
        for source in target.sources {
            println!("{}\t{}\t{}", source.label, source.priority, source.path);
        }
    }
    Ok(())
}
