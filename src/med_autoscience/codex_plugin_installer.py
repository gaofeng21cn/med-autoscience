from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


PLUGIN_NAME = "mas"
MARKETPLACE_NAME = "mas-local"
MARKETPLACE_DISPLAY_NAME = "MAS Local"
PLUGIN_CATEGORY = "Research"
LEGACY_PLUGIN_NAMES = ("med-autoscience",)
LEGACY_TEST_SKILL_MARKERS = (
    "description: mas test skill",
    "# mas",
)


def _repo_plugin_root(repo_root: Path) -> Path:
    return repo_root / "plugins" / PLUGIN_NAME


def _repo_skill_root(repo_root: Path) -> Path:
    return _repo_plugin_root(repo_root) / "skills" / PLUGIN_NAME


def _repo_marketplace_path(repo_root: Path) -> Path:
    return repo_root / ".agents" / "plugins" / "marketplace.json"


def _user_plugin_root(home: Path) -> Path:
    return home / "plugins" / PLUGIN_NAME


def _user_skill_root(home: Path) -> Path:
    return home / ".agents" / "skills" / PLUGIN_NAME


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _ensure_expected_symlink(*, link_path: Path, target_path: Path) -> None:
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.is_symlink():
        if link_path.resolve() == target_path.resolve():
            return
        raise FileExistsError(f"Refusing to replace existing symlink with different target: {link_path}")
    if link_path.exists():
        raise FileExistsError(f"Refusing to replace existing non-symlink path: {link_path}")
    os.symlink(target_path, link_path)


def _remove_legacy_symlink(path: Path) -> None:
    if path.is_symlink():
        path.unlink()


def _remove_legacy_test_skill_stub(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        return
    skill_file = path / "SKILL.md"
    if not skill_file.is_file():
        return
    if any(item.name != "SKILL.md" for item in path.iterdir()):
        return
    content = skill_file.read_text(encoding="utf-8")
    if all(marker in content for marker in LEGACY_TEST_SKILL_MARKERS):
        skill_file.unlink()
        path.rmdir()


def _upsert_marketplace(*, marketplace_path: Path) -> None:
    payload = _load_json(marketplace_path)
    plugins = payload.get("plugins")
    if not isinstance(plugins, list):
        plugins = []

    plugin_entry = {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": f"./plugins/{PLUGIN_NAME}",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": PLUGIN_CATEGORY,
    }

    replaced = False
    normalized_plugins: list[dict[str, Any]] = []
    for item in plugins:
        if not isinstance(item, dict):
            continue
        if item.get("name") in LEGACY_PLUGIN_NAMES:
            continue
        if item.get("name") == PLUGIN_NAME:
            normalized_plugins.append(plugin_entry)
            replaced = True
        else:
            normalized_plugins.append(item)
    if not replaced:
        normalized_plugins.append(plugin_entry)

    normalized_payload: dict[str, Any] = {
        "name": str(payload.get("name") or MARKETPLACE_NAME),
        "interface": payload.get("interface") if isinstance(payload.get("interface"), dict) else {},
        "plugins": normalized_plugins,
    }
    if not normalized_payload["interface"].get("displayName"):
        normalized_payload["interface"]["displayName"] = MARKETPLACE_DISPLAY_NAME
    _write_json(marketplace_path, normalized_payload)


def install_repo_local_codex_plugin(*, repo_root: Path, home: Path | None = None) -> dict[str, str]:
    resolved_repo_root = repo_root.expanduser().resolve()
    resolved_home = (home or Path.home()).expanduser().resolve()

    repo_plugin_root = _repo_plugin_root(resolved_repo_root)
    repo_skill_root = _repo_skill_root(resolved_repo_root)
    if not repo_plugin_root.is_dir():
        raise FileNotFoundError(f"Plugin root not found: {repo_plugin_root}")
    if not repo_skill_root.is_dir():
        raise FileNotFoundError(f"Plugin skill root not found: {repo_skill_root}")

    marketplace_path = _repo_marketplace_path(resolved_repo_root)

    for legacy_name in LEGACY_PLUGIN_NAMES:
        _remove_legacy_symlink(resolved_home / "plugins" / legacy_name)
        _remove_legacy_symlink(resolved_home / ".agents" / "skills" / legacy_name)
    _remove_legacy_symlink(_user_plugin_root(resolved_home))
    _remove_legacy_symlink(_user_skill_root(resolved_home))
    _remove_legacy_test_skill_stub(resolved_home / ".codex" / "skills" / PLUGIN_NAME)

    _upsert_marketplace(marketplace_path=marketplace_path)

    return {
        "repo_root": str(resolved_repo_root),
        "home": str(resolved_home),
        "plugin_root": str(repo_plugin_root),
        "skill_root": str(repo_skill_root),
        "marketplace_path": str(marketplace_path),
    }


def install_home_local_codex_plugin(*, repo_root: Path, home: Path | None = None) -> dict[str, str]:
    return install_repo_local_codex_plugin(repo_root=repo_root, home=home)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--home")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = install_repo_local_codex_plugin(
        repo_root=Path(args.repo_root),
        home=Path(args.home) if args.home else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
