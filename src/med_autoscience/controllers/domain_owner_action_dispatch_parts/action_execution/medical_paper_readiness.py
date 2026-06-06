from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import medical_paper_operator_actions
from med_autoscience.controllers import medical_paper_readiness as readiness_surface
from med_autoscience.controllers import medical_paper_readiness_owner_blocker
from med_autoscience.controllers import medical_paper_readiness_payload_authoring
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
        return _blocked(
            reason="study_root_missing",
            study_root=study_root,
            owner_result=None,
            owner_delta_result=_owner_delta_result(
                study_id=study_id,
                study_root=study_root,
                owner_result={},
            ),
        )

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
        operator_payload = _operator_payload_from_ref(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch_payload,
            request_payload=request_payload,
        )
    authored_payload: dict[str, Any] = {}
    if not operator_payload:
        authored_payload = medical_paper_readiness_payload_authoring.author_operator_payload(
            study_root=study_root,
            surface_key=surface_key,
            write_provider_response_ledger=apply,
        )
        if _text(authored_payload.get("status")) != "blocked":
            operator_payload = authored_payload
    if not operator_payload:
        blocker = medical_paper_readiness_owner_blocker.materialize_readiness_owner_blocker(
            study_root=study_root,
            source=CALLABLE_SURFACE,
            apply=apply,
        )
        owner_result = {
            "surface_kind": "medical_paper_readiness_surface_completion_result",
            "status": "typed_blocker_or_stop_loss",
            "readiness_ref": str(readiness_surface.stable_medical_paper_readiness_path(study_root=study_root)),
            "requested_surface_key": surface_key,
            "missing_operator_payload": True,
            "operator_payload_authoring": authored_payload or None,
            "owner_blocker": blocker,
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
            "authority_boundary": _authority_boundary(
                writes_readiness=False,
                writes_owner_blocker=bool(apply),
            ),
        }
        return _blocked(
            reason="medical_paper_readiness_surface_input_required",
            study_root=study_root,
            owner_result=owner_result,
            owner_delta_result=_owner_delta_result(
                study_id=study_id,
                study_root=study_root,
                owner_result=owner_result,
            ),
        )

    if not surface_key:
        blocker = medical_paper_readiness_owner_blocker.materialize_readiness_owner_blocker(
            study_root=study_root,
            source=CALLABLE_SURFACE,
            apply=apply,
        )
        owner_result = {
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
        }
        return _blocked(
            reason="medical_paper_readiness_surface_key_required",
            study_root=study_root,
            owner_result=owner_result,
            owner_delta_result=_owner_delta_result(
                study_id=study_id,
                study_root=study_root,
                owner_result=owner_result,
            ),
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
            "owner_delta_result": _owner_delta_result(
                study_id=study_id,
                study_root=study_root,
                owner_result=owner_result,
            ),
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
        owner_delta_result=_owner_delta_result(
            study_id=study_id,
            study_root=study_root,
            owner_result=owner_result,
        ),
    )


def _blocked(
    *,
    reason: str,
    study_root: Path,
    owner_result: Mapping[str, Any] | None,
    owner_delta_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "execution_status": "blocked",
        "blocked_reason": reason,
        "owner_callable_surface": CALLABLE_SURFACE,
        "owner_result": dict(owner_result) if isinstance(owner_result, Mapping) else owner_result,
        "quest_root": str(study_root),
    }
    if isinstance(owner_delta_result, Mapping):
        payload["owner_delta_result"] = dict(owner_delta_result)
    return payload


