from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import medical_paper_operator_actions
from med_autoscience.controllers import medical_paper_readiness as readiness_surface
from med_autoscience.controllers import medical_paper_readiness_owner_blocker
from med_autoscience.controllers import medical_paper_readiness_payload_authoring
from med_autoscience.controllers.domain_owner_action_dispatch_parts import owner_request_paths
from med_autoscience.profiles import WorkspaceProfile

from . import medical_paper_readiness_stage_closeout


ACTION_TYPE = "complete_medical_paper_readiness_surface"
CALLABLE_SURFACE = "medical_paper_readiness.complete_medical_paper_readiness_surface"
DEFAULT_ACTION_ID_BY_SURFACE = {
    "literature_scout": "materialize_literature_scout",
    "literature_provider_runtime": "run_provider_literature_scout",
    "study_line_selection": "materialize_study_line_selection",
    "archetype_analysis_contract": "materialize_archetype_analysis_contract",
    "bounded_analysis_candidate_board": "materialize_bounded_analysis_candidate_board",
    "stop_loss_memo": "materialize_stop_loss_memo",
    "target_journal_writing_layer": "materialize_target_journal_writing_layer",
    "real_study_soak_matrix_evidence": "materialize_real_study_soak_matrix_evidence",
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
    closeout_binding = _closeout_binding(dispatch_payload)
    request_payload = _mapping(owner_request_paths.owner_request_payload(profile, study_id, ACTION_TYPE))
    current_readiness = readiness_surface.build_medical_paper_readiness_surface(study_root=study_root)
    current_surface_key = _text(_mapping(current_readiness.get("next_action")).get("surface_key"))
    declared_surface_key, declared_surface_has_currentness_binding = (
        _declared_surface_key_and_currentness_binding(
            dispatch_payload=dispatch_payload,
            request_payload=request_payload,
        )
    )
    surface_key = _current_surface_key_if_declared_surface_is_stale(
        current_readiness,
        current_surface_key=current_surface_key,
        declared_surface_key=declared_surface_key,
        declared_surface_has_currentness_binding=declared_surface_has_currentness_binding,
    ) or declared_surface_key or current_surface_key
    operator_payload = _operator_payload(dispatch_payload, surface_key=surface_key) or _operator_payload(
        request_payload,
        surface_key=surface_key,
    )
    if not operator_payload:
        operator_payload = _operator_payload_from_ref(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch_payload,
            request_payload=request_payload,
            surface_key=surface_key,
        )
    authored_payload: dict[str, Any] = {}
    if not operator_payload:
        authored_payload = medical_paper_readiness_payload_authoring.author_operator_payload(
            study_root=study_root,
            surface_key=surface_key,
            profile=profile,
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
        owner_delta_result = _owner_delta_result(
            study_id=study_id,
            study_root=study_root,
            owner_result=owner_result,
            closeout_binding=closeout_binding,
        )
        return _with_stage_native_closeout(
            _blocked(
                reason="medical_paper_readiness_surface_input_required",
                study_root=study_root,
                owner_result=owner_result,
                owner_delta_result=owner_delta_result,
            ),
            reason="medical_paper_readiness_surface_input_required",
            study_root=study_root,
            owner_result=owner_result,
            owner_delta_result=owner_delta_result,
            closeout_binding=closeout_binding,
            apply=apply,
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
        owner_delta_result = _owner_delta_result(
            study_id=study_id,
            study_root=study_root,
            owner_result=owner_result,
            closeout_binding=closeout_binding,
        )
        return _with_stage_native_closeout(
            _blocked(
                reason="medical_paper_readiness_surface_key_required",
                study_root=study_root,
                owner_result=owner_result,
                owner_delta_result=owner_delta_result,
            ),
            reason="medical_paper_readiness_surface_key_required",
            study_root=study_root,
            owner_result=owner_result,
            owner_delta_result=owner_delta_result,
            closeout_binding=closeout_binding,
            apply=apply,
        )

    action_id = _action_id(dispatch_payload, surface_key)
    operator_idempotency_key = _operator_idempotency_key(
        dispatch=dispatch_payload,
        surface_key=surface_key,
        action_id=action_id,
    )
    action_result = medical_paper_operator_actions.dispatch_guarded_medical_paper_operator_action(
        study_root=study_root,
        action_id=action_id,
        surface_key=surface_key,
        operator_payload=operator_payload,
        action_instance_id=_text(dispatch_payload.get("action_id")),
        idempotency_key=operator_idempotency_key,
        apply=apply,
    )
    readiness = (
        readiness_surface.build_medical_paper_readiness_surface(study_root=study_root)
        if apply
        else _projected_readiness_after_action(current_readiness, surface_key=surface_key, action_result=action_result)
    )
    owner_result = {
        "surface_kind": "medical_paper_readiness_surface_completion_result",
        "status": "ready" if _text(readiness.get("overall_status")) == "ready" else "blocked",
        "readiness_ref": str(readiness_surface.stable_medical_paper_readiness_path(study_root=study_root)),
        "readiness_status": _text(readiness.get("overall_status")),
        "ready_count": readiness.get("ready_count"),
        "required_count": readiness.get("required_count"),
        "completed_surface_key": surface_key,
        "guarded_operator_action_result": action_result,
        "operator_payload_authoring": authored_payload or None,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "authority_boundary": _authority_boundary(
            writes_readiness=bool(apply) and _text(action_result.get("status")) not in {"blocked", "missing"},
            writes_owner_blocker=False,
        ),
    }
    if _text(readiness.get("overall_status")) == "ready":
        owner_delta_result = _owner_delta_result(
            study_id=study_id,
            study_root=study_root,
            owner_result=owner_result,
            closeout_binding=closeout_binding,
        )
        return _with_stage_native_closeout(
            {
                "execution_status": "executed" if apply else "dry_run",
                "blocked_reason": None,
                "owner_callable_surface": CALLABLE_SURFACE,
                "owner_result": owner_result,
                "owner_delta_result": owner_delta_result,
                "quest_root": str(profile.runtime_root / study_id),
            },
            reason="medical_paper_readiness_ready",
            study_root=study_root,
            owner_result=owner_result,
            owner_delta_result=owner_delta_result,
            closeout_binding=closeout_binding,
            apply=apply,
        )
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
    owner_delta_result = _owner_delta_result(
        study_id=study_id,
        study_root=study_root,
        owner_result=owner_result,
        closeout_binding=closeout_binding,
    )
    return _with_stage_native_closeout(
        _blocked(
            reason=_text(action_result.get("missing_reason")) or "medical_paper_readiness_not_ready",
            study_root=study_root,
            owner_result=owner_result,
            owner_delta_result=owner_delta_result,
        ),
        reason=_text(action_result.get("missing_reason")) or "medical_paper_readiness_not_ready",
        study_root=study_root,
        owner_result=owner_result,
        owner_delta_result=owner_delta_result,
        closeout_binding=closeout_binding,
        apply=apply,
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


def _with_stage_native_closeout(
    payload: Mapping[str, Any],
    *,
    reason: str,
    study_root: Path,
    owner_result: Mapping[str, Any],
    owner_delta_result: Mapping[str, Any],
    closeout_binding: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    result = dict(payload)
    stage_closeout = medical_paper_readiness_stage_closeout.materialize_stage_native_owner_answer(
        study_id=_text(owner_delta_result.get("study_id")) or study_root.name,
        study_root=study_root,
        owner_result=owner_result,
        owner_delta_result=owner_delta_result,
        closeout_binding=closeout_binding,
        apply=apply,
    )
    result["stage_native_closeout"] = stage_closeout
    result["stage_native_closeout_reason"] = reason
    if _text(stage_closeout.get("status")) == "materialized":
        result["stage_native_owner_answer_ref"] = _text(stage_closeout.get("written_ref"))
        result["stage_native_terminal_outcome_kind"] = _text(stage_closeout.get("terminal_outcome_kind"))
    return result


def _projected_readiness_after_action(
    readiness: Mapping[str, Any],
    *,
    surface_key: str,
    action_result: Mapping[str, Any],
) -> dict[str, Any]:
    projected = dict(readiness)
    if _text(action_result.get("status")) in {"blocked", "missing"}:
        return projected
    surfaces = [
        {
            **dict(item),
            "status": "present",
            "missing_reason": "",
        }
        if isinstance(item, Mapping) and _text(item.get("surface_key")) == surface_key
        else dict(item)
        for item in _sequence(readiness.get("capability_surfaces"))
        if isinstance(item, Mapping)
    ]
    if surfaces:
        projected["capability_surfaces"] = surfaces
        projected["ready_count"] = sum(1 for item in surfaces if _text(item.get("status")) == "present")
        projected["next_action"] = _next_action_from_surfaces(surfaces)
        required_count = sum(1 for item in surfaces if item.get("required_for_ready") is True)
        if required_count:
            projected["required_count"] = required_count
            projected["overall_status"] = "ready" if projected["ready_count"] >= required_count else "blocked"
    return projected


def _next_action_from_surfaces(surfaces: list[dict[str, Any]]) -> dict[str, Any]:
    for item in surfaces:
        if item.get("required_for_ready") is True and _text(item.get("status")) != "present":
            surface_key = _text(item.get("surface_key"))
            spec = readiness_surface._spec_by_key(surface_key)
            return {
                "action_id": ACTION_TYPE,
                "surface_key": surface_key,
                "summary": spec["next_action_summary"],
            }
    return {
        "action_id": "continue_medical_paper_pipeline",
        "summary": "medical paper readiness surfaces complete.",
    }


def _current_surface_key_if_declared_surface_is_stale(
    readiness: Mapping[str, Any],
    *,
    current_surface_key: str | None,
    declared_surface_key: str | None,
    declared_surface_has_currentness_binding: bool,
) -> str | None:
    if not declared_surface_has_currentness_binding:
        return None
    if not current_surface_key or not declared_surface_key or current_surface_key == declared_surface_key:
        return None
    for item in _sequence(readiness.get("capability_surfaces")):
        if not isinstance(item, Mapping):
            continue
        if _text(item.get("surface_key")) != declared_surface_key:
            continue
        if _text(item.get("status")) == "present":
            return current_surface_key
        return None
    return None


def _declared_surface_key_and_currentness_binding(
    *,
    dispatch_payload: Mapping[str, Any],
    request_payload: Mapping[str, Any],
) -> tuple[str | None, bool]:
    for payload in (dispatch_payload, request_payload):
        if text := _current_owner_surface_key(payload):
            return text, _has_owner_route_currentness_binding(payload)
        if text := _surface_key(payload):
            return text, _has_owner_route_currentness_binding(payload)
    return None, False


def _has_owner_route_currentness_binding(payload: Mapping[str, Any]) -> bool:
    prompt_contract = _mapping(payload.get("prompt_contract"))
    handoff_packet = _mapping(payload.get("handoff_packet"))
    owner_pickup = _mapping(payload.get("owner_pickup")) or _mapping(handoff_packet.get("owner_pickup"))
    for item in (payload, prompt_contract, handoff_packet, owner_pickup):
        if _currentness_basis_has_identity(_mapping(item.get("owner_route_currentness_basis"))):
            return True
        if _currentness_contract_has_basis(_mapping(item.get("currentness_contract"))):
            return True
        owner_route = _mapping(item.get("owner_route"))
        if _currentness_basis_has_identity(_mapping(owner_route.get("owner_route_currentness_basis"))):
            return True
        if _currentness_contract_has_basis(_mapping(owner_route.get("currentness_contract"))):
            return True
    return False


def _currentness_contract_has_basis(contract: Mapping[str, Any]) -> bool:
    if not contract:
        return False
    return _currentness_basis_has_identity(_mapping(contract.get("basis")))


def _currentness_basis_has_identity(basis: Mapping[str, Any]) -> bool:
    if not basis:
        return False
    return bool(
        _text(basis.get("work_unit_fingerprint"))
        and (
            _text(basis.get("truth_epoch"))
            or _text(basis.get("source_eval_id"))
            or _text(basis.get("runtime_health_epoch"))
        )
    )


def _owner_delta_result(
    *,
    study_id: str,
    study_root: Path,
    owner_result: Mapping[str, Any],
    closeout_binding: Mapping[str, Any] | None = None,
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
    result = {
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
    if closeout_binding:
        binding = dict(closeout_binding)
        result["closeout_binding"] = binding
        result["stage_run_id"] = _text(binding.get("stage_run_id"))
        result["stage_manifest_ref"] = _text(binding.get("stage_manifest_ref"))
        result["current_pointer_ref"] = _text(binding.get("current_pointer_ref"))
        result["source_fingerprint"] = _text(binding.get("source_fingerprint"))
        result["idempotency_key"] = _text(binding.get("idempotency_key"))
    return result


def _closeout_binding(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    dispatch_binding = _mapping(dispatch.get("closeout_binding")) or _mapping(prompt_contract.get("closeout_binding"))
    env_binding = _env_closeout_binding()
    authorization = _mapping(dispatch.get("opl_execution_authorization")) or _mapping(
        prompt_contract.get("opl_execution_authorization")
    ) or _env_opl_execution_authorization()
    provider_attempt_ref = _first_text(
        authorization.get("provider_attempt_ref"),
        dispatch.get("provider_attempt_ref"),
        prompt_contract.get("provider_attempt_ref"),
        dispatch_binding.get("provider_attempt_ref"),
        env_binding.get("provider_attempt_ref"),
    )
    attempt_lease_ref = _first_text(
        authorization.get("attempt_lease_ref"),
        dispatch.get("attempt_lease_ref"),
        prompt_contract.get("attempt_lease_ref"),
        dispatch_binding.get("attempt_lease_ref"),
        env_binding.get("attempt_lease_ref"),
    )
    execution_authorization_decision_ref = _first_text(
        authorization.get("execution_authorization_decision_ref"),
        dispatch.get("execution_authorization_decision_ref"),
        prompt_contract.get("execution_authorization_decision_ref"),
        dispatch_binding.get("execution_authorization_decision_ref"),
        env_binding.get("execution_authorization_decision_ref"),
    )
    binding = {
        "surface_kind": _first_text(
            dispatch_binding.get("surface_kind"),
            env_binding.get("surface_kind"),
            "medical_paper_readiness_closeout_binding",
        ),
        "trusted_opl_execution_authorization": bool(
            provider_attempt_ref and attempt_lease_ref and execution_authorization_decision_ref
        ),
        "stage_run_id": _first_text(
            dispatch_binding.get("stage_run_id"),
            env_binding.get("stage_run_id"),
            dispatch.get("stage_run_id"),
            prompt_contract.get("stage_run_id"),
        ),
        "stage_run_ref": _first_text(
            dispatch_binding.get("stage_run_ref"),
            env_binding.get("stage_run_ref"),
            dispatch.get("stage_run_ref"),
            prompt_contract.get("stage_run_ref"),
        ),
        "stage_manifest_ref": _first_text(
            dispatch_binding.get("stage_manifest_ref"),
            env_binding.get("stage_manifest_ref"),
            dispatch.get("stage_manifest_ref"),
            prompt_contract.get("stage_manifest_ref"),
        ),
        "current_pointer_ref": _first_text(
            dispatch_binding.get("current_pointer_ref"),
            env_binding.get("current_pointer_ref"),
            dispatch.get("current_pointer_ref"),
            prompt_contract.get("current_pointer_ref"),
        ),
        "closeout_refs": _text_list(
            dispatch_binding.get("closeout_refs")
            or env_binding.get("closeout_refs")
            or dispatch.get("closeout_refs")
            or prompt_contract.get("closeout_refs")
        ),
        "provider_attempt_ref": provider_attempt_ref,
        "attempt_lease_ref": attempt_lease_ref,
        "attempt_lease_status": _first_text(
            authorization.get("attempt_lease_status"),
            dispatch_binding.get("attempt_lease_status"),
            env_binding.get("attempt_lease_status"),
        ),
        "execution_authorization_decision_ref": execution_authorization_decision_ref,
        "source_fingerprint": _first_text(
            dispatch_binding.get("source_fingerprint"),
            env_binding.get("source_fingerprint"),
            owner_route.get("source_fingerprint"),
            dispatch.get("source_fingerprint"),
            prompt_contract.get("source_fingerprint"),
        ),
        "work_unit_fingerprint": _first_text(
            dispatch_binding.get("work_unit_fingerprint"),
            env_binding.get("work_unit_fingerprint"),
            owner_route.get("work_unit_fingerprint"),
            dispatch.get("work_unit_fingerprint"),
            prompt_contract.get("work_unit_fingerprint"),
        ),
        "idempotency_key": _first_text(
            dispatch_binding.get("idempotency_key"),
            env_binding.get("idempotency_key"),
            authorization.get("idempotency_key"),
            owner_route.get("idempotency_key"),
            dispatch.get("idempotency_key"),
            prompt_contract.get("idempotency_key"),
        ),
    }
    required = (
        binding["stage_run_id"],
        binding["stage_manifest_ref"],
        binding["current_pointer_ref"],
        binding["source_fingerprint"],
        binding["idempotency_key"],
    )
    if not all(required):
        return {}
    return {key: value for key, value in binding.items() if value not in (None, [], "")}


def _env_opl_execution_authorization() -> dict[str, Any]:
    values = {
        "owner": "one-person-lab",
        "provider_attempt_ref": os.environ.get("OPL_PROVIDER_ATTEMPT_REF"),
        "stage_attempt_id": os.environ.get("OPL_STAGE_ATTEMPT_ID"),
        "attempt_lease_ref": os.environ.get("OPL_ATTEMPT_LEASE_REF"),
        "attempt_lease_status": os.environ.get("OPL_ATTEMPT_LEASE_STATUS"),
        "execution_authorization_decision_ref": os.environ.get(
            "OPL_EXECUTION_AUTHORIZATION_DECISION_REF"
        ),
        "source_fingerprint": os.environ.get("OPL_SOURCE_FINGERPRINT"),
        "idempotency_key": os.environ.get("OPL_IDEMPOTENCY_KEY"),
        "stage_run_id": os.environ.get("OPL_STAGE_RUN_ID"),
        "stage_manifest_ref": os.environ.get("OPL_STAGE_MANIFEST_REF"),
        "current_pointer_ref": os.environ.get("OPL_CURRENT_POINTER_REF"),
    }
    return {key: text for key, value in values.items() if (text := _text(value))}


def _env_closeout_binding() -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    if raw := _text(os.environ.get("OPL_CLOSEOUT_BINDING_JSON")):
        try:
            candidate = json.loads(raw)
            if isinstance(candidate, Mapping):
                parsed = dict(candidate)
        except json.JSONDecodeError:
            parsed = {}
    aliases = {
        "stage_run_id": os.environ.get("OPL_STAGE_RUN_ID"),
        "stage_manifest_ref": os.environ.get("OPL_STAGE_MANIFEST_REF"),
        "current_pointer_ref": os.environ.get("OPL_CURRENT_POINTER_REF"),
        "provider_attempt_ref": os.environ.get("OPL_PROVIDER_ATTEMPT_REF"),
        "attempt_lease_ref": os.environ.get("OPL_ATTEMPT_LEASE_REF"),
        "attempt_lease_status": os.environ.get("OPL_ATTEMPT_LEASE_STATUS"),
        "execution_authorization_decision_ref": os.environ.get(
            "OPL_EXECUTION_AUTHORIZATION_DECISION_REF"
        ),
        "source_fingerprint": os.environ.get("OPL_SOURCE_FINGERPRINT"),
        "idempotency_key": os.environ.get("OPL_IDEMPOTENCY_KEY"),
    }
    merged = {**parsed, **_env_opl_execution_authorization()}
    merged.update({key: text for key, value in aliases.items() if (text := _text(value))})
    return merged


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


def _operator_payload(dispatch: Mapping[str, Any], *, surface_key: str | None = None) -> dict[str, Any]:
    declared_surface_key = _declared_surface_key(dispatch)
    if surface_key and declared_surface_key and declared_surface_key != surface_key:
        return {}
    for payload in _payload_candidates(dispatch):
        payload_surface_key = _payload_surface_key(payload)
        if surface_key and payload_surface_key and payload_surface_key != surface_key:
            continue
        if payload:
            return payload
    return {}


def _operator_payload_from_ref(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
    request_payload: Mapping[str, Any],
    surface_key: str | None,
) -> dict[str, Any]:
    for ref in _operator_payload_ref_candidates(dispatch, request_payload):
        payload = _read_owner_payload_ref(profile=profile, study_id=study_id, ref=ref)
        declared_surface_key = _declared_surface_key(payload)
        if surface_key and declared_surface_key and declared_surface_key != surface_key:
            continue
        operator_payload = _operator_payload(payload, surface_key=surface_key)
        if operator_payload:
            return operator_payload
        target = _mapping(payload.get("payload_authoring_target"))
        target_payload = _mapping(target.get("operator_payload"))
        target_surface_key = _payload_surface_key(target_payload)
        if target_surface_key is None:
            target_surface_key = _text(target.get("surface_key"))
        if surface_key and target_surface_key and target_surface_key != surface_key:
            continue
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
    if text := _declared_surface_key(dispatch):
        return text
    for payload in _payload_candidates(dispatch):
        if text := _text(payload.get("surface_key")):
            return text
    return None


def _current_owner_surface_key(dispatch: Mapping[str, Any]) -> str | None:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    handoff_packet = _mapping(dispatch.get("handoff_packet"))
    owner_pickup = _mapping(dispatch.get("owner_pickup")) or _mapping(handoff_packet.get("owner_pickup"))
    for payload in (dispatch, prompt_contract, handoff_packet, owner_pickup):
        identity = _mapping(payload.get("readiness_surface_identity"))
        if _text(identity.get("source")) == "current_owner_action":
            return _text(identity.get("surface_key"))
    return None


def _payload_surface_key(payload: Mapping[str, Any]) -> str | None:
    if text := _text(payload.get("surface_key")):
        return text
    surface = _text(payload.get("surface"))
    if surface in DEFAULT_ACTION_ID_BY_SURFACE:
        return surface
    aliases = {
        "literature_intelligence_os": "literature_scout",
        "study_line_decision": "study_line_selection",
        "study_line_selection_scorecard": "study_line_selection",
        "archetype_specific_analysis_contract": "archetype_analysis_contract",
        "route_control_stoploss": "stop_loss_memo",
    }
    if surface in aliases:
        return aliases[surface]
    return None


def _declared_surface_key(dispatch: Mapping[str, Any]) -> str | None:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    handoff_packet = _mapping(dispatch.get("handoff_packet"))
    owner_pickup = _mapping(dispatch.get("owner_pickup")) or _mapping(handoff_packet.get("owner_pickup"))
    for payload in (dispatch, prompt_contract, handoff_packet, owner_pickup):
        identity = _mapping(payload.get("readiness_surface_identity"))
        if text := _text(identity.get("surface_key")):
            return text
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


def _operator_idempotency_key(*, dispatch: Mapping[str, Any], surface_key: str, action_id: str) -> str | None:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    base_key = _text(dispatch.get("idempotency_key")) or _text(prompt_contract.get("idempotency_key"))
    if not base_key:
        return None
    return f"{base_key}::surface::{surface_key}::action::{action_id}"


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


def _first_text(*values: object) -> str | None:
    for value in values:
        if text := _text(value):
            return text
    return None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


def _sequence(value: object) -> list[object]:
    if isinstance(value, list | tuple):
        return list(value)
    return []


__all__ = ["execute_complete_medical_paper_readiness_surface"]
