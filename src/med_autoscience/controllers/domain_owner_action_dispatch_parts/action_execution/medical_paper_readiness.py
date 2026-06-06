from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import medical_paper_operator_actions
from med_autoscience.controllers import medical_paper_readiness as readiness_surface
from med_autoscience.controllers import medical_paper_readiness_owner_blocker
from med_autoscience.controllers.domain_owner_action_dispatch_parts import owner_request_paths
from med_autoscience.profiles import WorkspaceProfile


ACTION_TYPE = "complete_medical_paper_readiness_surface"
CALLABLE_SURFACE = "medical_paper_readiness.complete_medical_paper_readiness_surface"
DEFAULT_ACTION_ID_BY_SURFACE = {
    "literature_provider_runtime": "run_provider_literature_scout",
    "route_decision_orchestrator": "materialize_route_decision",
    "statistical_discipline_operations": "resolve_statistical_blockers",
    "revision_rebuttal_loop": "start_revision_rebuttal_loop",
    "authoring_runtime_authorization": "authorize_manuscript_drafting",
    "real_workspace_soak_monitor": "run_real_workspace_soak_monitor",
}


def execute_complete_medical_paper_readiness_surface(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    study_root = profile.studies_root / study_id
    if not study_root.exists():
        return _blocked(reason="study_root_missing", study_root=study_root, owner_result=None)

    dispatch_payload = _mapping(dispatch)
    request_payload = _mapping(owner_request_paths.owner_request_payload(profile, study_id, ACTION_TYPE))
    current_readiness = readiness_surface.build_medical_paper_readiness_surface(study_root=study_root)
    surface_key = (
        _surface_key(dispatch_payload)
        or _surface_key(request_payload)
        or _text(_mapping(current_readiness.get("next_action")).get("surface_key"))
    )
    operator_payload = _operator_payload(dispatch_payload) or _operator_payload(request_payload)
    if not operator_payload:
        blocker = medical_paper_readiness_owner_blocker.materialize_readiness_owner_blocker(
            study_root=study_root,
            source=CALLABLE_SURFACE,
            apply=apply,
        )
        return _blocked(
            reason="medical_paper_readiness_surface_input_required",
            study_root=study_root,
            owner_result={
                "surface_kind": "medical_paper_readiness_surface_completion_result",
                "status": "typed_blocker_or_stop_loss",
                "readiness_ref": str(readiness_surface.stable_medical_paper_readiness_path(study_root=study_root)),
                "requested_surface_key": surface_key,
                "missing_operator_payload": True,
                "owner_blocker": blocker,
                "quality_claim_authorized": False,
                "mechanical_projection_can_authorize_quality": False,
                "authority_boundary": _authority_boundary(
                    writes_readiness=False,
                    writes_owner_blocker=bool(apply),
                ),
            },
        )

    if not surface_key:
        blocker = medical_paper_readiness_owner_blocker.materialize_readiness_owner_blocker(
            study_root=study_root,
            source=CALLABLE_SURFACE,
            apply=apply,
        )
        return _blocked(
            reason="medical_paper_readiness_surface_key_required",
            study_root=study_root,
            owner_result={
                "surface_kind": "medical_paper_readiness_surface_completion_result",
                "status": "typed_blocker_or_stop_loss",
                "readiness_ref": str(readiness_surface.stable_medical_paper_readiness_path(study_root=study_root)),
                "missing_surface_key": True,
                "owner_blocker": blocker,
                "quality_claim_authorized": False,
                "mechanical_projection_can_authorize_quality": False,
                "authority_boundary": _authority_boundary(
                    writes_readiness=False,
                    writes_owner_blocker=bool(apply),
                ),
            },
        )

    action_id = _action_id(dispatch_payload, surface_key)
    action_result = medical_paper_operator_actions.dispatch_guarded_medical_paper_operator_action(
        study_root=study_root,
        action_id=action_id,
        surface_key=surface_key,
        operator_payload=operator_payload,
        action_instance_id=_text(dispatch_payload.get("action_id")),
        idempotency_key=_text(dispatch_payload.get("idempotency_key"))
        or _text(_mapping(dispatch_payload.get("prompt_contract")).get("idempotency_key")),
    )
    readiness = readiness_surface.build_medical_paper_readiness_surface(study_root=study_root)
    owner_result = {
        "surface_kind": "medical_paper_readiness_surface_completion_result",
        "status": "ready" if _text(readiness.get("overall_status")) == "ready" else "blocked",
        "readiness_ref": str(readiness_surface.stable_medical_paper_readiness_path(study_root=study_root)),
        "readiness_status": _text(readiness.get("overall_status")),
        "ready_count": readiness.get("ready_count"),
        "required_count": readiness.get("required_count"),
        "completed_surface_key": surface_key,
        "guarded_operator_action_result": action_result,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "authority_boundary": _authority_boundary(
            writes_readiness=bool(apply) and _text(action_result.get("status")) not in {"blocked", "missing"},
            writes_owner_blocker=False,
        ),
    }
    if _text(readiness.get("overall_status")) == "ready":
        return {
            "execution_status": "executed" if apply else "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": CALLABLE_SURFACE,
            "owner_result": owner_result,
            "quest_root": str(profile.runtime_root / study_id),
        }
    blocker = medical_paper_readiness_owner_blocker.materialize_readiness_owner_blocker(
        study_root=study_root,
        source=CALLABLE_SURFACE,
        apply=apply,
    )
    owner_result["owner_blocker"] = blocker
    owner_result["authority_boundary"] = _authority_boundary(
        writes_readiness=bool(apply) and _text(action_result.get("status")) not in {"blocked", "missing"},
        writes_owner_blocker=bool(apply),
    )
    return _blocked(
        reason=_text(action_result.get("missing_reason")) or "medical_paper_readiness_not_ready",
        study_root=study_root,
        owner_result=owner_result,
    )


def _blocked(
    *,
    reason: str,
    study_root: Path,
    owner_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "execution_status": "blocked",
        "blocked_reason": reason,
        "owner_callable_surface": CALLABLE_SURFACE,
        "owner_result": dict(owner_result) if isinstance(owner_result, Mapping) else owner_result,
        "quest_root": str(study_root),
    }


def _operator_payload(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    for payload in _payload_candidates(dispatch):
        if payload:
            return payload
    return {}


def _payload_candidates(dispatch: Mapping[str, Any]) -> list[dict[str, Any]]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    handoff_packet = _mapping(dispatch.get("handoff_packet"))
    owner_pickup = _mapping(dispatch.get("owner_pickup")) or _mapping(handoff_packet.get("owner_pickup"))
    return [
        _mapping(dispatch.get("operator_payload")),
        _mapping(dispatch.get("medical_paper_readiness_payload")),
        _mapping(prompt_contract.get("operator_payload")),
        _mapping(prompt_contract.get("medical_paper_readiness_payload")),
        _mapping(handoff_packet.get("operator_payload")),
        _mapping(handoff_packet.get("medical_paper_readiness_payload")),
        _mapping(owner_pickup.get("operator_payload")),
        _mapping(owner_pickup.get("medical_paper_readiness_payload")),
    ]


def _surface_key(dispatch: Mapping[str, Any]) -> str | None:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    handoff_packet = _mapping(dispatch.get("handoff_packet"))
    owner_pickup = _mapping(dispatch.get("owner_pickup")) or _mapping(handoff_packet.get("owner_pickup"))
    for payload in (dispatch, prompt_contract, handoff_packet, owner_pickup):
        if text := _text(payload.get("surface_key")):
            return text
    for payload in _payload_candidates(dispatch):
        if text := _text(payload.get("surface_key")):
            return text
    return None


def _action_id(dispatch: Mapping[str, Any], surface_key: str) -> str:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    handoff_packet = _mapping(dispatch.get("handoff_packet"))
    for payload in (dispatch, prompt_contract, handoff_packet):
        action_id = _text(payload.get("operator_action_id")) or _text(payload.get("medical_paper_action_id"))
        if action_id:
            return action_id
    return DEFAULT_ACTION_ID_BY_SURFACE.get(surface_key, f"complete_{surface_key}")


def _authority_boundary(*, writes_readiness: bool, writes_owner_blocker: bool) -> dict[str, Any]:
    return {
        "owner": "MedAutoScience",
        "surface_owner": "MedAutoScience",
        "writes_medical_paper_readiness": bool(writes_readiness),
        "writes_controller_decision_owner_blocker": bool(writes_owner_blocker),
        "writes_publication_quality": False,
        "writes_current_package": False,
        "writes_paper_body": False,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["execute_complete_medical_paper_readiness_surface"]
