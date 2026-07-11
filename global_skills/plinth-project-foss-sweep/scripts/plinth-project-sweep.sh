#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DISCOVER="$SKILL_DIR/scripts/discover-recent-owned-foss.sh"
ROOT="~/canix/Projects"
SINCE="5-months"
LIMIT=0
APPLY=0
OWNERS="caniko,memorycircuits"
TARGET_FILE=""
EXCLUDE_FILE=""

usage() {
  cat <<'EOF'
Usage: plinth-project-sweep.sh [OPTIONS]

Dry-run or apply plinth-project configs across discovered owned FOSS targets.

Options:
  --root PATH       Projects root to scan (default: ~/canix/Projects)
  --since VALUE    Recent activity window (default: 5-months)
  --owners CSV     Owned forge namespaces (default: caniko,memorycircuits)
  --limit N        Process at most N target projects
  --target-file F  Only process relative repo paths listed in F
  --exclude-file F Skip relative repo paths listed in F
  --dry-run        Report only; default
  --apply          Write missing configs and run plinth-project check/build
  -h, --help       Show this help

Output:
  TSV columns: verdict, relative_path, action, detail, validation
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT="$2"
      shift 2
      ;;
    --since)
      SINCE="$2"
      shift 2
      ;;
    --owners)
      OWNERS="$2"
      shift 2
      ;;
    --limit)
      LIMIT="$2"
      shift 2
      ;;
    --target-file)
      TARGET_FILE="$2"
      shift 2
      ;;
    --exclude-file)
      EXCLUDE_FILE="$2"
      shift 2
      ;;
    --dry-run)
      APPLY=0
      shift
      ;;
    --apply)
      APPLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -x "$DISCOVER" ]]; then
  echo "discovery script is not executable: $DISCOVER" >&2
  exit 1
fi

if [[ -n "$TARGET_FILE" && ! -f "$TARGET_FILE" ]]; then
  echo "target file does not exist: $TARGET_FILE" >&2
  exit 1
fi

if [[ -n "$EXCLUDE_FILE" && ! -f "$EXCLUDE_FILE" ]]; then
  echo "exclude file does not exist: $EXCLUDE_FILE" >&2
  exit 1
fi

path_list_contains() {
  local file="$1"
  local rel="$2"
  [[ -n "$file" ]] || return 1
  grep -Fx -- "$rel" "$file" >/dev/null 2>&1
}

plinth_project_cmd() {
  if command -v plinth-project >/dev/null 2>&1; then
    printf 'plinth-project'
  elif command -v cargo >/dev/null 2>&1 && [[ -f ~/canix/Projects/repos/owned/codeberg.org/caniko/plinth/Cargo.toml ]]; then
    printf 'cargo run --manifest-path ~/canix/Projects/repos/owned/codeberg.org/caniko/plinth/Cargo.toml --package plinth-project --'
  elif command -v nix >/dev/null 2>&1 && [[ -f ~/canix/Projects/repos/owned/codeberg.org/caniko/plinth/flake.nix ]]; then
    printf 'nix run ~/canix/Projects/repos/owned/codeberg.org/caniko/plinth#plinth-project --'
  else
    printf ''
  fi
}

toml_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

first_readme() {
  find "$1" -maxdepth 1 -type f \( -iname 'README' -o -iname 'README.*' \) -print -quit
}

readme_title() {
  local readme="$1"
  awk '
    /^#[[:space:]]+/ {
      sub(/^#[[:space:]]+/, "")
      gsub(/[[:space:]]+$/, "")
      print
      exit
    }
  ' "$readme"
}

