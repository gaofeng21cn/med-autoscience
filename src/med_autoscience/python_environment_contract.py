from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from typing import Any


REQUIRED_RUNTIME_REQUIREMENTS = ("matplotlib>=3.9",)
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
        checks[f"{requirement_name}_importable"] = importable
        checks[f"{requirement_name}_version_satisfied"] = version_satisfied
        modules[requirement_name] = {"version": version, "import_name": import_name}
        if not (importable and version_satisfied):
            missing_requirements.append(requirement.raw)

    issues = [f"python_environment.{name}" for name, ok in checks.items() if not ok]
    return {
        "ready": all(checks.values()),
        "checks": checks,
        "issues": issues,
        "modules": modules,
        "interpreter": sys.executable,
        "requirements": [requirement.raw for requirement in normalized_requirements],
        "missing_requirements": missing_requirements,
        "provisioning": {
            "owner": "uv",
            "owner_surface": "project dependency resolution",
            "requirement_profile": "med-autoscience[analysis]",
            "effect": "read_only",
            "mas_provisioning_allowed": False,
        },
    }


__all__ = [
    "CURATED_PYTHON_ANALYSIS_BUNDLE_REQUIREMENTS",
    "REQUIRED_RUNTIME_MODULES",
    "REQUIRED_RUNTIME_REQUIREMENTS",
    "inspect_python_environment_contract",
]
