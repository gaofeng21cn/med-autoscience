#!/usr/bin/env bash
set -euo pipefail

readonly DEFAULT_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="${DEFAULT_REPO_ROOT}"
INSTALL_HOME="${HOME}"
SKIP_TOOLS=0
PYTHON_BIN=""

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
  for cmd in bash; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
      fail "required command not found: ${cmd}"
    fi
  done
  PYTHON_BIN="$(resolve_python)" || fail "required command not found: python3.12 or python3"
}

python_works_with_install_home() {
  local candidate="$1"
  HOME="${INSTALL_HOME}" "${candidate}" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 12) else 1)
PY
}

resolve_python() {
  local candidate
  local candidates=()
  if [[ -n "${PYTHON:-}" ]]; then
    candidates+=("${PYTHON}")
  fi
  candidates+=(python3.12 python3)
  for candidate in "${candidates[@]}"; do
    if ! command -v "${candidate}" >/dev/null 2>&1; then
      continue
    fi
    candidate="$(command -v "${candidate}")"
    if python_works_with_install_home "${candidate}"; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

install_python_tools() {
  mkdir -p "${INSTALL_HOME}/.local/bin"
  write_clean_runner_entrypoint medautosci med_autoscience.cli
  write_clean_runner_entrypoint medautosci-mcp med_autoscience.mcp_server
  remove_stale_mas_cli_wrapper
}

write_clean_runner_entrypoint() {
  local name="$1"
  local module="$2"
  local script_path="${INSTALL_HOME}/.local/bin/${name}"
  local uv_entrypoint_path="${script_path}.uv-entrypoint"
  rm -f "${script_path}"
  rm -f "${uv_entrypoint_path}"
  cat >"${script_path}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
# med-autoscience clean runner wrapper: avoid repo-local virtualenv, bytecode, and editable metadata.
export MAS_CLEAN_RUNNER_ANALYSIS_EXTRA=1
exec "${REPO_ROOT}/scripts/run-python-clean.sh" -m "${module}" "\$@"
EOF
  chmod +x "${script_path}"
}

remove_stale_mas_cli_wrapper() {
  local script_path="${INSTALL_HOME}/.local/bin/mas"
  if [[ ! -e "${script_path}" && ! -L "${script_path}" ]]; then
    return 0
  fi
  if [[ -L "${script_path}" ]]; then
    rm -f "${script_path}"
    return 0
  fi
  if grep -q "med_autoscience.cli" "${script_path}" 2>/dev/null; then
    rm -f "${script_path}"
  fi
}

install_codex_paths() {
  HOME="${INSTALL_HOME}" PYTHONPATH="${REPO_ROOT}/src" "${PYTHON_BIN}" -m med_autoscience.codex_plugin_installer \
    --repo-root "${REPO_ROOT}" \
    --home "${INSTALL_HOME}"
}

main() {
  parse_args "$@"
  check_dependencies
  if [[ "${SKIP_TOOLS}" -eq 0 ]]; then
    install_python_tools
  else
    printf "skip tool installation; only validating MedAutoScience tracked Codex plugin source\n" >&2
  fi
  install_codex_paths
  printf "installed MedAutoScience CLI tools into %s and validated tracked Codex plugin source\n" "${INSTALL_HOME}" >&2
  printf "use OPL startup maintenance to register the OPL-owned Codex marketplace wrapper\n" >&2
}

main "$@"
