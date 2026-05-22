from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import publication_work_unit_lifecycle
from med_autoscience.controllers import analysis_harmonization_owner_result
from med_autoscience.controllers import provenance_limited_harmonization_owner_result
from med_autoscience.controllers.story_surface_work_units import (
    is_story_surface_delta_write_work_unit,
)
from med_autoscience.publication_eval_specificity_targets import specificity_target_status


RUNTIME_CONTROLLER_REDRIVE_REASON = "runtime_controller_redrive_required"
QUALITY_REPAIR_BATCH_RELATIVE_PATH = Path("artifacts/controller/quality_repair_batch/latest.json")
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
    "route_back_same_line": {"ensure_study_runtime"},
}
METHODOLOGY_REFRAME_DECISION_FINGERPRINT = "decision::methodology_reframe_route_decision"
METHODOLOGY_REFRAME_ANALYSIS_WORK_UNIT = "provenance_limited_harmonization_audit"
METHODOLOGY_REFRAME_REBUILD_WORK_UNIT = "unit_harmonized_external_validation_rerun"


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
    from med_autoscience.controllers.domain_route_scan_parts import abnormal_stopped_runtime

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
    methodology_reframe_allowed = methodology_reframe_runtime_route_allowed(
        decision=decision,
        work_unit=work_unit,
        work_unit_fingerprint=decision_fingerprint,
        action_types=action_types,
        work_unit_id=work_unit_id,
    )
    if not domain_transition_allowed and not methodology_reframe_allowed:
        if not action_types & RUNTIME_REDRIVE_ACTIONS:
            return None
        publication_fingerprints = _publication_work_unit_fingerprints(publication_eval_payload)
        if decision_fingerprint not in publication_fingerprints:
            return None
    if work_unit_id in SPECIFICITY_WORK_UNIT_IDS and not domain_transition_allowed and not methodology_reframe_allowed:
        if not _publication_eval_specificity_targets_complete_for_fingerprint(
            publication_eval_payload,
            decision_fingerprint=decision_fingerprint,
        ):
            return None
    if _publication_work_unit_closed(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=decision_fingerprint,
    ):
        return None
    if (
        work_unit_id == METHODOLOGY_REFRAME_ANALYSIS_WORK_UNIT
        and provenance_limited_harmonization_owner_result.required_output_satisfied(study_root=study_root)
    ):
        return None
    if (
        work_unit_id == METHODOLOGY_REFRAME_REBUILD_WORK_UNIT
        and analysis_harmonization_owner_result.required_output_satisfied(study_root=study_root)
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


def current_story_surface_delta_blocker_route(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    batch_path = resolved_study_root / QUALITY_REPAIR_BATCH_RELATIVE_PATH
    batch = _read_json_object(batch_path)
    if batch is None:
        return None
    source_eval_id = _text(batch.get("source_eval_id"))
    if source_eval_id is None or source_eval_id != _text(publication_eval_payload.get("eval_id")):
        return None
    if not _story_surface_delta_blocker_present(batch):
        return None
    if _text(batch.get("next_owner")) != "write":
        return None
    action = _publication_story_repair_action(publication_eval_payload)
    if action is None:
        return None
    next_work_unit = _mapping(action.get("next_work_unit"))
    work_unit_id = _text(next_work_unit.get("unit_id"))
    gate_batch = _mapping(batch.get("gate_clearing_batch"))
    return {
        "decision_path": None,
        "decision_id": None,
        "controller_actions": ["run_quality_repair_batch"],
        "route_target": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": _text(action.get("work_unit_fingerprint"))
        or _text(gate_batch.get("work_unit_fingerprint"))
        or _text(gate_batch.get("source_work_unit_fingerprint")),
        "quality_repair_batch_path": str(batch_path),
        "authorization_basis": "quality_repair_story_surface_delta_blocker",
    }


def _publication_story_repair_action(publication_eval_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(actions, list):
        return None
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        next_work_unit = _mapping(action.get("next_work_unit"))
        if _text(action.get("action_type")) != "route_back_same_line":
            continue
        if _text(action.get("route_target")) != "write" and _text(next_work_unit.get("lane")) != "write":
            continue
        return dict(action)
    return None


def _story_surface_delta_blocker_present(batch: Mapping[str, Any]) -> bool:
    if _text(batch.get("blocked_reason")) == "manuscript_story_surface_delta_missing":
        return True
    evidence = _mapping(batch.get("repair_execution_evidence"))
    if _text(evidence.get("status")) != "blocked":
        return False
    blockers = _string_set(evidence.get("blockers"))
    if "manuscript_story_surface_delta_missing" in blockers:
        return True
    artifact_delta = _mapping(evidence.get("canonical_artifact_delta"))
    return (
        _text(artifact_delta.get("status")) == "blocked"
        and artifact_delta.get("meaningful_artifact_delta") is False
        and "forbidden_manuscript_terms_present" in blockers
    )


def methodology_reframe_runtime_route_allowed(
    *,
    decision: Mapping[str, Any],
    work_unit: Mapping[str, Any],
    work_unit_fingerprint: str | None,
    action_types: set[str],
    work_unit_id: str | None,
) -> bool:
    if not (
        _text(decision.get("decision_type")) in {"route_back_same_line", "bounded_analysis", "stop_loss"}
        and work_unit_fingerprint == METHODOLOGY_REFRAME_DECISION_FINGERPRINT
        and "ensure_study_runtime" in action_types
        and work_unit.get("hard_methodology") is True
        and work_unit.get("terminal_source_provenance_blocker_consumed") is True
        and work_unit.get("current_transport_claim_must_not_be_used_as_medical_conclusion") is True
    ):
        return False
    if (
        work_unit_id == METHODOLOGY_REFRAME_ANALYSIS_WORK_UNIT
        and _text(work_unit.get("selected_route_option")) == "provenance_limited_harmonization_audit"
    ):
        return True
    return bool(
        work_unit_id == METHODOLOGY_REFRAME_REBUILD_WORK_UNIT
        and _text(work_unit.get("selected_route_option")) == "rebuild_reproducible_model_route"
        and work_unit.get("clean_reproducible_model_rebuild_authorized") is True
    )


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
    work_unit_fingerprint: str | None = None,
) -> bool:
    resolved_study_root = Path(study_root).expanduser().resolve()
    lifecycle_path = (
        resolved_study_root
        / "artifacts"
        / "controller"
        / "publication_work_unit_lifecycle"
        / "latest.json"
    )
    lifecycle = _read_json_object(lifecycle_path)
    if lifecycle is not None and publication_work_unit_lifecycle.lifecycle_payload_is_closed(lifecycle):
        source_eval_id = _text(lifecycle.get("source_eval_id"))
        current_eval_id = _text(publication_eval_payload.get("eval_id"))
        if source_eval_id is not None and current_eval_id is not None and source_eval_id == current_eval_id:
            lifecycle_work_unit = _mapping(lifecycle.get("work_unit"))
            if _text(lifecycle_work_unit.get("unit_id")) == work_unit_id:
                return True
    return _runtime_turn_closeout_closes_work_unit(
        study_root=resolved_study_root,
        publication_eval_payload=publication_eval_payload,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
    )


def _runtime_turn_closeout_closes_work_unit(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    work_unit_id: str,
    work_unit_fingerprint: str | None,
) -> bool:
    quest_root = _publication_eval_quest_root(publication_eval_payload)
    if quest_root is None:
        return False
    closeout_root = quest_root / "artifacts" / "runtime" / "turn_closeouts"
    if not closeout_root.exists():
        return False
    for closeout_path in sorted(closeout_root.glob("*.json")):
        closeout = _read_json_object(closeout_path)
        if closeout is None or closeout.get("status") != "completed":
            continue
        if closeout.get("meaningful_artifact_delta") is not True:
            continue
        for artifact_ref in closeout.get("artifact_refs") or []:
            artifact_path = _resolve_runtime_artifact_ref(quest_root, artifact_ref)
            if artifact_path is None or not _runtime_artifact_ref_is_json_payload(artifact_path):
                continue
            package_closure = _read_json_artifact_object(artifact_path)
            if _package_closure_matches_work_unit(
                package_closure,
                study_root=study_root,
                work_unit_id=work_unit_id,
                work_unit_fingerprint=work_unit_fingerprint,
            ):
                return True
    return False


def _publication_eval_quest_root(publication_eval_payload: Mapping[str, Any]) -> Path | None:
    runtime_context_refs = _mapping(publication_eval_payload.get("runtime_context_refs"))
    runtime_escalation_ref = _text(runtime_context_refs.get("runtime_escalation_ref"))
    if runtime_escalation_ref is not None:
        path = Path(runtime_escalation_ref).expanduser()
        parts = path.parts
        if "artifacts" in parts:
            artifacts_index = parts.index("artifacts")
            if artifacts_index > 0:
                return Path(*parts[:artifacts_index]).resolve()
    return None


def _resolve_runtime_artifact_ref(quest_root: Path, artifact_ref: object) -> Path | None:
    text = _text(artifact_ref)
    if text is None:
        return None
    path = Path(text).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (quest_root / path).resolve()


def _runtime_artifact_ref_is_json_payload(path: Path) -> bool:
    return path.suffix.lower() == ".json"


def _read_json_artifact_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _package_closure_matches_work_unit(
    payload: Mapping[str, Any] | None,
    *,
    study_root: Path,
    work_unit_id: str,
    work_unit_fingerprint: str | None,
) -> bool:
    if payload is None:
        return False
    if _text(payload.get("artifact_kind")) != work_unit_id:
        return False
    work_unit = _mapping(payload.get("work_unit"))
    if _text(work_unit.get("unit_id")) != work_unit_id:
        return False
    if work_unit_fingerprint is not None and _text(work_unit.get("fingerprint")) != work_unit_fingerprint:
        return False
    authority_closure = _mapping(payload.get("authority_closure"))
    if _text(authority_closure.get("status")) != "closed_for_bundle_stage":
        return False
    if _text(authority_closure.get("publication_gate_status")) != "clear":
        return False
    if authority_closure.get("publication_gate_allow_write") is not True:
        return False
    if list(authority_closure.get("publication_gate_blockers") or []):
        return False
    submission_authority = _mapping(payload.get("submission_minimal_authority"))
    if _text(submission_authority.get("status")) != "current":
        return False
    human_facing_delivery = _mapping(payload.get("human_facing_delivery"))
    current_package_zip = _text(human_facing_delivery.get("current_package_zip"))
    if current_package_zip is None:
        return False
    package_path = Path(current_package_zip).expanduser()
    if not package_path.is_absolute():
        package_path = study_root / package_path
    try:
        package_path.resolve().relative_to(study_root.resolve())
    except ValueError:
        return False
    return _text(human_facing_delivery.get("status")) == "current"


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


def _string_set(value: object) -> set[str]:
    if isinstance(value, str):
        item = value.strip()
        return {item} if item else set()
    if not isinstance(value, list | tuple | set):
        return set()
    return {text for item in value if (text := _text(item)) is not None}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "QUALITY_REPAIR_BATCH_RELATIVE_PATH",
    "RUNTIME_CONTROLLER_REDRIVE_REASON",
    "current_story_surface_delta_blocker_route",
    "current_controller_runtime_route",
    "next_owner_for_reason",
    "runtime_platform_repair_reason",
    "runtime_platform_repair_action",
]
