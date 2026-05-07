from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .publication_runtime import _latest_runtime_watch_report
from .shared import _candidate_path, _non_empty_text


@dataclass(frozen=True)
class ProjectionInputPaths:
    quest_id: str | None
    quest_root: Path | None
    launch_report_path: Path
    publication_eval_path: Path
    controller_decision_path: Path
    runtime_escalation_path: Path | None
    runtime_watch_path: Path | None
    runtime_supervision_path: Path
    gate_clearing_batch_path: Path
    bash_summary_path: Path | None
    details_projection_path: Path | None


def resolve_projection_input_paths(
    *,
    status: dict[str, Any],
    study_root: Path,
) -> ProjectionInputPaths:
    quest_id = _non_empty_text(status.get("quest_id"))
    quest_root = _candidate_path(status.get("quest_root"))
    launch_report_path = (
        _candidate_path(status.get("launch_report_path"))
        or study_root / "artifacts" / "runtime" / "last_launch_report.json"
    )
    runtime_escalation_path = _candidate_path(
        ((status.get("runtime_escalation_ref") or {}).get("artifact_path"))
    )
    if runtime_escalation_path is None and quest_root is not None:
        runtime_escalation_path = (
            quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
        )
    return ProjectionInputPaths(
        quest_id=quest_id,
        quest_root=quest_root,
        launch_report_path=launch_report_path,
        publication_eval_path=study_root / "artifacts" / "publication_eval" / "latest.json",
        controller_decision_path=study_root / "artifacts" / "controller_decisions" / "latest.json",
        runtime_escalation_path=runtime_escalation_path,
        runtime_watch_path=_latest_runtime_watch_report(quest_root),
        runtime_supervision_path=study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        gate_clearing_batch_path=study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        bash_summary_path=quest_root / ".ds" / "bash_exec" / "summary.json" if quest_root is not None else None,
        details_projection_path=(
            quest_root / ".ds" / "projections" / "details.v1.json" if quest_root is not None else None
        ),
    )
