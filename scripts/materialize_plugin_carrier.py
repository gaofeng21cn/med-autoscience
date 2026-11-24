#!/usr/bin/env python3
"""Project tracked MAS owner resources into the self-contained native carrier via Framework CLI."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def resolve_opl_bin() -> str:
    env_bin = os.environ.get("OPL_BIN", "").strip()
    if env_bin:
        return env_bin
    fw_root = os.environ.get("OPL_FRAMEWORK_ROOT", "").strip()
    if fw_root:
        candidate = Path(fw_root) / "bin" / "opl"
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    sibling = ROOT.parent / "one-person-lab" / "bin" / "opl"
    if sibling.is_file() and os.access(sibling, os.X_OK):
        return str(sibling)
    found = shutil.which("opl")
    if found:
        return found
    raise SystemExit("OPL CLI is unavailable; set OPL_BIN or OPL_FRAMEWORK_ROOT.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check projection bytes without writing files.")
    args = parser.parse_args()
    cmd = [resolve_opl_bin(), "pack", "project-carrier", "--repo", str(ROOT), "--json"]
    if args.check:
        cmd.append("--check")
    return subprocess.run(cmd, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
