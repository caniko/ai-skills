# mdBook Documentation Guide

Use this reference from invocable Codeberg skills when creating or reorganizing documentation. This file is not a skill and should not be invoked directly.

## Structure

Use `docs/book.toml` for mdBook configuration and `docs/src/` for content. Keep source pages grouped by reader task, not by implementation module, unless the project is explicitly API-reference-only.

Recommended starter layout:

```text
docs/
  book.toml
  src/
    SUMMARY.md
    introduction.md
    getting-started/
      installation.md
      quick-start.md
    guides/
      <workflow>.md
    concepts/
      <concept>.md
```

## SUMMARY.md

Use `# Section Title` lines for section headers and Markdown links for pages:

```markdown
# Summary

Introduction page: `./introduction.md`

# Getting Started

- Installation page: `./getting-started/installation.md`
- Quick Start page: `./getting-started/quick-start.md`
```

Every linked file must exist. Do not add placeholder chapters unless the user explicitly wants stubs.

## Page Conventions

- Use standard Markdown without frontmatter.
- Start each page with one `# Title` heading.
- Prefer task-oriented examples near the start of getting-started and guide pages.
- Use relative links between mdBook pages, such as `../guides/example.md`.
- Keep commands copyable and include the working directory when it is not obvious.
- Do not invent configuration, features, commands, or APIs. Derive them from source, tests, manifests, README, or user-provided material.

## Quality Expectations

- Document the happy path first, then constraints and failure modes.
- Keep introductory pages concise and link into deeper guides.
- Explain prerequisites before commands that depend on them.
- Validate examples against the repository when feasible.
- If required source information is missing, stop and report the missing artifact, why it is required, the upstream source that must provide it, the regeneration workflow, and the validation command.
