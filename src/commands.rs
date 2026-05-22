use std::fs;

use anyhow::{bail, Context as AnyhowContext, Result};
use camino::{Utf8Path, Utf8PathBuf};

use crate::{config::Config, fs_ops, model::Target, reconcile};

pub struct Context {
    pub config: Config,
    pub mirror_root: Utf8PathBuf,
}

impl Context {
    pub fn load(config_path: &Utf8Path, mirror_root: &Utf8Path) -> Result<Self> {
        Ok(Self {
            config: Config::load(config_path)?,
            mirror_root: mirror_root.to_path_buf(),
        })
    }

    fn all_targets(&self) -> Result<Vec<Target>> {
        self.config.targets(&self.mirror_root)
    }

    fn target(&self, name: &str) -> Result<Target> {
        if name == "global" {
            return self.config.global_target(&self.mirror_root);
        }
        let project = self
            .config
            .projects
            .iter()
            .find(|p| p.name == name)
            .with_context(|| format!("unknown target `{name}`"))?;
        self.config.project_target(&self.mirror_root, project)
    }

    fn selected_targets(&self, selector: &str) -> Result<Vec<Target>> {
        match selector {
            "all" => self.all_targets(),
            "global" => Ok(vec![self.target("global")?]),
            other => Ok(vec![self.target(other)?]),
        }
    }
}

pub fn reconcile(ctx: &Context, target: &str, sync: bool, dry_run: bool) -> Result<()> {
    for target in ctx.selected_targets(target)? {
        reconcile::reconcile_target(&target, sync, dry_run)?;
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
        reconcile::sync_target(&target)?;
        println!("synced {}", target.name);
    }
    Ok(())
}

pub fn delete(
    ctx: &Context,
    scope: &str,
    skill: &str,
    sync_live: bool,
    dry_run: bool,
) -> Result<()> {
    let target = ctx.target(scope)?;
    let path = target.mirror_path.join(skill);
    fs_ops::ensure_skill_dir(&path)?;
    if dry_run {
        println!("delete {path}");
    } else {
        fs::remove_dir_all(&path)?;
        maybe_sync(&target, sync_live)?;
    }
    Ok(())
}

pub fn rename(
    ctx: &Context,
    scope: &str,
    old: &str,
    new: &str,
    force: bool,
    sync_live: bool,
    dry_run: bool,
) -> Result<()> {
    let target = ctx.target(scope)?;
    let src = target.mirror_path.join(old);
    let dest = target.mirror_path.join(new);
    fs_ops::ensure_skill_dir(&src)?;
    prepare_dest(&src, &dest, force)?;
    if dry_run {
        println!("rename {src} {dest}");
    } else {
        if dest.exists() {
            fs::remove_dir_all(&dest)?;
        }
        fs::rename(&src, &dest)?;
        maybe_sync(&target, sync_live)?;
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
pub fn move_skill(
    ctx: &Context,
    from_scope: &str,
    skill: &str,
    to_scope: &str,
    as_name: Option<&str>,
    copy: bool,
    force: bool,
    sync_live: bool,
    dry_run: bool,
) -> Result<()> {
    let from = ctx.target(from_scope)?;
    let to = ctx.target(to_scope)?;
    let src = from.mirror_path.join(skill);
    let dest = to.mirror_path.join(as_name.unwrap_or(skill));
    fs_ops::ensure_skill_dir(&src)?;
    prepare_dest(&src, &dest, force)?;

    if dry_run {
        let action = if copy { "copy" } else { "move" };
        println!("{action} {src} {dest}");
    } else {
        if dest.exists() {
            fs::remove_dir_all(&dest)?;
        }
        if copy {
            fs_ops::copy_dir(&src, &dest)?;
        } else {
            fs::create_dir_all(dest.parent().context("destination has no parent")?)?;
            fs::rename(&src, &dest)?;
        }
        if sync_live {
            reconcile::sync_target(&from)?;
            if from.name != to.name {
                reconcile::sync_target(&to)?;
            }
        }
    }
    Ok(())
}

pub fn list(ctx: &Context, target: &str) -> Result<()> {
    for target in ctx.selected_targets(target)? {
        println!("# {}", target.name);
        for skill in reconcile::mirror_skill_dirs(&target.mirror_path)? {
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

fn maybe_sync(target: &Target, sync_live: bool) -> Result<()> {
    if sync_live {
        reconcile::sync_target(target)?;
    }
    Ok(())
}

fn prepare_dest(src: &Utf8Path, dest: &Utf8Path, force: bool) -> Result<()> {
    if !dest.exists() {
        return Ok(());
    }
    fs_ops::ensure_skill_dir(dest)?;
    if force {
        return Ok(());
    }

    let src_mtime = fs_ops::newest_mtime_nanos(src)?;
    let dest_mtime = fs_ops::newest_mtime_nanos(dest)?;
    if src_mtime > dest_mtime {
        return Ok(());
    }
    if src_mtime == dest_mtime
        && fs_ops::content_signature(src)? == fs_ops::content_signature(dest)?
    {
        return Ok(());
    }
    bail!("destination `{dest}` exists and is not older; pass --force to overwrite");
}
