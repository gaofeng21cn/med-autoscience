from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
from pathlib import Path
from typing import Any


_OUTER_LOOP_WATCHED_QUEST_STATUSES = frozenset(
    {
        "created",
        "idle",
        "paused",
        "running",
        "active",
        "waiting_for_user",
        "stopped",
    }
)


class QuestRuntimeLivenessStatus(StrEnum):
    LIVE = "live"
    NONE = "none"
    UNKNOWN = "unknown"
    OTHER = "other"


@dataclass(frozen=True)
class QuestRuntimeSnapshot:
    quest_exists: bool
    quest_status: str | None
    bash_session_audit: dict[str, Any] | None = None
    runtime_liveness_audit: dict[str, Any] | None = None

    @property
    def runtime_liveness_status(self) -> QuestRuntimeLivenessStatus:
        payload = self.runtime_liveness_audit
        if not isinstance(payload, dict):
            return QuestRuntimeLivenessStatus.NONE
        status = str(payload.get("status") or "").strip().lower()
        if status == QuestRuntimeLivenessStatus.LIVE.value:
            source = str(payload.get("source") or "").strip()
            if source and source != "opl_current_control_state_provider_attempt":
                return QuestRuntimeLivenessStatus.UNKNOWN
            return QuestRuntimeLivenessStatus.LIVE
        if status == QuestRuntimeLivenessStatus.NONE.value:
            return QuestRuntimeLivenessStatus.NONE
        if status == QuestRuntimeLivenessStatus.UNKNOWN.value:
            return QuestRuntimeLivenessStatus.UNKNOWN
        return QuestRuntimeLivenessStatus.OTHER

    def with_bash_session_audit(self, bash_session_audit: dict[str, Any]) -> "QuestRuntimeSnapshot":
        return QuestRuntimeSnapshot(
            quest_exists=self.quest_exists,
            quest_status=self.quest_status,
            bash_session_audit=dict(bash_session_audit),
            runtime_liveness_audit=dict(self.runtime_liveness_audit) if self.runtime_liveness_audit is not None else None,
        )

    def with_runtime_liveness_audit(self, runtime_liveness_audit: dict[str, Any]) -> "QuestRuntimeSnapshot":
        snapshot = runtime_liveness_audit.get("snapshot")
        quest_status = (
            str(snapshot.get("status") or "").strip()
            if isinstance(snapshot, dict)
            else None
        )
        return QuestRuntimeSnapshot(
            quest_exists=self.quest_exists,
            quest_status=quest_status or self.quest_status,
            bash_session_audit=dict(self.bash_session_audit) if self.bash_session_audit is not None else None,
            runtime_liveness_audit=dict(runtime_liveness_audit),
        )


def find_latest(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=lambda item: item.stat().st_mtime)


SCHEMA_VERSION = 1


def canonical_runtime_state_path(quest_root: Path) -> Path:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    return resolved_quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json"


def legacy_runtime_state_path(quest_root: Path) -> Path:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    return resolved_quest_root / ".ds" / "runtime_state.json"


def runtime_state_path_candidates(quest_root: Path) -> tuple[Path, ...]:
    return (
        canonical_runtime_state_path(quest_root),
    )


