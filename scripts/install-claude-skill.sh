#!/usr/bin/env bash
set -euo pipefail

readonly DEFAULT_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

REPO_ROOT="${DEFAULT_REPO_ROOT}"
INSTALL_HOME="${HOME}"

fail() {
  printf "med-autoscience claude-skill installer error: %s\n" "$1" >&2
  exit 1
}

usage() {
  cat >&2 <<'EOF'
Usage: install-claude-skill.sh [--repo-root /abs/path/to/repo] [--home /abs/path/to/home]

Installs the MedAutoScience Claude Code skill by symlinking
  <repo>/plugins/med-autoscience-claude/skills/med-autoscience/
into
  ~/.claude/skills/med-autoscience/

After installation, Claude Code will discover the skill automatically.
Restart Claude Code if it is already running.
EOF
}

parse_args() {
  while (($#)); do
    case "$1" in
      --repo-root)
        [[ $# -ge 2 ]] || fail "--repo-root requires a value"
        REPO_ROOT="$2"
        shift 2
        ;;
      --home)
        [[ $# -ge 2 ]] || fail "--home requires a value"
        INSTALL_HOME="$2"
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        fail "unknown argument: $1"
        ;;
    esac
  done
}

ensure_expected_symlink() {
  local link_path="$1"
  local target_path="$2"
  mkdir -p "$(dirname "${link_path}")"
  if [[ -L "${link_path}" ]]; then
    local existing_target
    existing_target="$(readlink -f "${link_path}")"
    local canonical_target
    canonical_target="$(cd "${target_path}" && pwd)"
    if [[ "${existing_target}" == "${canonical_target}" ]]; then
      return 0
    fi
    fail "refusing to replace existing symlink with a different target: ${link_path} -> ${existing_target}"
  fi
  if [[ -e "${link_path}" ]]; then
    fail "refusing to replace existing non-symlink path: ${link_path}"
  fi
  ln -s "${target_path}" "${link_path}"
}

main() {
  parse_args "$@"

  local repo_skill_dir="${REPO_ROOT}/plugins/med-autoscience-claude/skills/med-autoscience"
  local claude_skills_dir="${INSTALL_HOME}/.claude/skills/med-autoscience"

  [[ -d "${repo_skill_dir}" ]] || fail "skill directory not found: ${repo_skill_dir}"
  [[ -f "${repo_skill_dir}/SKILL.md" ]] || fail "SKILL.md not found in: ${repo_skill_dir}"

  ensure_expected_symlink "${claude_skills_dir}" "${repo_skill_dir}"

  printf "installed MedAutoScience Claude Code skill\n" >&2
  printf "  skill link : %s\n" "${claude_skills_dir}" >&2
  printf "  target     : %s\n" "${repo_skill_dir}" >&2
  printf "restart Claude Code so skill discovery picks up the new skill\n" >&2
}

main "$@"
