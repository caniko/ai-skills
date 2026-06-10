#!/usr/bin/env bash
set -euo pipefail

prefix=()
check_args=()
test_args=()
extra=()
all_targets=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefix)
      shift
      # shellcheck disable=SC2206
      prefix=($1)
      ;;
    --check)
      shift
      # shellcheck disable=SC2206
      check_args=($1)
      ;;
    --test)
      shift
      # shellcheck disable=SC2206
      test_args=($1)
      ;;
    --extra)
      shift
      extra+=("$1")
      ;;
    --all-targets)
      all_targets=(--all-targets)
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
  shift
done

run() {
  printf '+'
  printf ' %q' "${prefix[@]}" "$@"
  printf '\n'
  "${prefix[@]}" "$@"
}

run cargo fmt --check
run cargo clippy "${check_args[@]}" "${all_targets[@]}" -- -D warnings

if [[ ${#test_args[@]} -gt 0 ]]; then
  run cargo test "${test_args[@]}"
else
  run cargo test
fi

if [[ ${#check_args[@]} -gt 0 ]]; then
  run cargo check "${check_args[@]}"
fi

for cmd in "${extra[@]}"; do
  printf '+ %s\n' "$cmd"
  if [[ ${#prefix[@]} -gt 0 ]]; then
    "${prefix[@]}" bash -lc "$cmd"
  else
    bash -lc "$cmd"
  fi
done