def load_runtime_state(quest_root: Path) -> dict[str, Any]:
    for path in runtime_state_path_candidates(quest_root):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def materialize_runtime_state_surface(quest_root: Path, *, recorded_at: str | None = None) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    canonical_path = canonical_runtime_state_path(resolved_quest_root)
    legacy_path = legacy_runtime_state_path(resolved_quest_root)
    result: dict[str, Any] = {
        "surface_kind": "runtime_state_surface_materialization",
        "schema_version": SCHEMA_VERSION,
        "recorded_at": recorded_at,
        "quest_root": str(resolved_quest_root),
        "canonical_path": str(canonical_path),
        "legacy_path": str(legacy_path),
        "canonical_surface": "artifacts/runtime/state/runtime_state.json",
        "legacy_surface": ".ds/runtime_state.json",
        "body_included": False,
        "changed": False,
        "blockers": [],
    }
    canonical_exists = canonical_path.exists()
    legacy_exists = legacy_path.exists()
    result["canonical_exists_before"] = canonical_exists
    result["legacy_exists"] = legacy_exists
    if not legacy_exists:
        result["status"] = "already_canonical" if canonical_exists else "missing_runtime_state"
        return result
    try:
        legacy_bytes = legacy_path.read_bytes()
        json.loads(legacy_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        result["status"] = "blocked_legacy_runtime_state_unreadable"
        result["blockers"] = [{"reason": "legacy_runtime_state_unreadable", "error": str(exc)}]
        return result
    legacy_sha256 = _sha256_bytes(legacy_bytes)
    result["legacy_sha256"] = legacy_sha256
    if canonical_exists:
        try:
            canonical_bytes = canonical_path.read_bytes()
        except OSError as exc:
            result["status"] = "blocked_canonical_runtime_state_unreadable"
            result["blockers"] = [{"reason": "canonical_runtime_state_unreadable", "error": str(exc)}]
            return result
        canonical_sha256 = _sha256_bytes(canonical_bytes)
        result["canonical_sha256_before"] = canonical_sha256
        if canonical_sha256 == legacy_sha256:
            result["status"] = "already_materialized"
            return result
        if canonical_path.stat().st_mtime_ns >= legacy_path.stat().st_mtime_ns:
            result["status"] = "canonical_runtime_state_diverged"
            result["blockers"] = [{"reason": "canonical_runtime_state_newer_or_same_mtime"}]
            return result
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = canonical_path.with_name(f"{canonical_path.name}.tmp")
    tmp_path.write_bytes(legacy_bytes)
    tmp_path.replace(canonical_path)
    result["status"] = "materialized_from_legacy"
    result["changed"] = True
    result["canonical_exists_after"] = True
    result["canonical_sha256_after"] = legacy_sha256
    return result


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def quest_status(quest_root: Path) -> str:
    payload = load_runtime_state(quest_root)
    return str(payload.get("status") or "").strip().lower()


def inspect_quest_runtime(quest_root: Path) -> QuestRuntimeSnapshot:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    quest_exists = (resolved_quest_root / "quest.yaml").exists()
    return QuestRuntimeSnapshot(
        quest_exists=quest_exists,
        quest_status=quest_status(resolved_quest_root) if quest_exists else None,
    )


def iter_active_quests(runtime_root: Path) -> list[Path]:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    if not resolved_runtime_root.exists():
        return []
    quests: list[Path] = []
    for quest_root in sorted(path for path in resolved_runtime_root.iterdir() if path.is_dir()):
        if quest_status(quest_root) in _OUTER_LOOP_WATCHED_QUEST_STATUSES:
            quests.append(quest_root)
    return quests


def find_latest_main_result_path(quest_root: Path) -> Path:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    canonical_main_result = resolved_quest_root / "artifacts" / "results" / "main_result.json"
    if canonical_main_result.exists():
        return canonical_main_result
    patterns = ["experiments/main/*/RESULT.json"]
    candidates: list[Path] = []
    for pattern in patterns:
        candidates.extend(resolved_quest_root.glob(pattern))
    latest = find_latest(candidates)
    if latest is None:
        raise FileNotFoundError(f"No main RESULT.json found under {resolved_quest_root}")
    return latest


def find_latest_main_result(quest_root: Path) -> Path:
    return find_latest_main_result_path(quest_root)


def resolve_active_stdout_path(*, quest_root: Path, runtime_state: dict[str, Any]) -> Path | None:
    active_run_id = runtime_state.get("active_run_id")
    if not active_run_id:
        return None
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    candidates = (
        resolved_quest_root / "artifacts" / "runtime" / "runs" / str(active_run_id) / "stdout.jsonl",
    )
    return next((path for path in candidates if path.exists()), None)


def read_recent_stdout_lines(stdout_path: Path | None, *, limit: int = 40) -> list[str]:
    if stdout_path is None:
        return []
    raw_lines = Path(stdout_path).expanduser().resolve().read_text(encoding="utf-8").splitlines()[-limit:]
    lines: list[str] = []
    for raw in raw_lines:
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        line = str(event.get("line") or "")
        if line:
            lines.append(line)
    return lines
