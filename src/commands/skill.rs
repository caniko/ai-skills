use std::fs;

use anyhow::{bail, Context as AnyhowContext, Result};
use camino::Utf8Path;

use super::Context;
use crate::{fs_ops, model::Target, reconcile};

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
