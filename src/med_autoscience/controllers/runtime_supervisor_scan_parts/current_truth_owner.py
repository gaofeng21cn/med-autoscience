from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


RUNTIME_CONTROLLER_REDRIVE_REASON = "runtime_controller_redrive_required"
SPECIFICITY_WORK_UNIT_IDS = {"gate_needs_specificity", "needs_specificity"}
RUNTIME_REDRIVE_ACTIONS = {"ensure_study_runtime", "ensure_study_runtime_relaunch_stopped"}


def runtime_platform_repair_action(
    *,
    study_root: Path,
    status: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    default_reason: str,
) -> dict[str, Any]:
    controller_route = current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if controller_route is None:
        return {
            "action_type": "runtime_platform_repair",
            "authority": "external_supervisor",
            "owner": "external_engineering_agent",
            "recommended_owner": "external_engineering_agent",
            "reason": default_reason,
            "summary": _runtime_repair_summary(default_reason),
            "paper_package_mutation_allowed": False,
        }
    return {
        "action_type": "runtime_platform_repair",
        "authority": "observability_only",
        "owner": "mas_controller",
        "request_owner": "mas_controller",
        "recommended_owner": "mas_controller",
        "reason": RUNTIME_CONTROLLER_REDRIVE_REASON,
        "summary": "Current controller truth names an executable same-line work unit; redrive the no-live runtime through MAS controller ownership.",
        "controller_route": controller_route,
        "runtime_reason": _text(status.get("reason")),
        "paper_package_mutation_allowed": False,
    }


def runtime_platform_repair_reason(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str:
    from med_autoscience.controllers.runtime_supervisor_scan_parts import abnormal_stopped_runtime

    if reason := abnormal_stopped_runtime.repair_reason(status, progress):
        return reason
    return "runtime_recovery_retry_budget_exhausted"


def next_owner_for_reason(reason: str | None) -> str | None:
    if reason == RUNTIME_CONTROLLER_REDRIVE_REASON:
        return "mas_controller"
    return None


def current_controller_runtime_route(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    decision_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    decision = _read_json_object(decision_path)
    if decision is None or decision.get("requires_human_confirmation") is True:
        return None
    action_types = _controller_action_types(decision)
    if not action_types & RUNTIME_REDRIVE_ACTIONS:
        return None
    work_unit = _mapping(decision.get("next_work_unit"))
    work_unit_id = _text(work_unit.get("unit_id"))
    if work_unit_id is None or work_unit_id in SPECIFICITY_WORK_UNIT_IDS:
        return None
    decision_fingerprint = _text(decision.get("work_unit_fingerprint")) or _text(work_unit.get("fingerprint"))
    publication_fingerprints = _publication_work_unit_fingerprints(publication_eval_payload)
    if decision_fingerprint is None or decision_fingerprint not in publication_fingerprints:
        return None
    return {
        "decision_path": str(decision_path),
        "decision_id": _text(decision.get("decision_id")),
        "controller_actions": sorted(action_types),
        "route_target": _text(decision.get("route_target")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": decision_fingerprint,
    }


def _runtime_repair_summary(reason: str) -> str:
    if reason == "abnormal_stopped_runtime_resume_required":
        return "Quest is stopped with controller/runtime facts requiring resume and no live worker is attached."
    return "Runtime recovery retry budget is exhausted and no live worker is attached."


def _publication_work_unit_fingerprints(publication_eval_payload: Mapping[str, Any]) -> set[str]:
    fingerprints: set[str] = set()
    for action in publication_eval_payload.get("recommended_actions") or []:
        if not isinstance(action, Mapping):
            continue
        if fingerprint := _text(action.get("work_unit_fingerprint")):
            fingerprints.add(fingerprint)
        next_work_unit = _mapping(action.get("next_work_unit"))
        if fingerprint := _text(next_work_unit.get("fingerprint")):
            fingerprints.add(fingerprint)
    return fingerprints


def _controller_action_types(payload: Mapping[str, Any]) -> set[str]:
    action_types: set[str] = set()
    for action in payload.get("controller_actions") or []:
        if isinstance(action, Mapping):
            text = _text(action.get("action_type"))
        else:
            text = _text(action)
        if text is not None:
            action_types.add(text)
    return action_types


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "RUNTIME_CONTROLLER_REDRIVE_REASON",
    "current_controller_runtime_route",
    "next_owner_for_reason",
    "runtime_platform_repair_reason",
    "runtime_platform_repair_action",
]
