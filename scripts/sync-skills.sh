#!/usr/bin/env bash
#
# sync-skills.sh — render canonical skills for configured agent targets.
#
# The canonical tree in skills/ is the source of truth. This wrapper dispatches
# the Parse -> IR -> Render pipeline; generated target trees are never edited.
#
# Usage:
#   scripts/sync-skills.sh                    # render DSH + validate/index
#   scripts/sync-skills.sh --target all       # render every configured target
#   scripts/sync-skills.sh --target cursor    # render one target
#   scripts/sync-skills.sh --install          # install selected target
#   scripts/sync-skills.sh --install --install-deps   # npm install for installed skills
#   scripts/sync-skills.sh --check            # parse canonical skills only
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
  # DSH validation/indexing applies only to the DSH target.
  local target="dsh"
  local index=0
  while [[ $index -lt ${#args[@]} ]]; do
    if [[ "${args[$index]}" == "--target" && $((index + 1)) -lt ${#args[@]} ]]; then
      target="${args[$((index + 1))]}"
    fi
    index=$((index + 1))
  done
  if [[ "$target" == "dsh" || "$target" == "all" ]]; then
    "$PYTHON" "$REPO_ROOT/scripts/validate_dsh_skills.py" "$REPO_ROOT/.dsh/skills"
    "$PYTHON" "$REPO_ROOT/scripts/generate_skill_index.py"
  fi
}

main "$@"
