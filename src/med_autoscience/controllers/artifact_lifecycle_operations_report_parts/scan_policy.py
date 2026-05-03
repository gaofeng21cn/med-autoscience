from __future__ import annotations


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
