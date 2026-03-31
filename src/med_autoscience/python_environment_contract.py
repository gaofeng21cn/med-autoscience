from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement
from packaging.version import InvalidVersion, Version


def _resolve_repo_root(*, module_file: Path | None = None) -> Path:
    candidate = (module_file or Path(__file__)).resolve().parents[2]
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=candidate,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return candidate
    if completed.returncode != 0:
        return candidate
    common_dir = Path(completed.stdout.strip())
    if not common_dir.is_absolute():
        return candidate
    if common_dir.name == ".git":
        return common_dir.parent
    return common_dir


REPO_ROOT = _resolve_repo_root()
MANAGED_RUNTIME_PREFIX = (REPO_ROOT / ".venv").resolve()
REQUIRED_RUNTIME_REQUIREMENTS = ("matplotlib>=3.9", "pandas>=2.2")
CURATED_PYTHON_ANALYSIS_BUNDLE_REQUIREMENTS = (
    "matplotlib>=3.9",
    "pandas>=2.2",
    "numpy>=1.26",
    "scipy>=1.13",
    "scikit-learn>=1.5",
    "statsmodels>=0.14",
    "lifelines>=0.30",
    "seaborn>=0.13",
    "openpyxl>=3.1",
    "python-docx>=1.1",
    "pillow>=10.0",
    "pypdf>=5.0",
)
_DEFAULT_REQUIREMENTS = tuple(Requirement(requirement) for requirement in REQUIRED_RUNTIME_REQUIREMENTS)
REQUIRED_RUNTIME_MODULES = tuple(requirement.name for requirement in _DEFAULT_REQUIREMENTS)
REQUIREMENT_IMPORT_NAME_MAP = {
    "scikit-learn": "sklearn",
    "python-docx": "docx",
    "pillow": "PIL",
}


def _collect_check_issues(checks: dict[str, bool], *, prefix: str) -> list[str]:
    return [f"{prefix}.{name}" for name, ok in checks.items() if not ok]


def _normalize_requirements(
    requirements: tuple[str, ...] | list[str] | None,
) -> tuple[Requirement, ...]:
    raw_requirements = REQUIRED_RUNTIME_REQUIREMENTS if requirements is None else tuple(requirements)
    return tuple(Requirement(requirement) for requirement in raw_requirements)


def _resolve_import_name(requirement: Requirement) -> str:
    return REQUIREMENT_IMPORT_NAME_MAP.get(requirement.name, requirement.name)


def inspect_python_environment_contract(
    *,
    requirements: tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    normalized_requirements = _normalize_requirements(requirements)
    checks: dict[str, bool] = {}
    modules: dict[str, dict[str, str | None]] = {}
    missing_requirements: list[str] = []
    for requirement in normalized_requirements:
        requirement_name = requirement.name
        import_name = _resolve_import_name(requirement)
        check_import = f"{requirement_name}_importable"
        check_version = f"{requirement_name}_version_satisfied"
        version: str | None = None
        importable = False
        version_satisfied = False
        try:
            module = importlib.import_module(import_name)
            importable = True
            raw_version = getattr(module, "__version__", None)
            if raw_version is not None:
                version = str(raw_version)
                try:
                    version_obj = Version(version)
                    version_satisfied = requirement.specifier.contains(version_obj, prereleases=True)
                except InvalidVersion:
                    version_satisfied = False
        except ImportError:
            pass
        checks[check_import] = importable
        checks[check_version] = version_satisfied
        modules[requirement_name] = {"version": version, "import_name": import_name}
        if not (importable and version_satisfied):
            missing_requirements.append(str(requirement))

    issues = _collect_check_issues(checks, prefix="python_environment")
    ready = all(checks.values())
    return {
        "ready": ready,
        "checks": checks,
        "issues": issues,
        "modules": modules,
        "interpreter": sys.executable,
        "requirements": [str(requirement) for requirement in normalized_requirements],
        "missing_requirements": missing_requirements,
    }


def _is_managed_runtime() -> bool:
    try:
        return Path(sys.prefix).resolve() == MANAGED_RUNTIME_PREFIX
    except OSError:
        return False


def ensure_python_environment_contract(
    *,
    requirements: tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    before = inspect_python_environment_contract(requirements=requirements)

    if not _is_managed_runtime():
        message = (
            "Current interpreter is not the repo-managed runtime at `.venv`. "
            "Please run the contract under the repo `.venv` or via `rtk uv run ...` before calling this function."
        )
        return {
            "action": "managed_runtime_required",
            "before": before,
            "after": before,
            "exit_code": None,
            "stdout": "",
            "stderr": message,
        }

    if before["ready"]:
        return {"action": "already_ready", "before": before, "after": before}

    missing_requirements = [str(item) for item in before["missing_requirements"]]
    completed = subprocess.run(
        ["uv", "pip", "install", "--python", sys.executable, *missing_requirements],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    importlib.invalidate_caches()
    after = inspect_python_environment_contract(requirements=requirements)
    return {
        "action": "uv_pip_install",
        "before": before,
        "after": after,
        "requested_requirements": before["requirements"],
        "missing_requirements": missing_requirements,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
