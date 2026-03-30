"""Adapter layer for external runtimes and protocols."""

from . import autofigure_edit_sidecar
from . import aris_sidecar
from . import sidecar_provider
from .tooluniverse import TOOLUNIVERSE_ROLES, detect_tooluniverse

__all__ = [
    "autofigure_edit_sidecar",
    "aris_sidecar",
    "sidecar_provider",
    "TOOLUNIVERSE_ROLES",
    "detect_tooluniverse",
]
