from __future__ import annotations

from typing import Any


NOISE_SCAN_MODE = "statistical_only"
CLASSIFIED_SCAN_MODE = "classified_files"
SKIPPED_SCAN_MODE = "skipped"
SNAPSHOT_SCAN_MODE = "snapshot_reference"
DEEP_STATISTICAL_SCAN_MODE = "deep_statistical"
DEFAULT_ARTIFACT_SAMPLE_LIMIT = 50
DEFAULT_MAX_FILES = 1000
DEFAULT_MAX_SECONDS = 5.0
HARD_SKIPPED_DIR_NAMES = {
    ".git",
    ".hg",
    ".tox",
    ".venv",
    "node_modules",
    "venv",
}
STATISTICAL_DIR_BUCKETS = {
    ".cache": "cache",
    ".ds": "runtime",
    ".mypy_cache": "cache",
    ".pytest_cache": "cache",
    ".ruff_cache": "cache",
    "__pycache__": "cache",
    "cache": "cache",
}
STATISTICAL_RELATIVE_DIR_BUCKETS = {
    (".ds", "worktrees"): "runtime",
    ("ops", "med-deepscientist", "runtime", "quests"): "runtime",
    ("ops", "med-deepscientist", "runtime", "archives"): "runtime",
    ("ops", "med-deepscientist", "runtime", "recovery"): "runtime",
    ("ops", "med-deepscientist", "runtime", "runtime"): "runtime",
    ("datasets", "raw"): "dataset",
    ("datasets", "release"): "dataset",
    ("datasets", "private_release"): "dataset",
}
STATISTICAL_STUDY_ARTIFACT_DIR_BUCKETS = {
    ("artifacts", "autonomy"): "audit_log",
    ("artifacts", "runtime"): "audit_log",
    ("artifacts", "publication_eval"): "audit_log",
}
STATISTICAL_ROLE_LIFECYCLE_BY_BUCKET = {
    "runtime": ("runtime_ephemeral", "runtime_transient"),
    "dataset": ("data_release", "active_authoritative"),
    "audit_log": ("audit_log", "active_authoritative"),
}


def build_scan_policy(*, deep: bool, max_files: int | None, max_seconds: float | None) -> dict[str, Any]:
    resolved_max_files = DEFAULT_MAX_FILES if max_files is None else int(max_files)
    resolved_max_seconds = DEFAULT_MAX_SECONDS if max_seconds is None else float(max_seconds)
    if resolved_max_files < 1:
        raise ValueError("max_files must be >= 1")
    if resolved_max_seconds <= 0:
        raise ValueError("max_seconds must be > 0")
    return {
        "deep_scan_enabled": bool(deep),
        "artifact_listing": "bounded",
        "artifact_sample_limit": DEFAULT_ARTIFACT_SAMPLE_LIMIT,
        "max_files": resolved_max_files,
        "max_seconds": int(resolved_max_seconds)
        if resolved_max_seconds.is_integer()
        else resolved_max_seconds,
    }
