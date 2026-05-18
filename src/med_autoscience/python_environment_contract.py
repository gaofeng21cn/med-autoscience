from __future__ import annotations

import importlib
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _is_uv_tool_runtime_root(path: Path) -> bool:
    receipt = path / "uv-receipt.toml"
    pyvenv_cfg = path / "pyvenv.cfg"
    if not receipt.is_file() or not pyvenv_cfg.is_file():
        return False
    try:
        receipt_text = receipt.read_text(encoding="utf-8")
    except OSError:
        return False
    return "med-autoscience" in receipt_text


def _resolve_uv_tool_runtime_root(*, module_file: Path | None = None) -> Path | None:
    resolved = (module_file or Path(__file__)).resolve()
    for parent in resolved.parents:
        if _is_uv_tool_runtime_root(parent):
            return parent
    return None


def _current_uv_tool_runtime_root() -> Path | None:
    try:
        prefix = Path(sys.prefix).resolve()
    except OSError:
        return None
    if _is_uv_tool_runtime_root(prefix):
        return prefix
    return None


def _resolve_repo_root(*, module_file: Path | None = None) -> Path:
    candidate = (module_file or Path(__file__)).resolve().parents[2]
    uv_tool_root = _resolve_uv_tool_runtime_root(module_file=module_file)
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=candidate,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return uv_tool_root or candidate
    if completed.returncode != 0:
        return uv_tool_root or candidate
    common_dir = Path(completed.stdout.strip())
    if not common_dir.is_absolute():
        return uv_tool_root or candidate
    if common_dir.name == ".git":
        return common_dir.parent
    return common_dir


def _resolve_checkout_root(*, module_file: Path | None = None) -> Path:
    candidate = (module_file or Path(__file__)).resolve().parents[2]
    uv_tool_root = _resolve_uv_tool_runtime_root(module_file=module_file)
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=candidate,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return uv_tool_root or candidate
    if completed.returncode != 0:
        return uv_tool_root or candidate
    checkout_root = Path(completed.stdout.strip())
    if not checkout_root.is_absolute():
        return uv_tool_root or candidate
    return checkout_root


REPO_ROOT = _resolve_repo_root()
CHECKOUT_ROOT = _resolve_checkout_root()
MANAGED_RUNTIME_PREFIX = (REPO_ROOT / ".venv").resolve()
CHECKOUT_MANAGED_RUNTIME_PREFIX = (CHECKOUT_ROOT / ".venv").resolve()
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
REQUIREMENT_IMPORT_NAME_MAP = {
    "scikit-learn": "sklearn",
    "python-docx": "docx",
    "pillow": "PIL",
}


@dataclass(frozen=True)
class RuntimeRequirement:
    name: str
    minimum_version: tuple[int, ...] | None
    raw: str


def _parse_version_parts(value: str) -> tuple[int, ...] | None:
    parts: list[int] = []
    for raw_part in value.split("."):
        numeric = ""
        for char in raw_part:
            if not char.isdigit():
                break
            numeric += char
        if numeric == "":
            return None
        parts.append(int(numeric))
    return tuple(parts)


def _parse_requirement(requirement: str) -> RuntimeRequirement:
    if ">=" not in requirement:
        return RuntimeRequirement(name=requirement.strip(), minimum_version=None, raw=requirement.strip())
    name, raw_minimum = requirement.split(">=", 1)
    return RuntimeRequirement(
        name=name.strip(),
        minimum_version=_parse_version_parts(raw_minimum.strip()),
        raw=f"{name.strip()}>={raw_minimum.strip()}",
    )


def _version_satisfies_minimum(version: str, minimum: tuple[int, ...] | None) -> bool:
    if minimum is None:
        return True
    parsed = _parse_version_parts(version)
    if parsed is None:
        return False
    width = max(len(parsed), len(minimum))
    return parsed + (0,) * (width - len(parsed)) >= minimum + (0,) * (width - len(minimum))


_DEFAULT_REQUIREMENTS = tuple(_parse_requirement(requirement) for requirement in REQUIRED_RUNTIME_REQUIREMENTS)
REQUIRED_RUNTIME_MODULES = tuple(requirement.name for requirement in _DEFAULT_REQUIREMENTS)


def _collect_check_issues(checks: dict[str, bool], *, prefix: str) -> list[str]:
    return [f"{prefix}.{name}" for name, ok in checks.items() if not ok]


def _normalize_requirements(
    requirements: tuple[str, ...] | list[str] | None,
) -> tuple[RuntimeRequirement, ...]:
    raw_requirements = REQUIRED_RUNTIME_REQUIREMENTS if requirements is None else tuple(requirements)
    return tuple(_parse_requirement(requirement) for requirement in raw_requirements)


def _resolve_import_name(requirement: RuntimeRequirement) -> str:
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
                version_satisfied = _version_satisfies_minimum(version, requirement.minimum_version)
        except ImportError:
            pass
        checks[check_import] = importable
        checks[check_version] = version_satisfied
        modules[requirement_name] = {"version": version, "import_name": import_name}
        if not (importable and version_satisfied):
            missing_requirements.append(requirement.raw)

    issues = _collect_check_issues(checks, prefix="python_environment")
    ready = all(checks.values())
    return {
        "ready": ready,
        "checks": checks,
        "issues": issues,
        "modules": modules,
        "interpreter": sys.executable,
        "requirements": [requirement.raw for requirement in normalized_requirements],
        "missing_requirements": missing_requirements,
    }


def _is_managed_runtime() -> bool:
    try:
        runtime_prefix = Path(sys.prefix).resolve()
    except OSError:
        return False
    if _is_uv_tool_runtime_root(runtime_prefix):
        return True
    if _is_clean_runner_runtime(runtime_prefix):
        return True
    if _is_mas_workspace_runtime(runtime_prefix):
        return True
    return runtime_prefix in {
        MANAGED_RUNTIME_PREFIX,
        CHECKOUT_MANAGED_RUNTIME_PREFIX,
    }


def _is_clean_runner_runtime(runtime_prefix: Path) -> bool:
    configured_environment = str(os.environ.get("UV_PROJECT_ENVIRONMENT") or "").strip()
    if not configured_environment:
        return False
    try:
        configured_prefix = Path(configured_environment).expanduser().resolve()
    except OSError:
        return False
    return runtime_prefix == configured_prefix


def _is_mas_workspace_runtime(runtime_prefix: Path) -> bool:
    if runtime_prefix.name != ".venv":
        return False
    workspace_root = runtime_prefix.parent
    config_env = workspace_root / "ops" / "medautoscience" / "config.env"
    if not config_env.is_file():
        return False
    workspace_pyproject = workspace_root / "pyproject.toml"
    if not workspace_pyproject.is_file():
        return True
    try:
        pyproject_text = workspace_pyproject.read_text(encoding="utf-8")
    except OSError:
        return True
    return "med-autoscience" in pyproject_text


def ensure_python_environment_contract(
    *,
    requirements: tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    before = inspect_python_environment_contract(requirements=requirements)

    if not _is_managed_runtime():
        message = (
            "Current interpreter is not an approved MAS managed runtime. "
            "Please run the contract under a MAS repo/worktree `.venv`, a MAS study workspace `.venv`, "
            "a uv-tool runtime, or the repo clean runner before calling this function."
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
