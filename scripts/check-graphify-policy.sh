#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
graphify="$root/global_skills/graphify/SKILL.md"
clause='**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.'

declare -a files=()

while IFS= read -r file; do
  files+=("$file")
done < <(find "$root/global_skills" -mindepth 2 -maxdepth 2 -type f -name SKILL.md | sort)

while IFS=$'\t' read -r project path; do
  if [[ -z "$project" || -z "$path" ]]; then
    echo "invalid project registry row: project='${project}' path='${path}'" >&2
    exit 1
  fi
  canonical="$path/.skills"
  if [[ ! -d "$canonical" ]]; then
    echo "missing canonical skill store for $project: $canonical" >&2
    echo "producer: the project checkout declared by Skillnet" >&2
    echo "validate: skillnet project list && test -d '$canonical'" >&2
    exit 1
  fi
  while IFS= read -r file; do
    files+=("$file")
  done < <(find "$canonical" -mindepth 2 -maxdepth 2 -type f -name SKILL.md | sort)
done < <(skillnet project list)

listed_count="$(
  skillnet skill list --all |
    awk 'NF && $1 != "#" { count += 1 } END { print count + 0 }'
)"

if [[ "${#files[@]}" -ne "$listed_count" ]]; then
  echo "canonical inventory mismatch: found ${#files[@]} SKILL.md files, Skillnet listed $listed_count" >&2
  echo "producer: Skillnet's global and project registry configuration" >&2
  echo "validate: skillnet project list && skillnet skill list --all" >&2
  exit 1
fi

failures=0
graphify_seen=0
for file in "${files[@]}"; do
  if [[ "$file" == "$graphify" ]]; then
    graphify_seen=$((graphify_seen + 1))
    continue
  fi

  count="$(
    rg --no-config --fixed-strings --count-matches \
      --regexp "$clause" "$file" || true
  )"
  if [[ "$count" != "1" ]]; then
    echo "expected the Graphify prerequisite exactly once: $file (found ${count:-0})" >&2
    failures=$((failures + 1))
    continue
  fi

  if ! awk -v clause="$clause" '
    NR == 1 && $0 != "---" { exit 1 }
    $0 == "---" {
      delimiters += 1
      if (delimiters == 2) {
        if ((getline <= 0) || $0 != "") exit 1
        if ((getline <= 0) || $0 != clause) exit 1
        if ((getline <= 0) || $0 != "") exit 1
        positioned = 1
        exit 0
      }
    }
    END { if (!positioned) exit 1 }
  ' "$file"; then
    echo "Graphify prerequisite must immediately follow YAML frontmatter: $file" >&2
    failures=$((failures + 1))
  fi
done

if [[ "$graphify_seen" -ne 1 ]]; then
  echo "expected exactly one canonical Graphify skill, found $graphify_seen" >&2
  failures=$((failures + 1))
elif rg --no-config --fixed-strings --quiet \
  --regexp '**Cross-repository work:**' "$graphify"; then
  echo "Graphify must not carry its own recursive invocation prerequisite" >&2
  failures=$((failures + 1))
elif [[ ! -f "$root/global_skills/graphify/references/github-and-merge.md" ]]; then
  echo "Graphify is missing references/github-and-merge.md" >&2
  failures=$((failures + 1))
elif ! rg --no-config --fixed-strings --quiet \
  --regexp '/graphify <url1> <url2> ...' "$graphify"; then
  echo "Graphify no longer advertises its multi-repository merge entrypoint" >&2
  failures=$((failures + 1))
elif ! rg --no-config --fixed-strings --quiet \
  --regexp '### Step 0 - GitHub repos and multi-path merge' "$graphify"; then
  echo "Graphify no longer defines the mandatory multi-path merge step" >&2
  failures=$((failures + 1))
fi

if [[ "$failures" -ne 0 ]]; then
  exit 1
fi

echo "Graphify policy passed for ${#files[@]} skills ($(("${#files[@]}" - 1)) required, 1 exempt)"
