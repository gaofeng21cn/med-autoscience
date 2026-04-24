from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
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
        return QuestRuntimeSnapshot(
            quest_exists=self.quest_exists,
            quest_status=self.quest_status,
            bash_session_audit=dict(self.bash_session_audit) if self.bash_session_audit is not None else None,
            runtime_liveness_audit=dict(runtime_liveness_audit),
        )


def find_latest(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=lambda item: item.stat().st_mtime)


def load_runtime_state(quest_root: Path) -> dict[str, Any]:
    path = Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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
    patterns = [
        ".ds/worktrees/*/experiments/main/*/RESULT.json",
        "experiments/main/*/RESULT.json",
    ]
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
    path = Path(quest_root).expanduser().resolve() / ".ds" / "runs" / str(active_run_id) / "stdout.jsonl"
    return path if path.exists() else None


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
