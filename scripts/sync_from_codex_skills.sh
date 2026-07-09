#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_root="${CODEX_HOME:-$HOME/.codex}/skills"
target_root="$repo_root/skills"
list_file="$repo_root/skills-to-archive.txt"

mkdir -p "$target_root"

while IFS= read -r raw_name || [[ -n "$raw_name" ]]; do
  skill_name="$(printf '%s' "$raw_name" | sed 's/[[:space:]]*#.*$//' | xargs)"
  [[ -z "$skill_name" ]] && continue

  case "$skill_name" in
    .*|*/*)
      echo "Refusing unsafe skill name: $skill_name" >&2
      exit 1
      ;;
  esac

  source_dir="$source_root/$skill_name"
  target_dir="$target_root/$skill_name"

  if [[ ! -d "$source_dir" ]]; then
    echo "Missing local skill: $source_dir" >&2
    exit 1
  fi
  if [[ ! -f "$source_dir/SKILL.md" ]]; then
    echo "Missing SKILL.md in: $source_dir" >&2
    exit 1
  fi

  rsync -a --delete \
    --exclude '.DS_Store' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude 'outputs/' \
    "$source_dir/" "$target_dir/"

  echo "Synced $skill_name"
done < "$list_file"
