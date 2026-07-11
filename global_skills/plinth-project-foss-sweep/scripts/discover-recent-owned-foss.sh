#!/usr/bin/env bash
set -euo pipefail

ROOT="~/canix/Projects"
SINCE="5 months ago"
OWNERS="caniko,memorycircuits"
DRY_RUN=1
MAX_DEPTH=5

usage() {
  cat <<'EOF'
Usage: discover-recent-owned-foss.sh [OPTIONS]

Inventory recent owned FOSS candidates as TSV.

Options:
  --root PATH         Projects root to scan (default: ~/canix/Projects)
  --since VALUE      Git --since value; "5-months" becomes "5 months ago"
  --owners CSV       Owned forge namespaces (default: caniko,memorycircuits)
  --max-depth N      find(1) max depth for .git dirs (default: 5)
  --dry-run          No-op flag for workflow consistency; this script never mutates
  -h, --help         Show this help

Columns:
  verdict, relative_path, last_commit_date, remote, license, reason, proposed_move
EOF
}

normalize_since() {
  case "$1" in
    *-months) printf '%s months ago' "${1%-months}" ;;
    *-month) printf '%s month ago' "${1%-month}" ;;
    *) printf '%s' "$1" ;;
  esac
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT="$2"
      shift 2
      ;;
    --since)
      SINCE="$(normalize_since "$2")"
      shift 2
      ;;
    --owners)
      OWNERS="$2"
      shift 2
      ;;
    --max-depth)
      MAX_DEPTH="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
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

if [[ ! -d "$ROOT" ]]; then
  echo "root does not exist: $ROOT" >&2
  exit 1
fi

IFS=',' read -r -a OWNER_LIST <<<"$OWNERS"

remote_fetch_url() {
  git -C "$1" remote -v 2>/dev/null | awk '/\(fetch\)/ { print $2; exit }'
}

owner_from_remote() {
  local remote="$1"
  local path
  path="$remote"
  path="${path#git@github.com:}"
  path="${path#git@gitlab.com:}"
  path="${path#git@codeberg.org:}"
  path="${path#ssh://git@github.com/}"
  path="${path#ssh://git@gitlab.com/}"
  path="${path#ssh://git@codeberg.org/}"
  path="${path#https://github.com/}"
  path="${path#https://gitlab.com/}"
  path="${path#https://codeberg.org/}"
  path="${path%.git}"
  printf '%s' "${path%%/*}"
}

is_owned_remote() {
  local owner="$1"
  local candidate
  for candidate in "${OWNER_LIST[@]}"; do
    [[ "$owner" == "$candidate" ]] && return 0
  done
  return 1
}

is_public_forge_remote() {
  case "$1" in
    *github.com:*|*github.com/*|*gitlab.com:*|*gitlab.com/*|*codeberg.org:*|*codeberg.org/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

license_file() {
  find "$1" -maxdepth 1 -type f \( -iname 'LICENSE*' -o -iname 'COPYING*' \) -printf '%f' -quit 2>/dev/null
}

excluded_reason() {
  local rel="$1"
  case "$rel" in
    upstream/*) echo "excluded-upstream"; return 0 ;;
    worktrees/*) echo "excluded-worktree"; return 0 ;;
    assesments/*|assessments/*) echo "excluded-assessment"; return 0 ;;
    nix/nixpkgs|nix/nixpkgs/*|nix/home-manager|nix/home-manager/*|nix/nixos-hardware|nix/nixos-hardware/*) echo "excluded-known-upstream-fork"; return 0 ;;
    */target/*|*/node_modules/*|*/vendor/*) echo "excluded-vendored"; return 0 ;;
    *.tmp|tmp/*|*/tmp/*) echo "excluded-scratch"; return 0 ;;
    *) return 1 ;;
  esac
}

is_nested_git_repo() {
  local repo="$1"
  local parent
  parent="$(dirname "$repo")"
  while [[ "$parent" != "$ROOT" && "$parent" != "/" ]]; do
    if [[ -d "$parent/.git" ]]; then
      return 0
    fi
    parent="$(dirname "$parent")"
  done
  return 1
}

is_obvious_third_party_fork() {
  case "$(basename "$1")" in
    nixpkgs|home-manager|nixos-hardware|llvm-project|osxcross|disko|goose|openobserve|rauthy)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

printf 'verdict\trelative_path\tlast_commit_date\tremote\tlicense\treason\tproposed_move\n'

find "$ROOT" -maxdepth "$MAX_DEPTH" -type d -name .git -print | sort |
while IFS= read -r gitdir; do
  repo="${gitdir%/.git}"
  rel="${repo#"$ROOT"/}"

  if reason="$(excluded_reason "$rel")"; then
    verdict="skip"
    remote="$(remote_fetch_url "$repo")"
    last="$(git -C "$repo" log --since="$SINCE" --format=%cI -1 --all 2>/dev/null || true)"
    [[ -n "$last" ]] || last="-"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$verdict" "$rel" "${last%%T*}" "${remote:-"-"}" "-" "$reason" "-"
    continue
  fi

  if is_nested_git_repo "$repo"; then
    remote="$(remote_fetch_url "$repo")"
    last="$(git -C "$repo" log --since="$SINCE" --format=%cI -1 --all 2>/dev/null || true)"
    [[ -n "$last" ]] || last="-"
    printf 'skip\t%s\t%s\t%s\t%s\texcluded-nested-git-repo\t%s\n' "$rel" "${last%%T*}" "${remote:-"-"}" "$(license_file "$repo")" "-"
    continue
  fi

  last="$(git -C "$repo" log --since="$SINCE" --format=%cI -1 --all 2>/dev/null || true)"
  [[ -n "$last" ]] || continue

  remote="$(remote_fetch_url "$repo")"
  owner="$(owner_from_remote "$remote")"
  license="$(license_file "$repo")"
  proposed="~/canix/Projects/repos/owned/$(basename "$repo")"

  if [[ -z "$remote" ]]; then
    printf 'needs-user-review\t%s\t%s\t-\t%s\tmissing-remote\t%s\n' "$rel" "${last%%T*}" "${license:-no-license}" "$proposed"
  elif is_obvious_third_party_fork "$repo"; then
    printf 'skip\t%s\t%s\t%s\t%s\tobvious-third-party-fork\t%s\n' "$rel" "${last%%T*}" "$remote" "${license:-no-license}" "$proposed"
  elif ! is_public_forge_remote "$remote"; then
    printf 'needs-user-review\t%s\t%s\t%s\t%s\tunsupported-remote\t%s\n' "$rel" "${last%%T*}" "$remote" "${license:-no-license}" "$proposed"
  elif ! is_owned_remote "$owner"; then
    printf 'skip\t%s\t%s\t%s\t%s\tnon-owned-remote:%s\t%s\n' "$rel" "${last%%T*}" "$remote" "${license:-no-license}" "$owner" "$proposed"
  elif [[ -z "$license" ]]; then
    printf 'needs-user-review\t%s\t%s\t%s\tno-license\tmissing-license\t%s\n' "$rel" "${last%%T*}" "$remote" "$proposed"
  else
    printf 'target\t%s\t%s\t%s\t%s\towned-foss\t%s\n' "$rel" "${last%%T*}" "$remote" "$license" "$proposed"
  fi
done

if [[ "$DRY_RUN" != 1 ]]; then
  echo "internal error: discovery script is read-only" >&2
  exit 1
fi
