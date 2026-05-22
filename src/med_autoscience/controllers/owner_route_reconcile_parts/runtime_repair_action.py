from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import current_truth_owner
from med_autoscience.controllers.owner_route_reconcile_parts import runtime_facts


def action(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    gate_specificity: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not (
        runtime_facts.runtime_platform_repair_required(status, progress, gate_specificity=gate_specificity)
        or runtime_facts.live_activity_timeout_current_controller_route_available(
            status,
            progress,
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
        )
        or runtime_facts.current_controller_route_redrive_required(
            status,
            progress,
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
            gate_specificity=gate_specificity,
        )
        or runtime_facts.current_controller_owner_handoff_redrive_required(
            status=status,
            progress=progress,
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
        )
        or external_supervisor_repair_required(status, progress)
    ):
        return None
    return current_truth_owner.runtime_platform_repair_action(
        study_root=study_root,
        status=status,
        publication_eval_payload=publication_eval_payload,
        default_reason=external_supervisor_repair_reason(status, progress)
        or current_truth_owner.runtime_platform_repair_reason(status, progress),
    )


def external_supervisor_repair_required(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    return external_supervisor_repair_reason(status, progress) is not None


def external_supervisor_repair_reason(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    if runtime_facts.active_run_id(status, progress) is not None and runtime_facts.worker_running(status):
        return None
    lifecycle = _mapping(progress.get("ai_repair_lifecycle"))
    if _text(lifecycle.get("state")) not in {"blocked", "external_supervisor_required"}:
        return None
    if lifecycle.get("external_supervisor_required") is not True:
        return None
    blocked_reason = _text(lifecycle.get("blocked_reason"))
    if blocked_reason != "runtime_recovery_not_authorized":
        return None
    top_action = _mapping(lifecycle.get("top_action"))
    if (
        _text(top_action.get("action_type")) == "controller_repair"
        and _text(top_action.get("repair_kind")) == "bounded_work_unit_redrive"
        and top_action.get("auto_apply_allowed") is True
    ):
        return blocked_reason
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["action", "external_supervisor_repair_required", "external_supervisor_repair_reason"]
