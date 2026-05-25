from __future__ import annotations

from pathlib import Path


SCHEMA_VERSION = 1
EVENT_LOG_RELATIVE_PATH = Path("artifacts") / "truth" / "events.jsonl"
SNAPSHOT_RELATIVE_PATH = Path("artifacts") / "truth" / "latest.json"

TRUTH_EVENT_TYPES = frozenset(
    {
        "task_intake",
        "controller_decision",
        "runtime_native_event",
        "opl_runtime_owner_handoff",
        "publication_gate_eval",
        "quality_review_eval",
        "package_authority_eval",
        "delivery_sync",
        "human_gate",
        "stop_loss",
        "explicit_resume",
        "writer_lock_acquired",
        "writer_lock_released",
    }
)


def truth_events_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / EVENT_LOG_RELATIVE_PATH


def truth_snapshot_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / SNAPSHOT_RELATIVE_PATH


__all__ = [
    "EVENT_LOG_RELATIVE_PATH",
    "SCHEMA_VERSION",
    "SNAPSHOT_RELATIVE_PATH",
    "TRUTH_EVENT_TYPES",
    "truth_events_path",
    "truth_snapshot_path",
]
