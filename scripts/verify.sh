#!/usr/bin/env bash
set -euo pipefail

lane="${1:-}"

if [[ -z "${lane}" ]]; then
  make test-fast
  exit 0
fi

if [[ "${lane}" == "fast" ]]; then
  make test-fast
  exit 0
fi

if [[ "${lane}" == "meta" ]]; then
  make test-meta
  exit 0
fi

if [[ "${lane}" == "display" ]]; then
  make test-display
  exit 0
fi

if [[ "${lane}" == "full" ]]; then
  make test-full
  exit 0
fi

echo "Usage: scripts/verify.sh [fast|meta|display|full]" >&2
exit 1
