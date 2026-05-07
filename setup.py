from __future__ import annotations

from pathlib import Path
from shutil import copy2, rmtree

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.sdist import sdist as _sdist


PROJECT_ROOT = Path(__file__).resolve().parent
RESOURCE_PROJECTION_PATH = Path("src/med_autoscience/resources/display_pack_repo")
DISPLAY_PACK_CONFIG_PATH = Path("config/display_packs.toml")
DISPLAY_PACKS_ROOT = Path("display-packs")
IGNORED_DIR_NAMES = frozenset((".git", ".hg", ".svn", "__pycache__"))
IGNORED_FILE_SUFFIXES = frozenset((".pyc", ".pyo"))


def _should_copy(path: Path) -> bool:
    if any(part in IGNORED_DIR_NAMES for part in path.parts):
        return False
    if path.name == ".DS_Store":
        return False
    return path.suffix not in IGNORED_FILE_SUFFIXES


def _copy_file(source_path: Path, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    copy2(source_path, target_path)


def _copy_tree(source_root: Path, target_root: Path) -> None:
    if not source_root.is_dir():
        raise RuntimeError(f"missing display-pack source directory: {source_root}")
    for source_path in sorted(source_root.rglob("*")):
        if not source_path.is_file() or not _should_copy(source_path.relative_to(source_root)):
            continue
        _copy_file(source_path, target_root / source_path.relative_to(source_root))


def _project_display_pack_repo(source_root: Path, target_root: Path) -> None:
    config_path = source_root / DISPLAY_PACK_CONFIG_PATH
    packs_root = source_root / DISPLAY_PACKS_ROOT
    if not config_path.is_file():
        raise RuntimeError(f"missing display-pack config source: {config_path}")
    if target_root.exists():
        rmtree(target_root)
    _copy_file(config_path, target_root / "config" / "display_packs.toml")
    _copy_tree(packs_root, target_root / "display-packs")


class build_py(_build_py):
    def run(self) -> None:
        super().run()
        target_root = Path(self.build_lib) / "med_autoscience" / "resources" / "display_pack_repo"
        _project_display_pack_repo(PROJECT_ROOT, target_root)


class sdist(_sdist):
    def make_release_tree(self, base_dir: str, files: list[str]) -> None:
        super().make_release_tree(base_dir, files)
        release_root = Path(base_dir)
        _project_display_pack_repo(release_root, release_root / RESOURCE_PROJECTION_PATH)


setup(cmdclass={"build_py": build_py, "sdist": sdist})
