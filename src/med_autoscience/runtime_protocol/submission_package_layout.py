from __future__ import annotations

from pathlib import Path


AUDIT_DIRNAME = "audit"
SUBMISSION_MANIFEST_BASENAME = "submission_manifest.json"


def audit_root(package_root: Path) -> Path:
    return Path(package_root) / AUDIT_DIRNAME


def legacy_submission_manifest_path(package_root: Path) -> Path:
    return Path(package_root) / SUBMISSION_MANIFEST_BASENAME


def submission_manifest_path(package_root: Path) -> Path:
    return audit_root(package_root) / SUBMISSION_MANIFEST_BASENAME


def resolve_submission_manifest_path(package_root: Path) -> Path:
    v2_path = submission_manifest_path(package_root)
    if v2_path.exists():
        return v2_path
    return legacy_submission_manifest_path(package_root)


__all__ = [
    "AUDIT_DIRNAME",
    "SUBMISSION_MANIFEST_BASENAME",
    "audit_root",
    "legacy_submission_manifest_path",
    "resolve_submission_manifest_path",
    "submission_manifest_path",
]