readme_description() {
  local readme="$1"
  awk '
    BEGIN { in_code=0 }
    /^```/ { in_code = !in_code; next }
    in_code { next }
    /^#/ { next }
    /^[[:space:]]*$/ { next }
    {
      line=$0
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", line)
      if (length(line) > 20) {
        print line
        exit
      }
    }
  ' "$readme"
}

detect_stack() {
  local repo="$1"
  local stack=()
  [[ -f "$repo/Cargo.toml" ]] && stack+=("Rust")
  [[ -f "$repo/flake.nix" ]] && stack+=("Nix")
  [[ -f "$repo/package.json" ]] && stack+=("JavaScript")
  [[ -f "$repo/pyproject.toml" || -f "$repo/setup.py" ]] && stack+=("Python")
  [[ -f "$repo/go.mod" ]] && stack+=("Go")
  [[ -f "$repo/typst.toml" ]] && stack+=("Typst")
  if [[ ${#stack[@]} -eq 0 ]]; then
    stack+=("FOSS")
  fi
  printf '%s\n' "${stack[@]}"
}

write_config() {
  local repo="$1"
  local remote="$2"
  local config="$repo/website/plinth-project.toml"
  local readme title description tagline stack_array

  readme="$(first_readme "$repo")"
  if [[ -z "$readme" ]]; then
    return 2
  fi

  title="$(readme_title "$readme")"
  [[ -n "$title" ]] || title="$(basename "$repo")"
  description="$(readme_description "$readme")"
  [[ -n "$description" ]] || return 3
  tagline="$description"

  stack_array="$(detect_stack "$repo" | awk '{ printf "    { title = \"%s\", description = \"Project technology detected from repository manifests.\" }\\n", $0 }')"

  mkdir -p "$repo/website"
  cat >"$config" <<EOF
[site]
title = "$(toml_escape "$title")"
description = "$(toml_escape "$description")"
base_url = "/"
footer_note = "Generated from repository metadata by the plinth-project FOSS sweep."

[[nav]]
label = "Overview"
href = "#overview"

[[nav]]
label = "Source"
href = "$(toml_escape "$remote")"

[[footer_links]]
label = "Source"
href = "$(toml_escape "$remote")"

[[pages]]
slug = "index"
title = "$(toml_escape "$title")"
description = "$(toml_escape "$description")"

[[pages.sections]]
type = "hero"
title = "$(toml_escape "$title")"
tagline = "$(toml_escape "$tagline")"
subtitle = "$(toml_escape "$description")"

[[pages.sections.ctas]]
label = "View source"
href = "$(toml_escape "$remote")"
primary = true

[[pages.sections]]
type = "feature_grid"
id = "overview"

EOF

  while IFS= read -r tech; do
    cat >>"$config" <<EOF
[[pages.sections.features]]
title = "$(toml_escape "$tech")"
description = "Project technology detected from repository manifests."

EOF
  done < <(detect_stack "$repo")
}

run_validation() {
  local repo="$1"
  local cmd="$2"
  local config="website/plinth-project.toml"
  (
    cd "$repo"
    eval "$cmd check --config '$config'" >/tmp/plinth-project-check.log 2>&1
    eval "$cmd build --config '$config'" >/tmp/plinth-project-build.log 2>&1
  )
}

printf 'verdict\trelative_path\taction\tdetail\tvalidation\n'

count=0
"$DISCOVER" --root "$ROOT" --since "$SINCE" --owners "$OWNERS" --dry-run |
tail -n +2 |
while IFS=$'\t' read -r verdict rel last remote license reason proposed; do
  [[ "$verdict" == "target" ]] || continue
  if [[ -n "$TARGET_FILE" ]] && ! path_list_contains "$TARGET_FILE" "$rel"; then
    continue
  fi
  if path_list_contains "$EXCLUDE_FILE" "$rel"; then
    printf 'skipped\t%s\texcluded\texcluded-by-file\tremove from exclude file and rerun\n' "$rel"
    continue
  fi
  count=$((count + 1))
  if [[ "$LIMIT" -gt 0 && "$count" -gt "$LIMIT" ]]; then
    continue
  fi

  repo="$ROOT/$rel"
  config="$repo/website/plinth-project.toml"
  config_status="$(git -C "$repo" status --short -- website/plinth-project.toml 2>/dev/null || true)"
  public_status="$(git -C "$repo" status --short -- website/public 2>/dev/null || true)"

  if [[ "$APPLY" -eq 1 && ( -n "$config_status" || -n "$public_status" ) ]]; then
    printf 'blocked\t%s\tno-write\tdirty-website-paths\tgit status --short -- website/plinth-project.toml website/public\n' "$rel"
    continue
  fi

  if [[ -f "$config" ]]; then
    action="preserve-existing-config"
  else
    readme="$(first_readme "$repo")"
    if [[ -z "$readme" ]]; then
      printf 'blocked\t%s\tmissing-readme\tREADME is required to derive title/description\tcreate README then rerun plinth-project-sweep.sh --dry-run --limit 1\n' "$rel"
      continue
    fi
    if [[ -z "$(readme_description "$readme")" ]]; then
      printf 'blocked\t%s\tmissing-description\tREADME needs a descriptive paragraph\tupdate README then rerun plinth-project-sweep.sh --dry-run --limit 1\n' "$rel"
      continue
    fi
    action="create-config"
  fi

  if [[ "$APPLY" -eq 0 ]]; then
    if [[ "$action" == "preserve-existing-config" ]]; then
      dry_verdict="already-current"
    else
      dry_verdict="dry-run"
    fi
    printf '%s\t%s\t%s\tdry-run:%s\tplinth-project check --config website/plinth-project.toml && plinth-project build --config website/plinth-project.toml\n' "$dry_verdict" "$rel" "$action" "$reason"
    continue
  fi

  cmd="$(plinth_project_cmd)"
  if [[ -z "$cmd" ]]; then
    printf 'blocked\t%s\tmissing-tool\tplinth-project or cargo is required\tinstall plinth-project or run inside Plinth dev shell\n' "$rel"
    continue
  fi

  if [[ ! -f "$config" ]]; then
    if ! write_config "$repo" "$remote"; then
      code=$?
      printf 'blocked\t%s\twrite-config-failed\tmetadata extraction failed with code %s\trerun dry-run and inspect README/license/remote\n' "$rel" "$code"
      continue
    fi
  fi

  if run_validation "$repo" "$cmd"; then
    if [[ "$action" == "preserve-existing-config" ]]; then
      printf 'already-current\t%s\t%s\tvalidated\tplinth-project check/build\n' "$rel" "$action"
    else
      printf 'updated\t%s\t%s\tvalidated\tplinth-project check/build\n' "$rel" "$action"
    fi
  else
    printf 'blocked\t%s\tvalidation-failed\tsee /tmp/plinth-project-check.log and /tmp/plinth-project-build.log\t%s check --config website/plinth-project.toml\n' "$rel" "$cmd"
  fi
done
