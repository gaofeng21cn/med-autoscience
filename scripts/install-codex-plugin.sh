#!/usr/bin/env bash
set -euo pipefail

readonly DEFAULT_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly LOCAL_BIN_DIR="${HOME}/.local/bin"
readonly UV_INSTALL_SCRIPT_URL="https://astral.sh/uv/install.sh"

REPO_ROOT="${DEFAULT_REPO_ROOT}"
INSTALL_HOME="${HOME}"
SKIP_TOOLS=0

fail() {
  printf "med-autoscience codex installer error: %s\n" "$1" >&2
  exit 1
}

usage() {
  cat >&2 <<'EOF'
Usage: install-codex-plugin.sh [--repo-root /abs/path/to/repo] [--home /abs/path/to/home] [--skip-tools]
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
      --skip-tools)
        SKIP_TOOLS=1
        shift
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

check_dependencies() {
  local cmd
  for cmd in bash python3; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
      fail "required command not found: ${cmd}"
    fi
  done
}

ensure_uv() {
  mkdir -p "${INSTALL_HOME}/.local/bin"
  if ! command -v uv >/dev/null 2>&1; then
    printf "uv not found; installing to %s\n" "${INSTALL_HOME}/.local/bin" >&2
    curl -fsSL "${UV_INSTALL_SCRIPT_URL}" | env UV_INSTALL_DIR="${INSTALL_HOME}/.local/bin" sh
    export PATH="${INSTALL_HOME}/.local/bin:${PATH}"
  fi
  if ! command -v uv >/dev/null 2>&1; then
    fail "uv installation failed or uv is not on PATH"
  fi
}

install_python_tools() {
  mkdir -p "${INSTALL_HOME}/.local/bin"
  HOME="${INSTALL_HOME}" UV_TOOL_BIN_DIR="${INSTALL_HOME}/.local/bin" uv tool install \
    --managed-python \
    --python 3.12 \
    --force \
    --editable \
    "${REPO_ROOT}"
}

install_codex_paths() {
  HOME="${INSTALL_HOME}" PYTHONPATH="${REPO_ROOT}/src" python3 -m med_autoscience.codex_plugin_installer \
    --repo-root "${REPO_ROOT}" \
    --home "${INSTALL_HOME}"
}

main() {
  parse_args "$@"
  check_dependencies
  if [[ "${SKIP_TOOLS}" -eq 0 ]]; then
    ensure_uv
    install_python_tools
  else
    printf "skip tool installation; only syncing MedAutoScience Codex plugin paths into %s\n" "${INSTALL_HOME}" >&2
  fi
  install_codex_paths
  printf "installed MedAutoScience Codex integration into %s\n" "${INSTALL_HOME}" >&2
  printf "restart Codex so native skill discovery and plugin metadata are reloaded\n" >&2
}

main "$@"
