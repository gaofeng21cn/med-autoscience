"""Adapter layer for external runtimes and protocols."""

from .tooluniverse import TOOLUNIVERSE_ROLES, detect_tooluniverse

__all__ = [
    "TOOLUNIVERSE_ROLES",
    "detect_tooluniverse",
]
