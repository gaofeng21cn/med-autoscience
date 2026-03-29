"""Adapter layer for external runtimes and protocols."""

from . import aris_sidecar
from .tooluniverse import TOOLUNIVERSE_ROLES, detect_tooluniverse

__all__ = [
    "aris_sidecar",
    "TOOLUNIVERSE_ROLES",
    "detect_tooluniverse",
]
