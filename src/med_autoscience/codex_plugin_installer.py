from __future__ import annotations

import argparse
import json
from pathlib import Path


PLUGIN_NAME = "mas"
LEGACY_PLUGIN_NAMES = ("med-autoscience",)
LEGACY_TEST_SKILL_MARKERS = (
    "description: mas test skill",
    "# mas",
)


def _repo_plugin_root(repo_root: Path) -> Path:
    return repo_root / "plugins" / PLUGIN_NAME


def _repo_skill_root(repo_root: Path) -> Path:
    return _repo_plugin_root(repo_root) / "skills" / PLUGIN_NAME


def _repo_plugin_manifest_path(repo_root: Path) -> Path:
    return _repo_plugin_root(repo_root) / ".codex-plugin" / "plugin.json"


def _repo_marketplace_path(repo_root: Path) -> Path:
    return repo_root / ".agents" / "plugins" / "marketplace.json"


def _user_plugin_root(home: Path) -> Path:
    return home / "plugins" / PLUGIN_NAME


def _user_skill_root(home: Path) -> Path:
    return home / ".agents" / "skills" / PLUGIN_NAME


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


def _remove_repo_local_marketplace(marketplace_path: Path) -> bool:
    if not marketplace_path.exists() and not marketplace_path.is_symlink():
        return False
    if marketplace_path.is_dir():
        raise IsADirectoryError(f"Refusing to remove marketplace directory: {marketplace_path}")
    marketplace_path.unlink()
    return True


def install_repo_local_codex_plugin(*, repo_root: Path, home: Path | None = None) -> dict[str, str]:
    resolved_repo_root = repo_root.expanduser().resolve()
    resolved_home = (home or Path.home()).expanduser().resolve()

    repo_plugin_root = _repo_plugin_root(resolved_repo_root)
    repo_skill_root = _repo_skill_root(resolved_repo_root)
    repo_plugin_manifest_path = _repo_plugin_manifest_path(resolved_repo_root)
    repo_skill_path = repo_skill_root / "SKILL.md"
    if not repo_plugin_root.is_dir():
        raise FileNotFoundError(f"Plugin root not found: {repo_plugin_root}")
    if not repo_skill_root.is_dir():
        raise FileNotFoundError(f"Plugin skill root not found: {repo_skill_root}")
    if not repo_plugin_manifest_path.is_file():
        raise FileNotFoundError(f"Plugin manifest not found: {repo_plugin_manifest_path}")
    if not repo_skill_path.is_file():
        raise FileNotFoundError(f"Plugin skill file not found: {repo_skill_path}")

    for legacy_name in LEGACY_PLUGIN_NAMES:
        _remove_legacy_symlink(resolved_home / "plugins" / legacy_name)
        _remove_legacy_symlink(resolved_home / ".agents" / "skills" / legacy_name)
    _remove_legacy_symlink(_user_plugin_root(resolved_home))
    _remove_legacy_symlink(_user_skill_root(resolved_home))
    _remove_legacy_test_skill_stub(resolved_home / ".codex" / "skills" / PLUGIN_NAME)
    marketplace_path = _repo_marketplace_path(resolved_repo_root)
    repo_local_marketplace_removed = _remove_repo_local_marketplace(marketplace_path)

    return {
        "repo_root": str(resolved_repo_root),
        "home": str(resolved_home),
        "plugin_root": str(repo_plugin_root),
        "skill_root": str(repo_skill_root),
        "plugin_manifest_path": str(repo_plugin_manifest_path),
        "skill_path": str(repo_skill_path),
        "marketplace_path": str(marketplace_path),
        "repo_local_marketplace_written": "false",
        "repo_local_marketplace_removed": str(repo_local_marketplace_removed).lower(),
        "codex_marketplace_owner": "opl_owned_wrapper",
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