def _owner_delta_result(
    *,
    study_id: str,
    study_root: Path,
    owner_result: Mapping[str, Any],
) -> dict[str, Any]:
    quality_gate_receipt = _quality_gate_receipt(study_root=study_root, owner_result=owner_result)
    typed_blocker = _typed_blocker(owner_result)
    quality_gate_refs = _quality_gate_receipt_refs(quality_gate_receipt)
    stable_blocker_refs = _stable_typed_blocker_refs(owner_result)
    result_kind = _owner_delta_result_kind(
        readiness_status=_text(owner_result.get("readiness_status")),
        quality_gate_refs=quality_gate_refs,
        stable_blocker_refs=stable_blocker_refs,
    )
    return {
        "surface_kind": "mas_current_owner_delta_result",
        "study_id": study_id,
        "owner": "MedAutoScience",
        "result_kind": result_kind,
        "required_return_shape_satisfied": result_kind in {
            "owner_receipt",
            "quality_gate_receipt",
            "quality_gate_receipt_with_stable_typed_blocker",
            "stable_typed_blocker",
        },
        "owner_receipt_refs": quality_gate_refs if result_kind == "owner_receipt" else [],
        "quality_gate_receipt_refs": quality_gate_refs,
        "stable_typed_blocker_refs": stable_blocker_refs,
        "quality_gate_receipt": quality_gate_receipt or None,
        "typed_blocker": typed_blocker or None,
        "body_included": False,
        "authority_boundary": {
            "owner": "med-autoscience",
            "writes_publication_eval": False,
            "writes_controller_decision": bool(stable_blocker_refs),
            "writes_paper_or_package": False,
            "writes_memory_body": False,
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    }


def _owner_delta_result_kind(
    *,
    readiness_status: str | None,
    quality_gate_refs: list[str],
    stable_blocker_refs: list[str],
) -> str:
    if readiness_status == "ready" and quality_gate_refs:
        return "owner_receipt"
    if quality_gate_refs and stable_blocker_refs:
        return "quality_gate_receipt_with_stable_typed_blocker"
    if quality_gate_refs:
        return "quality_gate_receipt"
    if stable_blocker_refs:
        return "stable_typed_blocker"
    return "missing_owner_delta_result"


def _quality_gate_receipt(*, study_root: Path, owner_result: Mapping[str, Any]) -> dict[str, Any]:
    action_result = _mapping(owner_result.get("guarded_operator_action_result"))
    if not action_result:
        return {}
    return {
        "surface_kind": "medical_paper_readiness_quality_gate_receipt",
        "readiness_ref": _text(owner_result.get("readiness_ref"))
        or str(readiness_surface.stable_medical_paper_readiness_path(study_root=study_root)),
        "readiness_status": _text(owner_result.get("readiness_status")),
        "completed_surface_key": _text(owner_result.get("completed_surface_key")),
        "action_result_ref": _text(action_result.get("action_result_ref")),
        "durable_ref": _text(action_result.get("durable_ref")),
        "replay_ref": _text(action_result.get("replay_ref")),
        "action_status": _text(action_result.get("status")),
        "missing_reason": _text(action_result.get("missing_reason")),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _quality_gate_receipt_refs(receipt: Mapping[str, Any]) -> list[str]:
    refs = [
        _text(receipt.get("readiness_ref")),
        _text(receipt.get("action_result_ref")),
    ]
    return [ref for ref in refs if ref]


def _stable_typed_blocker_refs(owner_result: Mapping[str, Any]) -> list[str]:
    blocker = _mapping(owner_result.get("owner_blocker"))
    ref = _text(blocker.get("controller_decision_ref"))
    if ref and blocker.get("will_write_controller_decision") is True:
        return [ref]
    return []


def _typed_blocker(owner_result: Mapping[str, Any]) -> dict[str, Any]:
    blocker = _mapping(owner_result.get("owner_blocker"))
    controller_decision = _mapping(blocker.get("controller_decision"))
    controller_blocker = _mapping(controller_decision.get("controller_blocker"))
    if controller_blocker:
        return controller_blocker
    if _text(owner_result.get("status")) == "typed_blocker_or_stop_loss":
        return {
            "blocker_id": _text(owner_result.get("requested_surface_key"))
            or "medical_paper_readiness_surface_input_required",
            "owner": "MedAutoScience",
            "write_permitted": False,
        }
    return {}


def _operator_payload(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    for payload in _payload_candidates(dispatch):
        if payload:
            return payload
    return {}


def _operator_payload_from_ref(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
    request_payload: Mapping[str, Any],
) -> dict[str, Any]:
    for ref in _operator_payload_ref_candidates(dispatch, request_payload):
        payload = _read_owner_payload_ref(profile=profile, study_id=study_id, ref=ref)
        operator_payload = _operator_payload(payload)
        if operator_payload:
            return operator_payload
        target_payload = _mapping(_mapping(payload.get("payload_authoring_target")).get("operator_payload"))
        if target_payload:
            return target_payload
    return {}


def _operator_payload_ref_candidates(*dispatches: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for dispatch in dispatches:
        prompt_contract = _mapping(dispatch.get("prompt_contract"))
        handoff_packet = _mapping(dispatch.get("handoff_packet"))
        owner_pickup = _mapping(dispatch.get("owner_pickup")) or _mapping(handoff_packet.get("owner_pickup"))
        refs.extend(
            ref
            for ref in (
                _text(dispatch.get("operator_payload_ref")),
                _text(dispatch.get("medical_paper_readiness_payload_ref")),
                _text(prompt_contract.get("operator_payload_ref")),
                _text(prompt_contract.get("medical_paper_readiness_payload_ref")),
                _text(handoff_packet.get("operator_payload_ref")),
                _text(handoff_packet.get("medical_paper_readiness_payload_ref")),
                _text(owner_pickup.get("operator_payload_ref")),
                _text(owner_pickup.get("medical_paper_readiness_payload_ref")),
                _text(dispatch.get("request_packet_ref")),
                _text(prompt_contract.get("request_packet_ref")),
                _text(handoff_packet.get("request_packet_ref")),
            )
            if ref
        )
    return list(dict.fromkeys(refs))


def _read_owner_payload_ref(*, profile: WorkspaceProfile, study_id: str, ref: str) -> dict[str, Any]:
    path = Path(ref).expanduser()
    if not path.is_absolute():
        path = profile.studies_root / study_id / path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


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
