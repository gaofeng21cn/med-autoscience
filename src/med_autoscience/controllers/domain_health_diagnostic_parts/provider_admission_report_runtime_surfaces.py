from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
)


def sync_current_control_runtime_surfaces(
    report: dict[str, Any],
    *,
    current_control_state: Mapping[str, Any],
) -> None:
    current_control_envelopes = _mapping(current_control_state.get("current_execution_envelopes"))
    if current_control_envelopes:
        envelopes = _mapping(report.get("current_execution_envelopes"))
        envelopes.update(
            {
                str(study_id): dict(envelope)
                for study_id, envelope in current_control_envelopes.items()
                if isinstance(envelope, Mapping)
            }
        )
        report["current_execution_envelopes"] = envelopes
    current_control_actions = [
        dict(action)
        for action in current_control_state.get("action_queue") or []
        if isinstance(action, Mapping)
    ]
    if current_control_actions:
        report["action_queue"] = current_control_actions
        current_execution_evidence = _mapping(report.get("current_execution_evidence"))
        current_execution_evidence["action_queue"] = current_control_actions
        report["current_execution_evidence"] = current_execution_evidence


__all__ = ["sync_current_control_runtime_surfaces"]
