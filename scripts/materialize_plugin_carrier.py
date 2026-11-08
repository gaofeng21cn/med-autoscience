#!/usr/bin/env python3
"""Project tracked MAS owner resources into the self-contained native carrier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tomllib


ROOT = Path(__file__).resolve().parents[1]
CARRIER = ROOT / "plugins/med-autoscience"
RESOURCE_ROOTS = ("agent", "contracts", "src", "docs", "profiles", "runtime", "assets", "bootstrap")
RESOURCE_FILES = ("LICENSE", "README.md", "README.zh-CN.md", "pyproject.toml", "uv.lock", "MANIFEST.in", ".python-version")
SOURCE_ONLY_PREFIXES = ("docs/history/", "docs/site/")


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check projection bytes without writing files.")
    args = parser.parse_args()
    owner_path = ROOT / "contracts/opl_agent_package_manifest.json"
    owner = json.loads(owner_path.read_text())
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    locked = next(package for package in lock["package"] if package["name"] == project["name"])
    if owner["version"] != project["version"] or owner["version"] != locked["version"]:
        raise ValueError("Owner, Python project and uv lock versions must match before projection.")

    tracked = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=ROOT)
    expected: dict[Path, tuple[bytes, int]] = {}
    for entry in tracked.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        relative = raw_path.decode()
        if relative.split("/", 1)[0] not in RESOURCE_ROOTS and relative not in RESOURCE_FILES:
            continue
        if relative.startswith(SOURCE_ONLY_PREFIXES):
            continue
        mode, _object_id, stage = metadata.split()
        if mode not in (b"100644", b"100755") or stage != b"0":
            raise ValueError(f"Owner resource must be an unconflicted regular file: {relative}")
        source = ROOT / relative
        if source.is_symlink():
            raise ValueError(f"Owner resource must not be a symlink: {relative}")
        expected[CARRIER / relative] = (source.read_bytes(), int(mode, 8) & 0o777)

    expected[ROOT / "opl-package.json"] = (owner_path.read_bytes(), 0o644)
    descriptor = {key: value for key, value in owner.items() if key not in ("schema_ref", "machine_boundary")}
    expected[CARRIER / "opl-package.json"] = (json_bytes(descriptor), 0o644)
    for relative in (".codex-plugin/plugin.json", "plugins/med-autoscience/.codex-plugin/plugin.json", "plugins/med-autoscience/plugin.json"):
        target = ROOT / relative
        plugin = json.loads(target.read_text())
        plugin["version"] = owner["version"]
        expected[target] = (json_bytes(plugin), 0o644)
    for source, target in (
        ("agent/primary_skill/SKILL.md", "skills/med-autoscience/SKILL.md"),
        ("app-contribution-adapter.json", "app-contribution-adapter.json"),
    ):
        expected[CARRIER / target] = ((ROOT / source).read_bytes(), 0o644)

    stale = {
        item for name in RESOURCE_ROOTS for item in (CARRIER / name).rglob("*")
        if item.is_file() and item not in expected
        # These two carrier-owned icons predate the owner resource projection.
        and item.relative_to(CARRIER).as_posix() not in ("assets/icon.png", "assets/icon.svg")
    }
    changed = []
    for target, (data, mode) in expected.items():
        if target.is_symlink():
            raise ValueError(f"Carrier projection target must not be a symlink: {target}")
        if target.is_file() and target.read_bytes() == data and target.stat().st_mode & 0o777 == mode:
            continue
        changed.append(target.relative_to(ROOT).as_posix())
        if not args.check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(mode)
    if not args.check:
        for target in stale:
            target.unlink()
    print(json.dumps({"version": owner["version"], "projected_files": len(expected), "changed": len(changed), "stale": len(stale), "check": args.check}))
    return 1 if args.check and (changed or stale) else 0


if __name__ == "__main__":
    raise SystemExit(main())
