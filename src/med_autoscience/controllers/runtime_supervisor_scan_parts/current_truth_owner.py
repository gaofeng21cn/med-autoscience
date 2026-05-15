from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import publication_work_unit_lifecycle
from med_autoscience.publication_eval_specificity_targets import specificity_target_status


RUNTIME_CONTROLLER_REDRIVE_REASON = "runtime_controller_redrive_required"
SPECIFICITY_WORK_UNIT_IDS = {"gate_needs_specificity", "needs_specificity"}
RUNTIME_REDRIVE_ACTIONS = {
    "ensure_study_runtime",
    "ensure_study_runtime_relaunch_stopped",
    "run_gate_clearing_batch",
    "run_quality_repair_batch",
}
DOMAIN_TRANSITION_ACTIONS_BY_DECISION_TYPE = {
    "ai_reviewer_re_eval": {"return_to_ai_reviewer_workflow"},
    "bundle_stage_finalize": {"ensure_study_runtime"},
    "publication_gate_blocker": {"run_gate_clearing_batch"},
}


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
    work_unit = _mapping(decision.get("next_work_unit"))
    work_unit_id = _text(work_unit.get("unit_id"))
    if work_unit_id is None:
        return None
    decision_fingerprint = _text(decision.get("work_unit_fingerprint")) or _text(work_unit.get("fingerprint"))
    if decision_fingerprint is None:
        return None
    domain_transition_allowed = domain_transition_runtime_route_allowed(
        work_unit_fingerprint=decision_fingerprint,
        action_types=action_types,
        work_unit_id=work_unit_id,
    )
    if not domain_transition_allowed:
        if not action_types & RUNTIME_REDRIVE_ACTIONS:
            return None
        publication_fingerprints = _publication_work_unit_fingerprints(publication_eval_payload)
        if decision_fingerprint not in publication_fingerprints:
            return None
    if work_unit_id in SPECIFICITY_WORK_UNIT_IDS and not domain_transition_allowed:
        if not _publication_eval_specificity_targets_complete_for_fingerprint(
            publication_eval_payload,
            decision_fingerprint=decision_fingerprint,
        ):
            return None
    if _publication_work_unit_closed(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        work_unit_id=work_unit_id,
    ):
        return None
    return {
        "decision_path": str(decision_path),
        "decision_id": _text(decision.get("decision_id")),
        "controller_actions": sorted(action_types),
        "route_target": _text(decision.get("route_target")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": decision_fingerprint,
    }


def domain_transition_runtime_route_allowed(
    *,
    work_unit_fingerprint: str | None,
    action_types: set[str],
    work_unit_id: str | None,
) -> bool:
    decision_type, fingerprint_work_unit_id = _domain_transition_fingerprint_parts(work_unit_fingerprint)
    if decision_type is None or fingerprint_work_unit_id is None or work_unit_id is None:
        return False
    if fingerprint_work_unit_id != work_unit_id:
        return False
    allowed_actions = DOMAIN_TRANSITION_ACTIONS_BY_DECISION_TYPE.get(decision_type, set())
    return bool(action_types & allowed_actions)


def _domain_transition_fingerprint_parts(work_unit_fingerprint: str | None) -> tuple[str | None, str | None]:
    fingerprint = _text(work_unit_fingerprint)
    if fingerprint is None:
        return None, None
    parts = fingerprint.split("::", 2)
    if len(parts) != 3 or parts[0] != "domain-transition" or not parts[1] or not parts[2]:
        return None, None
    return parts[1], parts[2]


def _runtime_repair_summary(reason: str) -> str:
    if reason == "abnormal_stopped_runtime_resume_required":
        return "Quest is stopped with controller/runtime facts requiring resume and no live worker is attached."
    if reason == "failed_quest_runtime_relaunch_required":
        return "Quest is failed/non-resumable, auto continuation is allowed, and no live worker is attached."
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


def _publication_eval_specificity_targets_complete_for_fingerprint(
    publication_eval_payload: Mapping[str, Any],
    *,
    decision_fingerprint: str,
) -> bool:
    for action in publication_eval_payload.get("recommended_actions") or []:
        if not isinstance(action, Mapping):
            continue
        next_work_unit = _mapping(action.get("next_work_unit"))
        action_fingerprint = _text(action.get("work_unit_fingerprint")) or _text(next_work_unit.get("fingerprint"))
        if action_fingerprint != decision_fingerprint:
            continue
        if specificity_target_status(action.get("specificity_targets")).get("complete") is True:
            return True
    return False


def _publication_work_unit_closed(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    work_unit_id: str,
) -> bool:
    lifecycle_path = (
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "controller"
        / "publication_work_unit_lifecycle"
        / "latest.json"
    )
    lifecycle = _read_json_object(lifecycle_path)
    if lifecycle is None:
        return False
    if not publication_work_unit_lifecycle.lifecycle_payload_is_closed(lifecycle):
        return False
    source_eval_id = _text(lifecycle.get("source_eval_id"))
    current_eval_id = _text(publication_eval_payload.get("eval_id"))
    if source_eval_id is None or current_eval_id is None or source_eval_id != current_eval_id:
        return False
    lifecycle_work_unit = _mapping(lifecycle.get("work_unit"))
    return _text(lifecycle_work_unit.get("unit_id")) == work_unit_id


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
