from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .projection_inputs import ProjectionInputPaths
from .publication_runtime import _details_projection_payload, _refresh_publication_surfaces_from_gate_report
from .shared import (
    materialize_controller_confirmation_summary,
    read_controller_confirmation_summary,
    stable_controller_confirmation_summary_path,
    stable_evaluation_summary_path,
    _read_json_object,
)


@dataclass(frozen=True)
class ProjectionSurfacePayloads:
    launch_report_payload: dict[str, Any] | None
    controller_decision_payload: dict[str, Any] | None
    controller_confirmation_summary_path: Path
    controller_confirmation_summary: dict[str, Any] | None
    opl_runtime_owner_handoff_payload: dict[str, Any] | None
    runtime_escalation_payload: dict[str, Any] | None
    domain_health_diagnostic_payload: dict[str, Any] | None
    gate_clearing_batch_payload: dict[str, Any] | None
    publication_eval_payload: dict[str, Any] | None
    publishability_gate_path: Path | None
    publishability_gate_payload: dict[str, Any] | None
    bash_summary_payload: dict[str, Any] | None
    details_projection_wrapper: dict[str, Any] | None
    details_projection_payload: dict[str, Any] | None
    evaluation_summary_payload: dict[str, Any] | None


def read_projection_surface_payloads(
    *,
    study_root: Path,
    study_id: str,
    status: dict[str, Any],
    paths: ProjectionInputPaths,
    runtime_health_status: str | None,
) -> ProjectionSurfacePayloads:
    controller_decision_payload = _read_json_object(paths.controller_decision_path)
    if controller_decision_payload is not None:
        try:
            materialize_controller_confirmation_summary(
                study_root=study_root,
                decision_ref=paths.controller_decision_path,
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    controller_confirmation_summary_path = stable_controller_confirmation_summary_path(study_root=study_root)
    controller_confirmation_summary = _read_controller_confirmation_summary(
        study_root=study_root,
        ref=controller_confirmation_summary_path,
    )
    domain_health_diagnostic_payload = (
        _read_json_object(paths.domain_health_diagnostic_path) if paths.domain_health_diagnostic_path is not None else None
    )
    publication_eval_payload, publishability_gate_path, publishability_gate_payload = (
        _refresh_publication_surfaces_from_gate_report(
            study_root=study_root,
            study_id=study_id,
            quest_root=paths.quest_root,
            quest_id=paths.quest_id,
            publication_eval_path=paths.publication_eval_path,
            runtime_escalation_path=paths.runtime_escalation_path,
            domain_health_diagnostic_payload=domain_health_diagnostic_payload,
        )
    )
    return ProjectionSurfacePayloads(
        launch_report_payload=_read_json_object(paths.launch_report_path),
        controller_decision_payload=controller_decision_payload,
        controller_confirmation_summary_path=controller_confirmation_summary_path,
        controller_confirmation_summary=controller_confirmation_summary,
        opl_runtime_owner_handoff_payload=_read_json_object(paths.opl_runtime_owner_handoff_path),
        runtime_escalation_payload=_runtime_escalation_payload(
            status=status,
            runtime_health_status=runtime_health_status,
            path=paths.runtime_escalation_path,
        ),
        domain_health_diagnostic_payload=domain_health_diagnostic_payload,
        gate_clearing_batch_payload=_read_json_object(paths.gate_clearing_batch_path),
        publication_eval_payload=publication_eval_payload,
        publishability_gate_path=publishability_gate_path,
        publishability_gate_payload=publishability_gate_payload,
        bash_summary_payload=_read_json_object(paths.bash_summary_path)
        if paths.bash_summary_path is not None
        else None,
        details_projection_wrapper=_read_json_object(paths.details_projection_path)
        if paths.details_projection_path is not None
        else None,
        details_projection_payload=_details_projection_payload(paths.details_projection_path),
        evaluation_summary_payload=_read_json_object(stable_evaluation_summary_path(study_root=study_root)),
    )


def _read_controller_confirmation_summary(*, study_root: Path, ref: Path) -> dict[str, Any] | None:
    try:
        return read_controller_confirmation_summary(study_root=study_root, ref=ref) if ref.exists() else None
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _runtime_escalation_payload(
    *,
    status: dict[str, Any],
    runtime_health_status: str | None,
    path: Path | None,
) -> dict[str, Any] | None:
    if path is None:
        return None
    if status.get("runtime_escalation_ref") is not None or runtime_health_status in {"degraded", "escalated"}:
        return _read_json_object(path)
    return None
