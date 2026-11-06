#!/usr/bin/env bash
#
# sync-skills.sh — render the canonical skills/ tree for DeepSeek Harness.
#
# The canonical tree in skills/ is the source of truth and stays Codex-flavoured.
# This script renders a DSH-flavoured copy that DeepSeek Harness can load:
# valid frontmatter, a description that fits the catalog without losing its
# scope clause, and no Codex-only artifacts.
#
# Usage:
#   scripts/sync-skills.sh                 # render into .dsh/skills
#   scripts/sync-skills.sh --install       # also install into ~/.dsh/skills
#   scripts/sync-skills.sh --check         # validate only
#   scripts/sync-skills.sh --target codex # render a named agent target
#   scripts/sync-skills.sh --help
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"

usage() {
  sed -n '3,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

main() {
  local args=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
        usage
        return 0
        ;;
      *)
        args+=("$1")
        shift
        ;;
    esac
  done

  # ${args[@]+...} keeps an empty array safe under `set -u` on bash 3.2.
  if [[ ${#args[@]} -gt 0 ]]; then
    "$PYTHON" "$REPO_ROOT/scripts/sync_skills.py" "${args[@]}"
  else
    "$PYTHON" "$REPO_ROOT/scripts/sync_skills.py"
  fi
  "$PYTHON" "$REPO_ROOT/scripts/validate_dsh_skills.py" "$REPO_ROOT/.dsh/skills"
  "$PYTHON" "$REPO_ROOT/scripts/generate_skill_index.py"
}

main "$@"
