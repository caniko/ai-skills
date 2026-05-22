mod config;
mod discover;
mod entry;
mod frontmatter;
mod render;
mod validate;

use anyhow::{bail, Result};

use crate::commands::Context;

use config::CatalogConfig;
use discover::load_entries;
use render::{
    matching_entries, print_entry, render_catalog, render_conflicts, render_routing,
    write_generated_doc, write_project_indexes,
};
use validate::validate_entries;

pub fn generate(ctx: &Context) -> Result<()> {
    let config = CatalogConfig::load(&ctx.catalog_config_path)?;
    let entries = load_entries(ctx, &config)?;
    let lint_errors = validate_entries(&entries, &config);
    if !lint_errors.is_empty() {
        bail!("catalog metadata is invalid:\n{}", lint_errors.join("\n"));
    }

    write_generated_doc(
        &ctx.mirror_root.join("CATALOG.md"),
        &render_catalog(&entries)?,
    )?;
    write_generated_doc(
        &ctx.mirror_root.join("ROUTING.md"),
        &render_routing(&entries)?,
    )?;
    write_generated_doc(
        &ctx.mirror_root.join("SKILL_CONFLICTS.md"),
        &render_conflicts(&entries),
    )?;
    write_project_indexes(ctx, &entries)?;
    println!("generated catalog for {} skills", entries.len());
    Ok(())
}

pub fn lint(ctx: &Context) -> Result<()> {
    let config = CatalogConfig::load(&ctx.catalog_config_path)?;
    let entries = load_entries(ctx, &config)?;
    let errors = validate_entries(&entries, &config);
    if errors.is_empty() {
        println!("catalog lint passed for {} skills", entries.len());
        Ok(())
    } else {
        bail!("catalog lint failed:\n{}", errors.join("\n"))
    }
}

pub fn show(ctx: &Context, skill: &str) -> Result<()> {
    let config = CatalogConfig::load(&ctx.catalog_config_path)?;
    let entries = load_entries(ctx, &config)?;
    let matches = matching_entries(&entries, skill);
    match matches.as_slice() {
        [] => bail!("skill `{skill}` not found"),
        [entry] => {
            print_entry(entry);
            Ok(())
        }
        _ => bail!(
            "skill `{skill}` is ambiguous; use one of:\n{}",
            matches
                .iter()
                .map(|entry| format!("  - {}", entry.qualified_name))
                .collect::<Vec<_>>()
                .join("\n")
        ),
    }
}

pub fn search(ctx: &Context, query: &str) -> Result<()> {
    let config = CatalogConfig::load(&ctx.catalog_config_path)?;
    let query = query.to_lowercase();
    let entries = load_entries(ctx, &config)?;
    for entry in entries.iter().filter(|entry| entry.matches(&query)) {
        println!(
            "{}\t{}\t{}\t{}",
            entry.qualified_name,
            entry.category.as_deref().unwrap_or("uncategorized"),
            entry.status,
            entry.description
        );
    }
    Ok(())
}
