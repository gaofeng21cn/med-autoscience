#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

outdir=""
while [[ "$#" -gt 0 ]]; do
  case "${1}" in
    --outdir)
      if [[ "$#" -lt 2 ]]; then
        echo "run-build-clean.sh: --outdir requires a value" >&2
        exit 2
      fi
      outdir="${2}"
      shift 2
      ;;
    *)
      echo "Usage: scripts/run-build-clean.sh [--outdir PATH]" >&2
      exit 2
      ;;
  esac
done

tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/mas-build.XXXXXX")"
cleanup() {
  rm -rf "${tmp_root}"
}
trap cleanup EXIT

source_root="${tmp_root}/source"
build_outdir="${tmp_root}/dist"
mkdir -p "${source_root}" "${build_outdir}"

rsync -a \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '.worktree' \
  --exclude '.worktrees' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '*.egg-info' \
  --exclude 'build' \
  --exclude 'dist' \
  --exclude 'tmp' \
  "${repo_root}/" "${source_root}/"

MAS_CLEAN_RUNNER_TMP_ROOT="${tmp_root}/python" \
  "${repo_root}/scripts/run-python-clean.sh" -m build "${source_root}" --sdist --wheel --outdir "${build_outdir}"

if [[ -n "${outdir}" ]]; then
  mkdir -p "${outdir}"
  rsync -a "${build_outdir}/" "${outdir}/"
fi
