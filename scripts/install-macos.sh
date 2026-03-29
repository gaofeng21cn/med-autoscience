#!/usr/bin/env bash
set -euo pipefail

readonly RELEASE_VERSION="0.1.0a1"
readonly WHEEL_FILENAME="med_autoscience-0.1.0a1-py3-none-any.whl"
readonly RELEASE_BASE_URL="https://github.com/gaofeng/med-autoscience/releases/download/v0.1.0a1"
readonly LOCAL_BIN_DIR="${HOME}/.local/bin"
readonly UV_INSTALL_SCRIPT_URL="https://astral.sh/uv/install.sh"

fail() {
  printf "med-autoscience installer error: %s\n" "$1" >&2
  exit 1
}

check_platform() {
  local os_name
  local arch
  os_name="$(uname -s)"
  arch="$(uname -m)"

  if [[ "${os_name}" != "Darwin" ]]; then
    fail "this installer only supports macOS (Darwin), got ${os_name}"
  fi

  case "${arch}" in
    arm64|x86_64) ;;
    *)
      fail "unsupported macOS architecture: ${arch} (expected arm64 or x86_64)"
      ;;
  esac
}

check_dependencies() {
  local cmd
  for cmd in curl tar bash; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
      fail "required command not found: ${cmd}"
    fi
  done
}

ensure_uv() {
  mkdir -p "${LOCAL_BIN_DIR}"
  if ! command -v uv >/dev/null 2>&1; then
    printf "uv not found; installing to %s\n" "${LOCAL_BIN_DIR}" >&2
    curl -fsSL "${UV_INSTALL_SCRIPT_URL}" | env UV_INSTALL_DIR="${HOME}/.local/bin" sh
  fi

  if ! command -v uv >/dev/null 2>&1; then
    export PATH="${HOME}/.local/bin:${PATH}"
  fi

  if ! command -v uv >/dev/null 2>&1; then
    fail "uv installation failed or uv is not on PATH"
  fi
}

install_release_wheel() {
  local tmp_dir
  local wheel_url
  local wheel_path
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "${tmp_dir}"' EXIT

  wheel_url="${RELEASE_BASE_URL}/${WHEEL_FILENAME}"
  wheel_path="${tmp_dir}/${WHEEL_FILENAME}"

  printf "downloading %s\n" "${wheel_url}" >&2
  curl -fL "${wheel_url}" -o "${wheel_path}"

  mkdir -p "${LOCAL_BIN_DIR}"
  UV_TOOL_BIN_DIR="${HOME}/.local/bin" uv tool install \
    --managed-python \
    --python 3.12 \
    --force \
    "${wheel_path}"
}

main() {
  check_platform
  check_dependencies
  ensure_uv
  install_release_wheel
  printf "installed med-autoscience %s; binaries are in %s\n" "${RELEASE_VERSION}" "${LOCAL_BIN_DIR}" >&2
  printf "Add ~/.local/bin to your PATH if medautosci is not found:\n" >&2
  printf "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zprofile\n" >&2
}

main "$@"
