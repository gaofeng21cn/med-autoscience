from __future__ import annotations

from pathlib import Path
from shutil import copy2

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.sdist import sdist as _sdist


PROJECT_ROOT = Path(__file__).resolve().parent
STAGE_ROUTE_CONTRACT_SOURCE_PATH = Path("agent/stages/stage_route_contract.yaml")
STAGE_ROUTE_CONTRACT_RESOURCE_PATH = Path("src/med_autoscience/resources/stage_route_contract.yaml")


def _copy_file(source_path: Path, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    copy2(source_path, target_path)


def _project_stage_route_contract(source_root: Path, target_path: Path) -> None:
    source_path = source_root / STAGE_ROUTE_CONTRACT_SOURCE_PATH
    if not source_path.is_file():
        source_path = source_root / STAGE_ROUTE_CONTRACT_RESOURCE_PATH
    if not source_path.is_file():
        raise RuntimeError(
            "missing stage route contract source: "
            f"{source_root / STAGE_ROUTE_CONTRACT_SOURCE_PATH} or {source_root / STAGE_ROUTE_CONTRACT_RESOURCE_PATH}"
        )
    _copy_file(source_path, target_path)


class build_py(_build_py):
    def run(self) -> None:
        super().run()
        _project_stage_route_contract(
            PROJECT_ROOT,
            Path(self.build_lib) / "med_autoscience" / "resources" / "stage_route_contract.yaml",
        )


class sdist(_sdist):
    def make_release_tree(self, base_dir: str, files: list[str]) -> None:
        super().make_release_tree(base_dir, files)
        release_root = Path(base_dir)
        _project_stage_route_contract(release_root, release_root / STAGE_ROUTE_CONTRACT_RESOURCE_PATH)


setup(cmdclass={"build_py": build_py, "sdist": sdist})
