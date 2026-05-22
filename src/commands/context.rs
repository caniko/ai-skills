use anyhow::{Context as AnyhowContext, Result};
use camino::{Utf8Path, Utf8PathBuf};

use crate::{
    config::{Config, ProjectConfig},
    model::Target,
};

pub struct Context {
    pub config_path: Utf8PathBuf,
    pub catalog_config_path: Utf8PathBuf,
    pub config: Config,
    pub mirror_root: Utf8PathBuf,
}

impl Context {
    pub fn load(
        config_path: &Utf8Path,
        mirror_root: &Utf8Path,
        catalog_config_path: &Utf8Path,
    ) -> Result<Self> {
        Ok(Self {
            config_path: config_path.to_path_buf(),
            catalog_config_path: catalog_config_path.to_path_buf(),
            config: Config::load(config_path)?,
            mirror_root: mirror_root.to_path_buf(),
        })
    }

    pub(super) fn all_targets(&self) -> Result<Vec<Target>> {
        self.config.targets(&self.mirror_root)
    }

    pub(super) fn target(&self, name: &str) -> Result<Target> {
        if name == "global" {
            return self.config.global_target(&self.mirror_root);
        }
        let project = self
            .project(name)
            .with_context(|| format!("unknown target `{name}`"))?;
        self.config.project_target(&self.mirror_root, project)
    }

    pub(super) fn selected_targets(&self, selector: &str) -> Result<Vec<Target>> {
        match selector {
            "all" => self.all_targets(),
            "global" => Ok(vec![self.target("global")?]),
            "project" => self
                .config
                .projects
                .iter()
                .map(|project| self.config.project_target(&self.mirror_root, project))
                .collect(),
            other => Ok(vec![self.target(other)?]),
        }
    }

    pub(super) fn project(&self, name: &str) -> Option<&ProjectConfig> {
        self.config
            .projects
            .iter()
            .find(|project| project.name == name)
    }
}
