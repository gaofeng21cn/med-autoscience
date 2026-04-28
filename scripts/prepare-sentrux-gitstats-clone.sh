#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/prepare-sentrux-gitstats-clone.sh [--repo-root PATH] [--tmp-root PATH] [--path-only]

Create a temporary shared clone that is safe to pass to Sentrux MCP git_stats
when the source repository keeps worktree.useRelativePaths enabled.

Options:
  --repo-root PATH  Source repository or worktree path. Defaults to the current Git top-level.
  --tmp-root PATH   Directory under which the temporary clone parent is created.
  --path-only       Print only the prepared clone path.
  -h, --help        Show this help.
USAGE
}

repo_root_arg=""
tmp_root_arg=""
path_only=0
tmp_root=""
clone_ready=0

cleanup_on_error() {
  if [[ "${clone_ready}" -eq 0 && -n "${tmp_root}" && -d "${tmp_root}" ]]; then
    rm -rf "${tmp_root}"
  fi
}

trap cleanup_on_error EXIT

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      if [[ $# -lt 2 ]]; then
        echo "prepare-sentrux-gitstats-clone: --repo-root requires a path" >&2
        exit 2
      fi
      repo_root_arg="$2"
      shift 2
      ;;
    --tmp-root)
      if [[ $# -lt 2 ]]; then
        echo "prepare-sentrux-gitstats-clone: --tmp-root requires a path" >&2
        exit 2
      fi
      tmp_root_arg="$2"
      shift 2
      ;;
    --path-only)
      path_only=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "prepare-sentrux-gitstats-clone: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${repo_root_arg}" ]]; then
  repo_root_arg="$(git rev-parse --show-toplevel)"
fi

repo_root="$(git -C "${repo_root_arg}" rev-parse --show-toplevel)"
source_head="$(git -C "${repo_root}" rev-parse HEAD)"
source_dirty=0
if ! git -C "${repo_root}" diff --quiet --ignore-submodules --; then
  source_dirty=1
fi
if ! git -C "${repo_root}" diff --cached --quiet --ignore-submodules --; then
  source_dirty=1
fi

if [[ -n "${tmp_root_arg}" ]]; then
  mkdir -p "${tmp_root_arg}"
  tmp_parent="$(cd "${tmp_root_arg}" && pwd -P)"
  tmp_root="$(mktemp -d "${tmp_parent%/}/mas-sentrux-gitstats.XXXXXX")"
else
  tmp_parent="${TMPDIR:-/tmp}"
  tmp_root="$(mktemp -d "${tmp_parent%/}/mas-sentrux-gitstats.XXXXXX")"
fi

clone_path="${tmp_root}/repo"
git clone --quiet --shared --no-checkout "${repo_root}" "${clone_path}"
git -C "${clone_path}" checkout --quiet --detach "${source_head}"

if git -C "${clone_path}" config --local --get extensions.relativeWorktrees >/dev/null 2>&1; then
  echo "prepare-sentrux-gitstats-clone: compatible clone unexpectedly inherited extensions.relativeWorktrees" >&2
  exit 1
fi

repo_format="$(git -C "${clone_path}" config --local --get core.repositoryformatversion || true)"
clone_ready=1

if [[ "${path_only}" -eq 1 ]]; then
  printf '%s\n' "${clone_path}"
  exit 0
fi

if [[ "${source_dirty}" -eq 1 ]]; then
  echo "warning=source_worktree_has_uncommitted_changes_not_in_clone" >&2
fi

cleanup_target="$(printf '%q' "${tmp_root}")"
cat <<OUTPUT
sentrux_git_stats_clone=${clone_path}
source_repo=${repo_root}
source_head=${source_head}
core_repositoryformatversion=${repo_format:-unset}
extensions_relativeWorktrees=absent
cleanup_command=rm -rf ${cleanup_target}
mcp_usage=scan sentrux_git_stats_clone with Sentrux MCP, then run git_stats against that scan.
OUTPUT
