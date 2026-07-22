from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def frontmatter_value(frontmatter: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", frontmatter)
    assert match, f"missing {key}"
    return match.group(1).strip().strip('"\'')


def test_skill_frontmatter_matches_agent_skills_spec():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, frontmatter, body = text.split("---", 2)
    name = frontmatter_value(frontmatter, "name")
    description = frontmatter_value(frontmatter, "description")
    compatibility = frontmatter_value(frontmatter, "compatibility")
    assert name == ROOT.name
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
    assert 1 <= len(name) <= 64
    assert 1 <= len(description) <= 1024
    assert len(compatibility) <= 500
    assert body.strip()
    assert len(text.splitlines()) < 500
