#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from med_autoscience.controllers.workspace_entry_rendering import materialize_workspace_entries  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize workspace-local aliases to the canonical MAS domain entry."
    )
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    payload = materialize_workspace_entries(
        workspace_root=args.workspace_root,
        profile_ref=args.profile,
        repo_root=REPO_ROOT,
        dry_run=args.dry_run,
        force=args.force,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if payload["blocked_files"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
