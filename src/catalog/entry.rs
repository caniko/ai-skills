use camino::Utf8PathBuf;

#[derive(Debug, Clone)]
pub(super) struct SkillEntry {
    pub(super) name: String,
    pub(super) qualified_name: String,
    pub(super) scope: String,
    pub(super) project: Option<String>,
    pub(super) category: Option<String>,
    pub(super) status: String,
    pub(super) tags: Vec<String>,
    pub(super) related_skills: Vec<String>,
    pub(super) collision_note: Option<String>,
    pub(super) description: String,
    pub(super) path: Utf8PathBuf,
    pub(super) line_count: usize,
}

#[derive(Debug, Default)]
pub(super) struct Frontmatter {
    pub(super) name: Option<String>,
    pub(super) description: Option<String>,
}

impl SkillEntry {
    pub(super) fn matches(&self, query: &str) -> bool {
        let fields = [
            self.name.as_str(),
            self.qualified_name.as_str(),
            self.project.as_deref().unwrap_or_default(),
            self.category.as_deref().unwrap_or_default(),
            self.status.as_str(),
            self.description.as_str(),
        ];
        fields
            .iter()
            .any(|field| field.to_lowercase().contains(query))
            || self
                .tags
                .iter()
                .any(|tag| tag.to_lowercase().contains(query))
    }
}
