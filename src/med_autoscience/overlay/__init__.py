from __future__ import annotations

from importlib import import_module
from typing import Any

from .constants import DEFAULT_MEDICAL_OVERLAY_SKILL_IDS


_INSTALLER_EXPORTS = {
    "audit_runtime_medical_overlay",
    "describe_medical_overlay",
    "install_medical_overlay",
    "installer",
    "load_overlay_skill_text",
    "materialize_runtime_medical_overlay",
    "reapply_medical_overlay",
}


def __getattr__(name: str) -> Any:
    if name not in _INSTALLER_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    installer = import_module("med_autoscience.overlay.installer")
    if name == "installer":
        return installer
    return getattr(installer, name)

__all__ = [
    "DEFAULT_MEDICAL_OVERLAY_SKILL_IDS",
    "audit_runtime_medical_overlay",
    "describe_medical_overlay",
    "install_medical_overlay",
    "installer",
    "load_overlay_skill_text",
    "materialize_runtime_medical_overlay",
    "reapply_medical_overlay",
]
